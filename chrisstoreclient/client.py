"""
ChRIS store API client module.
An item in a collection is represented by a dictionary. A collection of items is
represented by a list of dictionaries.
"""

import requests
from collection_json import Collection

from.exceptions import StoreRequestException


class StoreClient(object):
    """
    A ChRIS store API client.
    """

    def __init__(self, store_url, username, password, timeout=30):
        self.store_url = store_url
        self.store_query_url = store_url + 'search/'
        self.username = username
        self.password = password
        self.timeout = timeout

    def get_plugin(self, plugin_name):
        """
        Get a plugin's information (descriptors and parameters) given its ChRIS store
        name.
        """
        search_params = {'name': plugin_name}
        return self.get_plugins(**search_params)[0]  #plugin names are unique

    def get_plugins(self, **search_params):
        """
        Get the information (descriptors and parameters) of a list of plugins given
        query search parameters. If no search parameters is given then return all
        plugins in the store.
        """
        if search_params:
            collection = self._get(self.store_query_url, search_params)
        else:
            collection = self._get(self.store_url)
            all_plugins_url = self._get_link_relation_url(collection, 'all_plugins')
            collection = self._get(all_plugins_url)
        return self._get_plugins_from_paginated_collections(collection)

    def get_authenticated_user_plugins(self):
        """
        Get the information (descriptors and parameters) of the plugins owned by the
        currently authenticated user.
        """
        collection = self._get(self.store_url)
        return self._get_plugins_from_paginated_collections(collection)

    def add_plugin(self, name, dock_image, descriptor_filename, public_repo):
        """
        Add a new plugin to the ChRIS store.
        """
        params = {'name': name, 'dock_image': dock_image,
                  'public_repo': public_repo, 'descriptor_file': descriptor_filename}
        url = self.store_url
        self._post(url, params)

    def modify_plugin(self, name, dock_image, descriptor_filename, public_repo,
                      newname = ''):
        """
        Modify an existing plugin in the ChRIS store.
        """
        search_params = {'name': name}
        collection = self._get(self.store_query_url, search_params)
        url = collection.href
        if newname:
            name = newname
        params = {'name': name, 'dock_image': dock_image, 'public_repo': public_repo,
                  'descriptor_file': descriptor_filename}
        self._put(url, params)

    def delete_plugin(self, name):
        """
        Delete an existing plugin from the ChRIS store.
        """
        search_params = {'name': name}
        collection = self._get(self.store_query_url, search_params)
        url = collection.href
        self._delete(url)

    def _get_plugins_from_paginated_collections(self, collection):
        """
        Internal method to get the information (descriptors and parameters) of a list of
        plugins distributed into several collection pages.
        """
        plugins = []
        while True:
            plugins.extend(self._get_plugins_from_collection(collection))
            next_page_url = self._get_link_relation_url(collection, 'next')
            if next_page_url:
                collection = self._get(next_page_url)
            else:
                break
        return plugins

    def _get_plugins_from_collection(self, collection):
        """
        Internal method to get the information (descriptors and parameters) of a list of
        plugins in a collection.
        """
        plugins = []
        items = collection.items
        for item in items:
            plugin = {}
            # collect the plugin's descriptors
            for descriptor in item.data:
                plugin[descriptor.name] = descriptor.value
            # collect the plugin's parameters' descriptors
            params_url = self._get_link_relation_url(item, 'parameters')
            collection = self._get(params_url)
            plugin['parameters'] = self._get_parameters_from_paginated_collections(collection)
            plugins.append(plugin)
        return plugins

    def _get_parameters_from_paginated_collections(self, collection):
        """
        Internal method to get the information of a list of plugin parameters
        distributed into several collection pages.
        """
        parameters = []
        while True:
            parameters.extend(self._get_parameters_from_collection(collection))
            next_page_url = self._get_link_relation_url(collection, 'next')
            if next_page_url:
                collection = self._get(next_page_url)
            else:
                break
        return parameters

    def _get_parameters_from_collection(self, collection):
        """
        Internal method to get the information of a list of plugin parameters in a
        collection.
        """
        items = collection.items
        params = []
        for item in items:
            param = {}
            for descriptor in item.data:
                param[descriptor.name] = descriptor.value
            params.append(param)
        return params

    def _get(self, url, params=None):
        """
        Internal method to make a GET request to the ChRIS store.
        """
        try:
            r = requests.get(url,
                             params=params,
                             auth=(self.username, self.password),
                             timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        return self._get_collection_from_response(r)

    def _post(self, url, params):
        """
        Internal method to make a POST request to the ChRIS store.
        """
        return self._post_put(requests.post, url, params)

    def _put(self, url, params):
        """
        Internal method to make a PUT request to the ChRIS store.
        """
        return self._post_put(requests.put, url, params)

    def _delete(self, url):
        """
        Internal method to make a DELETE request to the ChRIS store.
        """
        try:
            r = requests.delete(url,
                             auth=(self.username, self.password),
                             timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        return self._get_collection_from_response(r)

    def _post_put(self, request_method, url, params):
        """
        Internal method to make either a POST or PUT request to the ChRIS store.
        """
        try:
            descriptor_file_name = params['descriptor_file']
            files = {'descriptor_file': open(descriptor_file_name, 'rb')}
        except (KeyError, IOError) as e:
            raise StoreRequestException(str(e))
        data = params
        del data['descriptor_file']
        try:
            r = request_method(url, files=files, data=data,
                               auth=(self.username, self.password),
                               timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        return self._get_collection_from_response(r)

    @staticmethod
    def _get_collection_from_response(response):
        """
        Internal method to get the collection object from a response object.
        """
        collection = Collection.from_json(response.text)
        if collection.error:
            raise StoreRequestException(collection.error.message)
        return collection

    @staticmethod
    def _get_link_relation_url(obj, relation_name):
        """
        Internal method to get the url of a link relation in a collection or item object.
        """
        url = None
        links = [link for link in obj.links if link.rel == relation_name]
        if links:
            url = links[0].href
        return url
