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
        self.documents = keydefaultdict(MockDocument)

    def document(self, document_name):
        return self.documents[document_name]

class MockDocument(MagicMock):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference = MockDocumentReference()

    def get(self):
        return self.reference

class MockDocumentReference(MagicMock):
    #TODO: Implement creating documents
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exists = False

class keydefaultdict(defaultdict):
    """ Overrides defaultdict to pass the key to the factory """
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret
