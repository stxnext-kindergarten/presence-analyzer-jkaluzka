# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

import mock

from presence_analyzer import main, utils, views

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


def test_method():
    """
    Method returns dictionary for testing purposes.
    """
    return {
        1: 'one',
        2: 'two',
        3: 'three'
    }


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_mean_time_weekday_wrong_user(self):
        """
        Test user weekday view for wrong user
        """
        response = self.client.get('/api/v1/mean_time_weekday/100')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'text/html')

    def test_mean_time_weekday_view(self):
        """
        Test user weekday view
        """
        response = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(data[1], [u'Tue', 30047.0])

    def test_presence_weekday_view(self):
        """
        Test user presence weekday view
        """
        response = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(data[4], [u'Thu', 23705])

    def test_presence_weekday_wrong_user(self):
        """
        Test user weekday view for wrong user
        """
        response = self.client.get('/api/v1/presence_weekday/100')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'text/html')


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data_correct_type(self):
        """
        Test if method returns correct type of data
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)

    def test_get_data_read_correct_number_of_keys(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertItemsEqual(data.keys(), [10, 11])

    def test_get_data_read_correctly_values(self):
        """
        Test reading correctly values from CSV file.
        """
        data = utils.get_data()
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    @mock.patch('csv.reader')
    def test_get_data_corrupted_date(self, csv_reader):
        """
        Test if method log problem for corrupted date
        """
        csv_reader.return_value = [
            ['11', 'wrong_value', '13:16:56', '13:16:56']]
        self.assertEqual(utils.get_data(), {})

    @mock.patch('csv.reader')
    def test_get_data_corrupted_time(self, csv_reader):
        """
        Test if method log problem for corrupted time
        """
        csv_reader.return_value = [
            ['11', '2013-09-13', '13:16:56', 'wrong_value']]
        self.assertEqual(utils.get_data(), {})

    @mock.patch('csv.reader')
    def test_get_data_corrupted_id(self, csv_reader):
        """
        Test if method log problem for corrupted id
        """
        csv_reader.return_value = [
            ['wrong', '2013-09-13', '13:16:56', '13:16:56']]
        self.assertEqual(utils.get_data(), {})

    def test_group_by_weekday(self):
        """
        Test grouping results by weekday.
        """
        items = utils.get_data()
        results = utils.group_by_weekday(items[10])
        self.assertIsInstance(results, list)
        self.assertEqual(results[0], [])
        self.assertEqual(len(results[1]), 1)

    def test_seconds_since_midnight(self):
        """
        Test calculating seconds from midnight.
        """
        test_time = datetime.time(hour=8, minute=10, second=9)
        seconds = utils.seconds_since_midnight(test_time)
        self.assertIsInstance(seconds, int)
        self.assertEqual(seconds, 29409)

    def test_interval(self):
        """
        Test calculating proper interval between start <-> end dates.
        """
        start = datetime.time(hour=8)
        end = datetime.time(hour=10, minute=10, second=10)
        time_interval = utils.interval(start, end)
        self.assertIsInstance(time_interval, int)
        self.assertEqual(time_interval, 7810)

    def test_mean_if_items(self):
        """
        Test calculating mean from items.
        """
        items = [1, 2, 3, 4, 5]
        mean = utils.mean(items)
        self.assertIsInstance(mean, float)
        self.assertEqual(mean, 3)
        items.append(9.7)
        mean = utils.mean(items)
        self.assertEqual(mean, 4.116666666666666)

    def test_mean_if_empty_list(self):
        """
        Test mean function if list is empty.
        """
        mean = utils.mean([])
        self.assertIsInstance(mean, int)
        self.assertEqual(mean, 0)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
