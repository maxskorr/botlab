import json
from abc import abstractmethod

from pymongo import MongoClient
import redis


class KVStorage(object):
    def __init__(self, config):
        self._config = config

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def exists(self, key):
        pass


class RedisKVStorage(KVStorage):
    def __init__(self, config):
        super().__init__(config)

        redis_host = config['host']
        redis_port = config['port']
        redis_db = config['db']

        self._redis = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

    def get(self, key):
        found_val = self._redis.get(key)

        if found_val is None:
            return None

        result = found_val.decode('utf-8')

        return json.loads(result, encoding='utf-8')

    def set(self, key, value):
        str_value = json.dumps(value)
        self._redis.set(key, str_value)

    def exists(self, key):
        return self._redis.exists(key)


class InMemoryKVStorage(KVStorage):
    def __init__(self):
        super().__init__(None)
        self._kv_storage = {}

    def get(self, key):
        return self._kv_storage.get(key)

    def exists(self, key):
        return key in self._kv_storage.keys()

    def set(self, key, value):
        self._kv_storage[key] = value


class MongoKVStorage(KVStorage):
    def __init__(self, config):
        super().__init__(config)

        mongo_host = config['host']
        mongo_port = config['port']
        mongo_db_name = config['db']
        mongo_collection = config['collection']

        self._collection = MongoClient(host=mongo_host, port=mongo_port)[mongo_db_name][mongo_collection]

    def get(self, key):
        found_val = self._collection.find_one({'key': key})

        return found_val

    def set(self, key, value):
        self._collection.update_one({'key': key}, {'$set': value}, upsert=True)

    def exists(self, key):
        return self._collection.count({'key': key}) > 0
