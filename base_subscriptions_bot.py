from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler

from config_bot import BaseConfigBot
from db.models import Subscription


class BaseSubscriptionsBot(BaseConfigBot):
    SUBSCRIBE_PREFIX = "SUBSCRIBE_TO_"
    UNSUBSCRIBE_PREFIX = "UNSUBSCRIBE_TO_"

    def __init__(self):
        BaseConfigBot.__init__(self)

        self.available_subscriptions = []
        self.hidden_subscriptions = []

        self.dispatcher.add_handler(CommandHandler("subscribe", self.subscribe))
        self.dispatcher.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.dispatcher.add_handler(CommandHandler("subscriptions", self.subscriptions))

        self.dispatcher.add_handler(CallbackQueryHandler(self.subscribe,
                                                         pattern=r"^" + self.SUBSCRIBE_PREFIX + r"[\w_]+"))
        self.dispatcher.add_handler(CallbackQueryHandler(self.unsubscribe,
                                                         pattern=r"^" + self.UNSUBSCRIBE_PREFIX + r"[\w_]+"))

    def subscriptions(self, update, context):
        my_subscriptions = set([u.name for u in
                                Subscription.objects.filter(chat=update.effective_chat.id).all()])
        markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(sub + u"  \u274C", callback_data=self.UNSUBSCRIBE_PREFIX + sub)]
                if sub in my_subscriptions else
                [InlineKeyboardButton(sub + u"  \u2705", callback_data=self.SUBSCRIBE_PREFIX + sub)]
                for sub in self.available_subscriptions])

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Here is available subscriptions",
                                 reply_markup=markup)

    def _subscribe(self, update, context, name):
        Subscription.objects.update_or_create(name=name, chat=update.effective_chat.id)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Successfully subscribed on {0}".format(name))
        self.subscriptions(update, context)

    def _unsubscribe(self, update, context, name):
        Subscription.objects.filter(name=name, chat=update.effective_chat.id).delete()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Successfully unsubscribed from {0}".format(name))
        self.subscriptions(update, context)

    def subscribe(self, update, context):
        if update.callback_query is not None:
            self._subscribe(update, context, update.callback_query.data[len(self.SUBSCRIBE_PREFIX):])
            context.bot.answer_callback_query(update.callback_query.id)
            return

        if len(context.args) > 0 and \
            (context.args[0] in self.available_subscriptions
             or context.args[0] in self.hidden_subscriptions):
            self._subscribe(update, context, context.args[0])
            return
        self.logger.error(context.args)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="No valid subscription name provided")

    def unsubscribe(self, update, context):
        if update.callback_query is not None:
            self._unsubscribe(update, context, update.callback_query.data[len(self.UNSUBSCRIBE_PREFIX):])
            context.bot.answer_callback_query(update.callback_query.id)
            return

        if len(context.args) > 0 and \
            (context.args[0] in self.available_subscriptions
             or context.args[0] in self.hidden_subscriptions):
            self._unsubscribe(update, context, context.args[0])
            return
        self.logger.error(context.args)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="No valid subscription name provided")
