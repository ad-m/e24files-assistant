#!/bin/bash
import argparse
import ConfigParser
import csv
import sys

import boto
from api import e24filesClient, e24cloudClient
from config import get_access_pair


def build_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", nargs='?', type=argparse.FileType('r'),
                        help="INI-file with secret keys")
    parser.add_argument("--output", '-o', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, help="Output file")

    return parser.parse_args()


def fetch_data(writer, panel_client, files_client):
    buckets = files_client.list_buckets()

    writer.writerow([''] + [bucket.name.encode('utf-8') for bucket in buckets])

    for user in panel_client.get_accounts()['users']:
        user_client = e24filesClient(access_key=user['e24files']['s3']['api_id'],
                                     secret_key=user['e24files']['s3']['secret_key'])
        try:
            user_client.list_buckets()
        except boto.exception.S3ResponseError:
            row = ["SUSPENDED", ]
        else:
            row = [user_client.bucket_validate(bucket.name) for bucket in buckets]
        writer.writerow([user['name'].encode('utf-8'), ] + row)


def main():
    args = build_args()

    config = ConfigParser.ConfigParser()
    config.readfp(args.config)

    panel_client = e24cloudClient(*get_access_pair(config, 'panel'))
    files_client = e24filesClient(*get_access_pair(config, 'files'))

    writer = csv.writer(args.output)

    fetch_data(writer, panel_client, files_client)


if __name__ == "__main__":
    main()
