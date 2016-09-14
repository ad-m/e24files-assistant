import base64
import hashlib
import hmac
from urlparse import urlsplit
import requests
from api import API_ACCESS_KEY, API_SECRET_KEY
from email.utils import formatdate
from requests.auth import AuthBase

API_ENDPOINT = "https://eu-poland-1poznan.api.e24cloud.com/v2/"


class e24cloudAuth(AuthBase):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def signature(self, msg):
        digest = hmac.new(self.api_secret, msg=msg, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode()
        return signature

    def auth_string(self, date, request):
        parse_result = urlsplit(request.url)
        query = "?" + parse_result.query if parse_result.query else ''
        params = [request.method,
                  parse_result.netloc or '',
                  date,
                  (parse_result.path or '' + query),
                  request.body or '']
        signature = self.signature("\n".join(params))
        return "%s:%s" % (self.api_key, signature)

    def __call__(self, r):
        date = formatdate(timeval=None, localtime=False, usegmt=True)
        r.headers['Content-Type'] = 'application/json'
        r.headers['X-Date'] = date
        r.headers['Authorization'] = self.auth_string(date, r)
        return r


print requests.get(API_ENDPOINT + "regions",
                   auth=e24cloudAuth(API_ACCESS_KEY, API_SECRET_KEY)).json()
