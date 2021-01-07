import time
from datetime import datetime, timedelta
import os

from django.db import reset_queries, connection
from django.db.models import Count, Sum
from telegram.ext.filters import Filters
from telegram.ext import Updater, CommandHandler, Job, CallbackQueryHandler, MessageHandler
import logging
import requests
import random
import re

from base_subscriptions_bot import BaseSubscriptionsBot
from bot_decorators import required_args, filtered_users
from db.models import TelegramUser, MessageHistory
from db_adapters import DBAdapter
from pushes import BaseSubscription, DaSubscription, AdviseSubscription, CurrenciesSubscription


class CadovvlBot(BaseSubscriptionsBot):
    ADVISE_URL = "http://fucking-great-advice.ru/api/random"
    SUB_INTERVAL_PREFIX = "SUBSCRIPTION_INTERVAL_TO_"
    def __init__(self):
        BaseSubscriptionsBot.__init__(self)
        self.logger = logging.getLogger()
        self.logger.info("Starting bot")

        self.dispatcher.add_handler(CommandHandler("advise", self.advise))
        self.dispatcher.add_handler(CommandHandler("polymery", self.polymery))
        self.dispatcher.add_handler(CommandHandler("top", self.top))
        self.dispatcher.add_handler(CommandHandler("true_top", self.true_top))
        self.dispatcher.add_handler(CommandHandler("reschedule", self.reschedule))

        self.dispatcher.add_handler(MessageHandler(Filters.all, self.add_top))

        self.run_subscription(DaSubscription("da_art"), 60*60)
        self.run_subscription(AdviseSubscription("advise"), 60*60)
        self.run_subscription(CurrenciesSubscription("currencies"), 60*60*24)

        self.run_subscription(DaSubscription("hidden_da_art"), 60*60, hidden=True)

    def add_top(self, update, context):
        if update.effective_user.is_bot:
            return
        user = TelegramUser.objects.get_or_create(
            pk=update.effective_user.id,
            defaults={'username': update.effective_user.username if update.effective_user.username  else update.effective_user.full_name,
                      'first_name': update.effective_user.first_name if update.effective_user.first_name else "",
                      'last_name': update.effective_user.last_name if update.effective_user.last_name else ""})
        MessageHistory.objects.create(
            user=user[0],
            chat=update.effective_chat.id,
            message=update.effective_message.text if update.effective_message.text else "",
            message_length=len(update.effective_message.text) if update.effective_message.text else 0,
            message_words=len(re.split(r'\W+', update.effective_message.text)) if update.effective_message.text else 0
        )

    def top(self, update, context):
        mh = MessageHistory.objects\
            .filter(time__gte=datetime.now() - timedelta(days=7))\
            .filter(chat=update.effective_chat.id)\
            .select_related('user')\
            .all()\
            .values('user__username', 'user__first_name', 'user__last_name')\
            .annotate(total=Count('user'))\
            .order_by('-total')

        message = "Top flooders of this week: \n\n" + "\n".join(
            ["__*{0} {1}*__:\t{2}\tmessages".format(u['user__first_name'],
                                            u['user__last_name'],
                                            u['total'])
                for u in mh
            ]
        )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message,
                                 parse_mode="MarkdownV2")


    def true_top(self, update, context):
        mh = MessageHistory.objects\
            .filter(time__gte=datetime.now() - timedelta(days=7))\
            .filter(chat=update.effective_chat.id)\
            .select_related('user')\
            .all()\
            .values('user__username', 'user__first_name', 'user__last_name')\
            .annotate(total=Sum('message_length'), words=Sum('message_words'))\
            .order_by('-total')

        message = "Top flooders of this week: \n\n" + "\n".join(
            ["__*{0} {1}*__:\t{2}\tsymbols in {3} words".format(u['user__first_name'],
                                            u['user__last_name'],
                                            u['total'],
                                            u['words'])
                for u in mh
            ]
        )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message,
                                 parse_mode="MarkdownV2")


    def run_subscription(self,
                         subscription: BaseSubscription,
                         default_interval: int,
                         hidden: bool = False):
        if hidden:
            self.hidden_subscriptions.append(subscription.name)
        else:
            self.available_subscriptions.append(subscription.name)

        interval = DBAdapter.get_int_const(self.SUB_INTERVAL_PREFIX + subscription.name, default_interval)

        self.updater.job_queue.run_repeating(
            subscription,
            interval,
            name=subscription.name,
            first=random.randint(0, interval))

    @filtered_users
    @required_args(2)
    def reschedule(self, update, context):
        interval = int(context.args[1])
        jobs = self.updater.job_queue.get_jobs_by_name(context.args[0])
        if jobs is not None and len(jobs) > 0:
            for j in jobs:
                j.schedule_removal()
            DBAdapter.set_int_const(self.SUB_INTERVAL_PREFIX + context.args[0], interval)
            job = jobs[0]
            self.updater.job_queue.run_repeating(
                job.callback,
                interval,
                name=job.name,
                first=random.randint(0, interval)
            )
            self.logger.info("Rescheduled {0} to interval {1}".format(job.name, interval))

    def advise(self, update, context):
        adv = requests.get(self.ADVISE_URL)
        if adv.status_code != 200:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error")
            return
        ans = adv.json()
        context.bot.send_message(chat_id=update.effective_chat.id, text=ans["text"])

    def polymery(self, update, context):
        phrase = random.choice(self.poly.split('\n'))
        context.bot.send_message(chat_id=update.effective_chat.id, text=phrase)

    def run(self):
        self.updater.start_polling()

    poly = """Я не понял, вы чё-то, блядь, легко к этому всему, хуйне, относитесь!
Вы чё, мальчики, охуели, что ли, блядь?
Чё, блядь, воздух свободы жопу защекотал?
Я, блядь, где-где добрый, а где-где вы меня заёбываете!
Или вы, блядь, лохи, сука, работать начинаете, или я вас, твари, блядь, как жеглов давить начну!
Проектанты хуевы, блядь!
И если ваши твари, блядь, и прочая, извиняюсь за выражение, хуета, не начнёт, блядь, работать!
Чё, охуели, что ли, совсем?! Чё за улыбки, блядь?! Я те кто, клоун?
Хуйня, блядь, демократия! Забудь нахуй о демократии, блядь! Пока я здесь командир, тут тоталитаризм будет.
Я ебальники скоро бить начну!
Не доводите до греха, не доводите! А то поздно будет.
Просрали все полимеры!
Нет потенции — сваливайте нахуй с рынка! И не позорьтесь! Нихуя сделать не можете!
Ни одного проекта вовремя не дали! Всё, что дали, — всё переделывается!
Подвесные потолки, блядь, в сортирах закладывать — это вы мастера! 
Вы сами понимаете, что вы нули перед ним, блядь?
По ходу дела, мальчики, надо бы за вас взяться, блядь."""

