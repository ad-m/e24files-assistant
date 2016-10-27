from __future__ import print_function

import argparse
from datetime import date, datetime, timedelta
from decimal import Decimal
from pprint import pprint

import pygal
import requests


class Client(object):
    LOGIN_URL = 'https://panel.e24cloud.com/login/check'
    HISTORY_URL = "https://panel.e24cloud.com/payments/history/"

    def __init__(self, session=None):
        self.session = session or requests.Session()

    def login(self, email, password):
        resp = self.session.post(self.LOGIN_URL,
                                 data={'email': email, 'password': password},
                                 headers={'Referer': 'https://panel.e24cloud.com'})
        json = resp.json()
        return json['status'] == 1

    def payments_history(self, date_from, date_to):
        resp = self.session.get(self.HISTORY_URL,
                                params={'from': date_from.strftime("%Y-%m-%d"),
                                        'to': date_to.strftime("%Y-%m-%d"),
                                        'format': 'json'})
        return resp.json()['rows']


def daterange(start_date, end_date, delta=None):
    d = start_date
    delta = delta or datetime.timedelta(days=1)
    while d <= end_date:
        end_limited = end_date if d + delta > end_date else d + delta
        yield d, end_limited
        d += delta


def get_bills(client, start_date, end_date, delta):
    labels = set()
    bills = []
    for range_start, range_end in daterange(start_date, end_date, delta):
        print("Query for %s" % (range_start.strftime("%Y-%m-%d")))
        data = client.payments_history(range_start, range_end)
        labels.update(row['type'] for row in data)
        payments = {}
        for row in data:
            payments[row['type']] = payments.get(row['type'], 0) + Decimal(row['amount'])
        bills.append((range_start, range_end, payments))
    return labels, bills


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def build_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", nargs=1, required=True, help="Username to e24cloud")
    parser.add_argument("-p", "--password", nargs=1, required=True, help="Password to e24cloud")
    parser.add_argument("-o", "--output", required=True, help="Filename of output file")
    parser.add_argument('-s', "--startdate",
                        help="The start date - format YYYY-MM-DD (default: 90 days ago)",
                        default=(datetime.now() - timedelta(days=90)).date(),
                        type=valid_date)
    parser.add_argument('-e', "--enddate",
                        help="The end date - format YYYY-MM-DD (default: today)",
                        default=date.today(),
                        type=valid_date)
    parser.add_argument('--resolution',
                        type=int,
                        default=30,
                        help='Resolution in days of chart (default: 30)')
    return parser.parse_args()


def main():
    args = build_args()
    start_date = args.startdate
    end_date = args.enddate
    resolution_days = args.resolution
    client = Client()
    assert client.login(args.username, args.password) is True
    labels, bills = get_bills(client, start_date, end_date, timedelta(days=resolution_days))
    pprint(bills)

    line_chart = pygal.Line(x_label_rotation=85, )
    line_chart.title = 'e24cloud bills evolution ' + \
                       'in the period from %s to %s' % (start_date.strftime("%Y-%m-%d"),
                                                        end_date.strftime("%Y-%m-%d"))
    line_chart.x_labels = [str(x) for x, _, _ in bills]

    for label in labels:
        line_chart.add(label, [payment.get(label, None) for _, _, payment in bills])

    line_chart.render_to_file(args.output)
    print("Chart saved in file %s " % (args.output))


if __name__ == "__main__":
    main()