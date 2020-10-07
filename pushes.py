import logging
from typing import Optional

import requests
import os

from telegram.ext import CallbackContext
from db.models import Subscription, IntConstants


COUNTER_CONST_PATTERN = 'COUNTER_FOR_{0}'
DA_TAGS = "https://www.deviantart.com/api/v1/oauth2/browse/tags"
DA_POPULAR = "https://www.deviantart.com/api/v1/oauth2/browse/popular"
DA_TOKEN = "https://www.deviantart.com/oauth2/token"


class BaseSubscription:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger("subscription_{0}".format(name))

    def _subscribers(self) -> Optional[list]:
        users = Subscription.objects.filter(name=self.name).all()
        if len(users) <= 0:
            self.logger.info("No subscribers for {0}".format(self.name))
            return None
        return [u.chat for u in users]

    def _get_counter(self) -> int:
        counter_name = COUNTER_CONST_PATTERN.format(self.name)
        # Get offset from db
        counter = IntConstants.objects.filter(name=counter_name).first()
        if counter is None:
            self.logger.info("Counter {0} is None. Creating new".format(counter_name))
            counter = IntConstants(name=counter_name, value=0)
        val = counter.value
        counter.value += 1
        if counter.value > 1000:
            self.logger.info("Counter is too high. Making zero")
            counter.value = 0
        counter.save()
        return val


class DaSubscription(BaseSubscription):
    def __call__(self, context: CallbackContext):
        chats = self._subscribers()
        if chats is None:
            return

        offset = self._get_counter()

        resp = requests.get(DA_TOKEN, params={
            "client_id": os.getenv("DA_CLIENT_ID"),
            "client_secret": os.getenv("DA_CLIENT_SECRET"),
            "grant_type": "client_credentials"
        })
        resp.raise_for_status()

        # get image
        resp = requests.get(DA_POPULAR, params={"access_token": resp.json()["access_token"],
                                             "limit": 1,
                                             "tag": "wallpaper",
                                             "offset": offset})
        resp.raise_for_status()
        res = resp.json()
        img_url = res['results'][0]['content']['src']
        for c in chats:
            context.bot.send_photo(chat_id=c, photo=img_url)


ADVISE_URL = "http://fucking-great-advice.ru/api/random"


class AdviseSubscription(BaseSubscription):
    def __call__(self, context: CallbackContext):
        chats = self._subscribers()
        if chats is None:
            return

        adv = requests.get(ADVISE_URL)
        ans = adv.json()
        for c in chats:
            context.bot.send_message(chat_id=c, text=ans["text"])

