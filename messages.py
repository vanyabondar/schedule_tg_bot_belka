TIME_MESSAGE = [
    {'part_of_time': 0.25,
        'message': 'Відміть зміни якомога швидше☝️'},
    {'part_of_time': 0.75,
        'message': 'Час майже закінчився. Відміть хоча б ті, у яких \
        впевнений'},
    {'part_of_time': 1,
        'message': 'Ігнорщик. Аллах все бачить 😒'},
]

bot_messages = {
    'shift_selected_icon': '✅',
    'all_shifts_selected': 'Готово',
    'choose_all_shifts': 'Вибери всі зміни, в які ти зможеш почергувати:',
    'no_shifts_selected': '😔 Спробуємо впоратися без тебе',
    'button_accept_worker': 'Додати чергового',
    'button_decline_worker': 'Відмінити',
    'answer_decline_worker': 'Без поняття хто ти і що хочеш. Пиши сюди @elohssa',
    'your_wishes': 'Твій вибір:',
    'start_auth': 'Дарова, чєл! Ти вже в списку чергових',
    'worker_does_not_exist': 'Чергового з таким id не існує',
    'worker_username_does_not_exist': 'Чергового з таким username не існує',
    'worker_already_exists': 'Черговий з таким id уже існує',
    'invalid_data': 'Некоректні дані. Дивись шаблон',
    'invalid_time': 'Некоректно заданий час, час вже минув',
    'wishes_header': 'Побажання:\n',
    'worker_schedule_header': 'Твої зміни:\n',
    'delete_your_shift_header': 'Це більше не твоя зміна - ',
    'add_your_shift_header': 'Це твоя нова зміна - ',
    'all_shifts_has_worker': 'Всі зміни розподілені 👍🏾',
    'you_have_not_shift': 'Найближчим часом ти не чергуєш',
    'full_schedule_header': 'Графік чергувань:\n',
    'schedule_is_empty': 'Графік поки не створений',
    'shift_does_not_exist': 'Зміни з таким id не існує серед актульних',
    'ok': '👌🏿',
    'schedule_is_not_creating': 'Зараз розклад не створюється',
    'unknown_user': 'Зачекайте, іде ідентифікація вашої особистості',
    'shifts_without_worker_header': 'У ці дні немає бажаючих:\n',
    'non-existent_user': 'Користувача не існує',
    'schedule_header': 'Графік на наступний тиждень:\n',
    'personal_schedule_header': 'Твій графік на наступний тиждень:\n',
    'personal_schedule_without_shifts': 'Наступного тижня ти не чергуєш',
    'notify_all_template': '/notify_all Хто зможе завтра почергувати?',
    'delete_worker_template': '/delete_worker 5018287782',
    'delete_shift_template': '/delete_shift 232',
    'add_worker_template': '/add_worker 5018287782 @test 55.5',
    'get_schedule_template_template': '/get_schedule_template 2022-02-07',
    'change_worker_for_shift_template': '/change_worker_for_shift 264 @elohssa',
    'change_rating_template': '''/change_rating
@elohssa 20
@test 22''',

    'create_schedule_template':
    '''/create_schedule 2022-02-26 16:00:00
2022-02-28 10:0 - 16:0
2022-02-28 16:0 - 22:0
2022-03-01 10:0 - 16:0
2022-03-01 16:0 - 22:0
2022-03-02 10:0 - 16:0
2022-03-02 16:0 - 22:0
2022-03-03 10:0 - 16:0
2022-03-03 16:0 - 22:0
2022-03-04 10:0 - 16:0
2022-03-04 16:0 - 22:0
2022-03-05 12:0 - 22:0''',
    'admin_help': '''Список команд
/help - список команд
/rating - рейтинг чергових
/schedule - повний графік чергувань
/shifts_without_worker - зміни, які потребують чергового
/change_worker_for_shift - змінити чергового на зміну (щоб видалити введіть None)
/change_rating - змінити рейтинг чергових
/add_worker - додати нового чергового
/delete_worker - видалити чергового
/create_schedule - запуск створення розкладу
/stop_schedule_creating - зупинити створення розкладу
/notify_all - відправити повідомлення всім черговим
/get_schedule_template - отримати шаблон графіку починаючи з дати
/clean_shifts - підтвердити пройдені зміни''',
    'worker_help': '''Зачекайте, поки адміністратор запустить створення розкладу, тоді відмітьте всі зніни, в які можете чергувати і натисніть \"Готово\".
/schedule - повний графік чергувань
/my_schedule - особистий графік чергувань
Поки іншого функціоналу для вас не передбачено.
З питаннями, побажаннями і скаргами звертайтесь сюди @elohssa''',
    'all_help': '''Якщо ви черговий BelkaSpace введіть /start і чекайте, поки адміністратор вас додасть.
Якщо ви знаєте, що таке BelkaSpace і хочете чергувати напишіть @elohssa.
Інакше цей бот не для вас'''
}
