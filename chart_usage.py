#!/bin/python2.7
from __future__ import print_function

import argparse
import csv
from collections import namedtuple
from datetime import date, datetime, timedelta
from decimal import Decimal

import enum
import pygal
import requests
from dateutil.relativedelta import relativedelta

ChartDataset = namedtuple('ChartDataset', ['labels', 'bills', 'title'])


class ResultType(enum.Enum):
    PAYMENT = 1
    BW = 2
    OP = 3
    SIZE = 4

    def __str__(self):
        return self.name


class Period(namedtuple('Period', ['start', 'end'])):

    def __str__(self):
        return "Period from %s to %s" % (self.start.strftime("%Y-%m-%d"),
                                         self.end.strftime("%Y-%m-%d"))


class Client(object):
    LOGIN_URL = 'https://panel.e24cloud.com/login/check'
    HISTORY_URL = "https://panel.e24cloud.com/payments/history/format/json"
    BUCKET_STAT_URL = "https://panel.e24cloud.com/cloud-files/get-buckets-stats"

    def __init__(self, session=None):
        self.session = session or requests.Session()

    def login(self, email, password):
        resp = self.session.post(self.LOGIN_URL,
                                 data={'email': email, 'password': password},
                                 headers={'Referer': 'https://panel.e24cloud.com'})
        json = resp.json()
        return json['status'] == 1

    def payments_history(self, period):
        resp = self.session.post(self.HISTORY_URL,
                                 json={'date_from': period.start.strftime("%Y-%m-%d"),
                                       'date_to': period.end.strftime("%Y-%m-%d")})
        json = resp.json()
        assert json['status'] == 1
        return json['rows']

    def buckets_stats(self, period):
        resp = self.session.post(self.BUCKET_STAT_URL,
                                 json={'date_from': period.start.strftime("%Y-%m-%d"),
                                       'date_to': period.end.strftime("%Y-%m-%d")})
        json = resp.json()
        assert json['status'] == 1
        return json['rows']


class Service(object):

    def __init__(self, client, period, delta=None):
        self.client = client
        self.period = period
        self.delta = delta or datetime.timedelta(days=1)

    def _daterange(self):
        d = self.period.start
        delta = self.delta
        while d <= self.period.end:
            end_limited = self.period.end if d + delta > self.period.end else d + delta
            yield Period(d, end_limited)
            d += delta

    def get_bills(self):
        title = "e24cloud bills evolution"
        labels = set()
        bills = []
        for range_period in self._daterange():
            print("Query for", range_period)
            data = self.client.payments_history(range_period)['resources']
            labels.update(row['type'] for row in data)
            payments = {}
            for row in data:
                payments[row['type']] = payments.get(row['type'], 0) + Decimal(row['amount'])
            bills.append((range_period, payments))
        return ChartDataset(labels, bills, title)

    def get_buckets(self, kind):
        buckets = set()
        fields = {ResultType['SIZE']: ["size", ],
                  ResultType['BW']: ["bw_out", "bw_in", ],
                  ResultType['OP']: ["op_in", "op_get", ]}[kind]
        title = "e24cloud %s evolution" % (kind, )
        bills = []
        for range_period in self._daterange():
            print("Query for", range_period)
            data = self.client.buckets_stats(range_period)
            buckets.update(row['bucket'] for row in data)
            usage = {}
            for row in data:
                for field in fields:
                    usage["%s_%s" % (row['bucket'], field)] = Decimal(row[field])
            bills.append((range_period, usage))
        labels = ["%s_%s" % (bucket, field)
                  for bucket in buckets
                  for field in fields]
        return ChartDataset(labels, bills, title)


class Validator(object):
    @staticmethod
    def valid_date(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise argparse.ArgumentTypeError(msg)

    @staticmethod
    def valid_delta(s):
        deltas = {'month': relativedelta(months=+1),
                  'year': relativedelta(years=+1),
                  'week': relativedelta(weeks=+1),
                  'quarter': relativedelta(months=3)}
        if s in deltas:
            return deltas[s]
        try:
            return relativedelta(days=int(s))
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise argparse.ArgumentTypeError(msg)


def build_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", nargs=1, required=True, help="Username to e24cloud")
    parser.add_argument("-p", "--password", nargs=1, required=True, help="Password to e24cloud")
    parser.add_argument("-g", "--graphic", required=False, help="Filename of graphic output file")
    parser.add_argument("-c", "--csv", required=False, help="Filename of CSV file")
    parser.add_argument("-t", "--type",
                        type=str,
                        action="store",
                        choices=tuple(t.name.lower() for t in ResultType),
                        default=ResultType.PAYMENT.name.lower(),
                        dest="type")
    parser.add_argument('-s', "--startdate",
                        help="The start date - format YYYY-MM-DD (default: 90 days ago)",
                        default=(datetime.now() - timedelta(days=90)).date(),
                        type=Validator.valid_date)
    parser.add_argument('-e', "--enddate",
                        help="The end date - format YYYY-MM-DD (default: today)",
                        default=date.today(),
                        type=Validator.valid_date)
    parser.add_argument('--resolution',
                        type=Validator.valid_delta,
                        default=relativedelta(months=+1),
                        help='Resolution in days of chart (default: month)')
    args = parser.parse_args()
    args.type = ResultType[args.type.upper()]
    return args


class Export(object):
    def __init__(self, period, dataset, filename):
        self.period = period
        self.dataset = dataset
        self.labels = self.dataset.labels
        self.bills = self.dataset.bills
        self.title = self.dataset.title
        self.filename = filename

    def render(self):
        raise RuntimeError("It should be overwritten!")


class GraphicExport(Export):
    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop('title')
        super(GraphicExport, self).__init__(*args, **kwargs)

    def render(self):
        line_chart = pygal.Line(x_label_rotation=85, )
        line_chart.title = '%s in the period from %s to %s' % (self.title,
                                                               self.period.start.strftime(
                                                                   "%Y-%m-%d"),
                                                               self.period.end.strftime("%Y-%m-%d"))
        line_chart.x_labels = [str(period.start)
                               for period, _ in self.bills]

        for label in self.labels:
            line_chart.add(label, [payment.get(label, None) for _, payment in self.bills])

        line_chart.render_to_file(self.filename)
        print("Chart saved in file %s " % (self.filename))


class CSVExport(Export):
    def render(self):
        filename = self.filename
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(self.labels) + ['start', 'end'])
            writer.writeheader()
            for period, payment in self.bills:
                row = payment.copy()
                row['start'] = period.start
                row['end'] = period.end
                writer.writerow(row)
        print("CSV saved in file %s " % (filename))


def main():
    args = build_args()
    period = Period(args.startdate, args.enddate)
    client = Client()
    assert client.login(args.username, args.password) is True, \
        "Authentication failed. Check username and password."
    service = Service(client, period, args.resolution)
    if args.type == ResultType.PAYMENT:
        dataset = service.get_bills()
    else:
        dataset = service.get_buckets(args.type)

    if args.graphic:
        export = GraphicExport(period=period,
                               dataset=dataset,
                               filename=args.graphic,
                               title='e24cloud bills evolution')
        export.render()
    if args.csv:
        export = CSVExport(period=period,
                           dataset=dataset,
                           filename=args.csv)
        export.render()
    if not (args.csv or args.graphic):
        print('No chart or CSV files generated. Use "-o" or "-c".')


if __name__ == "__main__":
    main()
