# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
import calendar
from copy import deepcopy
import csv
from json import dumps
from functools import wraps
from datetime import datetime, timedelta
import locale
import logging
from threading import RLock

from apscheduler.scheduler import Scheduler
from lxml import etree
from flask import Response
import requests
from requests import ConnectionError

from presence_analyzer.main import app

log = logging.getLogger(__name__)  # pylint: disable=invalid-name
locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function
    result.
    """

    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        json_data = dumps(function(*args, **kwargs), )
        return Response(json_data, mimetype='application/json')

    return inner


def cache_data(seconds=0):
    """
    Decorator for caching data in memory.
    """
    delta = timedelta(seconds=seconds)

    def decorate(function):
        """
        Main decorator function.
        """
        function.lock = RLock()
        updates = {}
        results = {}

        def do_cache(*args, **kwargs):
            """
            Cache method.
            """
            should_cache = app.config.get('CACHE_DATA', True)
            cache_lock = function.lock
            cache_lock.acquire()
            try:
                now = datetime.now()
                updated = updates.get(function, now)
                old_data = function not in results or now - updated > delta

                if not should_cache or old_data:
                    # Calculate
                    updates[function] = now
                    result = function(*args, **kwargs)
                    results[function] = deepcopy(result)
                    return result
                else:
                    # Cache
                    return deepcopy(results[function])
            finally:
                cache_lock.release()

        return do_cache

    return decorate


@cache_data(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)
                continue

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}
    return data


def weekday_abbr(weekday):
    """
    Returns weekday abbreviation according to the passed number of day.
    """
    return calendar.day_abbr[weekday].decode('utf8')


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates interval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def get_mean_start_end_time(items):
    """
    Calculates mean starting and ending time for user data get from
    parameter. Mean values are calculated according to daf of week.

    :param items: user in/out datetime
    :return: list of tuples (mean_start_time, mean_end_time)
    """
    starts = [[] for _ in xrange(7)]  # one list for every day in week
    ends = [[] for _ in xrange(7)]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        starts[date.weekday()].append(seconds_since_midnight(start))
        ends[date.weekday()].append(seconds_since_midnight(end))

    results = [[] for _ in xrange(7)]
    for weekday, day in enumerate(zip(starts, ends)):
        results[weekday] = (mean(day[0]), mean(day[1]))
    return results


def download_users_information():
    """
    Download xml file from http localization set in config file.
    """
    try:
        xml_file = process_request(app.config['XML_URL'])
        with open(app.config['DATA_XML'], 'w') as output_file:
            return output_file.write(xml_file.content)
    except IOError as error:
        log.error('error during saving xml_content to file\n%s', error)
    except KeyError:
        log.warning('application start first time, some keys are not '
                    'available yet')


def process_xml_file():
    """
    Read XML file and returns object.
    """
    try:
        with open(app.config['DATA_XML'], 'r') as xml_file:
            tree = etree.fromstring(xml_file.read())
        return tree
    except AttributeError as error:
        log.error("parsing xml failed\n%s", error)
    except IOError as error:
        log.error('reading from file fails\n%s', error)


def process_request(url, method='get'):
    """
    Method execute request to url provided as parameter. Default
    method is GET
    """
    try:
        if method.lower() == 'post':
            return requests.post(url)
        return requests.get(url)
    except ConnectionError as error:
        log.error('network error - file wasn\'t downloaded\n%s', error)


def get_related_xml_values(items):
    """
    Returns list of user name according to list provided as parameter.

    :param items: list of user ids
    :return: list of user names
    """
    try:
        tree = process_xml_file()
        users_names = {}
        for user_id in items:
            user_name = tree.xpath("//user[@id='%s']/name/text()" % user_id)
            try:
                users_names[user_id] = user_name[0]
            except IndexError:
                log.warning('User name for id %d wasn\'t found', user_id)
                users_names[user_id] = 'User %s' % str(user_id).rjust(4, ' ')
        return users_names
    except AttributeError as error:
        log.error('processing xml file fails\n%s', error)


def get_user_photo_url(user_id):
    """
    Return image from external api according to the user id.
    """
    tree = process_xml_file()
    try:
        host = tree.xpath('server/host/text()')
        protocol = tree.xpath('server/protocol/text()')
        img_path = tree.xpath("//user[@id='{}']/avatar/text()".format(user_id))
        photo_url = '{0}://{1}{2}'.format(protocol[0], host[0], img_path[0])
    except IndexError as error:
        log.warning('creating photo url failed.\n%s', error)
        photo_url = "https://intranet.stxnext.pl/api/images/users/1"
    return photo_url


def time_separated_by_months(items):
    """
    Returns dictionary with Years and list of months related to it.
    """
    years = {}
    for date, times in items.iteritems():
        years.setdefault(date.year, {})
        years[date.year].setdefault(date.month, [])
        years[date.year][date.month].append(
            interval(times['start'], times['end'])
        )
    return years


def group_time_by_month_year(years):
    """
    Sum monthly worked hours for each year in dict passed as parameter.
    """
    result = {}
    for month in xrange(1, 13):
        for year, data in years.iteritems():
            result.setdefault(year, [])
            try:
                month_data = data[month]
                result[year].append(
                    [calendar.month_abbr[month], sum(month_data) / 3600]
                )
            except KeyError:
                result[year].append([calendar.month_abbr[month], 0])
    return result


def get_monthly_worked_hours(items):
    """
    Returns average working hours for each month in year.
    """
    years = time_separated_by_months(items)
    grouped_result = group_time_by_month_year(years)
    output = [['Year'] + map(str, years.iterkeys())]

    for month in xrange(12):
        month_data = [calendar.month_abbr[month + 1]]
        for month_values in grouped_result.itervalues():
            month_data.append(month_values[month][1])
        output.append(month_data)
    return output


def download_user_info_scheduler():
    """
    Create and prepare scheduler for downloading xml data from url.
    """
    scheduler = Scheduler()
    scheduler.start()

    # backup Schedule to run once every 4 hours
    day_of_week = app.config.get('cron_day_of_week_pattern', '*')
    hour = app.config.get('cron_hour_pattern', '*/4')
    minute = app.config.get('cron_minutes_pattern', '0')
    scheduler.add_cron_job(download_users_information, day_of_week=day_of_week,
                           hour=hour, minute=minute)


download_user_info_scheduler()
