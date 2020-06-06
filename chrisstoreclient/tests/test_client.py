
from unittest import TestCase
from unittest import mock

from chrisstoreclient import client

response_text = '{"collection":{"items":[{"links":[{"rel":"plugins",' \
                '"href":"http://localhost:8010/api/v1/1/plugins/"}],' \
                '"href":"http://localhost:8010/api/v1/1/",' \
                '"data":[{"value":1,"name":"id"}, {"value":"simplefsapp","name":"name"}]}],' \
                '"links":[],' \
                '"href":"http://localhost:8010/api/v1/1/",' \
                '"version":"1.0"}}'

response = type('test', (object,), {})()
response.text = response_text


class StoreClientTests(TestCase):

    def setUp(self):
        self.store_url = "http://localhost:8010/api/v1/"
        self.username = "cubeadmin"
        self.password = "cubeadmin1234"
        self.plugin_name = 'simplefsapp'
        self.plugin_id = 1
        self.mock_url = 'mock_url/'
        self.client = client.StoreClient(self.store_url, self.username, self.password)
        self.client.get_url = mock.Mock(return_value=self.mock_url)
        self.headers = {'Content-Type': self.client.content_type,
                        'Accept': self.client.content_type}

    def test_get_plugins(self):
        """
        Test whether get_plugins method makes the appropriate request to the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               return_value=response) as requests_get_mock:
            plugins = self.client.get_plugins()
            requests_get_mock.assert_called_with(self.mock_url,
                                                 params=None,
                                                 auth=(self.username, self.password),
                                                 headers=self.headers,
                                                 timeout=30)
            self.assertEqual(plugins['data'], [{"id": 1, "name": "simplefsapp"}])

            plugins = self.client.get_plugins({'name_exact_latest': self.plugin_name})
            requests_get_mock.assert_called_with(self.mock_url + 'search/',
                                                 auth=(self.username, self.password),
                                                 headers=self.headers,
                                                 params={'name_exact_latest': self.plugin_name},
                                                 timeout=30)
            self.assertEqual(plugins['data'], [{"id": 1, "name": "simplefsapp"}])

    def test_get_plugin(self):
        """
        Test whether get_plugin method makes the appropriate request to the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               return_value=response) as requests_get_mock:
            plugin = self.client.get_plugin(self.plugin_name)
            requests_get_mock.assert_called_with(self.mock_url + 'search/',
                                                 params={
                                                     'name_exact_latest': 'simplefsapp'},
                                                 auth=(self.username, self.password),
                                                 headers=self.headers,
                                                 timeout=30)
            self.assertEqual(plugin, {"id": 1, "name": "simplefsapp"})

            self.client.get_plugin(self.plugin_name, '0.1')
            requests_get_mock.assert_called_with(self.mock_url + 'search/',
                                                 auth=(self.username, self.password),
                                                 headers=self.headers,
                                                 params={'name_exact': self.plugin_name,
                                                         'version': '0.1'},
                                                 timeout=30)
            self.assertEqual(plugin, {"id": 1, "name": "simplefsapp"})

    def test_add_plugin(self):
        """
        Test whether add_plugin method sends the appropriate POST request to add a new
        plugin.
        """
        with mock.patch.object(client.requests, 'post',
                               return_value=response) as requests_post_mock:
            plugin = self.client.add_plugin(self.plugin_name, 'dock_image',
                                            'descriptor_file', 'public_repo')
            requests_post_mock.assert_called_with(self.mock_url,
                                                  data={'name': 'simplefsapp',
                                                        'dock_image': 'dock_image',
                                                        'public_repo': 'public_repo'},
                                                  auth=(self.username, self.password),
                                                  files={'descriptor_file': 'descriptor_file'},
                                                  headers=None, timeout=30)
            self.assertEqual(plugin, {"id": 1, "name": "simplefsapp"})
