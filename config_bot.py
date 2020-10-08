import logging
import os

from telegram.ext import Updater, CommandHandler

from bot_decorators import required_args, filtered_users
from db_adapters import DBAdapter


class BaseConfigBot:
    def __init__(self):
        self.logger = logging.getLogger("bot")
        self.logger.info("Init base bot")

        self.updater = Updater(token=os.getenv("TELEGRAM_TOKEN"), use_context=True)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler("configure", self.configure))
        self.dispatcher.add_handler(CommandHandler("clean_config", self.clean_config))
        self.dispatcher.add_handler(CommandHandler("list_config", self.list_config))
        self.dispatcher.add_handler(CommandHandler("set_constant", self.set_constant))

    @filtered_users
    @required_args(3)
    def configure(self, update, context):
        DBAdapter.set_config(context.args[0], context.args[1], context.args[2])

    @filtered_users
    @required_args(2)
    def clean_config(self, update, context):
        DBAdapter.clean_config(context.args[0], context.args[1])

    @filtered_users
    @required_args(1)
    def list_config(self, update, context):
        configs = DBAdapter.get_configs(context.args[0])
        reply = "\n".join("{0}={1}".format(k, configs[k])
                          for k in configs)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=reply)

    @filtered_users
    @required_args(2)
    def set_constant(self, update, context):
        DBAdapter.set_int_const(context.args[0], int(context.args[1]))
