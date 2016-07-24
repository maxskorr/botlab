import unittest

from botlab import ConfigurationManager
from botlab.exceptions import WrongConfigurationException


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.basic_settings = {
            'config': {
                'sync_strategy': None
            },
            'kv_storage': {
                'type': 'redis',
                'params': {
                    'host': '10.0.75.1',
                    'port': 6379,
                    'db': 0
                }
            },
            'l10n': {
                'default_lang': 'en',
                'file_path': 'assets/l10n.json'
            }
        }

    def test_cant_be_created_without_sync_strategy(self):
        with self.assertRaises(WrongConfigurationException):
            ConfigurationManager(self.basic_settings)

    def test_cold_sync(self):
        settings = self.basic_settings
        settings['config']['sync_strategy'] = 'cold'

        cm = ConfigurationManager(settings)
        l10n = cm.get('l10n')

        self.assertEqual(l10n.get('default_lang'), 'en')

        l10n['default_lang'] = 'ru'

        cm.set('l10n', l10n)

        self.assertEqual(cm.get('l10n').get('default_lang'), 'ru')

    def test_hot_sync_impossible_without_type(self):
        settings = self.basic_settings
        settings['config']['sync_strategy'] = 'hot'

        with self.assertRaises(WrongConfigurationException):
            ConfigurationManager(settings)

    def test_hot_sync(self):
        settings = self.basic_settings
        settings['config']['sync_strategy'] = 'hot'
        settings['kv_storage']['type'] = 'inmemory'

        cm = ConfigurationManager(settings)
        l10n = cm.get('l10n')

        self.assertEqual(l10n.get('default_lang'), 'en')

        l10n['default_lang'] = 'ru'

        cm.set('l10n', l10n)

        self.assertEqual(cm.get('l10n').get('default_lang'), 'ru')



