import os

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, Job, CallbackQueryHandler
import logging
import requests
import random

from base_subscriptions_bot import BaseSubscriptionsBot
from bot_adapters import required_args
from db.models import IntConstants, Subscription
from pushes import BaseSubscription, DaSubscription, AdviseSubscription


class CadovvlBot(BaseSubscriptionsBot):
    ADVISE_URL = "http://fucking-great-advice.ru/api/random"

    def __init__(self):
        BaseSubscriptionsBot.__init__(self)
        self.logger = logging.getLogger()
        self.logger.info("Starting bot")

        self.dispatcher.add_handler(CommandHandler("advise", self.advise))
        self.dispatcher.add_handler(CommandHandler("reschedule", self.reschedule))

        self.run_subscription(DaSubscription("da_art"), 60*60)
        self.run_subscription(AdviseSubscription("advise"), 60*60)

        self.run_subscription(DaSubscription("hidden_da_art"), 60*60, hidden=True)

    def run_subscription(self,
                         subscription: BaseSubscription,
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

    @required_args(2)
    def reschedule(self, update, context):
        interval = int(context.args[1])
        jobs = self.updater.job_queue.get_jobs_by_name(context.args[0])
        if jobs is not None and len(jobs) > 0:
            for j in jobs:
                j.schedule_removal()

            job = jobs[0]
            self.updater.job_queue.run_repeating(
                job.callback,
                interval,
                name=job.name,
                first=random.randint(0, interval)
            )

    def advise(self, update, context):
        adv = requests.get(self.ADVISE_URL)
        if adv.status_code != 200:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error")
            return
        ans = adv.json()
        context.bot.send_message(chat_id=update.effective_chat.id, text=ans["text"])

    def run(self):
        self.updater.start_polling()


