import logging

from dotenv import load_dotenv
load_dotenv()

## Importing django
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
## Django

from telegram_adapter import CadovvlBot


logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s|<%(name)s>|%(levelname)s]  %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bot = CadovvlBot()
bot.run()

