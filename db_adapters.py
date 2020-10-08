import logging
from typing import Optional

from db.models import IntConstants, Config


class DBAdapter:
    @staticmethod
    def get_int_const(name: str, default: int) -> int:
        const = IntConstants.objects.filter(name=name).first()
        if const is None:
            return default
        return const.value

    @staticmethod
    def set_int_const(name: str, val: int) -> None:
        IntConstants.objects.update_or_create(name=name, defaults={'value': val})

    @staticmethod
    def get_configs(app: str) -> dict:
        return {i['key']: i['val'] for i in \
                Config.objects.filter(name=app).values('key', 'val')}

    @staticmethod
    def get_config(app: str, key: str, default=None) -> Optional[str]:
        val = Config.objects.filter(name=app, key=key).values('val').first()
        if val is None:
            return default
        return val['val']

    @staticmethod
    def set_config(app: str, key: str, val: str):
        Config.objects.update_or_create(name=app, key=key, defaults={'val': val})

    @staticmethod
    def clean_config(app: str, key: str):
        Config.objects.filter(name=app, key=key).delete()

