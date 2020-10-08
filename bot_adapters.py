from functools import wraps


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
