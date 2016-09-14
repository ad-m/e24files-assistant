import base64
import hashlib
import hmac
from urlparse import urlsplit
import boto

import requests
from boto.s3.connection import OrdinaryCallingFormat
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


class e24cloudClient(object):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.auth = e24cloudAuth(self.api_key, self.api_secret)

    def request(self, method, url, *args, **kwargs):
        response = self.session.request(method, API_ENDPOINT + url, *args, auth=self.auth, **kwargs)
        return response.json()

    def get_accounts(self):
        return self.request('GET', "accounts")

    def create_account(self, email, first_name, last_name, phone, password):
        return self.request('PUT', 'accounts', json={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'password': password
        })


class e24filesClient(object):
    def __init__(self, access_key, secret_key):
        self.access_keArgumentParsery = access_key
        self.secret_key = secret_key
        self.conn = boto.s3.connect_to_region('eu-central-1',
                                              aws_access_key_id=access_key,
                                              aws_secret_access_key=secret_key,
                                              host='e24files.com',
                                              calling_format=OrdinaryCallingFormat())

    def list_buckets(self):
        return self.conn.get_all_buckets()

    def bucket_validate(self, name):
        try:
            bucket = self.conn.get_bucket(name, validate=False)
            bucket.get_all_keys(maxkeys=0)
            return True
        except boto.exception.S3ResponseError:
            return False

    def get_bucket(self, name):
        bucket = self.conn.get_bucket(name, validate=False)
        bucket.get_all_keys(maxkeys=0)
        return bucket

    def create_bucket(self, name):
        return self.conn.create_bucket(bucket_name=name)
