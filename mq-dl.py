#!/usr/bin/env python3
import os
import re
import sys
import json
import argparse
import platform
import traceback

import requests
from tqdm import tqdm
from mutagen import File
from mutagen import id3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3NoHeaderError
from requests.exceptions import HTTPError

from api import client


def err(msg):
	print(msg)
	traceback.print_exc()

def auth(email, pwd, lang):
	try:
		client.auth(email, pwd, lang)
	except HTTPError:
		err('Failed to login.')
		sys.exit(1)
	print('Signed in successfully.')

def parse_cfg():
	with open('config.json') as f:
		return json.load(f)

def read_txt(txt_path):
	with open(txt_path) as f:
		return f.readlines()

def process_urls(urls):
	all_fixed = []
	txt_paths = []
	fix = lambda x : x.strip().split('?type')[0]
	for url in urls:
		if url.endswith('.txt'):
			if url in txt_paths:
				continue
			for txt_url in read_txt(url):
				fixed = fix(txt_url)
				if not fixed in all_fixed:
					all_fixed.append(fixed)
			txt_paths.append(url)
		else:
			fixed = fix(url)
			if not fixed in all_fixed:
				all_fixed.append(fixed)
	return all_fixed

def process_cfg(cfg):
	cfg['meta_lang'] = {1: 'en-US', 2: 'ja-JP'}[cfg['meta_lang']]
	cfg['quality'] = {
		1: 'AAC PLUS', 2: 'MP3', 3: 'AAC', 4: 'FLAC'}[cfg['quality']]	
	cfg['cover_size'] = {
		1: '70', 2: '170', 3: '300', 4: '500', 5: '600'}[cfg['cover_size']]
	if (cfg['media_types']['artist']['albums'] == False and
		cfg['media_types']['artist']['compilations'] == False and
		cfg['media_types']['artist']['singles_and_eps'] == False):
			raise ValueError('All artists values cannot be false.')
	cfg['media_types']['artist']['main'] = cfg['media_types']['artist']['albums']
	cfg['media_types']['artist']['singlesAndEPs'] = cfg['media_types']['artist']['singles_and_eps']
	del cfg['media_types']['artist']['albums']
	del cfg['media_types']['artist']['singles_and_eps']
	if not cfg["output_dir"]:
		cfg['output_dir'] = "MQ-DL downloads"
	cfg['urls'] = process_urls(cfg['urls'])
	return cfg

def resolve_ids(match, groups_len):
	alb_art = None
	alb_shcut = None
	tra_shcut = None
	if groups_len == 1:
		alb_art = match.group(1)
	elif groups_len == 2:
		alb_art = match.group(1)
		alb_shcut = match.group(2)
	elif groups_len == 3:
		alb_art = match.group(1)
		alb_shcut = match.group(2)
		tra_shcut = match.group(3)
	return client.resolve_id(alb_art, alb_shcut=alb_shcut, tra_shcut=tra_shcut)

def get_artist_meta(art_id):
	alb_ids = []
	art_meta = client.get_art_meta(art_id)
	if not art_meta.get('albumGroups'):
		return art_meta['name'], None
	for k, v in cfg['media_types']['artist'].items():
		if v:
			try:
				alb_ids.extend(art_meta['albumGroups'][k])
			except KeyError:
				pass
	return art_meta['name'], alb_ids

def parse_prefs():
	cfg = parse_cfg()
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-u', '--urls', 
		nargs='+', required=True,
		help='Multiple links seperated by spaces or a text file path.'
	)
	parser.add_argument(
		'-q', '--quality',
		choices=[1, 2, 3, 4], default=cfg['quality'], type=int,
		help='1: AAC PLUS, 2: MP3, 3: AAC, 4: best/FLAC.'
	)
	parser.add_argument(
		'-c', '--cover-size', 
		choices=[1, 2, 3, 4 ,5], default=cfg['cover_size'], type=int,
		help='1: 70, 2: 170, 3: 300, 4: 500, 5: 600.' 
	)
	parser.add_argument(
		'-t', '--template', 
		default=cfg['fname_template'],
		help='Naming template for track filenames.'
	)
	parser.add_argument(
		'-k', '--keep-cover', 
		action='store_true', default=cfg['keep_cover'],
		help='Keep cover in album folder. Does not apply to playlists or favourites.'
	)
	parser.add_argument(
		'-o', '--output-dir',
		default=cfg['output_dir'],
		help='Output directory. Double up backslashes or use single '
			 'forward slashes for Windows. Default: \MQ-DL downloads'
	)
	parser.add_argument(
		'-l', '--meta-lang',
		choices=[1, 2], type=int, default=cfg['meta_language'],
		help='Metadata language. 1 = English, 2 = Japanese.'
	)
	args = vars(parser.parse_args())
	cfg.update(args)
	cfg = process_cfg(cfg)
	return cfg

def check_url(url):
	url_types = [
		# regex | url type | at least one resolve needed
		(r'https://content.mora-qualitas.com/members/[a-zA-Z-\d]+/favorites$', 'favourites', False),
		(r'https://content.mora-qualitas.com/favorites$', 'favourites', False),
		(r'https://content.mora-qualitas.com/\?id=(alb.\d+)$', 'album', False),
		(r'https://content.mora-qualitas.com/artist/(art.\d+)$', 'artist', False),
		(r'https://content.mora-qualitas.com/artist/([a-zA-Z-\d]+)$', 'artist', True),
		(r'https://content.mora-qualitas.com/artist/([a-zA-Z-\d]+)/album/([a-zA-Z-\d*]+)$', 'album', True),
		(r'https://content.mora-qualitas.com/artist/(art.\d+)/album/(alb.\d+)$', 'album', False),
		(r'https://content.mora-qualitas.com/artist/([a-zA-Z-\d]+)/album/([a-zA-Z-\d*]+)/track/([A-Za-z\d-]+)$', 'track', True),
		(r'https://content.mora-qualitas.com/\?id=(tra.\d+)$', 'track', False),
		(r'https://content.mora-qualitas.com/artist/([a-zA-Z-\d]+)/album/([a-zA-Z-\d*]+)/track/(t.\d+)$', 'track', True),
		(r'https://content.mora-qualitas.com/playlist/(mp.\d+)$', 'usr_playlist', False),
		(r'https://content.mora-qualitas.com/playlist/(pp\.\d+)$', 'playlist', False)
	]
	for url_type in url_types:
		match = re.match(url_type[0], url, re.IGNORECASE)
		if not match:
			continue
		groups_len = len(match.groups())
		if url_type[2] == True:
			_id = resolve_ids(match, groups_len)
		else:
			if groups_len == 0:
				_id = None
			else:
				_id = match.group(groups_len)
		media_type = url_type[1]
		break
	if match:
		return media_type, _id
	else:
		return None, None

def parse_meta(src, meta=None, num=None, total=None):
	# Set tracktotal / num manually in case of disked albums.
	if meta:
		meta['artist'] =  src.get('artistName')
		meta['isrc'] =  src.get('isrc')
		meta['title'] =  src.get('name')
		meta['track'] = num
		meta['trackpadded'] = str(num).zfill(len(str(meta['tracktotal'])))
	else:
		meta = {
			'album': src.get('name'),
			'albumartist': src.get('artistName'),
			'copyright': src.get('copyright'),
			'label': src.get('label'),
			'tracktotal': total,
			'upc': src.get('upc')
		}
		try:
			meta['year'] = src.get('originallyReleased').split('-')[0]
		except AttributeError:
			meta['year'] = None
	return meta

def query_quals(quals):
	parsed_quals = {}
	best_order = ['FLAC', 'AAC', 'MP3', 'AAC PLUS']
	want = cfg['quality']
	orig_want = want
	for q in quals:
		parsed_quals.setdefault(q['name'], []).extend(
			[(q['bitrate'], q['sampleBits'], q['sampleRate'])]
		)		
	while True:
		if parsed_quals[want]:
			best = max(parsed_quals[want])
			ext = {
				'FLAC': '.flac',
				'AAC': '.m4a',
				'MP3': '.mp3',
				'AAC PLUS': '.m4a'
			}[want]
			specs = {
				'fmt': want,
				'brate': best[0],
				'bdepth': best[1], 
				'srate': best[2],
				'ext': ext
			}
			break
		else:
			want = best_order[best_order.index(want)+1]
	if orig_want != want:
		print(
			"Unavailable in your chosen quality. {} will be used "
			"instead.".format(want)
		)
	return specs

def parse_template(meta, unparsed, default):
	try:
		parsed = unparsed.format(**meta)
	except KeyError:
		print('Failed to parse template. Default one will be used instead.')
		parsed = default.format(**meta)
	return sanitize(parsed)

def sanitize(f):
	if is_win:
		return re.sub(r'[\/:*?"><|]', '_', f)
	else:
		return re.sub('/', '_', f)

def dir_setup(path):
	if not os.path.isdir(path):
		os.makedirs(path)

def get_track(stream_url):
	r = requests.get(stream_url, stream=True, 
		headers={
			'Range': 'bytes=0-',
			'User-Agent': client.s.headers['User-Agent'],
			'Referer': client.s.headers['Referer']
		}
	)
	r.raise_for_status()
	return r, int(r.headers['content-length'])

def download_track(stream_url, specs, title, num, total, pre_path):
	if specs['fmt'] == "FLAC":
		fmtted_specs = "{}-bit / {} Hz FLAC".format(specs['bdepth'], 
													specs['srate'])
	else:
		fmtted_specs = "{} kbps {}".format(specs['brate'], specs['fmt'])
	print("Downloading track {} of {}: {} - {}".format(num, total, title, 
													   fmtted_specs)
	)
	r, size = get_track(stream_url)
	with open(pre_path, 'wb') as f:
		with tqdm(total=size, unit='B', unit_scale=True, unit_divisor=1024) as bar:
			for chunk in r.iter_content(32*1024):
				if chunk:
					f.write(chunk)
					bar.update(len(chunk))

def write_tags(pre_path, meta, fmt, cov_path):
	if fmt == "FLAC":
		audio = FLAC(pre_path)
		del meta['trackpadded']
		for k, v in meta.items():
			if v:
				audio[k] = str(v)
		if cov_path:
			with open(cov_path, 'rb') as f:
				image = Picture()
				image.type = 3
				image.mime = "image/jpeg"
				image.data = f.read()
				audio.add_picture(image)
	elif fmt == "MP3":
		try: 
			audio = id3.ID3(pre_path)
		except ID3NoHeaderError:
			audio = id3.ID3()
		audio['TRCK'] = id3.TRCK(
			encoding=3, text="{}/{}".format(meta['track'], meta['tracktotal'])
		)
		legend={
			'album': id3.TALB,
			'albumartist': id3.TPE2,
			'artist': id3.TPE1,
			#"comment": id3.COMM,
			'copyright': id3.TCOP,
			'isrc': id3.TSRC,
			'label': id3.TPUB,
			'title': id3.TIT2,
			'year': id3.TYER
		}
		for k, v in meta.items():
			id3tag = legend.get(k)
			if v and id3tag:
				audio[id3tag.__name__] = id3tag(encoding=3, text=v)
		if cov_path:
			with open(cov_path, 'rb') as f:
				audio.add(id3.APIC(3, 'image/jpeg', 3, None, f.read()))
	else:
		audio = MP4(pre_path)
		audio['\xa9nam'] = meta['title']
		audio['\xa9alb'] = meta['album']
		audio['aART'] = meta['albumartist']
		audio['\xa9ART'] = meta['artist']
		audio['trkn'] = [(meta['track'], meta['tracktotal'])]
		audio['\xa9day'] = meta['year']
		audio['cprt'] = meta['copyright']
		if cov_path:
			with open(cov_path, "rb") as f:
				audio['covr'] = [MP4Cover(f.read(), imageformat = MP4Cover.FORMAT_JPEG)]
	audio.save(pre_path)

def write_cov(alb_id, cov_path):
	url = client.get_cover(alb_id, cfg['cover_size'])
	r = requests.get(url,
		headers={
			'User-Agent': client.s.headers['User-Agent'],
			'Referer': client.s.headers['Referer']
		}
	)
	r.raise_for_status()
	with open(cov_path, 'wb') as f:
		f.write(r.content)

def iter_track(tra_src_meta, alb_path, total, cov_path, alb_id=None, cov=True, alb_meta=None, n=-1):
	for num, track in enumerate(tra_src_meta, 1):
		if n == -1:
			print("Track {} of {}:".format(num, total))
		else:
			#print("Track 1 of 1:")
			num = n
		try:
			if track['isStreamable'] == False:
				print('Track isn\'t allowed to be streamed.')
				continue
			specs = query_quals(track['formats'] + track['losslessFormats'])
			if alb_meta == None:
				alb_id = track['albumId']
				alb_src_meta = client.get_alb_meta(alb_id)
				alb_meta = parse_meta(alb_src_meta, total=total)
			meta = parse_meta(track, meta=alb_meta, num=num)
			pre_path = os.path.join(alb_path, str(num) + ".mq-dl")
			template = parse_template(meta, cfg['fname_template'], '{trackpadded}. {title}')
			post_path = os.path.join(alb_path, template) + specs['ext']
			if os.path.isfile(post_path):
				print('Track already exists locally.')
				continue
			stream_url = client.get_tra_stream(specs['brate'], specs['fmt'], 
												 track['id'])
			if n != -1:
				num = 1
			download_track(stream_url, specs, meta['title'], num, total, pre_path)
			try:
				write_cov(alb_id, cov_path)
			except HTTPError:
				err('Failed to get cover.')
				cov_path = None
			except OSError:
				err('Failed to write cover.')
				cov_path = None
			write_tags(pre_path, meta, specs['fmt'], cov_path)
			try:
				os.rename(pre_path, post_path)
			except OSError:
				err('Failed to rename track.')
			if cov_path != None:
				if cov == False or cfg['keep_cover'] == False:
					os.remove(cov_path)
		except Exception:
			err('Track failed.')

def album(alb_id, template=''):
	alb_src_meta = client.get_alb_meta(alb_id)
	tra_src_meta = client.get_alb_tra_meta(alb_id)
	total = len(tra_src_meta)
	alb_meta = parse_meta(alb_src_meta, total=total)
	if not template:
		template = parse_template(
			alb_meta, cfg['media_types']['album']['folder_template'], '{albumartist} - {album}')
	alb_fol = "{} - {}".format(alb_meta['albumartist'], alb_meta['album'])
	alb_path = os.path.join(cfg['output_dir'], template, sanitize(alb_fol))
	cov_path = os.path.join(alb_path, 'cover.jpg')
	dir_setup(alb_path)
	print(alb_fol)
	iter_track(tra_src_meta, alb_path, total, cov_path, alb_id=alb_id, alb_meta=alb_meta)

def artist(art_id):
	artist, art_ids = get_artist_meta(art_id)
	print(artist)
	if art_ids == None:
		print("Artist either doesn't have any albums or they have been filtered out.")
		return
	template = parse_template(
		{'artist': artist}, cfg['media_types']['artist']['folder_template'], '{artist} discography')
	total = len(art_ids)
	for num, art_id in enumerate(art_ids, 1):
		print("Album {} of {}:".format(num, total))
		try:
			album(art_id, template=template)
		except Exception:
			err('Album failed.')

def favourites(_):
	favs_src_meta = client.get_favs_meta()
	total = len(favs_src_meta)
	favs_path = os.path.join(cfg['output_dir'], sanitize(cfg['media_types']['favourites']['folder_name']))
	cov_path = os.path.join(favs_path, 'cover.jpg')
	dir_setup(favs_path)
	print('Favourites')
	iter_track(favs_src_meta, favs_path, total, cov_path, cov=False)

def track(tra_id):
	tra_src_meta = client.get_tra_meta(tra_id)
	alb_src_meta = client.get_alb_meta(tra_src_meta['albumId'])
	alb_tra_src_meta = client.get_alb_tra_meta(tra_src_meta['albumId'])
	for num, track in enumerate(alb_tra_src_meta, 1):
		if track['id'].lower() == tra_id.lower():
			alb_tra_src_meta = track
			track_num = num
	total = alb_src_meta['trackCount']
	alb_meta = parse_meta(alb_src_meta, total=total)
	print("{} - {}".format(tra_src_meta['artistName'], tra_src_meta['name']))
	template = parse_template(
		alb_meta, cfg['media_types']['track']['folder_template'], '{albumartist} - {album}')
	tra_path = os.path.join(cfg['output_dir'], template)
	cov_path = os.path.join(tra_path, 'cover.jpg')
	dir_setup(tra_path)
	iter_track([tra_src_meta], tra_path, 1, cov_path, alb_id=tra_src_meta['albumId'], alb_meta=alb_meta, n=track_num)

def playlist(plist_id, key='playlist'):
	plist_src_meta = client.get_plist_meta(plist_id)
	if len(plist_src_meta) == 0:
		print('Playlist does not exist.')
		return
	plist_src_meta = plist_src_meta[0]
	total = plist_src_meta['trackCount']
	if total == 0:
		print('Playlist does not contain any tracks.')
		return	
	print(plist_src_meta['name'])
	template_dict = {'id': plist_src_meta['id'], 'name': plist_src_meta['name']}
	template = parse_template(template_dict, 
		cfg['media_types'][key]['folder_template'], '{name}_{id}')
	plist_path = os.path.join(cfg['output_dir'], template)
	cov_path = os.path.join(plist_path, 'cover.jpg')
	dir_setup(plist_path)
	plist_tra_src_meta = client.get_plist_tra_meta(plist_id)
	iter_track(plist_tra_src_meta, plist_path, total, cov_path, cov=False)

def usr_playlist(plist_id):
	playlist(plist_id, key='user_playlist')

def main(media_type, _id):
	globals()[media_type](_id)

if __name__ == "__main__":
	client = client.Client()
	is_win = platform.system() == "Windows"
	try:
		if hasattr(sys, 'frozen'):
			os.chdir(os.path.dirname(sys.executable))
		else:
			os.chdir(os.path.dirname(__file__))
	except OSError:
		pass
	print('''
 _____ _____     ____  __    
|     |     |___|    \|  |   
| | | |  |  |___|  |  |  |__ 
|_|_|_|__  _|   |____/|_____|
	 |__|                
''')
	cfg = parse_prefs()
	auth(cfg['email'], cfg['password'], cfg['meta_lang'])
	total = len(cfg['urls'])
	for num, url in enumerate(cfg['urls'], 1):
		print("\nItem {} of {}:".format(num, total))
		media_type, _id = check_url(url)
		if media_type == None:
			print("Invalid URL:", url)
			continue
		try:
			main(media_type, _id)
		except KeyboardInterrupt:
			sys.exit()
		except Exception:
			err('Item failed.')
