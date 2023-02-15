from messages import bot_messages


class MessageCreator:
    @staticmethod
    def worker_wishes(shifts):
        res = [shift.name for shift in shifts]

        if res:
            res.insert(0, bot_messages['your_wishes'])
        else:
            res.append(bot_messages['no_shifts_selected'])

        return '\n'.join(res)

    @staticmethod
    def rating(workers):
        lst = []
        for w in workers:
            lst.append(f'{w.chat_id}\t{w.username}\t{str(round(w.rating, 2))}')
        return '\n'.join(lst)

    @staticmethod
    def schedule(schedule):
        res = [f'{shift.id} {shift.final_worker.id}' for shift in schedule]
        message = bot_messages['schedule_header'] + '\n'.join(res)
        return message

    # @staticmethod
    # def change_rating_from_schedule(schedule):
    #     res = [f'{line[4]} {str(line[2])}' for line in schedule if line[1]]
    #     message = '/change_rating\n' + '\n'.join(res)
    #     return message

    @staticmethod
    def personal_schedule(chat_id, schedule):

        res = [line.id for line in schedule if line.final_worker == chat_id]
        message = bot_messages['personal_schedule_without_shifts']
        if res:
            message = bot_messages['personal_schedule_header'] + '\n'.join(res)
        return message

    @staticmethod
    def start_from_anonymous(message):
        res = f'''name:\t{message.chat.first_name}
chat_id:\t<code>{message.chat.id}</code>
username:\t@{message.chat.username if 'username' in message.chat else 'None'}
text:\t{message.text}
'''
        return res

    @staticmethod
    def worker_schedule(schedule):
        if schedule:
            message = (
                bot_messages['worker_schedule_header'] + '\n'
                + '\n'.join([s.shift.name for s in schedule]))
        else:
            message = bot_messages['you_have_not_shift']
        return message

    @staticmethod
    def full_schedule_worker(schedule):
        if schedule:
            message = (
                bot_messages['full_schedule_header'] + '\n'
                + '\n'.join(
                    [f'{s.shift.name} {s.worker.username}' for s in schedule]))
        else:
            message = bot_messages['schedule_is_empty']
        return message

    @staticmethod
    def full_schedule_admin(schedule):
        if schedule:
            message = (
                bot_messages['full_schedule_header'] + '\n'
                + '\n'.join(
                    [f'{s.shift_id} {s.shift.name} \
{s.worker.username} {round(s.rating, 2)}' for s in schedule]))
        else:
            message = bot_messages['schedule_is_empty']
        return message

    @staticmethod
    def shifts_without_worker(schedule):
        if schedule:
            message = (
                bot_messages['shifts_without_worker_header'] + '\n'
                + '\n'.join(
                    [f'{s.shift_id} {s.name}' for s in schedule]))
        else:
            message = bot_messages['all_shifts_has_worker']
        return message

    @staticmethod
    def delete_your_shift(shift_name):
        message = bot_messages['delete_your_shift_header'] + shift_name
        return message

    @staticmethod
    def add_your_shift(shift_name):
        message = bot_messages['add_your_shift_header'] + shift_name
        return message
