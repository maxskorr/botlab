import json
from abc import abstractmethod
from argparse import ArgumentTypeError
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

    # work with entire objects from collection
    # TODO: add deprecations

    @abstractmethod
    def get_object(self, collection_name, filter_options, multi=False):
        pass

    @abstractmethod
    def set_object(self, collection_name, new_object, filter_options, multi=False):
        pass

    @staticmethod
    def remove_object(self, collection_name, filter_options, multi=False):
        pass

    def collection(self, collection_name):
        coll = Collection()

        def decorated_get_field(key, **filter_options):
            return self.get_field(collection_name, key, **filter_options)

        def decorated_set_field(key, new_value, multi=False, **filter_options):
            return self.set_field(collection_name, key, new_value, multi=multi, **filter_options)

        def decorated_get_object(filter_options, multi=False):
            return self.get_object(collection_name, filter_options, multi)

        def decorated_set_object(new_object, filter_options, multi=False):
            return self.set_object(collection_name, new_object, filter_options, multi)

        def decorated_remove_object(filter_options, multi=False):
            return self.remove_object(collection_name, filter_options, multi)

        decorated_get_field.__name__ = 'get_field'
        decorated_set_field.__name__ = 'set_field'
        decorated_get_object.__name__ = 'get_object'
        decorated_set_object.__name__ = 'set_object'
        decorated_remove_object.__name__ = 'remove_object'

        setattr(coll, decorated_get_field.__name__, decorated_get_field)
        setattr(coll, decorated_set_field.__name__, decorated_set_field)
        setattr(coll, decorated_get_object.__name__, decorated_get_object)
        setattr(coll, decorated_set_object.__name__, decorated_set_object)
        setattr(coll, decorated_remove_object.__name__, decorated_remove_object)

        return coll


class InMemoryStorage(Storage):
    def __init__(self, config):
        super().__init__(config)
        self.store = {}

    @staticmethod
    def _find_conforming_objects(collection, filter_options):
        conforming_objects = []

        for obj in collection:
            conforms = True

            for filter_key in filter_options.keys():
                if obj.get(filter_key) != filter_options[filter_key]:
                    conforms = False
                    break

            if conforms:
                # object fully conforms
                conforming_objects.append(obj)

        return conforming_objects

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

    def get_object(self, collection_name, filter_options, multi=False):
        if filter_options is None or not isinstance(filter_options, dict) or len(filter_options.keys()) < 1:
            raise ArgumentTypeError('filter_options must be a non-empty dict!')

        arr = self.store.get(collection_name, [])

        if len(arr) < 1:
            if multi:
                return []
            return None

        reduce_filter_func = lambda dict_key, elem, res: \
            res and (elem.get(dict_key) == filter_options.get(dict_key))

        arr_elem_meets_filter = lambda elem: reduce(lambda res, dict_key: reduce_filter_func(dict_key, elem, res),
                                                    filter_options.keys(), True)

        filtered_arr = list(filter(lambda elem: arr_elem_meets_filter(elem), arr))

        if len(filtered_arr) < 1:
            if multi:
                return []
            else:
                return None

        if multi:
            return filtered_arr
        else:
            return filtered_arr[0]

    def set_object(self, collection_name, new_object, filter_options, multi=False):
        if filter_options is None or not isinstance(filter_options, dict) or len(filter_options.keys()) < 1:
            raise ArgumentTypeError('filter_options must be a non-empty dict!')

        collection = self.store.get(collection_name, [])

        if len(collection) < 1:
            self.store[collection_name] = collection

            collection.append(new_object)

            return True

        found_objects = self._find_conforming_objects(collection, filter_options)

        if len(found_objects) > 0:
            for found_object in found_objects:
                collection.remove(found_object)

                if not multi:
                    # we've already removed one
                    break

        collection.append(new_object)

        return True

    def remove_object(self, collection_name, filter_options, multi=False):
        if filter_options is None or not isinstance(filter_options, dict) or len(filter_options.keys()) < 1:
            raise ArgumentTypeError('filter_options must be a non-empty dict!')

        collection = self.store.get(collection_name, [])

        if len(collection) < 1:
            return False

        found_objects = self._find_conforming_objects(collection, filter_options)

        if len(found_objects) > 0:
            for found_object in found_objects:
                collection.remove(found_object)

                if not multi:
                    # we've already removed one
                    break
        else:
            return False

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

    def set_object(self, collection_name, new_object, filter_options, multi=False):
        result = super().set_object(collection_name, new_object, filter_options, multi)

        json.dump(self.store, open(self.storage_file_path, 'w'))

        return result

    def get_object(self, collection_name, filter_options, multi=False):
        result = super().get_object(collection_name, filter_options, multi)
        return result

    def remove_object(self, collection_name, filter_options, multi=False):
        result = super().remove_object(collection_name, filter_options, multi)

        json.dump(self.store, open(self.storage_file_path, 'w'))

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

    def get_object(self, collection_name, filter_options, multi=False):
        if multi:
            return self.db[collection_name].find(filter_options)
        else:
            return self.db[collection_name].find_one(filter_options)

    def set_object(self, collection_name, new_object, filter_options, multi=False):
        return self.db[collection_name].update(filter_options, new_object, upsert=True, multi=multi)

    def remove_object(self, collection_name, filter_options, multi=False):
        if multi:
            return self.db[collection_name].delete_many(filter_options)
        else:
            return self.db[collection_name].delete_one(filter_options)
