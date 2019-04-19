
import io
import json
from unittest import TestCase
from unittest import mock

from chrisstoreclient import client


def _get(url, **kwargs):
    response_text = '{"collection":{"items":[{"links":[{"rel":"parameters",' \
                         '"href":"http://localhost:8010/api/v1/1/parameters/"},' \
                         '{"rel":"owner","href":"http://localhost:8010/api/v1/users/2/"}],' \
                         '"href":"http://localhost:8010/api/v1/1/",' \
                         '"data":[{"value":1,"name":"id"}, {"value":"simplefsapp","name":"name"},' \
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
                         '"links":[{"rel":"user_plugins","href":"http://localhost:8010/api/v1/user-plugins/"}],' \
                         '"href":"http://localhost:8010/api/v1/search/?name=simplefsapp",' \
                         '"version":"1.0"}}'

    parameter_response_text = '{"collection":{"items":[{"links":[{"rel":"plugin",' \
                                   '"href":"http://localhost:8010/api/v1/1/"}],' \
                                   '"href":"http://localhost:8010/api/v1/parameters/1/",' \
                                   '"data":[{"value":1,"name":"id"}, {"value":"dir","name":"name"}, {"value":"path","name":"type"},' \
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
        self.user_plugins_url = self.store_url + 'user-plugins/'
        self.username = "cubeadmin"
        self.password = "cubeadmin1234"
        self.plugin_name = 'simplefsapp'
        self.plugin_id = 1
        self.client = client.StoreClient(self.store_url, self.username, self.password)
        self.headers = {'Content-Type': self.client.content_type,
                        'Accept': self.client.content_type}
        self.plugin_representation = {'id': 1,
                                      'name': 'simplefsapp',
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
                                      'max_gpu_limit': 0 }
        self.parameters_representation = [{'id': 1, 'name': 'dir', 'type': 'path',
                                           'optional': True, 'default': './',
                                           'flag': '--dir', 'action': 'store',
                                           'help': 'look up directory'}]

    def test_get_plugin(self):
        """
        Test whether get_plugin method can get a plugin representation from the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            plugin = self.client.get_plugin(self.plugin_name)
            self.assertEqual(plugin, self.plugin_representation)
            requests_get_mock.assert_any_call(self.client.store_query_url,
                                              auth=(self.username, self.password),
                                              headers=self.headers,
                                              params={'name_exact_latest': self.plugin_name},
                                              timeout=30)

    def test_get_plugin_parameters(self):
        """
        Test whether get_plugin_parameters method can get the list of all plugin parameter
        representations for the given plugin from the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            result = self.client.get_plugin_parameters(self.plugin_id)
            self.assertEqual(result['data'], self.parameters_representation)
            requests_get_mock.assert_any_call(self.store_url + '1/parameters/',
                                              auth=(self.username, self.password),
                                              headers=self.headers,
                                              params=None, timeout=30)


    def test_get_plugins_with_no_args(self):
        """
        Test whether get_plugins method can get the list of all plugin representations
        from the ChRIS store.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            result = self.client.get_plugins()
            self.assertEqual(result['data'], [self.plugin_representation])
            requests_get_mock.assert_any_call(self.store_url,
                                              auth=(self.username, self.password),
                                              headers=self.headers,
                                              params=None, timeout=30)

    def test_get_plugins_with_search_args(self):
        """
        Test whether get_plugins method can get a list of plugin representations
        from the ChRIS store given query search parameters.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            result = self.client.get_plugins({'name': self.plugin_name})
            self.assertEqual(result['data'], [self.plugin_representation])
            requests_get_mock.assert_any_call(self.client.store_query_url,
                                              auth=(self.username, self.password),
                                              headers=self.headers,
                                              params={'name': self.plugin_name}, timeout=30)

    def test_get_authenticated_user_plugins(self):
        """
        Test whether get_authenticated_user_plugins method can get the list of all plugin
        representations from the ChRIS store for the currently authenticated user.
        """
        with mock.patch.object(client.requests, 'get',
                               side_effect=_get) as requests_get_mock:
            result = self.client.get_authenticated_user_plugins()
            self.assertEqual(result['data'], [self.plugin_representation])
            requests_get_mock.assert_any_call(self.store_url,
                                              auth=(self.username, self.password),
                                              headers=self.headers,
                                              params=None, timeout=30)

    def test_add_plugin(self):
        """
        Test whether add_plugin method sends the appropriate POST request to add a new
        plugin.
        """
        with mock.patch.object(client.requests, 'post',
                               return_value=_get(self.store_url)) as requests_post_mock:
            with mock.patch.object(client.requests, 'get',
                                   side_effect=_get) as requests_get_mock:
                with io.BytesIO(json.dumps(self.plugin_representation).encode()) as dfile:
                    self.client.add_plugin(self.plugin_name,
                                           self.plugin_representation['dock_image'],
                                           dfile,
                                           self.plugin_representation['public_repo'])
                    data = {'name': self.plugin_name,
                            'dock_image': self.plugin_representation['dock_image'],
                            'public_repo': self.plugin_representation['public_repo']}
                    files = {'descriptor_file': dfile}
                    requests_get_mock.assert_called_with(self.client.store_url,
                                                         auth=(
                                                         self.username, self.password),
                                                         headers=self.headers,
                                                         params=None,
                                                         timeout=30)
                    requests_post_mock.assert_called_with(self.user_plugins_url,
                                                          files=files, data=data,
                                                          auth=(self.username, self.password),
                                                          headers = None,
                                                          timeout=30)

    def test_modify_plugin(self):
        """
        Test whether modify_plugin method sends the appropriate PUT request to modify an
        existing plugin.
        """
        with mock.patch.object(client.requests, 'put',
                               return_value=_get(self.store_url)) as requests_put_mock:
            with mock.patch.object(client.requests, 'get',
                                   side_effect=_get) as requests_get_mock:
                self.client.modify_plugin(self.plugin_id,
                                          self.plugin_representation['dock_image'],
                                          self.plugin_representation['public_repo'])
                data = {'dock_image': self.plugin_representation['dock_image'],
                        'public_repo': self.plugin_representation['public_repo']}
                requests_get_mock.assert_called_with(self.client.store_query_url,
                                                     auth=(self.username, self.password),
                                                     headers=self.headers,
                                                     params={'id': self.plugin_id},
                                                     timeout=30)
                data = json.dumps(self.client._makeTemplate(data))
                requests_put_mock.assert_called_with(self.store_url + '1/',
                                                     data=data,
                                                     auth=(self.username, self.password),
                                                     files=None,
                                                     headers=self.headers,
                                                     timeout=30)

    def test_remove_plugin(self):
        """
        Test whether remove_plugin method sends the appropriate DELETE request to remove
        an existing plugin.
        """
        with mock.patch.object(client.requests, 'delete') as requests_delete_mock:
            with mock.patch.object(client.requests, 'get',
                                   side_effect=_get) as requests_get_mock:
                self.client.remove_plugin(self.plugin_id)
                requests_get_mock.assert_called_with(self.client.store_query_url,
                                                     auth=(self.username, self.password),
                                                     headers=self.headers,
                                                     params={'id': self.plugin_id},
                                                     timeout=30)
                requests_delete_mock.assert_called_with(self.store_url + '1/',
                                                        auth=(self.username, self.password),
                                                        timeout=30)
