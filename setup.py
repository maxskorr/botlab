from distutils.core import setup
setup(
  name = 'botlab',
  packages = ['botlab'],
  version = '0.2.0',
  description = 'Tool to ease the development of telegram bots',
  author = 'Max(TrickOrTreat)',
  author_email = 'max@anybots.top',
  url = 'https://github.com/aivel/botlab',
  download_url = 'https://github.com/aivel/botlab/tarball/0.2.0',
  keywords = ['telegram', 'bot', 'api'],
  classifiers = [],
  install_requires = ['pyTelegramBotApi', 'pymongo', 'redis'],
  license = 'MIT'
)
