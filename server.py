import functools

from telegram_bot import TelegramBot
from aiogram import types
from loguru import logger
from aiogram.utils import exceptions

from log_message_creator import LogMessageCreator as lmc
import config

tb = TelegramBot()
logger.add(config.LOG_FILE, rotation=config.LOG_ROTATION)


def command_decorator(func):
    @functools.wraps(func)
    def wrapper(message):
        # logger.info(func.__name__ + lmc.command(message))
        try:
            val = func(message)
        except exceptions.TelegramAPIError as err:
            logger.error(err)
        finally:
            return val
    return wrapper


@tb.dp.callback_query_handler(
    lambda callback: callback.data and callback.data.startswith('accept_worker'))
async def process_callback_accept_worker(callback_query: types.CallbackQuery):
    chat_id, username = callback_query.data.split('\t')[1:]
    logger.info(lmc.callback(callback_query))
    await tb.accept_new_worker(int(chat_id), username)


@tb.dp.callback_query_handler(
    lambda c: c.data and c.data.startswith('decline_worker'))
async def process_callback_decline_worker(callback_query: types.CallbackQuery):
    worker_chat_id = int(callback_query.data[len('decline_worker'):])
    logger.info(lmc.callback(callback_query))
    await tb.decline_worker(worker_chat_id)


@tb.dp.callback_query_handler(
    lambda c: c.data and c.data.startswith('shift'))
async def process_callback_shift(callback_query: types.CallbackQuery):
    code = int(callback_query.data[len('shift'):])
    chat_id = callback_query.message.chat.id
    logger.info(lmc.callback(callback_query))
    await tb.choose_shift(chat_id, code)


@tb.dp.callback_query_handler(lambda c: c.data and c.data == 'done')
async def process_callback_shifts_done(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    logger.info(lmc.callback(callback_query))
    await tb.confirm_chosen_shifts(chat_id)


@tb.dp.message_handler(tb.is_worker, commands=['start'])
@command_decorator
async def command_start_from_worker(message: types.Message):
    logger.info(lmc.command(message))
    await tb.send_welcome(message)


@tb.dp.message_handler(tb.is_admin, commands=['create_schedule'])
@command_decorator
async def command_create_schedule(message):
    logger.info(lmc.command(message))
    await tb.create_schedule(message)


@tb.dp.message_handler(tb.is_admin, commands=['get_schedule_template'])
@command_decorator
async def command_get_schedule_template(message):
    logger.info(lmc.command(message))
    await tb.get_schedule_template(message)


@tb.dp.message_handler(tb.is_admin, commands=['rating'])
@command_decorator
async def command_rating(message):
    logger.info(lmc.command(message))
    await tb.get_rating(message)


@tb.dp.message_handler(tb.is_admin, commands=['change_rating'])
@command_decorator
async def command_change_rating(message):
    logger.info(lmc.command(message))
    await tb.change_rating(message)


@tb.dp.message_handler(tb.is_admin, commands=['add_worker'])
@command_decorator
async def command_add_worker(message):
    logger.info(lmc.command(message))
    await tb.add_worker(message)


@tb.dp.message_handler(tb.is_admin, commands=['delete_worker'])
@command_decorator
async def command_delete_worker(message):
    logger.info(lmc.command(message))
    await tb.delete_worker(message)


@tb.dp.message_handler(tb.is_admin, commands=['delete_shift'])
@command_decorator
async def command_delete_shift(message):
    logger.info(lmc.command(message))
    await tb.delete_shift(message)


@tb.dp.message_handler(tb.is_admin, commands=['change_worker_for_shift'])
@command_decorator
async def command_change_worker_for_shift(message):
    logger.info(lmc.command(message))
    await tb.change_worker_for_shift(message)


@tb.dp.message_handler(tb.is_admin, commands=['stop_schedule_creating'])
@command_decorator
async def command_stop_schedule_creating(message):
    logger.info(lmc.command(message))
    await tb.stop_schedule_creating(message)


@tb.dp.message_handler(tb.is_admin, commands=['cancel_schedule_creating'])
@command_decorator
async def command_cancel_schedule_creating(message):
    logger.info(lmc.command(message))
    await tb.stop_schedule_creating(message)


@tb.dp.message_handler(tb.is_admin, commands=['notify_all'])
@command_decorator
async def command_notify_all(message):
    logger.info(lmc.command(message))
    await tb.notify_workers(message)


@tb.dp.message_handler(tb.is_admin, commands=['h', 'help'])
@command_decorator
async def command_admin_help(message):
    logger.info(lmc.command(message))
    await tb.admin_help(message)


@tb.dp.message_handler(tb.is_worker, commands=['h', 'help'])
@command_decorator
async def command_worker_help(message):
    logger.info(lmc.command(message))
    await tb.worker_help(message)


@tb.dp.message_handler(commands=['h', 'help'])
@command_decorator
async def command_help_help(message):
    logger.info(lmc.command(message))
    await tb.all_help(message)


@tb.dp.message_handler(
    lambda message: tb.is_worker(message), commands=['my_schedule'])
@command_decorator
async def command_my_schedule(message: types.Message):
    logger.info(lmc.command(message))
    await tb.send_personal_schedule(message)


@tb.dp.message_handler(
    lambda message: tb.is_admin(message), commands=['schedule'])
@command_decorator
async def command_schedule_admin(message: types.Message):
    logger.info(lmc.command(message))
    await tb.send_full_schedule_admin(message)


@tb.dp.message_handler(
    lambda message: tb.is_worker(message), commands=['schedule'])
@command_decorator
async def command_schedule_worker(message: types.Message):
    logger.info(lmc.command(message))
    await tb.send_full_schedule_worker(message)


@tb.dp.message_handler(
    lambda message: tb.is_admin(message), commands=['shifts_without_worker'])
@command_decorator
async def command_shifts_without_worker(message: types.Message):
    logger.info(lmc.command(message))
    await tb.send_shifts_without_worker(message)


@tb.dp.message_handler(
    lambda message: tb.is_admin(message), commands=['clean_shifts'])
@command_decorator
async def command_clean_shifts(message: types.Message):
    logger.info(lmc.command(message))
    await tb.clean_shifts(message)


@tb.dp.message_handler(
    lambda message: not tb.is_worker(message), commands=['start'])
@command_decorator
async def start_from_anonymous(message: types.Message):
    logger.info(lmc.command(message))
    await tb.uncknown_user(message)


@tb.dp.message_handler(lambda message: not tb.is_admin(message))
@command_decorator
async def all_message(message):
    logger.info(lmc.command(message))
    await tb.forward_to_admins(message)


@tb.dp.message_handler(tb.is_admin)
@command_decorator
async def all_from_admin(message):
    logger.info(lmc.command(message))
    await tb.invalid_command(message)


if __name__ == '__main__':
    # tb.db.print_all('workers')
    # tb.db.print_all('shifts')
    # tb.db.print_all('worker_shift')
    # tb.db.print_all('commands')
    tb.run()
