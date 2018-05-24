
import json
from unittest import TestCase
from unittest import mock

from chrisstoreclient import client

def _get(url, **kwargs):
    response_text = '{"collection":{"items":[{"links":[{"rel":"parameters",' \
                         '"href":"http://localhost:8010/api/v1/1/parameters/"},' \
                         '{"rel":"owner","href":"http://localhost:8010/api/v1/users/2/"}],' \
                         '"href":"http://localhost:8010/api/v1/1/",' \
                         '"data":[{"value":"simplefsapp","name":"name"},' \
                         '{"value":"2018-05-22T15:49:52.419437Z","name":"creation_date"},' \
                         '{"value":"2018-05-22T15:49:52.419481Z","name":"modification_date"},' \
                         '{"value":"fnndsc/pl-simplefsapp","name":"dock_image"},' \
                         '{"value":"https://github.com/FNNDSC","name":"public_repo"},' \
                         '{"value":"fs","name":"type"},{"value":"FNNDSC (dev@babyMRI.org)",' \
                         '"name":"authors"},{"value":"Simple chris fs app","name":"title"},' \
                         '{"value":"","name":"category"},{"value":"A simple chris fs app demo",' \
                         '"name":"description"},{"value":"http://wiki","name":"documentation"},' \
                         '{"value":"Opensource (MIT)","name":"license"},' \
                         '{"value":"0.1","name":"version"},{"value":"python3","name":"execshell"},' \
                         '{"value":"/usr/src/simplefsapp","name":"selfpath"},' \
                         '{"value":"simplefsapp.py","name":"selfexec"},' \
                         '{"value":1,"name":"min_number_of_workers"},' \
                         '{"value":1,"name":"max_number_of_workers"},' \
                         '{"value":1000,"name":"min_cpu_limit"},' \
                         '{"value":2147483647,"name":"max_cpu_limit"},' \
                         '{"value":200,"name":"min_memory_limit"},' \
                         '{"value":2147483647,"name":"max_memory_limit"},' \
                         '{"value":0,"name":"min_gpu_limit"},{"value":0,"name":"max_gpu_limit"}]}],' \
                         '"links":[{"rel":"all_plugins","href":"http://localhost:8010/api/v1/plugins/"}],"href":"http://localhost:8010/api/v1/search/?name=simplefsapp",' \
                         '"version":"1.0"}}'

    parameter_response_text = '{"collection":{"items":[{"links":[{"rel":"plugin",' \
                                   '"href":"http://localhost:8010/api/v1/1/"}],' \
                                   '"href":"http://localhost:8010/api/v1/parameters/1/",' \
                                   '"data":[{"value":"dir","name":"name"},{"value":"path","name":"type"},' \
                                   '{"value":true,"name":"optional"},{"value":"./","name":"default"},' \
                                   '{"value":"--dir","name":"flag"},{"value":"store","name":"action"},' \
                                   '{"value":"look up directory","name":"help"}]}],"links":[],' \
                                   '"href":"http://localhost:8010/api/v1/1/parameters/","version":"1.0"}}'
    response = type('test', (object,), {})()
    response.text = response_text
    if 'parameters' in url:
        response.text = parameter_response_text
    return response


class StoreClientTests(TestCase):

    def setUp(self):
        self.store_url = "http://localhost:8010/api/v1/"
        self.username = "cubeadmin"
        self.password = "cubeadmin1234"
        self.plugin_name = 'simplefsapp'
        self.client = client.StoreClient(self.store_url, self.username, self.password)
        self.plugin_representation = {'name': 'simplefsapp',
                                      'creation_date': '2018-05-22T15:49:52.419437Z',
                                      'modification_date': '2018-05-22T15:49:52.419481Z',
                                      'dock_image': 'fnndsc/pl-simplefsapp',
                                      'public_repo': 'https://github.com/FNNDSC',
                                      'type': 'fs', 'authors': 'FNNDSC (dev@babyMRI.org)',
                                      'title': 'Simple chris fs app', 'category': '',
                                      'description': 'A simple chris fs app demo',
                                      'documentation': 'http://wiki',
                                      'license': 'Opensource (MIT)',
                                      'version': '0.1', 'execshell': 'python3',
                                      'selfpath': '/usr/src/simplefsapp',
                                      'selfexec': 'simplefsapp.py',
                                      'min_number_of_workers': 1,
                                      'max_number_of_workers': 1,
                                      'min_cpu_limit': 1000,
                                      'max_cpu_limit': 2147483647,
                                      'min_memory_limit': 200,
                                      'max_memory_limit': 2147483647,
                                      'min_gpu_limit': 0,
                                      'max_gpu_limit': 0,
                                      'parameters': [{'name': 'dir', 'type': 'path',
                                                      'optional': True, 'default': './',
                                                      'flag': '--dir', 'action': 'store',
                                                      'help': 'look up directory'}]}

    def test_get_plugin(self):
        """
        Test whether get_plugin method can get a plugin representation from the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            pl = self.client.get_plugin(self.plugin_name)
            self.assertEqual(pl, self.plugin_representation)
            requests_get_mock.assert_any_call(self.client.store_query_url,
                                              auth=(self.username, self.password),
                                              params={'name': self.plugin_name}, timeout=30)

    def test_get_plugins_with_no_args(self):
        """
        Test whether get_plugins method can get the list of all plugin representations
        from the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            plugins = self.client.get_plugins()
            self.assertEqual(plugins, [self.plugin_representation])
            requests_get_mock.assert_any_call(self.store_url,
                                              auth=(self.username, self.password),
                                              params=None, timeout=30)

    def test_get_plugins_with_search_args(self):
        """
        Test whether get_plugins method can get a list of plugin representations
        from the ChRIS store given query search parameters.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            plugins = self.client.get_plugins(name=self.plugin_name)
            self.assertEqual(plugins, [self.plugin_representation])
            requests_get_mock.assert_any_call(self.client.store_query_url,
                                              auth=(self.username, self.password),
                                              params={'name': self.plugin_name}, timeout=30)

    def test_get_authenticated_user_plugins(self):
        """
        Test whether get_authenticated_user_plugins method can get the list of all plugin
        representations from the ChRIS store for the currently authenticated user.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            plugins = self.client.get_authenticated_user_plugins()
            self.assertEqual(plugins, [self.plugin_representation])
            requests_get_mock.assert_any_call(self.store_url,
                                              auth=(self.username, self.password),
                                              params=None, timeout=30)

