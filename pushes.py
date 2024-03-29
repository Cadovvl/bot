import abc
import logging
import random
from typing import Optional

import requests
import os

from telegram.ext import CallbackContext
from db.models import Subscription
from db_adapters import DBAdapter


class BaseSubscription(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger("subscription_{0}".format(name))

    def _subscribers(self) -> Optional[list]:
        users = Subscription.objects.filter(name=self.name).all()
        if len(users) <= 0:
            self.logger.info("No subscribers for {0}".format(self.name))
            return None
        return [u.chat for u in users]

    def __call__(self, context: CallbackContext):
        chats = self._subscribers()
        if chats is None:
            return
        self.call_for_subscribers(context, chats)

    @abc.abstractmethod
    def call_for_subscribers(self, context: CallbackContext, chats: list):
        pass


class DaSubscription(BaseSubscription):
    COUNTER_LIMIT = 200
    DA_SOURCE_KEY = "DA_SOURCE"
    DA_TOKEN = "https://www.deviantart.com/oauth2/token"
    DA_POPULAR = "https://www.deviantart.com/api/v1/oauth2/browse/tags"

    def __init__(self, name):
        BaseSubscription.__init__(self, name)
        self.counter_name = "COUNTER_FOR_{0}".format(name)
        self.params_name = "{0}_url_params".format(name)

    def call_for_subscribers(self, context: CallbackContext, chats: list):
        offset = DBAdapter.get_int_const(self.counter_name, 0)
        if offset >= self.COUNTER_LIMIT:
            self.logger.info("Refreshing offset for {0}".format(self.name))
            offset = 0
        DBAdapter.set_int_const(self.counter_name, offset + random.randint(4, 16))

        resp = requests.get(self.DA_TOKEN, params={
            "client_id": os.getenv("DA_CLIENT_ID"),
            "client_secret": os.getenv("DA_CLIENT_SECRET"),
            "grant_type": "client_credentials"
        })
        resp.raise_for_status()

        source = DBAdapter.get_config(self.name, self.DA_SOURCE_KEY, default=self.DA_POPULAR)
        params = {"access_token": resp.json()["access_token"],
                  "limit": 1,
                  "tag": "wallpaper",
                  "offset": offset}
        db_params = DBAdapter.get_configs(self.params_name)
        params.update(db_params)

        # get image
        resp = requests.get(source, params=params)
        resp.raise_for_status()

        res = resp.json()
        img_url = res['results'][0]['content']['src']
        title = res['results'][0]['title'] if 'title' in res['results'][0] else None
        for c in chats:
            context.bot.send_photo(chat_id=c, photo=img_url, caption=title)


class AdviseSubscription(BaseSubscription):
    ADVISE_URL = "http://fucking-great-advice.ru/api/random"

    def call_for_subscribers(self, context: CallbackContext, chats: list):
        adv = requests.get(self.ADVISE_URL)
        ans = adv.json()
        for c in chats:
            context.bot.send_message(chat_id=c, text=ans["text"])


class CurrenciesSubscription(BaseSubscription):
    CURRENCIES_URL = "https://api.exchangeratesapi.io/latest?base=RUB&symbols=EUR,USD,NOK"

    def call_for_subscribers(self, context: CallbackContext, chats: list):
        adv = requests.get(self.CURRENCIES_URL)
        ans = adv.json()
        text = "USD: {0:.2f} RUB;\nEUR: {1:.2f} RUB;\nNOK: {2:.2f} RUB;"\
            .format(1.0/ans["rates"]["USD"],
                    1.0/ans["rates"]["EUR"],
                    1.0/ans["rates"]["NOK"])
        for c in chats:
            context.bot.send_message(chat_id=c, text=text)

class XKCDSubscription(BaseSubscription):
    XKCD_URL_TEMPLATE = 'https://xkcd.com/{0}/info.0.json'

    def call_for_subscribers(self, context: CallbackContext, chats: list):
        url = self.XKCD_URL_TEMPLATE.format(random.randint(0, 2000))
        adv = requests.get(url)
        ans = adv.json()
        img = ans["img"]

        title = ans["safe_title"]
        description = ans["alt"]

        for c in chats:
            context.bot.send_photo(chat_id=c, photo=img, caption=f"{title}: {description}")
