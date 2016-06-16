import botlab
import config
import telebot

bot = botlab.BotLab(config.SETTINGS)


def build_inline_kb_1():
    k = telebot.types.InlineKeyboardMarkup()
    k.add(telebot.types.InlineKeyboardButton(text='Hi', callback_data='hi'))
    return k


def build_inline_kb_2():
    k = telebot.types.InlineKeyboardMarkup()
    k.add(telebot.types.InlineKeyboardButton(text='Bye', callback_data='bye'))
    return k


@bot.message_handler(state='A')
def state_a(session, message):
    if message.text is not None:
        session.reply_message('A', reply_markup=build_inline_kb_1())
    #
    session.set_state('B')


@bot.message_handler(state='B')
def state_b(session, message):
    if message.text is not None:
        session.reply_message('B')
    #
    session.set_state('A')  # ciruling between two states: A and B


# ths callback will be called only once(as soon as we're setting
#   'inline_state' to 'IB', but never handle it)
@bot.callback_query_handler(func=lambda cbq: True, inline_state='IA')
def update_inline_state(session, cbq):
    bot.edit_message_reply_markup(chat_id=session.chat_id, message_id=cbq.message.message_id,
                                  reply_markup=build_inline_kb_2())
    session.set_inline_state('IB')


bot.polling(timeout=1)