import botlab
import config


bot = botlab.BotLab(config.SETTINGS)


@bot.message_handler(state='A')
def echo_text(session, message):
    if message.text is not None:
        session.reply_message('A')
    #
    session.set_state('B')


@bot.message_handler(state='B')
def echo_start(session, message):
    if message.text is not None:
        session.reply_message('B')
    #
    session.set_state('C')


@bot.message_handler(state='C')
def echo_start(session, message):
    if message.text is not None:
        session.reply_message('C')
    #
    session.set_state('A')



bot.polling(timeout=1)