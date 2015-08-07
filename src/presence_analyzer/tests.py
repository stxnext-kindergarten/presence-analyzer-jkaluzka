# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from lxml import etree
import mock
from requests import ConnectionError

from presence_analyzer import main, utils, views

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.xml'
)

XML_URL = "http://sargo.bolt.stxnext.pl/users.xml"


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
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        main.app.config.update({'XML_URL': XML_URL})
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
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 3)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'Adam P.'})

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

    def test_presence_start_end_wrong_user(self):
        """
        Test user weekday view for wrong user
        """
        response = self.client.get('/api/v1/presence_start_end/100')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'text/html')

    def test_presence_start_end_view(self):
        """
        Test user presence weekday view
        """
        response = self.client.get('/api/v1/presence_start_end/13')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(data[3], [u'Thu', 42466.0, 57163.5])

    def test_presence_weekday_page(self):
        """
        Test user presence weekday page rendering with proper template.
        """
        response = self.client.get('/presence_weekday')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h2>Presence by weekday</h2>', response.data)

    def test_mean_time_weekday_page(self):
        """
        Test user mean time presence weekday page rendering with proper.
        template
        """
        response = self.client.get('/mean_time_weekday')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h2>Presence mean time by weekday</h2>', response.data)

    def test_start_end_time_weekday_page(self):
        """
        Test user mean start / end presence time by weekday page
        rendering with proper template.
        """
        response = self.client.get('/start_end_mean_time_weekday')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h2>Presence start - end weekday</h2>', response.data)

    def test_user_photo_url_api_route(self):
        """
        Test user photo url api route.
        """
        response = self.client.get('/api/v1/user/10/photo')
        photo_url = 'https://intranet.stxnext.pl/api/images/users/10'
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertDictEqual(data[0], {"user_photo": photo_url})


class MockResponse(object):
    """
    Mock class for response objects.
    """

    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code


def raise_attribute_error(error):
    """
    Raise AttributeError
    """
    raise AttributeError(2, error)


def raise_io_error(error, flag):
    """
    Raise IOError
    """
    raise IOError(2, '{0} {1}'.format(error, flag))


def raise_connection_error(error):
    """
    Raise ConnectionError
    """
    raise ConnectionError(2, error)


def mocked_requests_get(url):
    """
    Mock method returns proper http response.
    """
    if url == 'wrong_url_path':
        raise ConnectionError
    with open(TEST_DATA_XML, 'r') as xml_file:
        response = MockResponse(xml_file.read(), 200)
    return response


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        main.app.config.update({'XML_URL': XML_URL})

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
        self.assertItemsEqual(data.keys(), [10, 11, 13])

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
    def test_get_data_corrupted_id_as_string(self, csv_reader):
        """
        Test if method log problem for corrupted id
        """
        csv_reader.return_value = [
            ['wrong', '2013-09-13', '13:16:56', '13:16:56']]
        self.assertEqual(utils.get_data(), {})

    @mock.patch('csv.reader')
    def test_get_data_corrupted_id_as_list(self, csv_reader):
        """
        Test if method log problem for corrupted id
        """
        csv_reader.return_value = [
            [[1, 2], '2013-09-13', '13:16:56', '13:16:56']]
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

    def test_mean_start_end_time(self):
        """
        Test calculating mean values of start and end times of user
        according to the weekdays
        """
        data = utils.get_data()
        mean_times = utils.get_mean_start_end_time(data[13])
        self.assertIsInstance(mean_times, list)
        self.assertEqual(len(mean_times), 7)
        self.assertTupleEqual(mean_times[1], (33398.0, 54340.5))

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_request_get(self, mock_requests):
        """
        Test processing get request passed as parameters
        """
        mock_requests.return_value = ''
        response = utils.process_request(XML_URL)
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_request_post(self, mock_requests):
        """
        Test processing post request passed as parameters
        """
        mock_requests.return_value = ''
        response = utils.process_request(XML_URL, 'post')
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.get', side_effect=raise_connection_error)
    def test_process_request_catch_connection_error(self, mock_requests):
        """
        Test catching io exception when processing request.
        """
        mock_requests.return_value = ''
        self.assertFalse(utils.process_request(XML_URL))

    @mock.patch('__builtin__.open')
    def test_downloading_users_information(self, mock_open):
        """
        Test downloading xml file from http location to file.
        """
        mock_open.return_value = open(XML_URL)
        data = utils.download_users_information()
        self.assertTrue(data)

    @mock.patch('__builtin__.open', side_effect=raise_io_error)
    def test_downloading_users_information_catch_error(self, mock_requests):
        """
        Test catching io exception during downloading xml file.
        """
        mock_requests.return_value = ''
        self.assertFalse(utils.download_users_information())

    def test_downloading_users_information_key_error(self):
        """
        Test catching io exception during downloading xml file.
        """
        main.app.config.pop('XML_URL')
        self.assertFalse(utils.download_users_information())

    def test_process_xml_file(self):
        """
        Test processing xml file
        """
        xml = utils.process_xml_file()
        self.assertIsNotNone(xml)
        self.assertIsInstance(xml, etree._Element)

    @mock.patch('lxml.etree.fromstring', side_effect=raise_attribute_error)
    def test_process_xml_file_catch_exception(self, etree_from_string):
        """
        Test catching AttributeError during parsing XML file.
        """
        etree_from_string.return_value = ''
        names = utils.process_xml_file()
        self.assertFalse(names)

    @mock.patch('__builtin__.open', side_effect=raise_io_error)
    def test_downloading_xml_file_connection_failure(self, mock_open):
        """
        Test catching connection failure during downloading xml file.
        """
        mock_open.return_value = ''
        main.app.config.update({'XML_URL': 'wrong_url_path'})
        self.assertFalse(utils.process_xml_file())

    def test_get_related_xml_values(self):
        """
        Test returning proper list of names according to the ids list.
        """
        data = utils.get_data()

        names = utils.get_related_xml_values(data.keys())
        self.assertEqual(len(names.keys()), 3)
        self.assertEqual(names[10], 'Adam P.')
        self.assertEqual(names[13], 'Andrzej S.')

    @mock.patch('lxml.etree.fromstring')
    def test_get_related_xml_values_processing_error(self, mock_etree):
        """
        Test returning none if xml file is corrupted.
        """
        data = utils.get_data()
        mock_etree.return_value = 'wrong_string'
        names = utils.get_related_xml_values(data.keys())
        self.assertFalse(names)

    @mock.patch('lxml.etree.fromstring')
    def test_get_related_xml_values_with_empty_items(self, etree_from_string):
        """
        Test returning empty dict if ids list is also empty.
        """
        etree_from_string.return_value = ''
        names = utils.get_related_xml_values([])
        self.assertDictEqual(names, {})

    def test_get_related_xml_values_with_no_matching_id(self):
        """
        Test returning default value if id wasn't found in XML file.
        """
        names = utils.get_related_xml_values([121])
        self.assertEqual(len(names.keys()), 1)
        self.assertEqual(names[121], 'User 121')

    def test_get_user_photo(self):
        """
        Test getting user photo.
        """
        photo_url = utils.get_user_photo_url(13)
        correct_url = 'https://intranet.stxnext.pl/api/images/users/13'
        self.assertIsNotNone(photo_url)
        self.assertEqual(photo_url, correct_url)

    def test_get_user_photo_wrong_user_id(self):
        """
        Test getting user photo.
        """
        photo_url = utils.get_user_photo_url('wrong_url')
        self.assertIsNone(photo_url)


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
