# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging

from flask import abort, render_template, url_for, redirect

from presence_analyzer.main import app
from presence_analyzer.utils import jsonify, get_data, mean, \
    group_by_weekday, get_mean_start_end_time, get_related_xml_values, \
    get_user_photo_url

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for('presence_weekday_page'))


@app.route('/presence_weekday', methods=['GET'])
def presence_weekday_page():
    """
    Method returns presence by weekday page using proper template.
    """
    title = 'Presence by weekday'
    return render_template('presence_weekday.html', title=title)


@app.route('/mean_time_weekday', methods=['GET'])
def mean_time_weekday_page():
    """
    Method returns mean time presence by weekday page using proper
    template.
    """
    title = 'Presence mean time by weekday'
    return render_template('mean_time_weekday.html', title=title)


@app.route('/start_end_mean_time_weekday', methods=['GET'])
def start_end_time_weekday_page():
    """
    Method returns mean start and end user presence by weekday page
    using proper template.
    """
    title = 'Presence start - end weekday'
    return render_template('presence_start_end.html', title=title)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_related_xml_values(get_data().keys())
    return [
        {
            'user_id': user_id,
            'name': user_name,
        }
        for user_id, user_name in data.items()
        ]


@app.route('/api/v1/user/<int:user_id>/photo', methods=['GET'])
@jsonify
def user_photo_view(user_id):
    """
    User photo loaded from external api.
    """
    return [
        {
            'user_photo': get_user_photo_url(user_id)
        }
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
        ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
        ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def start_end_time_view(user_id):
    """
    Returns time periods of given user spend in office.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    mean_start_end_times = get_mean_start_end_time(data[user_id])
    results = [
        (calendar.day_abbr[weekday], mean_times[0], mean_times[1])
        for weekday, mean_times in enumerate(mean_start_end_times)
        ]
    return results
