from datetime import datetime

from db import Command, Shift, Worker

WEEKDAYS = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'НД']


class Parser():
    @staticmethod
    def schedule(text, chat_id, message_id):
        end_time = datetime.strptime(
            text.split('\n')[0][len('/create_schedule') + 1:],
            '%Y-%m-%d %H:%M:%S')

        shifts = []
        for i, line in enumerate(text.split('\n')[1:]):
            start_date_str = (line.split(' ')[0])
            shift_start_time = datetime.strptime(
                start_date_str + ' ' + line.split(' ')[1],
                '%Y-%m-%d %H:%M')
            shift_finish_time = datetime.strptime(
                start_date_str + ' ' + line.split(' ')[3],
                '%Y-%m-%d %H:%M')
            if shift_finish_time < shift_start_time:
                raise ValueError(f'start time {shift_start_time} \
> finish time {shift_finish_time}')
            name = WEEKDAYS[shift_start_time.weekday()] + ' '\
                + shift_start_time.strftime('%m-%d %H:%M') + ' - '\
                + shift_finish_time.strftime('%H:%M')
            cost = round(
                (shift_finish_time - shift_start_time).seconds / 3600, 2)
            s = Shift(
                name=name,
                time_start=shift_start_time,
                time_finish=shift_finish_time,
                cost=cost
            )
            shifts.append(s)

        start_time = datetime.now()

        command = Command(
            message_id=message_id,
            chat_id=chat_id,
            name='create_schedule',
            start_time=start_time,
            end_time=end_time,
            step=0,
            is_done=False)

        return command, shifts

    @staticmethod
    def worker(text):
        lst = text[len('/add_worker') + 1:].split()
        w = Worker(
            chat_id=int(lst[0]),
            username=lst[1],
            rating=float(lst[2]),
            is_done=False,
            message_id=None
        )
        return w

    @staticmethod
    def username_rating(text):
        username_rating_dict = {}
        for line in text.split('\n')[1:]:
            arguments = line.split()
            if arguments[0] in username_rating_dict:
                username_rating_dict[arguments[0]] += float(arguments[1])
            else:
                username_rating_dict[arguments[0]] = float(arguments[1])

        return username_rating_dict

    @staticmethod
    def schedule_template(text):
        text = Parser.without_command(text, '/get_schedule_template')
        text = text.strip()
        start_date = datetime.strptime(text, '%Y-%m-%d')
        return start_date

    @staticmethod
    def worker_for_shift(text):
        args = text.split()
        shift_id = int(args[1])
        username = args[2]
        return shift_id, username

    @staticmethod
    def without_command(text, command):
        mess = text[:text.find(command)]
        text = text[text.find(command):]
        mess += text[len(command):]

        return mess
