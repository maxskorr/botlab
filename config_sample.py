
SETTINGS = {
    'bot': {
        'token':'<BOT_TOKEN_HERE>',
        'initial_state': 'A',
        'initial_inline_state': 'IA'
    },
    'storage': {
        'type': 'mongo', # 'disk', 'inmemory'
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

