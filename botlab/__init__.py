import json

import telebot
import pymongo


class BotLab(telebot.TeleBot):
    def __init__(self, config, threaded=True, skip_pending=False):
        super().__init__(config['bot']['token'], threaded=threaded, skip_pending=skip_pending)

        self.config = config
        self.l10n = L10n(config['l10n']['file_path'])

    def _get_session(self, chat_id):
        return Session(self, chat_id, self.l10n)

    def _exec_task(self, task, *args, **kwargs):
        args = list(args)
        session = None

        if isinstance(args[0], telebot.types.Message):
            session =  self._get_session(args[0].chat.id)
        else:
            session = None

        args.insert(0, session)

        return super()._exec_task(task, *args, **kwargs)

    def message_handler(self, state=None, commands=None, regexp=None, func=None, content_types=['text']):
        return super().message_handler(commands=commands, regexp=regexp,
                                       func=func, content_types=content_types,
                                       state=state)

    def _test_filter(self, filter, filter_value, message):
        test_result = super()._test_filter(filter, filter_value, message)

        if test_result:
            return True

        if filter == 'state':
            session = self._get_session(message.chat.id)
            return session.get_state() == filter_value

        return False


class Session(object):
    SESSIONS_COLLECTION = 'sessions'

    def __init__(self, bot, chat_id, l10n):
        self.bot = bot
        self.chat_id = chat_id

        mongo_client = pymongo.MongoClient(bot.config['database']['host'], bot.config['database']['port'])

        self.db = mongo_client[bot.config['database']['database_name']]

        self._translator = l10n.translator(self.get_lang())

    def get_field(self, key):
        return self.collection(Session.SESSIONS_COLLECTION) \
            .distinct(key, {'chat_id': self.chat_id})

    def set_field(self, key, value):
        return self.collection(Session.SESSIONS_COLLECTION) \
            .update({'chat_id': self.chat_id}, {'$set': {key: value}}, upsert=True)

    def _(self, key, **kwargs):
        return self._translator(key, **kwargs)

    def get_lang(self):
        found_lang_values = self.get_field('lang')
        found_lang = None

        if len(found_lang_values) == 0:
            found_lang = self.bot.config['l10n']['default_lang']
            self.set_field('lang', found_lang)
        else:
            found_lang = found_lang_values[0]

        return found_lang

    def get_state(self):
        found_state_values = self.get_field('state')
        found_state = None

        if len(found_state_values) == 0:
            found_state = self.bot.config['bot']['initial_state']
            self.set_field('state', found_state)
        else:
            found_state = found_state_values[0]

        return found_state

    def set_state(self, new_state):
        return self.set_field('state', new_state)

    def reply_message(self, text, *args, **kwargs):
        return self.bot.send_message(self.chat_id, text)

    def collection(self, collection_name):
        return self.db[collection_name]


class L10n(object):
    def __init__(self, locale_filename):
        self.locale = json.load(open(locale_filename))

    def translator(self, lang):
        def translate(key, **kwargs):
            return self.locale[key][lang].format(**kwargs)

        return translate
