import json

import telebot

from botlab import storage
from botlab.exceptions import UnknownStorageException


class BotLab(telebot.TeleBot):
    def __init__(self, config, threaded=True, skip_pending=False):
        super().__init__(config['bot']['token'], threaded=threaded, skip_pending=skip_pending)

        self.config = config
        self.l10n = L10n(config['l10n']['file_path'])

        storage_type = config['storage']['type']
        storage_params = config['storage']['params']

        if storage_type == 'mongo':
            self.storage = storage.MongoStorage(storage_params)
        elif storage_type == 'inmemory':
            self.storage = storage.InMemoryStorage(storage_params)
        elif storage_type == 'disk':
            self.storage = storage.DiskStorage(storage_params)
        else:
            raise UnknownStorageException()

    def _get_session(self, chat_id):
        return Session(self, chat_id, self.l10n, self.storage)

    def _get_session_from_any(self, any):
        if isinstance(any, telebot.types.Message):
            return self._get_session(any.chat.id)
        elif isinstance(any, telebot.types.CallbackQuery):
            callback_query = any

            if callback_query.message is not None and callback_query.message.chat is not None:
                return self._get_session(callback_query.message.chat.id)
            else:
                return self._get_session(callback_query.from_user.id)
        else:
            return None

    def _exec_task(self, task, *args, **kwargs):
        args = list(args)
        session = self._get_session_from_any(args[0])

        args.insert(0, session)

        return super()._exec_task(task, *args, **kwargs)

    def message_handler(self, state=None, commands=None, regexp=None, func=None, content_types=['text']):
        return super().message_handler(commands=commands, regexp=regexp,
                                       func=func, content_types=content_types,
                                       state=state)

    def callback_query_handler(self, inline_state=None, func=None, state=None):
        return super().callback_query_handler(func=func, inline_state=inline_state, state=state)

    def _test_filter(self, filter, filter_value, message):
        test_result = super()._test_filter(filter, filter_value, message)

        if test_result:
            return True

        if filter == 'state':
            session = self._get_session_from_any(message)

            if session.get_state() == filter_value:
                return True

        if filter == 'inline_state':
            session = self._get_session_from_any(message)

            if session.get_inline_state() == filter_value:
                return True

        return False


class Session(object):
    SESSIONS_COLLECTION = 'sessions'

    def __init__(self, bot, chat_id, l10n, storage):
        self.bot = bot
        self.chat_id = chat_id
        self.storage = storage

        self._translator = l10n.translator(self.get_lang())

    def profile(self):
        return self.storage.collection(Session.SESSIONS_COLLECTION)

    def get_field(self, key):
        return self.profile().get_field(key, chat_id=self.chat_id)

    def set_field(self, key, value):
        return self.profile().set_field(key, value, multi=False, chat_id=self.chat_id)

    def _(self, key, **kwargs):
        return self._translator(key, **kwargs)

    def get_lang(self):
        found_lang_values = self.profile().get_field('lang')
        found_lang = None

        if len(found_lang_values) < 1:
            found_lang = self.bot.config['l10n']['default_lang']
            self.set_field('lang', found_lang)
        else:
            found_lang = found_lang_values[0]

        return found_lang

    def set_lang(self, new_lang):
        return self.set_field('lang', new_lang)

    def get_state(self):
        found_state_values = self.get_field('state')
        found_state = None

        if len(found_state_values) == 0:
            found_state = self.bot.config['bot']['initial_state']
            self.set_state(found_state)
        else:
            found_state = found_state_values[0]

        return found_state

    def set_state(self, new_state):
        return self.set_field('state', new_state)

    def get_inline_state(self):
        found_inline_state_values = self.get_field('inline_state')
        found_inline_state = None

        if len(found_inline_state_values) == 0:
            found_inline_state = self.bot.config['bot']['initial_inline_state']
            self.set_inline_state(found_inline_state)
        else:
            found_inline_state = found_inline_state_values[0]

        return found_inline_state

    def set_inline_state(self, new_state):
        return self.set_field('inline_state', new_state)

    def reply_message(self, text, *args, **kwargs):
        return self.bot.send_message(self.chat_id, text, **kwargs)

    def collection(self, collection_name):
        return self.storage.collection(collection_name)


class L10n(object):
    def __init__(self, locale_filename):
        self.locale = json.load(open(locale_filename))

    def translator(self, lang):
        def translate(key, **kwargs):
            return self.locale[key][lang].format(**kwargs)

        return translate
