# botlab

Framework for development of Telegram Bots. 
Currently based on [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) library.

Facilitates the development process by providing basic needs of a bot developer out of the box.

Functionality:

* Stored sessions(mongodb)
* State machine
* L10n

### Example of usage:

    import botlab
    import config
    
    bot = botlab.BotLab(config.SETTINGS)
    
    @bot.message_handler(state='A')
    def state_a(session, message):
        if message.text is not None:
            session.reply_message('A')
        #
        session.set_state('B')
    
    
    @bot.message_handler(state='B')
    def state_b(session, message):
        if message.text is not None:
            session.reply_message('B')
        #
        session.set_state('A') # ciruling between two states: A and B
    
    bot.polling(timeout=1)

### Example of a configuration file:

    SETTINGS = {
        'bot': {
            'token':'<BOT TOKEN HERE>',
            'initial_state': 'start'
        },
        'database': {
            'host': 'localhost',
            'port': 27017,
            'database_name': 'test'
        },
        'l10n': {
            'default_lang': 'en',
            'file_path': 'l10n.json'
        }
    }

Contribution is welcome.
Take a look at [project milestones](https://github.com/aivel/botlab/wiki/Milestones).

Licensed under MIT
