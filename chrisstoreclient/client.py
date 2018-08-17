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

    def __init__(self, store_url, username=None, password=None, timeout=30):
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
        plugins = self.get_plugins(**search_params)
        if plugins:
            return plugins[0] # plugin names are unique

    def get_plugins(self, **search_params):
        """
        Get the data (descriptors and parameters) of a list of plugins given query
        search parameters. If no search parameters is given then return all plugins
        in the store.
        """
        if search_params:
            collection = self._get(self.store_query_url, search_params)
        else:
            collection = self._get(self.store_url)
        # follow the 'parameters' link relation in each collection document
        return self._get_items_from_paginated_collections(collection, ['parameters'])

    def get_authenticated_user_plugins(self):
        """
        Get the data (descriptors and parameters) of the plugins owned by the
        currently authenticated user.
        """
        collection = self._get(self.store_url)
        return self._get_items_from_paginated_collections(collection, ['parameters'])

    def add_plugin(self, name, dock_image, descriptor_file, public_repo):
        """
        Add a new plugin to the ChRIS store.
        """
        data = {'name': name, 'dock_image': dock_image, 'public_repo': public_repo}
        url = self.store_url
        self._post(url, data, descriptor_file)

    def modify_plugin(self, name, dock_image, descriptor_file, public_repo, newname = ''):
        """
        Modify an existing plugin in the ChRIS store.
        """
        search_params = {'name': name}
        collection = self._get(self.store_query_url, search_params)
        url = collection.items[0].href
        if newname:
            name = newname
        data = {'name': name, 'dock_image': dock_image, 'public_repo': public_repo}
        self._put(url, data, descriptor_file)

    def remove_plugin(self, name):
        """
        Remove an existing plugin from the ChRIS store.
        """
        search_params = {'name': name}
        collection = self._get(self.store_query_url, search_params)
        url = collection.items[0].href
        self._delete(url)

    def _get_items_from_paginated_collections(self, collection, follow_link_relations=[]):
        """
        Internal method to recursively get the data (descriptors and related item's
        descriptors) of all the items in a linked list of paginated collections.
        """
        if 'next' in follow_link_relations:
            follow_link_relations.remove('next')
        item_list = []
        # get the collection documents from all pages
        collections = self._get_paginated_collections(collection)
        for collection in collections:
            item_dict_list = []
            items = collection.items
            # for each item get its data and the data of all related items in a
            # depth-first search
            for item in items:
                item_dict = self._get_item_descriptors(item)
                for link_relation in follow_link_relations:
                    related_urls = self._get_link_relation_urls(item, link_relation)
                    if related_urls and (link_relation not in item_dict):
                        item_dict[link_relation] = []
                    for url in related_urls:
                        coll = self._get(url)
                        item_dict[link_relation].extend(
                            self._get_items_from_paginated_collections(
                                coll, follow_link_relations))
                item_dict_list.append(item_dict)
            item_list.extend(item_dict_list)
        return item_list

    def _get_item_descriptors(self, item):
        """
        Internal method to get an item's data (descriptors) in a dictionary.
        """
        item_dict = {}
        # collect the item's descriptors
        for descriptor in item.data:
            item_dict[descriptor.name] = descriptor.value
        return item_dict

    def _get_paginated_collections(self, collection):
        """
        Internal method to get a list of paginated collection objects.
        """
        collections = []
        while True:
            collections.append(collection)
            next_page_urls = self._get_link_relation_urls(collection, 'next')
            if next_page_urls:
                # there is only a single next page
                collection = self._get(next_page_urls[0])
            else:
                break
        return collections

    def _get(self, url, params=None):
        """
        Internal method to make a GET request to the ChRIS store.
        """
        try:
            if self.username or self.password:
                r = requests.get(url,
                                 params=params,
                                 auth=(self.username, self.password),
                                 timeout=self.timeout)
            else:
                r = requests.get(url, params=params, timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))
        return self._get_collection_from_response(r)

    def _post(self, url, data, descriptor_file):
        """
        Internal method to make a POST request to the ChRIS store.
        """
        return self._post_put(requests.post, url, data, descriptor_file)

    def _put(self, url, data, descriptor_file):
        """
        Internal method to make a PUT request to the ChRIS store.
        """
        return self._post_put(requests.put, url, data, descriptor_file)

    def _delete(self, url):
        """
        Internal method to make a DELETE request to the ChRIS store.
        """
        try:
            if self.username or self.password:
                requests.delete(url,
                                auth=(self.username, self.password),
                                timeout=self.timeout)
            else:
                requests.delete(url, timeout=self.timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise StoreRequestException(str(e))

    def _post_put(self, request_method, url, data, descriptor_file):
        """
        Internal method to make either a POST or PUT request to the ChRIS store.
        """
        files = {'descriptor_file': descriptor_file}
        try:
            if self.username or self.password:
                r = request_method(url, files=files, data=data,
                                   auth=(self.username, self.password),
                                   timeout=self.timeout)
            else:
                r = request_method(url, files=files, data=data, timeout=self.timeout)
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
    def _get_link_relation_urls(obj, relation_name):
        """
        Internal method to get the list of urls for a link relation in a collection or
        item object.
        """
        return [link.href for link in obj.links if link.rel == relation_name]
