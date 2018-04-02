"""
ChRIS store API client module.
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
        self.username = username
        self.password = password
        self.timeout = timeout

    def get_plugin(self, plugin_name):
        """
        Get a plugin's information (descriptors and parameters) given its ChRIS store
        name.
        """
        plugin = {}
        search_params = {'name': plugin_name}
        items = self._get(self.store_url + 'search/', search_params)
        if items:
            # collect the plugin's descriptors
            item = items[0]
            for descriptor in item.data:
                plugin[descriptor.name] = descriptor.value
            # collect the plugin's parameters descriptors
            params_url = [link for link in item.links if link.rel == 'parameters'][0].href
            items = self._get(params_url)
            params = []
            for item in items:
                param = {}
                for descriptor in item.data:
                    param[descriptor.name] = descriptor.value
                params.append(param)
            plugin['parameters'] = params
        return plugin

    def _get(self, url, params=None):
        """
        Internal method to make a GET request to the ChRIS store.
        """
        try:
            r = requests.get(url,
                             params=params,
                             auth=(self.username, self.username),
                             timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        collection = Collection.from_json(r.text)
        if collection.error:
            raise StoreRequestException(collection.error.message)
        return collection.items
