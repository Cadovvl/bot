from functools import wraps
from logging import Logger


def required_args(num: int):
    def inner_adapter(func):
        @wraps(func)
        def wrapper(self, update, context):
            if len(context.args) < num:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="Required {0} arg(s)".format(num))
                return
            return func(self, update, context)
        return wrapper
    return inner_adapter


def filtered_users(func):
    @wraps(func)
    def wrapper(self, update, context):
        if update.effective_user.id != 115486460:
            self.logger.error("Attempt to change configuration by user: {0} id: {1}".
                              format(update.effective_user.name, update.effective_user.id))
            return
        func(self, update, context)
    return wrapper

