import botlab
import config


db_config = {'host': 'localhost', 'port': 27017, 'database': 'botlabtest'}


bot = botlab.BotLab(config.TOKEN, db_config)


@bot.message_handler('start')
def echo_text(session, message):
    if message.text is not None:
        session.reply_message(message.text)


bot.polling()