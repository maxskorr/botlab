# botlab

Framework for development of Telegram Bots. 
Currently based on [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) library.

Facilitates the development process by providing basic needs of a bot developer out of the box.

#### Functionality available:

* Convenient storage(mongodb, disk, inmemory)
* Stored sessions
* State machine(separate global & inline states)
* L10n

### Example of usage:

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


### Example of a configuration file:


    SETTINGS = {
        'bot': {
            'token':'<BOT_TOKEN_HERE>',
            'initial_state': 'A',
            'initial_inline_state': 'IA'
        },
        'storage': {
            'type': 'inmemory', # 'disk', 'mongo'
            'params': {
                # for type = 'mongo'
                'host': 'localhost',
                'port': 27017,
                'database': 'botlab_test',
                # for type = 'disk'
                'file_path': 'storage.json'
                # for type = 'inmemory'
                # empty
            }
        },
        'l10n': {
            'default_lang': 'en',
            'file_path': 'l10n.json'
        },

    }


Contribution is welcome.
Take a look at [project milestones](https://github.com/aivel/botlab/wiki/Milestones).

Licensed under MIT
