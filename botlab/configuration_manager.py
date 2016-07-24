import json

from botlab.exceptions import NoConfigurationProvidedException, NoKVStorageProvidedException, \
    WrongConfigurationException, UnsupportedKVStorageException
from botlab.kv_storage import RedisKVStorage, InMemoryKVStorage, MongoKVStorage


class ConfigurationManager(object):
    """
        Enables synchronization of configuration with a key-value storage.

        There are two strategies of synchronization:
            * cold - any changes've been made to configuration manager are
                only stored in memory, but never synchronized with the original
                configuration file.
                ! Imposes the use of 'inmemory' kv-storage implementation.
            * hot - all the changes that have been made to configuration manager
                are immediately saved to kv-storage.
                When starting application, every high-level key of configuration
                file is checked against kv-storage keys. Only those keys absent
                in kv-storage are taken from the original configuration,
                others - from kv-storage.
    """
    def __init__(self, config_dict, *args, **kwargs):
        if config_dict is None:
            raise NoConfigurationProvidedException()

        if 'config' not in config_dict.keys() or 'sync_strategy' not in config_dict['config'].keys():
            raise WrongConfigurationException('config and/or config.sync_strategy is not set')

        self._sync_strategy = config_dict['config']['sync_strategy']

        if self._sync_strategy == 'hot':
            if 'kv_storage' not in config_dict.keys():
                raise NoKVStorageProvidedException()

            if 'type' not in config_dict['kv_storage'].keys():
                raise WrongConfigurationException('kv_storage.type is not set')

            if 'params' not in config_dict['kv_storage'].keys():
                raise WrongConfigurationException('kv_storage.params is not set')

            kv_storage_type = config_dict['kv_storage']['type']

            if kv_storage_type == 'redis':
                self._kv_storage = RedisKVStorage(config_dict['kv_storage']['params'])
            elif kv_storage_type == 'mongo':
                self._kv_storage = MongoKVStorage(config_dict['kv_storage']['params'])
            elif kv_storage_type == 'inmemory':
                self._kv_storage = InMemoryKVStorage()
            else:
                raise UnsupportedKVStorageException()
        elif self._sync_strategy == 'cold':
            self._kv_storage = InMemoryKVStorage()
        else:
            raise WrongConfigurationException('Unknown config.sync_strategy value')

        # load config from the dictionary provided
        self._setup_from_dictionary_(config_dict)

    def _setup_from_dictionary_(self, config_dict):
        if config_dict is None:
            raise NoConfigurationProvidedException()

        kv_storage = self._kv_storage

        if kv_storage is None:
            raise NoKVStorageProvidedException()

        for key in config_dict.keys():
            if not kv_storage.exists(key):
                kv_storage.set(key, config_dict[key])

    def get(self, key, default=None):
        found_val = self._kv_storage.get(key)

        if found_val is None:
            return None
        else:
            return found_val

    def set(self, key, value):
        self._kv_storage.set(key, value)

