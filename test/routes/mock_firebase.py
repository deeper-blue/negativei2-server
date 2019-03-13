import uuid
import copy
import time
import copy
from collections import defaultdict
from unittest.mock import MagicMock

# firebase_admin mocks

class MockAuth(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users = {}

    def get_user(self, user_id):
        """https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth#get_user"""
        try:
            return copy.deepcopy(self.users[user_id])
        except:
            raise self.AuthError("User doesn't exist")

    def _mock_add_user(self, user_id, data={}):
        """Helper function to add a user for setting up mock"""
        self.users[user_id] = copy.deepcopy(data)

    class AuthError(Exception):
        """https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth#firebase_admin.auth.AuthError"""
        pass

# firestore mocks

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

    def where(self, path, op_string, value):
        query = MockQuery(self)
        return query.where(path, op_string, value)

class MockDocumentReference(MagicMock):
    def __init__(self, id_, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exists = False
        self.data = None
        self.id = id_

    def to_dict(self):
        return copy.deepcopy(self.data)

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

class MockQuery(MagicMock):
    def __init__(self, collection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collection = collection
        self.matching = copy.deepcopy(collection.documents)

    def where(self, path, op_string, value):
        path_components = path.split('.')
        new_matching = {}
        for id_, doc in self.matching.items():
            # drill down through doc to check condition, this is our pointer
            doc_pointer = doc.data
            for component in path_components:
                doc_pointer = doc_pointer.get(component, None)
                if doc_pointer is None:
                    # If the path doesn't exist in this doc
                    break
            else:
                # If we don't break
                matched = False
                if op_string == '<':
                    matched = doc_pointer < value
                elif op_string == '<=':
                    matched = doc_pointer <= value
                elif op_string == '==':
                    matched = doc_pointer == value
                elif op_string == '>=':
                    matched = doc_pointer >= value
                elif op_string == '>':
                    matched = doc_pointer > value
                if matched:
                    new_matching[id_] = doc

        self.matching = new_matching
        return self

    def get(self):
        return self.matching.values()


class keydefaultdict(defaultdict):
    """ Overrides defaultdict to pass the key to the factory """
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret
