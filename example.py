import os
import telebot
import botlab

from example import config


settings = config.SETTINGS
# be sure to pass a telegram bot token
# as an environmental variable or within
# the configuration file
settings['bot']['token'] = os.environ.get('BOT_TOKEN')


bot = botlab.BotLab(settings)


def build_main_menu_keyboard(session):
    kb = telebot.types.ReplyKeyboardMarkup(row_width=1)

    kb.add(telebot.types.KeyboardButton(text=session._('btn_switch_lang')))
    kb.add(telebot.types.KeyboardButton(text=session._('btn_change_welcome_message')))

    return kb


def build_switch_language_keyboard(session):
    kb = telebot.types.ReplyKeyboardMarkup(row_width=1)

    # build a keyboard considering user language
    if session.get_lang() == 'en':
        btn_label = 'btn_switch_lang_to_ru'
    else:
        btn_label = 'btn_switch_lang_to_en'

    # From now on, `btn_label` variable will contain the label of the
    #   button that is to be shown to the user.
    # A label is the marker we use in `l10n.json` file to describe
    #   localization of a button or other text that should be localized.

    kb.add(telebot.types.KeyboardButton(
        text=session._(btn_label)  # That's how we find out the actual button caption
    ))

    return kb


def build_change_welcome_message_keyboard(session):
    kb = telebot.types.InlineKeyboardMarkup(row_width=1)

    # Button labels are also a good thing to use as `callback_data`
    #   parameter when dealing inline keyboards

    kb.add(telebot.types.InlineKeyboardButton(text=session._('btn_change_welcome_message_set_ru'),
                                              callback_data='btn_change_welcome_message_set_ru'))
    kb.add(telebot.types.InlineKeyboardButton(text=session._('btn_change_welcome_message_set_en'),
                                              callback_data='btn_change_welcome_message_set_en'))
    kb.add(telebot.types.InlineKeyboardButton(text=session._('btn_go_back'),
                                              callback_data='btn_go_back'))

    return kb


# If we want to intercept all the messages(but not inline ones)
#   - with no matter what content - we should place a hook with
#   `func=lambda msg: True` filter.
# It is strongly recommended writing such a hook
#   the first handler in the file due to the algorithm
#   that tests filters of handlers against incoming messages
@bot.message_handler(func=lambda msg: True)
def hook_all_messages(session, message):
    text = message.text

    if message.text.startswith('|>'):
        msg_to_broadcast = text[2:]

        if len(msg_to_broadcast) < 0:
            return

        # That's how we send different messages to users with different
        #   languages set in their settings.
        # By the way, there could be any other filter that takes into account
        #   any set of parameters that are kept in user sessions.
        # For example, it could be `state` or `inline_state` parameters - so
        #   that people with the states specified would receive the message.
        bot.broadcast_message({'lang': 'en'}, '%s [english version]' % msg_to_broadcast)
        bot.broadcast_message({'lang': 'ru'}, '%s [russian version]' % msg_to_broadcast)


# That's how we define a handler for a specific state
@bot.message_handler(state='main_menu')
def main_menu_state(session, message):
    kb = build_main_menu_keyboard(session)

    text = message.text

    # That's how we check text of incoming messages against button labels
    if text == session._('btn_switch_lang'):
        # Next message will be processed in the state specified below
        session.set_state('switch_lang')

        kb = build_switch_language_keyboard(session)

        # `session.reply_message` allows us to send a message right back to
        #   the person we're talking to without messing around their chat_id
        session.reply_message(session._('msg_switch_lang'), reply_markup=kb)
        return
    elif text == session._('btn_change_welcome_message'):
        session.set_state('change_welcome_message')
        # When working with inline keyboards, it is convenient to consider
        #   `inline_state`. That's how we set it
        session.set_inline_state('change_welcome_message')

        kb = build_change_welcome_message_keyboard(session)

        session.reply_message(session._('msg_change_welcome_message'), reply_markup=kb)
        return

    # Localized strings can also be formatted with custom parameters in the following form:
    #   `Hello, {name}`
    # `{name}` here is a placeholder for the parameter we gonna be passing to `session._`,
    #   while playing with localized strings.
    response_text = session._('msg_main_menu_welcome', name=message.from_user.first_name)

    session.reply_message(response_text, reply_markup=kb)


@bot.message_handler(state='switch_lang')
def switch_lang_state(session, message):
    text = message.text

    if text == session._('btn_switch_lang_to_en'):
        # Setting different language for a user is also as easy as that:
        session.set_lang('en')
        # ..
        session.set_state('main_menu')
        kb = build_main_menu_keyboard(session)
        session.reply_message(session._('msg_main_menu_welcome', name=message.from_user.first_name),
                              reply_markup=kb)
    elif text == session._('btn_switch_lang_to_ru'):
        session.set_lang('ru')
        session.set_state('main_menu')
        kb = build_main_menu_keyboard(session)
        session.reply_message(session._('msg_main_menu_welcome', name=message.from_user.first_name),
                              reply_markup=kb)
    else:
        session.reply_message(session._('msg_switch_lang_unknown_action'))
        return

    session.set_state('main_menu')
    kb = build_main_menu_keyboard(session)
    session.reply_message(session._('msg_main_menu'), reply_markup=kb)


@bot.message_handler(state='change_welcome_message')
def change_welcome_message_state(session, message):
    inline_state = session.get_inline_state()
    text = message.text

    if inline_state == 'change_welcome_message_ru':
        # Sometimes we want to have an ability to change localized
        #   bot content dynamically without restarting the application
        # And that's how we do that with botlab:

        bot.l10n.set_translation('msg_main_menu_welcome', 'ru', text)

        # Depending on configuration of the bot, the change may be
        #   persistent so that if the bot goes down the change is kept.

        session.set_inline_state('change_welcome_message')
        kb = build_change_welcome_message_keyboard(session)
        session.reply_message(session._('msg_change_welcome_message_success'),
                              reply_markup=kb)
    elif inline_state == 'change_welcome_message_en':
        bot.l10n.set_translation('msg_main_menu_welcome', 'en', text)
        session.set_inline_state('change_welcome_message')
        kb = build_change_welcome_message_keyboard(session)
        session.reply_message(session._('msg_change_welcome_message_success'),
                              reply_markup=kb)
    else:
        session.reply_message(session._('msg_change_welcome_message_try_again'))


# To catch inline queries we would set up a handler like this:
@bot.callback_query_handler(inline_state='change_welcome_message')
def change_welcome_message_inline_state(session, cbq):
    data = cbq.data

    if data == 'btn_change_welcome_message_set_ru':
        session.reply_message(session._('msg_change_welcome_message_set_ru'))
        session.set_inline_state('change_welcome_message_ru')
    elif data == 'btn_change_welcome_message_set_en':
        session.reply_message(session._('msg_change_welcome_message_set_en'))
        session.set_inline_state('change_welcome_message_en')
    elif data == 'btn_go_back':
        kb = build_main_menu_keyboard(session)

        session.set_state('main_menu')
        session.set_inline_state(None)

        session.reply_message(session._('msg_main_menu_welcome',
                                        name=cbq.from_user.first_name),
                              reply_markup=kb)

    bot.answer_callback_query(cbq.id)


bot.polling(timeout=1)
