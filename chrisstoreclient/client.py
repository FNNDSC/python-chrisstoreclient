"""
ChRIS store API client module.
An item in a collection is represented by a dictionary. A collection of items is
represented by a list of dictionaries.
"""

import json
import requests
from collection_json import Collection

from.exceptions import StoreRequestException


class StoreClient(object):
    """
    A ChRIS store API client.
    """

    def __init__(self, store_url, username=None, password=None, timeout=30):
        self.store_url = store_url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.content_type = 'application/vnd.collection+json'

        # urls of the high level API resources
        self._urls = {'plugin_metas': self.store_url,  'plugins': '', 'pipelines': '',
                      'plugin_stars': ''}

    def get_url(self, resource_name):
        if resource_name not in self._urls:
            raise NameError('Could not find resource %s.' % resource_name)
        if not self._urls[resource_name]:
            collection = self.get(self.store_url)
            self._urls = {'plugin_metas': self.store_url,
                          'plugins': self._get_link_relation_urls(collection,
                                                                  'plugins')[0],
                          'pipelines': self._get_link_relation_urls(collection,
                                                                    'pipelines')[0],
                          'plugin_stars': self._get_link_relation_urls(collection,
                                                                       'plugin_stars')[0]
                          }
        return self._urls[resource_name]

    def get_plugin_metas(self, search_params=None):
        """
        Get a paginated list of plugin metas (descriptors) given query search parameters.
        If no search parameters is given then get the default first page.
        """
        url = self.get_url('plugin_metas')
        query_url = url + 'search/'
        if search_params:
            collection = self.get(query_url, search_params)
        else:
            collection = self.get(url)
        return self.get_data_from_collection(collection)

    def get_plugin_meta(self, name):
        """
        Get a plugin meta's data (descriptors) given its ChRIS store name.
        """
        search_params = {'name_exact': name}
        result = self.get_plugin_metas(search_params)
        if result['data']:
            return result['data'][0]  # name is unique
        else:
            raise StoreRequestException('Could not find plugin meta with name %s.' % name)

    def get_plugin_meta_by_id(self, id):
        """
        Get a plugin meta's data (descriptors) given its ChRIS store id.
        """
        search_params = {'id': id}
        result = self.get_plugin_metas(search_params)
        if result['data']:
            return result['data'][0]  # ids are unique
        else:
            raise StoreRequestException('Could not find plugin meta with id %s' % id)

    def get_plugins(self, search_params=None):
        """
        Get a paginated list of plugin data (descriptors) given query search parameters.
        If no search parameters is given then get the default first page.
        """
        url = self.get_url('plugins')
        query_url = url + 'search/'
        if search_params:
            collection = self.get(query_url, search_params)
        else:
            collection = self.get(url)
        return self.get_data_from_collection(collection)

    def get_plugin(self, name, version=None):
        """
        Get a plugin's data (descriptors) given its ChRIS store name and version.
        If no version is passed then the latest version of the plugin according to
        creation date is retrieved.
        """
        if version is not None:
            search_params = {'name_exact': name, 'version': version}
        else:
            version = 'latest'
            search_params = {'name_exact_latest': name}
        result = self.get_plugins(search_params)
        if result['data']:
            return result['data'][0]  # combination of plugin name and version is unique
        else:
            raise StoreRequestException('Could not find plugin name %s with version %s.' %
                                        (name, version))

    def get_plugin_by_id(self, id):
        """
        Get a plugin's data (descriptors) given its ChRIS store id.
        """
        search_params = {'id': id}
        result = self.get_plugins(search_params)
        if result['data']:
            return result['data'][0]  # plugin ids are unique
        else:
            raise StoreRequestException('Could not find plugin with id %s' % id)

    def get_plugin_parameters(self, plugin_id, params=None):
        """
        Get a plugin's paginated parameters given its ChRIS store id.
        """
        url = self.get_url('plugins')
        query_url = url + 'search/'
        collection = self.get(query_url, {'id': plugin_id})
        if len(collection.items) == 0:
            raise StoreRequestException('Could not find plugin with id: %s.' % plugin_id)
        parameters_links = self._get_link_relation_urls(collection.items[0], 'parameters')
        if parameters_links:
            collection = self.get(parameters_links[0], params)  # there can only be a single parameters link
            return self.get_data_from_collection(collection)
        return {'data': [], 'hasNextPage': False, 'hasPreviousPage': False, 'total': 0}

    def get_data_from_collection(self, collection):
        """
        Get the result data dictionary from a collection object.
        """
        result = {'data': [], 'hasNextPage': False, 'hasPreviousPage': False, 'total': 0}
        for item in collection.items:
            item_dict = self._get_item_descriptors(item)
            result['data'].append(item_dict)
        if self._get_link_relation_urls(collection, 'next'):
            result['hasNextPage'] = True
        if self._get_link_relation_urls(collection, 'previous'):
            result['hasPreviousPage'] = True
        if hasattr(collection, 'total'):
            result['total'] = collection.total
        return result

    def add_plugin(self, name, dock_image, descriptor_file, public_repo):
        """
        Add a new plugin to the ChRIS store.
        """
        url = self.get_url('plugins')
        data = {'name': name, 'dock_image': dock_image, 'public_repo': public_repo}
        collection = self.post(url, data, descriptor_file)
        result = self.get_data_from_collection(collection)
        return result['data'][0]

    def remove_plugin(self, id):
        """
        Remove an existing plugin from the ChRIS store.
        """
        url = self.get_url('plugins')
        query_url = url + 'search/'
        search_params = {'id': id}
        collection = self.get(query_url, search_params)
        url = collection.items[0].href
        self.delete(url)

    def modify_plugin_meta(self, name, public_repo, new_owner=None):
        """
        Modify an existing plugin meta in the ChRIS store.
        """
        url = self.get_url('plugin_metas')
        query_url = url + 'search/'
        search_params = {'name_exact': name}
        collection = self.get(query_url, search_params)
        url = collection.items[0].href
        data = {'public_repo': public_repo}
        if new_owner:
            data['new_owner'] = new_owner
        collection = self.put(url, data)
        result = self.get_data_from_collection(collection)
        return result['data'][0]

    def remove_plugin_meta(self, id):
        """
        Remove an existing plugin from the ChRIS store.
        """
        url = self.get_url('plugin_metas')
        query_url = url + 'search/'
        search_params = {'id': id}
        collection = self.get(query_url, search_params)
        url = collection.items[0].href
        self.delete(url)

    def _get_item_descriptors(self, item):
        """
        Internal method to get an item's data (descriptors) in a dictionary.
        """
        item_dict = {}
        # collect the item's descriptors
        for descriptor in item.data:
            item_dict[descriptor.name] = descriptor.value
        return item_dict

    def get(self, url, params=None):
        """
        Internal method to make a GET request to the ChRIS store.
        """
        headers = {'Content-Type': self.content_type, 'Accept': self.content_type}
        try:
            if self.username or self.password:
                r = requests.get(url,
                                 params=params,
                                 auth=(self.username, self.password),
                                 timeout=self.timeout, headers=headers)
            else:
                r = requests.get(url, params=params, timeout=self.timeout,
                                 headers=headers)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        return self._get_collection_from_response(r)

    def post(self, url, data, descriptor_file=None):
        """
        Internal method to make a POST request to the ChRIS store.
        """
        return self._post_put(requests.post, url, data, descriptor_file)

    def put(self, url, data, descriptor_file=None):
        """
        Internal method to make a PUT request to the ChRIS store.
        """
        return self._post_put(requests.put, url, data, descriptor_file)

    def delete(self, url):
        """
        Internal method to make a DELETE request to the ChRIS store.
        """
        try:
            if self.username or self.password:
                r = requests.delete(url,
                                    auth=(self.username, self.password),
                                    timeout=self.timeout)
            else:
               r = requests.delete(url, timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))

    def _post_put(self, request_method, url, data, descriptor_file=None):
        """
        Internal method to make either a POST or PUT request to the ChRIS store.
        """
        if descriptor_file is None:
            headers = {'Content-Type': self.content_type, 'Accept': self.content_type}
            files = None
            data = json.dumps(self._makeTemplate(data))
        else:
            # this is a multipart request
            headers = None
            files = {'descriptor_file': descriptor_file}
        try:
            if self.username or self.password:
                r = request_method(url, files=files, data=data,
                                   auth=(self.username, self.password),
                                   timeout=self.timeout, headers=headers)
            else:
                r = request_method(url, files=files, data=data, timeout=self.timeout,
                                   headers=headers)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        return self._get_collection_from_response(r)

    @staticmethod
    def _get_collection_from_response(response):
        """
        Internal method to get the collection object from a response object.
        """
        content = json.loads(response.text)
        total = content['collection'].pop('total', None)
        collection = Collection.from_json(json.dumps(content))
        if collection.error:
            raise StoreRequestException(collection.error.message)
        if total is not None:
            collection.total = total
        return collection

    @staticmethod
    def _get_link_relation_urls(obj, relation_name):
        """
        Internal method to get the list of urls for a link relation in a collection or
        item object.
        """
        return [link.href for link in obj.links if link.rel == relation_name]

    @staticmethod
    def _makeTemplate(descriptors_dict):
        """
        Internal method to make a Collection+Json template from a regular dictionary whose
        properties are the item descriptors.
        """
        template = {'data': []}
        for key in descriptors_dict:
            template['data'].append({'name': key, 'value': descriptors_dict[key]})
        return {'template': template}
