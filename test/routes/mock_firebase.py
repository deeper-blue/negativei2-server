import uuid
import time
import copy
from collections import defaultdict
from unittest.mock import MagicMock

class MockClient(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # keeps track of existing collections and creates them on the fly
        self.collections = keydefaultdict(MockCollection)

    def collection(self, collection_name):
        return self.collections[collection_name]

class MockCollection(MagicMock):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.documents = keydefaultdict(MockDocumentReference)

    def document(self, document_name=None):
        if document_name is None:
            document_name = str(uuid.uuid4())
        return self.documents[document_name]

    def add(self, document_data, document_id=None):
        if document_id is None:
            document_id = str(uuid.uuid4())
        doc = self.documents[document_id]
        doc.data = copy.deepcopy(document_data)
        doc.exists = True
        return time.time(), doc

class MockDocumentReference(MagicMock):
    def __init__(self, id_, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exists = False
        self.data = None
        self.id = id_

    def to_dict(self):
        return self.data

    def get(self):
        return self

    def create(self, data):
        self.data = copy.deepcopy(data)
        self.exists = True
        # Should return a 'WriteResult' but not currently using

    def set(self, data):
        self.data = copy.deepcopy(data)
        self.exists = True
        # Should return a 'WriteResult' but not currently using

class keydefaultdict(defaultdict):
    """ Overrides defaultdict to pass the key to the factory """
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret
