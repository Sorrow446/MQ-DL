import requests


class Client():

	def __init__(self):	
		self.s = requests.Session()
		self.s.headers.update({
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
						  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
						  '/75.0.3770.100 Safari/537.36',
			'Referer':'http://localhost:19330/'
		})
		self.bases = ['https://api.napster.com/', 'http://direct.rhapsody.com/']
		self.key = "NTEwNDI1OGUtY2IyMi00MGNmLWIxMjQtYzI2MjVkYWM0ODJh"

	def make_call(self, method, epoint, data=None, params=None, headers=None, i=0):
		if headers:
			self.s.headers.update(headers)
		r = self.s.request(method, self.bases[i] + epoint, params=params, data=data)
		r.raise_for_status()
		if headers:
			for k in headers.keys():
				del self.s.headers[k]
		return r.json()

	def auth(self, email, pwd, lang):
		data = {
			'username': email, 
			'password': pwd,
			'grant_type': 'password'
		}
		headers = {
			'Authorization': 'Basic TlRFd05ESTFPR1V0WTJJeU1pMDBNR05tTFdJeE1qUXRZekkyT'
							 'WpWa1lXTTBPREpoOk56YzNPRE0yWWpVdE1XWTVNQzAwWWpVMkxXSm1P'
							 'RGN0TXpZd01UYzNOR0U1WkdFMQ=='
		}
		j = self.make_call(
			'POST', 'oauth/token', data=data, headers=headers)
		self.token = j['access_token']
		self.guid = j['guid']
		self.lang = lang

	def resolve_id(self, alb_art_shcut, alb_shcut=None, tra_shcut=None):
		params = {
			'albumShortcut': alb_shcut,
			'artistShortcut': alb_art_shcut,
			'trackShortcut': tra_shcut,
			'developerKey': '5C8F8G9G8B4D0E5J'
		}
		j = self.make_call(
			'GET', 'metadata/data/methods/getIdByShortcut.js', params=params, i=1)
		return j['id']

	def get_alb_meta(self, alb_id):
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'rights': 2
		}
		headers = {
			'apikey': self.key
		}
		j = self.make_call(
			'GET', "v2.2/albums/" + alb_id, params=params, headers=headers)
		return j['albums'][0]

	def get_art_meta(self, art_id):
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'rights': 2
		}
		headers = {
			'apikey': self.key
		}
		j = self.make_call(
			'GET', "v2.2/artists/" + art_id, params=params, headers=headers)
		return j['artists'][0]

	def get_favs_meta(self):
		favs_meta = []
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'user': self.guid,
			'filter': 'track',
			'rights': 2,
			'limit': 25,
			'offset': 0
		}
		headers = {
			'apikey': self.key,
			'Authorization': "Bearer " + self.token
		}
		while True:
			j = self.make_call(
				'GET', 'v2.2/me/favorites', params=params, headers=headers)
			if j['meta']['returnedCount'] == 0:
				break
			favs_meta.append(j['favorites']['data']['tracks'])
			params['offset'] += 25
		return favs_meta[0]

	def get_alb_tra_meta(self, alb_id):
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'rights': 2
		}
		headers = {
			'apikey': self.key
		}
		j = self.make_call(
			'GET', "v2.2/albums/" + alb_id + "/tracks", params=params, headers=headers)
		return j['tracks']

	def get_tra_meta(self, tra_id):
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'rights': 2
		}
		headers = {
			'apikey': self.key
		}
		j = self.make_call(
			'GET', "v2.2/tracks/" + tra_id, params=params, headers=headers)
		return j['tracks'][0]

	def get_plist_meta(self, plist_id):
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'user': self.guid,
			'rights': 2
		}
		headers = {
			'apikey': self.key,
			'Authorization': "Bearer " + self.token
		}
		j = self.make_call(
			'GET', "v2.2/me/library/playlists/" + plist_id, params=params, headers=headers)
		return j['playlists']

	def get_plist_tra_meta(self, plist_id):
		plist_meta = []
		params = {
			'catalog': 'JP_MORAQUALITAS',
			'lang': self.lang,
			'user': self.guid,
			'filter': 'track',
			'rights': 2,
			'limit': 25,
			'offset': 0
		}
		headers = {
			'apikey': self.key,
			'Authorization': "Bearer " + self.token
		}

		while True:
			j = self.make_call(
				'GET', "v2.2/playlists/" + plist_id + "/tracks", params=params, headers=headers)
			if j['meta']['returnedCount'] == 0:
				break
			plist_meta.append(j['tracks'])
			params['offset'] += 25
		return plist_meta[0]		
		
	def get_cover(self, alb_id, dim):
		alb_cov = "{0}imageserver/v2/albums/{1}/images/{2}x{2}.jpg".format(
			self.bases[0], alb_id, dim)
		return alb_cov

	def get_tra_stream(self, brate, fmt, tra_id):
		params = {
			'bitrate': brate,
			'format': fmt,
			'track': tra_id
		}
		headers = {
			'Authorization': 'Bearer ' + self.token
		}
		j = self.make_call(
			'GET', 'v2.2/streams', params=params, headers=headers)
		return j['streams'][0]['url']
