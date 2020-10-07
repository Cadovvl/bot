import os

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, Job, CallbackQueryHandler
import logging
import requests
import random

from db.models import IntConstants, Subscription
from pushes import BaseSubscription, DaSubscription, AdviseSubscription

ADVISE_URL = "http://fucking-great-advice.ru/api/random"

SUBSCRIBE_PREFIX = "SUBSCRIBE_TO_"
UNSUBSCRIBE_PREFIX = "UNSUBSCRIBE_TO_"

class CadovvlBot:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.info("Starting bot")

        self.available_subscriptions = []
        self.hidden_subscriptions = []

        self.updater = Updater(token=os.getenv("TELEGRAM_TOKEN"), use_context=True)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler("advise", self.advise))
        self.dispatcher.add_handler(CommandHandler("subscribe", self.subscribe))
        self.dispatcher.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.dispatcher.add_handler(CommandHandler("subscriptions", self.subscriptions))

        self.dispatcher.add_handler(CallbackQueryHandler(self.subscribe,
                                                         pattern=r"^" + SUBSCRIBE_PREFIX + r"[\w_]+"))
        self.dispatcher.add_handler(CallbackQueryHandler(self.unsubscribe,
                                                         pattern=r"^" + UNSUBSCRIBE_PREFIX + r"[\w_]+"))

        self.run_subscription(DaSubscription("da_art_hourly"), 60*60)
        self.run_subscription(AdviseSubscription("advise_daily"), 60*60*24)
        self.run_subscription(AdviseSubscription("advise_hourly"), 60*60)

    def run_subscription(self,
                         subscription: BaseSubscription ,
                         interval: int,
                         hidden: bool = False):
        if hidden:
            self.hidden_subscriptions.append(subscription.name)
        else:
            self.available_subscriptions.append(subscription.name)

        self.updater.job_queue.run_repeating(
            subscription,
            interval,
            name=subscription.name,
            first=random.randint(0, interval))

    def advise(self, update, context):
        adv = requests.get(ADVISE_URL)
        if adv.status_code != 200:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error")
            return
        ans = adv.json()
        context.bot.send_message(chat_id=update.effective_chat.id, text=ans["text"])

    def subscriptions(self, update, context):
        my_subscriptions = set([u.name for u in
                                Subscription.objects.filter(chat=update.effective_chat.id).all()])
        markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(sub + u"  \u274C", callback_data=UNSUBSCRIBE_PREFIX + sub)]
                if sub in my_subscriptions else
                [InlineKeyboardButton(sub + u"  \u2705", callback_data=SUBSCRIBE_PREFIX + sub)]
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
            self._subscribe(update, context, update.callback_query.data[len(SUBSCRIBE_PREFIX):])
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
            self._unsubscribe(update, context, update.callback_query.data[len(UNSUBSCRIBE_PREFIX):])
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

    def run(self):
        self.updater.start_polling()


