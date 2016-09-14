import argparse
import ConfigParser
import random
import string
import time

from api import e24cloudClient, e24filesClient
from config import get_access_pair


def random_string(N):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


def build_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", nargs='?', type=argparse.FileType('r'),
                        help="INI-file with secret keys")
    parser.add_argument("bucket_name", nargs='?', help="Bucket to create")
    parser.add_argument('--user', action='store_true', help='Allow assign existing bucket')
    parser.add_argument('--name', help="Name of account visible in ")
    return parser.parse_args()


def display_user(bucket_name, user):
    print "\n[user]"
    print "first_name = %s" % (user['name'], )
    print "email = %s" % (user['email'], )
    print "id = %s" % (user['id'], )
    print "\n[ftp]"
    print "host = ftpgw.e24files.com/%s" % (bucket_name, )
    print "username = %s" % (user['e24files']['swift']['api_id'], )
    print "password = %s" % (user['e24files']['swift']['secret_key'],)

    print "\n[sftp]"
    print "host = sftpgw.e24files.com/%s " % (bucket_name, )
    print "username = %s" % (user['e24files']['swift']['api_id'], )
    print "password = %s" % (user['e24files']['swift']['secret_key'],)

    print "\n[s3]"
    print "endpoint = https://e24files.com"
    print "access_key = %s" % (user['e24files']['s3']['api_id'], )
    print "secret_key = %s" % (user['e24files']['s3']['secret_key'], )

    print "\n[swift]"
    print "url = https://e24files.com/auth"
    print "access_key = %s" % (user['e24files']['swift']['api_id'], )
    print "secret_key = %s" % (user['e24files']['swift']['secret_key'], )

    for api in user['api']:
        print "\n[panel]"
        print "access_key = %s" % (api['api_key'],)
        print "secret_key = %s" % (api['secret_key'],)

    print "\n[duply config example]"
    print "TARGET='s3://%s:%s@%s'" % (user['e24files']['swift']['api_id'],
                                      user['e24files']['swift']['secret_key'],
                                      bucket_name, )

    print ""


def main():
    args = build_args()

    config = ConfigParser.ConfigParser()
    config.readfp(args.config)

    panel_client = e24cloudClient(*get_access_pair(config, 'panel'))
    files_client = e24filesClient(*get_access_pair(config, 'files'))

    if files_client.bucket_validate(args.bucket_name) and not args.user:
        print "ERROR: Bucket name are used. " + \
              "Use --user to assign existing bucket"
        return

    first_name = args.name
    if not first_name:
        first_name = "Bucket user" if args.user else "Bucket owner"

    user = panel_client.create_account(email=random_string(50) + "@example.com",
                                       first_name=first_name,
                                       last_name=args.bucket_name,
                                       phone=123456789,
                                       password=random_string(75))

    retry_limit = 5
    while ('e24files' not in user or not user['e24files']) and retry_limit:
        user = next((x for x in panel_client.get_accounts()['users']
                     if x['id'] == user['user']['id']), None)
        time.sleep(5)
        retry_limit -= 1

    if not user:
        print "ERROR: Unable to download API-keys."
        return

    display_user(args.bucket_name, user)

    if args.user:
        bucket = files_client.get_bucket(args.bucket_name)
        print "OK: Bucket got!"
    else:
        bucket = files_client.create_bucket(args.bucket_name)
        print "OK: Bucket created!"
    bucket.add_user_grant('FULL_CONTROL', user['id'])
    print "SUCCESS: Permission granted!"


if __name__ == "__main__":
    main()
