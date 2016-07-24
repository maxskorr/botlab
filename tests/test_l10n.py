import unittest

from botlab import ConfigurationManager, L10n


class TestL10n(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'config': {
                'sync_strategy': 'cold'
            },
            'kv_storage': {
                'type': 'inmemory'
            },
            'l10n': {
                'default_lang': 'en',
                'file_path': 'assets/l10n.json'
            }
        }
        self.cm = ConfigurationManager(self.settings)
        self.l10n = L10n(self.cm)
        self._ = self.l10n.translator('en')

    def test_can_translate(self):
        self.assertEqual(self._('hello', name='Max'), 'hello, Max!')

    def test_return_none_when_faced_unknown_field(self):
        self.assertEqual(self._('zbc'), None)

