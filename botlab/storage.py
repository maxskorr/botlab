import json
from abc import abstractmethod
from functools import reduce

import pymongo


class Collection(object):
    pass


class Storage(object):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_field(self, collection_name, key, **filter_options):
        pass

    @abstractmethod
    def set_field(self, collection_name, key, new_value, multi=False, **filter_options):
        pass

    def collection(self, collection_name):
        coll = Collection()

        def decorated_get_field(key, **filter_options):
            return self.get_field(collection_name, key, **filter_options)

        def decorated_set_field(key, new_value, multi=False, **filter_options):
            return self.set_field(collection_name, key, new_value, multi=multi, **filter_options)

        decorated_get_field.__name__ = 'get_field'
        decorated_set_field.__name__ = 'set_field'

        setattr(coll, decorated_get_field.__name__, decorated_get_field)
        setattr(coll, decorated_set_field.__name__, decorated_set_field)

        return coll


class InMemoryStorage(Storage):
    def __init__(self, config):
        super().__init__(config)
        self.store = {}

    def get_field(self, collection_name, key, **filter_options):
        arr = self.store.get(collection_name, [])

        if len(arr) < 1:
            return []

        reduce_filter_func = lambda dict_key, elem, res: \
            res and (elem.get(dict_key) == filter_options.get(dict_key))

        arr_elem_meets_filter = lambda elem: reduce(lambda res, dict_key: reduce_filter_func(dict_key, elem, res), filter_options.keys(), True)

        filtered_arr = tuple(filter(lambda elem: arr_elem_meets_filter(elem), arr))

        if len(filtered_arr) < 1:
            return []

        resulting_arr = list(filter(lambda elem: elem is not None, map(lambda elem: elem.get(key, None), filtered_arr)))

        return resulting_arr

    def set_field(self, collection_name, key, new_value, multi=False, **filter_options):
        collection = self.store.get(collection_name, [])

        def create_new_obj(filter_options, key, new_value):
            obj = dict(filter_options)
            obj[key] = new_value

            return obj

        if len(collection) < 1:
            collection = []
            self.store[collection_name] = collection

            collection.append(create_new_obj(filter_options, key, new_value))

            return True

        def find_conforming_obj(collection, filter_options):
            for obj in collection:
                conforms = True

                for filter_key in filter_options.keys():
                    if obj.get(filter_key) != filter_options[filter_key]:
                        conforms = False
                        break

                if conforms:
                    return obj

            return None

        found_obj = find_conforming_obj(collection, filter_options)

        if found_obj is None:
            collection.append(create_new_obj(filter_options, key, new_value))
        else:
            found_obj[key] = new_value

        return True


class DiskStorage(InMemoryStorage):
    def __init__(self, config):
        super().__init__(config)

        self.storage_file_path = config['file_path']

        try:
            self.store = json.load(open(self.storage_file_path, 'r'))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.store = {}


    def set_field(self, collection_name, key, new_value, multi=False, **filter_options):
        result = super().set_field(collection_name, key, new_value, multi, **filter_options)

        json.dump(self.store, open(self.storage_file_path, 'w'))

        return result

    def get_field(self, collection_name, key, **filter_options):
        result = super().get_field(collection_name, key, **filter_options)
        return result


class MongoStorage(Storage):
    def __init__(self, config):
        super().__init__(config)

        mongo_client = pymongo.MongoClient(config['host'], config['port'])

        self.db = mongo_client[config['database']]

    def set_field(self, collection_name, key, new_value, multi=False, **filter_options):
        return self.db[collection_name].update(filter_options, {'$set': {key: new_value}}, upsert=True, multi=multi)

    def get_field(self, collection_name, key, **filter_options):
        return self.db[collection_name].distinct(key, filter_options)

