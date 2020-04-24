import requests


class Client():

	def __init__(self):	
		self.s = requests.Session()
		self.s.headers.update({
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
						  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
						  "/75.0.3770.100 Safari/537.36",
			'Referer':'http://localhost:19330/'
		})
		self.bases = ["https://api.napster.com/", "http://direct.rhapsody.com/"]
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

	def auth(self, email, pwd):
		data = {
			"username": email, 
			"password": pwd,
			"grant_type": "password"
		}
		headers = {
			"Authorization": "Basic TlRFd05ESTFPR1V0WTJJeU1pMDBNR05tTFdJeE1qUXRZekkyT"
							 "WpWa1lXTTBPREpoOk56YzNPRE0yWWpVdE1XWTVNQzAwWWpVMkxXSm1P"
							 "RGN0TXpZd01UYzNOR0U1WkdFMQ=="
		}
		j = self.make_call(
			"POST", "oauth/token", data=data, headers=headers
		)
		self.token = j["access_token"]

	def resolve_id(self, alb_art, alb_shcut):
		params = {
			"albumShortcut": alb_shcut,
			"artistShortcut": alb_art,
			"developerKey": "5C8F8G9G8B4D0E5J"
		}
		j = self.make_call(
			"GET", "metadata/data/methods/getIdByShortcut.js", params=params, i=1
		)
		return j['id']

	def get_track_meta(self, alb_id, lang):
		params = {
			"catalog": "JP_MORAQUALITAS",
			"lang": lang,
			"rights": 2
		}
		headers = {
			"apikey": self.key
		}
		j = self.make_call(
			"GET", "v2.2/albums/" + alb_id + "/tracks", params=params, headers=headers
		)
		return j['tracks']
		
	def get_album_meta(self, alb_id, lang):
		params = {
			"catalog": "JP_MORAQUALITAS",
			"lang": lang,
			"rights": 2
		}
		headers = {
			"apikey": self.key
		}
		j = self.make_call(
			"GET", "v2.2/albums/"+alb_id, params=params, headers=headers
		)
		return j['albums'][0]

	def get_cover(self, alb_id, dim):
		alb_cov = "{0}imageserver/v2/albums/{1}/images/{2}x{2}.jpg".format(
			self.bases[0], alb_id, dim
		)
		return alb_cov
	
	def get_track_stream(self, brate, fmt, tra_id):
		params = {
			"bitrate": brate,
			"format": fmt,
			"track": tra_id
		}
		headers = {
			"Authorization": "Bearer " + self.token
		}
		j = self.make_call(
			"GET", "v2.2/streams", params=params, headers=headers
		)
		return j['streams'][0]['url']