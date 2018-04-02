
import unittest

from chrisstoreclient.client import StoreClient


class StoreClientTests(unittest.TestCase):

    def setUp(self):
        self.store_url = "http://localhost:8010/api/v1/"
        self.username = "cubeadmin"
        self.password = "cubeadmin1234"
        self.client = StoreClient(self.store_url,
                                  self.username,
                                  self.password)

    def test_get_plugin(self):
        """
        Test whether get_plugin method can get a plugin representation from the ChRIS
        store.
        """
        pass

