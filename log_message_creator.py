class LogMessageCreator:
    @staticmethod
    def callback(callback_query):
        res = f'\
{callback_query.message.chat.username} \
{callback_query.message.chat.id} \
\'{callback_query.data}\''
        return res

    @staticmethod
    def command(message):
        res = f'\
{message.chat.username} \
{message.chat.id} \
\'{message.text}\''
        return res
