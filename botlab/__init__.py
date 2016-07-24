import json

import telebot

from botlab import storage
from botlab.configuration_manager import ConfigurationManager
from botlab.exceptions import UnknownStorageException, NoConfigurationProvidedException


class BotLab(telebot.TeleBot):
    def __init__(self, config_dict, threaded=True, skip_pending=False):
        if config_dict is None:
            raise NoConfigurationProvidedException()

        config_manager = ConfigurationManager(config_dict)

        super().__init__(config_manager.get('bot').get('token'), threaded=threaded,
                         skip_pending=skip_pending)

        self._config_manager = config_manager
        self._suppress_exceptions = config_manager.get('bot').get('suppress_exceptions')

        self.l10n = L10n(config_manager)

        storage_type = config_manager.get('db_storage').get('type')
        storage_params = config_manager.get('db_storage').get('params')

        if storage_type == 'mongo':
            self._storage = storage.MongoStorage(storage_params)
        elif storage_type == 'inmemory':
            self._storage = storage.InMemoryStorage(storage_params)
        elif storage_type == 'disk':
            self._storage = storage.DiskStorage(storage_params)
        else:
            raise UnknownStorageException()

    def _get_session(self, chat_id):
        return Session(self, chat_id, self.l10n, self._storage, self._config_manager)

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

    def _remit(self, func, *args, **kwargs):
        """
        Prevent function from throwing an exception.

        :param func: function to be called
        :param args: function positional arguments
        :param kwargs: function named arguments
        :return: func result or None if exception was thrown
        """
        if self._suppress_exceptions:
            try:
                return func(*args, **kwargs)
            except:
                return None
        else:
            return func(*args, **kwargs)

    def _exec_task(self, task, *args, **kwargs):
        args = list(args)
        session = self._get_session_from_any(args[0])

        args.insert(0, session)

        if self.threaded:
            self.worker_pool.put(task, *args, **kwargs)
        else:
            task(*args, ** kwargs)

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

        session = self._get_session_from_any(message)

        if filter == 'state':
            if session.get_state() == filter_value:
                return True

        if filter == 'inline_state':
            if session.get_inline_state() == filter_value:
                return True

        return False

    def broadcast_message(self, filter_options, text, **kwargs):
        recipients = self._storage.collection(Session.SESSIONS_COLLECTION).get_field('chat_id', **filter_options)

        for recipient in recipients:
            self.send_message(recipient, text, **kwargs)

    # override api methods in order to implement exceptions suppression

    def set_webhook(self, url=None, certificate=None):
        return self._remit(super().set_webhook, url=url, certificate=certificate)

    def get_updates(self, offset=None, limit=None, timeout=20):
        return self._remit(super().get_updates, offset=offset, limit=limit)

    def get_me(self):
        return self._remit(super().get_me)

    def get_file(self, file_id):
        return self._remit(super().get_file, file_id=file_id)

    def download_file(self, file_path):
        return self._remit(super().download_file, file_path=file_path)

    def get_chat(self, chat_id):
        return self._remit(super().get_chat, chat_id=chat_id)

    def leave_chat(self, chat_id):
        return self._remit(super().leave_chat, chat_id=chat_id)

    def get_chat_administrators(self, chat_id):
        return self._remit(super().get_chat_administrators, chat_id=chat_id)

    def get_chat_members_count(self, chat_id):
        return self._remit(super().get_chat_members_count, chat_id=chat_id)

    def get_chat_member(self, chat_id, user_id):
        return self._remit(super().get_chat_member, chat_id=chat_id, user_id=user_id)

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None,
                     parse_mode=None, disable_notification=None):
        return self._remit(super().send_message, chat_id=chat_id, text=text,
                           disable_web_page_preview=disable_web_page_preview,
                           reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup,
                           parse_mode=parse_mode,
                           disable_notification=disable_notification)

    def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None):
        return self._remit(super().forward_message, chat_id=chat_id, from_chat_id=from_chat_id,
                           message_id=message_id, disable_notification=disable_notification)

    def send_photo(self, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None):
        return self._remit(super().send_photo, chat_id=chat_id, photo=photo, caption=caption,
                           reply_to_message_id=reply_to_message_id, reply_markup=reply_markup,
                           disable_notification=disable_notification)

    def send_audio(self, chat_id, audio, duration=None, performer=None, title=None, reply_to_message_id=None,
                   reply_markup=None, disable_notification=None, timeout=None):
        return self._remit(super().send_audio, chat_id=chat_id, audio=audio, duration=duration,
                           performer=performer, title=title, reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup, disable_notification=disable_notification,
                           timeout=timeout)

    def send_voice(self, chat_id, voice, duration=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None, timeout=None):
        return self._remit(super().send_voice, chat_id=chat_id, voice=voice, duration=duration,
                           reply_to_message_id=reply_to_message_id, reply_markup=reply_markup,
                           disable_notification=disable_notification, timeout=timeout)

    def send_document(self, chat_id, data, reply_to_message_id=None, caption=None, reply_markup=None,
                      disable_notification=None, timeout=None):
        return self._remit(super().send_document, chat_id=chat_id, data=data, reply_to_message_id=reply_to_message_id,
                           caption=caption, reply_markup=reply_markup, disable_notification=disable_notification,
                           timeout=timeout)

    def send_sticker(self, chat_id, data, reply_to_message_id=None, reply_markup=None, disable_notification=None,
                     timeout=None):
        return self._remit(super().send_sticker, chat_id=chat_id, data=data, reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup, disable_notification=disable_notification,
                           timeout=timeout)

    def send_video(self, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None, timeout=None):
        return self._remit(super().send_video, chat_id=chat_id, data=data, duration=duration,
                           caption=caption, reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup, disable_notification=disable_notification,
                           timeout=timeout)

    def send_location(self, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None,
                      disable_notification=None):
        return self._remit(super().send_location, chat_id=chat_id, latitude=latitude,
                           longitude=longitude, reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup, disable_notification=disable_notification)

    def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id=None, disable_notification=None,
                   reply_to_message_id=None, reply_markup=None):
        return self._remit(super().send_venue, chat_id=chat_id, latitude=latitude, longitude=longitude,
                           title=title, address=address, foursquare_id=foursquare_id,
                           disable_notification=disable_notification, reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup)

    def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                     reply_to_message_id=None, reply_markup=None):
        return self._remit(super().send_contact, chat_id=chat_id, phone_number=phone_number,
                           first_name=first_name, last_name=last_name, disable_notification=disable_notification,
                           reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)

    def send_chat_action(self, chat_id, action):
        return self._remit(super().send_chat_action, chat_id=chat_id, action=action)

    def kick_chat_member(self, chat_id, user_id):
        return self._remit(super().kick_chat_member, chat_id=chat_id, user_id=user_id)

    def unban_chat_member(self, chat_id, user_id):
        return self._remit(super().unban_chat_member, chat_id=chat_id, user_id=user_id)

    def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                          disable_web_page_preview=None, reply_markup=None):
        return self._remit(super().edit_message_text, text=text, chat_id=chat_id, message_id=message_id,
                           inline_message_id=inline_message_id, parse_mode=parse_mode,
                           disable_web_page_preview=disable_web_page_preview,
                           reply_markup=reply_markup)

    def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        return self._remit(super().edit_message_reply_markup, chat_id=chat_id, message_id=message_id,
                           inline_message_id=inline_message_id, reply_markup=reply_markup)

    def edit_message_caption(self, caption, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        return self._remit(super().edit_message_caption, caption=caption, chat_id=chat_id, message_id=message_id,
                           inline_message_id=inline_message_id, reply_markup=reply_markup)

    def reply_to(self, message, text, **kwargs):
        return self._remit(super().reply_to, message, text, **kwargs)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=None):
        return self._remit(super().answer_callback_query, callback_query_id=callback_query_id,
                           text=text, show_alert=show_alert)

    # --


class Session(object):
    SESSIONS_COLLECTION = 'sessions'

    def __init__(self, bot, chat_id, l10n, session_storage, config_manager):
        self._bot = bot
        self.chat_id = chat_id
        self._storage = session_storage
        self._l10n = l10n
        self._config_manager = config_manager

        self._translator = l10n.translator(self.get_lang())

    def profile(self):
        return self._storage.collection(Session.SESSIONS_COLLECTION)

    def get_field(self, key):
        return self.profile().get_field(key, chat_id=self.chat_id)

    def set_field(self, key, value):
        return self.profile().set_field(key, value, multi=False, chat_id=self.chat_id)

    def _(self, key, **kwargs):
        return self._translator(key, **kwargs)

    def get_lang(self):
        found_lang_values = self.profile().get_field('lang', chat_id=self.chat_id)
        found_lang = None

        if len(found_lang_values) < 1:
            found_lang = self._config_manager.get('l10n').get('default_lang')
            self.set_field('lang', found_lang)
        else:
            found_lang = found_lang_values[0]

        return found_lang

    def set_lang(self, new_lang):
        result = self.set_field('lang', new_lang)
        self._translator = self._l10n.translator(new_lang)
        return result

    def get_state(self):
        found_state_values = self.get_field('state')
        found_state = None

        if len(found_state_values) == 0:
            found_state = self._config_manager.get('bot').get('initial_state')
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
            found_inline_state = self._config_manager.get('bot').get('initial_inline_state')
            self.set_inline_state(found_inline_state)
        else:
            found_inline_state = found_inline_state_values[0]

        return found_inline_state

    def set_inline_state(self, new_state):
        return self.set_field('inline_state', new_state)

    def reply_message(self, text, *args, **kwargs):
        return self._bot.send_message(self.chat_id, text, **kwargs)

    def collection(self, collection_name):
        return self._storage.collection(collection_name)


class L10n(object):
    def __init__(self, config_manager):
        self._config_manager = config_manager

        l10n = config_manager.get('l10n')

        translations_filename = l10n.get('file_path')
        translations_from_file = json.load(open(translations_filename, encoding='utf-8'))

        hot_translations = l10n.get('translations')

        translations = translations_from_file

        if hot_translations is not None:
            for translation_key in hot_translations.keys():
                translations[translation_key] = hot_translations.get(translation_key)

        l10n['translations'] = translations
        config_manager.set('l10n', l10n)

    def translator(self, lang):
        def translate(key, **kwargs):
            translations = self._config_manager.get('l10n').get('translations')

            if translations is None:
                return None

            translation_pair = translations.get(key)

            if translation_pair is None:
                return None

            translation_value = translation_pair.get(lang)

            if translation_value is None:
                return None

            return translation_value.format(**kwargs)

        return translate

    def set_translation(self, key, lang, value):
        l10n = self._config_manager.get('l10n')

        l10n['translations'][key][lang] = value

        self._config_manager.set('l10n', l10n)

