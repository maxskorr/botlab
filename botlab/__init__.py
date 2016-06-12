import telebot
import pymongo


class BotLab(telebot.TeleBot):
    def __init__(self, token, db_config, threaded=True, skip_pending=False):
        super().__init__(token, threaded=threaded, skip_pending=skip_pending)

        self.db_config = db_config


    def add_message_handler(self, handler, commands=None, regexp=None, func=None, content_types=None):
        '''Overridden to add session argument to handler call. '''
        bot = self

        def handler_with_session(message):
            session = Session(bot, message.chat.id)
            return handler(session, message)

        return super().add_message_handler(handler_with_session, commands, regexp, func, content_types)


class Session(object):
    SESSIONS_COLLECTION = 'sessions'

    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

        mongo_client = pymongo.MongoClient(bot.db_config['host'], bot.db_config['port'])

        self.db = mongo_client[bot.db_config['database']]


    def reply_message(self, text, *args, **kwargs):
        self.bot.send_message(self.chat_id, text)


    def collection(self, collection_name):
        return self.db[collection_name]

