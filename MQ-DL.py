#!/usr/bin/env python3

# 1st
import os
import re
import sys
import json
import argparse
import platform

# 3rd
import requests
from tqdm import tqdm
from mutagen import File
from mutagen import id3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3NoHeaderError
from requests.exceptions import HTTPError

# own
from api import client


client = client.Client()
is_win = platform.system() == "Windows"
try:
	if hasattr(sys, "frozen"):
		os.chdir(os.path.dirname(sys.executable))
	else:
		os.chdir(os.path.dirname(__file__))
except OSError:
	pass

def title():
	if is_win:
		os.system("title MQ-DL R2 (by Sorrow446)")
	else:
		sys.stdout.write("\x1b]2;MQ-DL R2 (by Sorrow446)\x07")
	print("""
 _____ _____     ____  __    
|     |     |___|    \|  |   
| | | |  |  |___|  |  |  |__ 
|_|_|_|__  _|   |____/|_____|
         |__|                
   """)
	

def err(e, _exit=False):
	print("{}: {}".format(e.__class__.__name__, e))
	if _exit:
		sys.exit(1)

def auth():
	try:
		client.auth(cfg['email'], cfg['password'])
	except HTTPError as e:
		print("Failed to login.")
		err(e, _exit=True)
	print("Signed in successfully.")

def parse_cfg():
	with open("config.json") as f:
		return json.load(f)

def read_txt(txt_abs):
	with open(txt_abs) as f:
		return [l.strip() for l in f.readlines()]

def parse_prefs():
	cfg = parse_cfg()
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-u", "--url", 
		nargs="+", required=True,
		help="Multiple links or a text file filename / abs path."
	)
	parser.add_argument(
		"-q", "--quality",
		choices=[1,2,3,4], default=cfg['quality'], type=int,
		help="1: AAC PLUS, 2: MP3, 3: AAC, 4: best/FLAC."
	)
	parser.add_argument(
		"-c", "--cover-size", 
		choices=[1,2,3,4,5], default=cfg['cover_size'], type=int,
		help="1: 70, 2: 170, 3: 300, 4: 500, 5: 600." 
	)
	parser.add_argument(
		"-t", "--template", 
		default=cfg['fname_template'],
		help="Naming template for track filenames."
	)
	parser.add_argument(
		"-k", "--keep-cover", 
		action="store_true", default=cfg['keep_cover'],
		help="Leave albums' covers in their respective folders."
	)
	parser.add_argument(
		"-o", "--output-dir", 
		default=cfg['output_dir'],
		help="Abs output directory. Double up backslashes or use single "
			 "forward slashes for Windows. Default: \MQ-DL downloads"
	)
	parser.add_argument(
		"-l", "--meta-lang",
		choices=["en-US", "ja-JP"], default=cfg['meta_language'],
		help="Metadata language."
	)
	args = vars(parser.parse_args())
	cfg.update(args)
	cfg['quality'] = {
		1: "AAC PLUS", 2: "MP3", 3: "AAC", 4: "FLAC"
	}[cfg['quality']]
	cfg['cover_size'] = {
		1: "70", 2: "170", 3: "300", 4: "500", 5: "600"
	}[cfg['cover_size']]
	if cfg['url'][0].endswith(".txt"):
		cfg['url'] = read_txt(cfg['url'][0])
	if not cfg["output_dir"]:
		cfg['output_dir'] = "MQ-DL downloads"
	return cfg

def check_url(url):
	regex = (
		r'https://content.mora-qualitas.com/artist/([a-zA-Z-\d]+)/album/'
		r'(alb.\d{9}|[a-zA-Z-\d*]+)(?:/track/(t.\d{9}|[a-zA-Z=\d]+))?'
	)
	m = re.match(regex, url)
	return m.group(1), m.group(2), m.group(3)

def resolve_id(alb_art, alb_id):
	if "." not in alb_id:
		alb_id = client.resolve_id(al_art, alb_id)
	return alb_id

def parse_meta(src, meta=None, num=None, total=None):
	# Set tracktotal / num manually in case of disked albums.
	if meta:
		meta['artist'] =  src.get('artistName')
		meta['isrc'] =  src.get('isrc')
		meta['title'] =  src.get('name')
		meta['track'] = num
		meta['track_padded'] = str(num).zfill(len(str(meta['tracktotal'])))
		#meta['track_padded'] = str(num).zfill(2)
	else:
		meta = {
			"album": src.get('name'),
			"albumartist": src.get('artistName'),
			"copyright": src.get('copyright'),
			"label": src.get('label'),
			"tracktotal": total,
			"upc": src.get('upc')
		}
		try:
			meta['year'] = src.get('originallyReleased').split('-')[0]
		except AttributeError:
			pass
	return meta

def query_quals(quals):
	parsed_quals = {}
	best_order = [
		"FLAC",
		"AAC",
		"MP3",
		"AAC PLUS"
	]
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
				"FLAC": ".flac",
				"AAC": ".m4a",
				"MP3": ".mp3",
				"AAC PLUS": ".m4a"
			}[want]
			specs = {
				"fmt": want,
				"brate": best[0],
				"bdepth": best[1], 
				"srate": best[2],
				"ext": ext
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

def parse_template(meta):
	try:
		return cfg['fname_template'].format(**meta)
	except KeyError:
		print(
			"Failed to parse filename naming template. Default one "
			"will be used instead."
		)
		return "{track_padded}. {track}".format(**meta)

def sanitize(f):
	if is_win:
		return re.sub(r'[\/:*?"><|]', '_', f)
	else:
		return re.sub('/', '_', f)

def dir_setup(d):
	if not os.path.isdir(d):
		os.makedirs(d)

def get_track(stream_url):
	r = requests.get(stream_url, stream=True, 
		headers={
			"Range": "bytes=0-",
			"User-Agent": client.s.headers['User-Agent'],
			"Referer": client.s.headers['Referer']
		}
	)
	r.raise_for_status()
	return r, int(r.headers['content-length'])

def download_track(stream_url, specs, title, num, total, pre_abs):
	if specs['fmt'] == "FLAC":
		fmtted_specs = "{}-bit / {} Hz FLAC".format(specs['bdepth'], 
													specs['srate'])
	else:
		fmtted_specs = "{} kbps {}".format(specs['brate'], specs['fmt'])
	print("Downloading track {} of {}: {} - {}".format(num, total, title, 
													   fmtted_specs)
	)
	r, size = get_track(stream_url)
	with open(pre_abs, 'wb') as f:
		with tqdm(total=size, unit='B',
			unit_scale=True, unit_divisor=1024,
			initial=0, miniters=1) as bar:
				for chunk in r.iter_content(32*1024):
					if chunk:
						f.write(chunk)
						bar.update(len(chunk))

def write_tags(pre_abs, meta, fmt, cov_abs):
	if fmt == "FLAC":
		audio = FLAC(pre_abs)
		del meta['track_padded']
		for k, v in meta.items():
			if v:
				audio[k] = str(v)
		if cov_abs:
			with open(cov_abs, "rb") as f:
				image = Picture()
				image.type = 3
				image.mime = "image/jpeg"
				image.data = f.read()
				audio.add_picture(image)
	elif fmt == "MP3":
		try: 
			audio = id3.ID3(pre_abs)
		except ID3NoHeaderError:
			audio = id3.ID3()
		audio['TRCK'] = id3.TRCK(
			encoding=3, text="{}/{}".format(meta['track'], meta['tracktotal'])
		)
		legend={
			"album": id3.TALB,
			"albumartist": id3.TPE2,
			"artist": id3.TPE1,
			#"comment": id3.COMM,
			"copyright": id3.TCOP,
			"isrc": id3.TSRC,
			"label": id3.TPUB,
			"title": id3.TIT2,
			"year": id3.TYER
		}
		for k, v in meta.items():
			id3tag = legend.get(k)
			if v and id3tag:
				audio[id3tag.__name__] = id3tag(encoding=3, text=v)
		if cov_abs:
			with open(cov_abs, "rb") as cov_obj:
				audio.add(id3.APIC(3, "image/jpeg", 3, None, cov_obj.read()))
	else:
		audio = MP4(pre_abs)
		audio['\xa9nam'] = meta['title']
		audio['\xa9alb'] = meta['album']
		audio['aART'] = meta['albumartist']
		audio['\xa9ART'] = meta['artist']
		audio['trkn'] = [(meta['track'], meta['tracktotal'])]
		audio['\xa9day'] = meta['year']
		audio['cprt'] = meta['copyright']
		if cov_abs:
			with open(cov_abs, "rb") as f:
				audio['covr'] = [MP4Cover(f.read(), imageformat = MP4Cover.FORMAT_JPEG)]
	audio.save(pre_abs)

def download_cov(alb_id, cov_abs):
	url = client.get_cover(alb_id, cfg['cover_size'])
	r = requests.get(url,
		headers={
			"User-Agent": client.s.headers['User-Agent'],
			"Referer": client.s.headers['Referer']
		}
	)
	r.raise_for_status()
	with open(cov_abs, 'wb') as f:
		f.write(r.content)
	
def main(alb_id, tra_id):
	alb_src_meta = client.get_album_meta(alb_id, cfg['meta_lang'])
	tra_src_meta = client.get_track_meta(alb_id, cfg['meta_lang'])
	total = len(tra_src_meta)
	alb_meta = parse_meta(alb_src_meta, total=total)
	alb_fol = "{} - {}".format(alb_meta['albumartist'], alb_meta['album'])
	alb_abs = os.path.join(cfg['output_dir'], sanitize(alb_fol))
	cov_abs = os.path.join(alb_abs, "cover.jpg")
	dir_setup(alb_abs)
	print(alb_fol)
	for num, track in enumerate(tra_src_meta, 1):
		if not track['isStreamable']:
			print("Track isn't allowed to be streamed.")
			continue
		specs = query_quals(track['formats'] + track['losslessFormats'])
		meta = parse_meta(track, meta=alb_meta, num=num)
		pre_abs = os.path.join(alb_abs, str(num) + ".mq-dl")
		post_abs = os.path.join(alb_abs, sanitize(parse_template(meta)) + specs['ext'])
		if os.path.isfile(post_abs):
			print("Track already exists locally.")
			continue
		stream_url = client.get_track_stream(specs['brate'], specs['fmt'], 
											 track['id'])
		download_track(stream_url, specs, meta['title'], num, total, pre_abs)
		try:
			download_cov(alb_id, cov_abs)
		except HTTPError as e:
			print("Failed to get cover.")
			err(e)
			cov_abs = None
		write_tags(pre_abs, meta, specs['fmt'], cov_abs)
		try:
			os.rename(pre_abs, post_abs)
		except OSError as e:
			print("Failed to rename track.")
			err(e)
		if cov_abs and not cfg['keep_cover']:
			os.remove(cov_abs)

if __name__ == "__main__":
	title()
	cfg = parse_prefs()
	auth()
	total = len(cfg['url'])
	for num, url in enumerate(cfg['url'], 1):
		print("\nAlbum {} of {}:".format(num, total))
		try:
			alb_art, alb_id, tra_id = check_url(url)
		except AttributeError:
			print("Invalid url:", url)
			continue
		alb_id = resolve_id(alb_art, alb_id)
		try:
			main(alb_id, tra_id)
		except Exception as e:
			print("Album failed.")
			err(e)
