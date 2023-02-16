import asyncio
from datetime import datetime, timedelta
from dotenv import dotenv_values

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.bot_command import BotCommand
from aiogram.utils import exceptions
from loguru import logger

import integration_from_db_to_ga
from genetic_algorithm import GeneticAlgorithm
from GA_config import GA_config
from messages import bot_messages, TIME_MESSAGE
from schedule_db import ScheduleDB
from parser import Parser
from db import Worker, Schedule
from integration_from_db_to_ga import WorkerGA, ShiftGA
from message_creator import MessageCreator
import config as config


# ADMINS = [372805049]


STANDARD_SCHEDULE_TIMEDELTAS = [
    (timedelta(hours=10), timedelta(hours=6)),
    (timedelta(hours=16), timedelta(hours=6)),
    (timedelta(hours=34), timedelta(hours=6)),
    (timedelta(hours=40), timedelta(hours=6)),
    (timedelta(hours=58), timedelta(hours=6)),
    (timedelta(hours=64), timedelta(hours=6)),
    (timedelta(hours=82), timedelta(hours=6)),
    (timedelta(hours=88), timedelta(hours=6)),
    (timedelta(hours=106), timedelta(hours=6)),
    (timedelta(hours=112), timedelta(hours=6)),
    (timedelta(hours=132), timedelta(hours=10))
]


class TelegramBot:
    bot = None
    dp = None
    db = None

    def __init__(self):
        logger.add(config.LOG_FILE, rotation=config.LOG_ROTATION)
        env_config = dotenv_values()
        self.bot = Bot(token=env_config['TELEGRAM_API_TOKEN'])
        self.dp = Dispatcher(
            self.bot, storage=MemoryStorage(),
            loop=asyncio.get_event_loop())
        self.dp.middleware.setup(LoggingMiddleware())
        self.db = ScheduleDB(env_config['DB_CONF'])
        logger.success('Bot, Dispatcher and DataBase were connected')

    @staticmethod
    def get_worker_coefficient(ratio_chosen_to_all: float):
        return (
            config.MIN_WORKER_COEFF
            + (config.MAX_WORKER_COEFF - config.MIN_WORKER_COEFF) * ratio_chosen_to_all ** config.WORKER_COEFF_DEGREE)

    def is_admin(self, message):
        user = self.db.get_worker(message.chat.id)
        return user and user.is_admin

    def is_worker(self, message):
        worker = self.db.get_worker(message.chat.id)
        return worker is not None

    async def send_message_to_user(
            self,
            chat_id,
            message,
            parse_mode=None,
            reply_markup=None):
        try:
            return await self.bot.send_message(
                chat_id,
                message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except (exceptions.BotBlocked, exceptions.ChatNotFound) as err:
            logger.error(f'can not send message to user with id: {chat_id}. {err}')

    async def choose_shift(self, chat_id, shift_id):
        # get worker and shift from db
        worker = self.db.get_worker(chat_id)
        message_id = worker.message_id
        shift = self.db.get_shift(shift_id)

        # change shift on chosen or not chosen
        if shift.shift_id in [s.shift_id for s in worker.shifts]:
            for s in worker.shifts:
                if shift.shift_id == s.shift_id:
                    worker.shifts.remove(s)
        else:
            worker.shifts.append(shift)

        # save changes
        self.db.save_worker(worker)

        # update keyboard in message
        kb = self.make_keyboard_shifts(chat_id)
        await self.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=kb
        )

    async def confirm_chosen_shifts(self, chat_id):
        worker = self.db.get_worker(chat_id)
        actual_shifts = self.db.get_actual_shifts()
        actual_shifts_id = [shift.shift_id for shift in actual_shifts]

        # calculate worker coefficient
        worker_actual_shifts = \
            [worker_shift for worker_shift in worker.shifts if worker_shift.shift_id in actual_shifts_id]
        coefficient = self.get_worker_coefficient(
            len(worker_actual_shifts) / len(actual_shifts))

        # update worker data in db
        self.db.change_worker(chat_id, {'is_done': True, 'coefficient': coefficient})

        # update telegram chat
        await self.clear_keyboard(chat_id, worker.message_id)
        await self.send_message_to_user(
            chat_id,
            MessageCreator.worker_wishes(worker_actual_shifts)
        )

        logger.info(f'{worker.username} confirm chosen shifts')
        logger.debug(f'{worker.username} chose shifts \
{", ".join([str(s.shift_id) for s in worker_actual_shifts])} \
and got coeff {coefficient}')

    async def stop_schedule_creating(self, message):
        command = self.db.get_command()
        if not command or command.is_done:
            await message.reply(bot_messages['schedule_is_not_creating'])
            logger.warning('schedule is not creating')
            return

        command.is_done = True
        self.db.save_command(command)
        await message.reply(bot_messages['ok'])
        logger.success('schedule was stopped')

    async def get_rating(self, message):
        workers = self.db.get_all_workers()
        await message.reply(MessageCreator.rating(workers))
        logger.success(f'rating was sended to {message.chat.id}')

    async def change_rating(self, message):
        try:
            username_rating = Parser.username_rating(message.text)
            if not username_rating:
                raise ValueError('Empty list of changing')
        except (ValueError, IndexError) as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['change_rating_template'])
            logger.warning(f'invalid data, {err}')
            return

        workers = self.db.get_all_workers()
        usernames = [w.username for w in workers]

        for username in username_rating:
            if username not in usernames:
                await message.reply(
                    f'\'{username}\' ' + bot_messages['non-existent_user'])
                logger.warning(f'username {username} is not exists')
                return

        for username in username_rating:
            for worker in workers:
                if worker.username == username:
                    self.db.change_worker(
                        worker.chat_id,
                        {'rating': worker.rating + username_rating[username]})

        logger.success('rating was changed')
        await message.reply(bot_messages['ok'])

    async def unknown_user_start(self, message):
        chat_id = message.chat.id
        if 'username' in message.chat and message.chat.username is not None:
            username = '@' + message.chat.username
        else:
            username = 'id:' + str(chat_id)

        kb = self.make_keyboard_add_worker(chat_id, username)
        for admin in self.db.get_admins():
            mess = await self.send_message_to_user(
                admin.chat_id,
                MessageCreator.start_from_anonymous(message),
                parse_mode='HTML',
                reply_markup=kb)
            self.db.add_request_to_admin(
                admin.chat_id,
                mess.message_id,
                config.RequestType.NEW_WORKER,
                chat_id)

        await self.bot.send_photo(
            chat_id=chat_id, photo=(open('who_are_you.jpg', 'rb')))
        await message.reply(bot_messages['unknown_user'])
        logger.success(f'{username} request was sent to admins')

    async def create_schedule(self, message):
        try:
            command, shifts = Parser.schedule(
                message.text,
                message.chat.id,
                message.message_id)

            if command.end_time <= command.start_time:
                await message.reply(bot_messages['invalid_time'])
                logger.warning(f'schedule сreating canceled because \
end_time({command.end_time}) has passed')
                return
        except ValueError as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['create_schedule_template'])
            logger.error(f'invalid data. ValueError {err}')
            return

        logger.debug(str(shifts))
        self.db.save_shifts(shifts)

        shifts = self.db.get_actual_shifts()[:config.MAX_SHIFTS_IN_ONE_SCHEDULE]

        if not shifts:
            await message.reply(bot_messages['all_shifts_has_worker'])
            logger.warning(f'schedule сreating canceled because \
all_shifts_has_worker')
            return
        self.db.save_command(command)
        self.db.change_all_worker({'is_done': False})
        logger.info('schedule creating was started')
        await self.continue_creating_schedule()

    async def continue_creating_schedule(self):
        result = await self.get_wishes()
        logger.info('workers give their wishes')
        self.db.update_shift_coefficients()
        logger.info('coefficients for shift were chosen')
        await self.notify_admins(result)

        workers = self.db.get_all_workers()
        shifts = self.db.get_actual_shifts()

        s, w = integration_from_db_to_ga.from_db_objects_to_ga(shifts, workers)

        ga = GeneticAlgorithm(s, w)
        ga_schedule, ga_fitness = ga.calc_schedule(**GA_config)
        logger.info('generic algorithm was finished')
        # Не виводиться графік
        logger.debug(f'answer: {str(ga_schedule)} mark: {str(ga_fitness)}')


        shifts_with_workers = []
        for shift in ga_schedule:
            if shift.final_worker:
                shifts_with_workers.append(shift)
        self.db.update_shifts_has_worker([shift.id for shift in shifts_with_workers], True)

        await self.schedule_notify(shifts_with_workers, workers)
        self.db.save_schedule(integration_from_db_to_ga.from_ga_schedule_to_db(shifts_with_workers), many=True)
        self.db.change_command({'is_done': True})

        logger.success('schedule creating was finished')

    async def schedule_notify(self, schedule, workers):
        await self.notify_admins(MessageCreator.schedule(schedule))
        # await self.notify_admins(
        #     MessageCreator.change_rating_from_schedule(schedule))
        for worker in workers:
            mess = await self.send_message_to_user(
                worker.chat_id,
                MessageCreator.personal_schedule(worker.chat_id, schedule))
            if mess:
                logger.info(f'{worker.username} get his schedule')

    async def add_worker(self, message):
        try:
            new_worker = Parser.worker(message.text)
            worker_id = new_worker.chat_id
            w = self.db.get_worker(new_worker.chat_id)
            if w:
                await message.reply(bot_messages['worker_already_exists'])
                logger.warning(f'worker with id: {w.chat_id} already exists')
            else:
                self.db.save_worker(new_worker)
                w = self.db.get_worker(worker_id)
                await message.reply(bot_messages['ok'])
                logger.success(f'{w.username} {w.chat_id} with rating \
{w.rating} was added')
        except (ValueError, IndexError) as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['add_worker_template'])
            logger.warning(f'invalid data. ValuueError: {err}')

    async def delete_worker(self, message):
        try:
            worker_id = int(message.text.split()[-1])
            w = self.db.get_worker(worker_id)
            if w:
                self.db.delete_worker(worker_id)
                await message.reply(bot_messages['ok'])
                logger.success(f'{w.username} {w.chat_id} was deleted')
            else:
                await message.reply(bot_messages['worker_does_not_exist'])
                logger.warning('worker with id: {worker_id} does not exist')
        except (ValueError) as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['delete_worker_template'])
            logger.warning(f'invalid data. ValuueError: {err}')
            return

    async def send_welcome(self, message):
        await message.reply(bot_messages['start_auth'])
        logger.success(f'welcome sent to worker with id: {message.chat.id}')

    def make_keyboard_shifts(self, worker_id):
        worker = self.db.get_worker(worker_id)
        shifts = self.db.get_actual_shifts()
        worker_shifts_id = [s.shift_id for s in worker.shifts]
        inline_btns = []
        inline_kb_full = InlineKeyboardMarkup()
        for shift in shifts:

            if shift.shift_id in worker_shifts_id:
                inline_btns.append(
                    InlineKeyboardButton(
                        bot_messages['shift_selected_icon'] + shift.name,
                        callback_data=f'shift{shift.shift_id}'))
            else:
                inline_btns.append(
                    InlineKeyboardButton(
                        shift.name,
                        callback_data=f'shift{shift.shift_id}'))

            inline_kb_full.add(inline_btns[-1])

        inline_btns.append(
            InlineKeyboardButton(
                bot_messages['all_shifts_selected'],
                callback_data='done'))
        inline_kb_full.add(inline_btns[-1])
        return inline_kb_full

    def make_keyboard_add_worker(self, chat_id, username):

        inline_kb_full = InlineKeyboardMarkup()
        c_data = f'accept_worker\t{chat_id}\t{username}'
        accept_btn = InlineKeyboardButton(
            bot_messages['button_accept_worker'],
            callback_data=c_data
        )
        decline_btn = InlineKeyboardButton(
            bot_messages['button_decline_worker'],
            callback_data=f'decline_worker{chat_id}'
        )
        inline_kb_full.row(accept_btn, decline_btn)

        return inline_kb_full

    async def get_wishes(self):
        command = self.db.get_command()
        workers = self.db.get_all_workers()
        workers_id = [x.chat_id for x in workers]
        if command.step == 0:
            for worker_id in workers_id:
                kb = self.make_keyboard_shifts(worker_id)
                mess = await self.send_message_to_user(
                    worker_id,
                    bot_messages['choose_all_shifts'],
                    reply_markup=kb
                )
                if mess:
                    worker = self.db.get_worker(worker_id)
                    worker.message_id = mess.message_id
                    self.db.save_worker(worker)
            logger.info('workers start choose wishes')
            command = self.db.get_command()
            command.step += 1
            self.db.save_command(command)

        if command.step <= len(TIME_MESSAGE):
            await self.send_notification_choose_shifts()

        shifts = self.db.get_actual_shifts()
        workers = self.db.get_all_workers()

        result = bot_messages['wishes_header']
        for worker in workers:
            if worker.is_done:
                res = []
                for shift in shifts:
                    if shift.shift_id in [s.shift_id for s in worker.shifts]:
                        res.append(shift.name)
                result += worker.username + ' :\n' + \
                    '\n'.join(res) + '\n'
            else:
                await self.clear_keyboard(worker.chat_id, worker.message_id)
                logger.warning(f'{worker.username} is not done')
        return result

    def is_finish_creating(self):
        command = self.db.get_command()
        workers = self.db.get_all_workers()
        flag = True
        for worker in workers:
            flag = flag and worker.is_done
        return flag or command.is_done

    async def send_notification_choose_shifts(self):
        command = self.db.get_command()
        for time_message in TIME_MESSAGE[command.step - 1:]:
            if not self.is_finish_creating():
                t = command.start_time + \
                    (command.end_time - command.start_time) * \
                    time_message['part_of_time'] - \
                    datetime.now()

                seconds = int(t.total_seconds())
                while seconds > 0 and not self.is_finish_creating():
                    await asyncio.sleep(min(seconds, config.CHECK_END_SCHEDULE_CREATING_TIME))
                    t = command.start_time + \
                        (command.end_time - command.start_time) * \
                        time_message['part_of_time'] - \
                        datetime.now()
                    seconds = int(t.total_seconds())

                workers = self.db.get_all_workers()
                for worker in workers:
                    if not worker.is_done:
                        await self.send_message_to_user(
                            worker.chat_id,
                            time_message['message']
                        )
                logger.info('workers received a warning '
                            + time_message['message'])
                command = self.db.get_command()
                if not command.is_done:
                    command.step += 1
                    self.db.save_command(command)

    async def clear_keyboard(self, chat_id, message_id):
        try:
            await self.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=None
            )
        except (exceptions.MessageNotModified,
                exceptions.MessageToEditNotFound) as err:
            logger.error(err)

    async def invalid_command(self, message):
        logger.warning(f'unknown command \'{message.text}\' from admin \
with id {message.chat.id}')
        await message.reply(bot_messages['invalid_data'])
        await message.reply(bot_messages['admin_help'])

    async def notify_admins(self, message, keyboard=None):
        for admin in self.db.get_admins():
            await self.send_message_to_user(
                admin.chat_id,
                message,
                parse_mode="HTML",
                reply_markup=keyboard)

    async def forward_to_admins(self, message):
        for admin in self.db.get_admins():
            try:
                await self.bot.forward_message(
                    chat_id=admin.chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id)
                logger.success(f'\'{message.text}\' was forwarded to admins')
            except (exceptions.ChatNotFound, exceptions.BotBlocked) as err:
                logger.warning(f'{admin} - {err}')
            await message.reply(bot_messages['ok'])

    async def notify_workers(self, message):
        mess = Parser.without_command(message.text, '/notify_all')
        workers = self.db.get_all_workers()
        try:
            for worker in workers:
                try:
                    await self.bot.send_message(worker.chat_id, mess)
                    logger.success(f'{worker.username} was notified')
                except (exceptions.ChatNotFound, exceptions.BotBlocked) as err:
                    logger.warning(f'{worker.username} - {err}')
            logger.success(f'all workers were notified')

        except exceptions.MessageTextIsEmpty:
            logger.error('message is empty')

            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['notify_all_template'])

    # TODO_: add exception and logging
    async def accept_new_worker(self, chat_id, username):
        worker = Worker(
            chat_id=chat_id,
            username=username,
            rating=0,
            is_done=True,
            message_id=None
        )
        self.db.save_worker(worker)
        for rq in self.db.get_requests_to_admin(chat_id):
            await self.clear_keyboard(rq.chat_id, rq.message_id)
            self.db.delete_request(rq.request_id)
        await self.send_message_to_user(chat_id, bot_messages['start_auth'])

    # TODO_: add exception and logging
    async def decline_worker(self, chat_id):
        for rq in self.db.get_requests_to_admin(chat_id):
            await self.clear_keyboard(rq.chat_id, rq.message_id)
            self.db.delete_request(rq.request_id)
        await self.send_message_to_user(
            chat_id,
            bot_messages['answer_decline_worker'])

    async def get_schedule_template(self, message):
        try:
            start_date = Parser.schedule_template(message.text)
        except (ValueError, IndexError) as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['get_schedule_template_template'])
            logger.error(f'invalid data, {err}')
            return
        shifts = []
        for shift in STANDARD_SCHEDULE_TIMEDELTAS:
            shift_time_start = start_date + shift[0]
            shift_time_finish = shift_time_start + shift[1]
            shifts.append(
                str(shift_time_start.date()) + ' '
                + str(shift_time_start.hour) + ':'
                + str(shift_time_start.minute) + ' - '
                + str(shift_time_finish.hour) + ':'
                + str(shift_time_finish.minute))
        header = f'/create_schedule {str(start_date - timedelta(hours=32))}\n'
        mess = header + '\n'.join(shifts)
        await self.send_message_to_user(message.chat.id, mess)
        logger.success(f'schedule template was sent to admin \
{message.chat.id}')

    async def send_full_schedule_worker(self, message):
        schedule = self.db.get_schedule()
        await message.reply(
            MessageCreator.full_schedule_worker(schedule))
        logger.success(f'full schedule was sent to worker{message.chat.id}')

    async def send_full_schedule_admin(self, message):
        schedule = self.db.get_schedule()
        await message.reply(
            MessageCreator.full_schedule_admin(schedule))
        logger.success(f'full schedule was sent to admin {message.chat.id}')

    async def send_shifts_without_worker(self, message):
        shifts = self.db.get_actual_shifts()
        await message.reply(MessageCreator.shifts_without_worker(shifts))
        logger.success(f'shifts without workers was sent to admin \
{message.chat.id}')

    async def send_personal_schedule(self, message):
        schedule = self.db.get_schedule(message.chat.id)
        await message.reply(
            MessageCreator.worker_schedule(schedule))
        logger.success(f'personal schedule was sent to worker \
{message.chat.id}')

    async def delete_shift(self, message):
        try:
            shift_id = int(message.text.split()[-1])
            s = self.db.get_shift(shift_id)
            if s and s.has_worker is False:
                self.db.delete_shift(shift_id)
                await message.reply(bot_messages['ok'])
                logger.success(f'{s.name} {s.shift_id} was deleted')
            else:
                await message.reply(bot_messages['shift_does_not_exist'])
                logger.warning('shift with id: {shift_id} does not exist')
        except (ValueError) as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(bot_messages['delete_shift_template'])
            logger.error(f'invalid data. ValuueError: {err}')
            return

    async def change_worker_for_shift(self, message):
        try:
            shift_id, username = Parser.worker_for_shift(message.text)
            logger.debug(f'shift_id {shift_id} {username}')
            s = self.db.get_shift(shift_id)
            if s:
                if username.lower() == 'none' and s.schedule:
                    prev_chat_id = s.schedule.chat_id
                    self.db.delete_schedule(s.schedule.schedule_id)
                    self.db.update_shift_has_worker(shift_id, False)
                    await self.send_message_to_user(
                        prev_chat_id,
                        MessageCreator.delete_your_shift(s.name))
                else:
                    w = self.db.get_worker_by_username(username)
                    if not w:
                        await message.reply(
                            bot_messages['worker_username_does_not_exist'])
                        logger.error(f'worker username \'{username}\' \
does not exist')
                        return
                    if s.schedule:
                        prev_chat_id = s.schedule.chat_id
                        self.db.delete_schedule(s.schedule.schedule_id)
                        await self.send_message_to_user(
                            prev_chat_id,
                            MessageCreator.delete_your_shift(s.name))
                    schedule = Schedule(
                        shift_id=shift_id,
                        chat_id=w.chat_id,
                        rating=s.cost * s.coefficient * w.coefficient
                    )
                    self.db.save_schedule(schedule)
                    await self.send_message_to_user(
                        w.chat_id,
                        MessageCreator.add_your_shift(s.name))
                    self.db.update_shift_has_worker(shift_id, True)
                await message.reply(bot_messages['ok'])
                logger.success(f'worker for {s.name} was changed on \
{username}')
            else:
                await message.reply(bot_messages['shift_does_not_exist'])
                logger.warning('shift with id: {shift_id} does not exist')
        except (ValueError, IndexError) as err:
            await message.reply(bot_messages['invalid_data'])
            await message.reply(
                bot_messages['change_worker_for_shift_template'])
            logger.error(f'invalid data. ValuueError: {err}')
            return

    async def clean_shifts(self, message):
        shifts = self.db.get_past_shifts(datetime.now())

        for s in shifts:
            if s.has_worker:
                w = self.db.get_worker(s.schedule.chat_id)
                rating = w.rating
                d_rating = s.schedule.rating
                new_rating = rating + d_rating
                self.db.change_worker(w.chat_id, {'rating': new_rating})
                await message.reply(f'{s.name} {w.username} {rating} + \
{d_rating} = {new_rating}')
                logger.success(f'{s.name} {w.username} {rating} + {d_rating} \
= {new_rating}')
            else:
                await message.reply(s.name)
                logger.warning(f'{s.name} was deleted')
            self.db.delete_shift(s.shift_id)
        logger.success('shifts was cleaned')

    async def admin_help(self, message):
        await message.reply(bot_messages['admin_help'])
        logger.success(f'help request was sent to admin {message.chat.id}')

    async def worker_help(self, message):
        await message.reply(bot_messages['worker_help'])
        logger.success(f'help request was sent to worker {message.chat.id}')

    async def all_help(self, message):
        await message.reply(bot_messages['all_help'])
        logger.success(f'help request was sent to chat {message.chat.id}')

    async def setup_bot_commands(self, _):
        bot_commands = [
            BotCommand(command='/help', description='help message'),
            BotCommand(command='/schedule', description='full schedule'),
            BotCommand(
                command='/my_schedule', description='personal schedule'),
        ]
        await self.bot.set_my_commands(bot_commands)

    async def on_startup(self):
        command = self.db.get_command()
        if command and not command.is_done:
            await self.continue_creating_schedule()

    def run(self):

        self.dp.loop.create_task(self.on_startup())
        executor.start_polling(
            self.dp, skip_updates=True, on_startup=self.setup_bot_commands)
            # self.dp, skip_updates=True)
