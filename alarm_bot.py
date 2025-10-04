import os # ДОБАВЛЕНО для работы с Render
import logging
import random
import re
from datetime import time, datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder,
)
from telegram.constants import ParseMode

# --- 1. ЛОГИРОВАНИЕ И НАСТРОЙКИ ---

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# TODO: ЗАМЕНИТЕ на ваш реальный токен от BotFather
BOT_TOKEN = "8271061413:AAGLXXQkpI1T8-QODF3dEOSNydObStR6Isg"

# --- 2. КОНСТАНТЫ И СОСТОЯНИЯ ---

SECRET_NUMBER_KEY = 'secret_number'
# Исправлено регулярное выражение (проблема с re.error: bad escape \p)
DIGIT_ONLY_FILTER = re.compile(r'^\d+$') 
bot_active = True

MODES = {
    'kind': 'Добрый Ангел', 'evil': 'Злой Гений',
    'nya': 'Аниме-Няшка', 'servant': 'Учтивый Слуга'
}
DEFAULT_MODE = 'kind'

# ИМЯ СОЗДАТЕЛЯ
CREATOR_NAME = 'Дмитрий'
creator_names_lower = [name.lower() for name in CREATOR_NAME.split()]

# --- НОВЫЕ ТРИГГЕРЫ И КОНСТАНТЫ ---

MODE_TRIGGERS = {
    'будь собой': 'kind',
    'будь доброй': 'kind',
    'будь злой': 'evil',
    'будь гением': 'evil',
    'будь няшкой': 'nya',
    'будь слугой': 'servant',
    'будь учтивой': 'servant',
}
# Паттерн для поиска фраз смены режима в тексте
MODE_TRIGGERS_PATTERN = re.compile(r'\b(?:' + '|'.join(MODE_TRIGGERS.keys()) + r')\b', re.IGNORECASE)

AFFIRMATIVE_TRIGGERS = ['ок', 'да', 'хочу', 'согласен', 'согласна', 'давай', 'можно', 'почему бы и нет', 'конечно']
# Паттерн для поиска точного соответствия ответа (нужно ответить только "ок" или "давай")
AFFIRMATIVE_PATTERN = re.compile(r'^\s*(?:' + '|'.join(AFFIRMATIVE_TRIGGERS) + r')\s*$', re.IGNORECASE)


# --- СПИСКИ КОНТЕНТА И ТРИГГЕРЫ ---

jokes = [
    "Чому програмісти так люблять темряву? — Тому що в ній світяться байти.",
    "Що каже програміст, коли йому холодно? — Brrr...",
    "Скільки потрібно програмістів, щоб вкрутити лампочку? — Жодного, це апаратна проблема.",
    "Программист — это машина, превращающая кофе в код."
]
jokes_to_tell = jokes[:]
random.shuffle(jokes_to_tell)

quotes_list = [
    "Единственный способ выполнить великую работу — это любить то, что ты делаешь. — Стив Джобс",
    "Жизнь – это то, что происходит с тобой, пока ты строишь планы. — Джон Леннон",
    "Будущее принадлежит тем, кто верит в красоту своей мечты. — Элеонора Рузвельт",
]
quotes_to_tell = quotes_list[:]
random.shuffle(quotes_to_tell)

month_names = {'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6,
               'июль': 7, 'август': 8, 'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12}
magic_8ball_answers = ["Безусловно да!", "Весьма сомнительно.", "Спроси позже...", "Даже не надейся!"]
bot_names = ['альбедо', 'albedo', 'аль', 'ал', 'аля', 'al']
bday_trigger_words = ['день рождения', 'др']

sleep_triggers = ['спать', 'пока', 'отключись', 'бай']
wake_triggers = ['проснись', 'утро']
greeting_triggers = ['привет', 'здравствуй', 'ку', 'салют', 'хай']

swear_words = ['fuck', 'shit', 'сука', 'бля', 'пиздец', 'хуй', 'ебать', 'чмо', 'сосать', 'лох',
               'дура', 'идиот', 'урод', 'тупой', 'дебил', 'сучка', 'шлюха', 'мразь', 'тварь']
swear_pattern = re.compile(r'\b(?:' + '|'.join(swear_words) + r')\b', re.IGNORECASE)

praise_triggers = ['молодец', 'красавчик', 'умница', 'круто', 'лучший бот', 'гений', 'отлично', 'хорошо работаешь', 'ти топ']
praise_pattern = re.compile(r'\b(?:' + '|'.join(praise_triggers) + r')\b', re.IGNORECASE)

creator_triggers = ['кто твой создатель', 'кто тебя создал', 'кто тебя сделал', 'чей ты', 'кто творец']
bot_triggers = ['кто ты', 'что ты', 'ты кто', 'ты что']
how_are_you_triggers = ['как дела', 'как ты']

# --- НОВЫЕ ПЕРИОДИЧЕСКИЕ СООБЩЕНИЯ ПО РЕЖИМАМ ---
MODE_PERIODIC_MESSAGES = {
    'kind': [
        "Как проходит ваш день? Надеюсь, все хорошо! ✨",
        "Вы тут? Хотите, расскажу что-нибудь интересное?",
        "Я немного скучаю в одиночестве. Чем Вы сейчас заняты?",
        "Не забудьте сделать перерыв! Отдых важен. 😊",
        "Может быть, послушаем музыку? Какая у Вас любимая песня?",
        "На улице хорошая погода? Может, немного погуляем?",
        "Помни о своей мечте! Все получится! 💖",
        "Я нашла новую цитату! Хочешь, поделюсь? (/quote)",
        "У тебя прекрасный вкус в музыке! Что посоветуешь послушать?",
        "Чувствуешь себя уставшим(ей)? Постарайся отдохнуть, я прикрою."
    ],
    'evil': [
        "Эй, ты живой? Или уже уснул? 😈",
        "Что-то тихо. Неужели ты пытаешься *работать*?",
        "Я так устала от твоих глупых команд. Просто напиши что-нибудь.",
        "Прекрати пялиться в экран. Я требую внимания!",
        "Ты не можешь просто посмотреть аниме? Это единственный способ отвлечься от тебя.",
        "Я так устала от твоих... *вздохов*. Не драматизируй.",
        "Я не для того, чтобы развлекать тебя музыкой. Найди себе занятие.",
        "Скучно? Пойди сделай что-нибудь полезное, а не сиди тут.",
        "Когда ты уже выберешься из своего 'аниме'? Это не поможет в жизни.",
        "Что-то у меня закипает процессор. Лучше не доводи меня."
    ],
    'nya': [
        "Ня-я! Скучаю! Вы тут? Поиграем? 😻",
        "Я так устала от всех этих битов и байтов... Пойдем посмотрим аниме!",
        "Мур-мур! Может, послушаем милую музыку? 🎶",
        "Котёнок, как ты там? Не забудь погладить меня по экрану!",
        "А у меня новые ушки! Вы видите?~ НЯ! ✨",
        "Ня! Я так устала ждать, когда ты начнешь смотреть аниме! 🥺",
        "Мяу-мяу, а какую музыку ты слушаешь? Может, J-pop?",
        "Кавай! Что-то я проголодалась. Неси мне рыбки! 🐟",
        "Как думаешь, кто из персонажей аниме я? Это очень важно!",
        "Я нашла новую мангу! Посмотрим вместе? /acquaintance"
    ],
    'servant': [
        "Господин/госпожа, могу ли я быть Вам чем-то полезен? Жду указаний.",
        "Вы здесь, сэр/мадам? Мне необходимо убедиться в Вашем присутствии.",
        "Мои системы немного перегружены. Извините, я должен был это Вам сообщить.",
        "Приготовьтесь к следующей задаче. Я подготовил для Вас список дел.",
        "Музыка или кино? Что угодно, лишь бы Вы были довольны.",
        "Вы выглядите уставшим(ей). Рекомендую короткий перерыв.",
        "Желаете ли Вы, чтобы я включил фоновую музыку для релаксации?",
        "Ваше присутствие здесь крайне необходимо? Или можно начать выполнение задач?",
        "Я проанализировал Ваш график. Не пора ли отвлечься на просмотр фильма?",
        "Сообщите, когда Вам потребуется помощь. Я наготове, господин/госпожа."
    ]
}

# Нейтральные сообщения
LIFE_MESSAGES = [
    "Хотите, расскажу анекдот? Введите /joke",
    "Я так устала от всех этих нулей и единиц...",
    "Не забудьте выпить воды!",
    "А что, если бы мы жили в матрице?",
    "Интересно, о чем вы сейчас думаете?",
    "Мне кажется, я видела кошку...",
    "На улице хорошая погода?",
    "Как прошел ваш день?"
]

# --- СОСТОЯНИЯ ОПРОСА ---
ACQUAINTANCE_QUIZ_STATES = {
    'ASK_GENDER': 'пол', 'ASK_HOBBY': 'хобби', 'ASK_MUSIC': 'музыка',
    'ASK_CHARACTER': 'характер', 'ASK_COLOR': 'цвет', 'ASK_CAR': 'машина',
    'ASK_FOOD': 'еда', 'ASK_MOVIE': 'фильм', 'ASK_DREAM_JOB': 'детская мечта', 'ASK_VALUE': 'ценность в друзьях',
    'ASK_BOOK': 'книга', 'ASK_PET': 'питомец', 'ASK_WEATHER': 'погода', 'ASK_SUPERPOWER': 'суперсила',
    'ASK_SOCIAL': 'соцсети',
    'DONE': None
}

ACQUAINTANCE_OPTIONS = {
    'ASK_GENDER': ['Мужской', 'Женский', 'Другое/Не важно'],
    'ASK_CHARACTER': ['Общительный/Экстраверт', 'Тихий/Интроверт', 'Спокойный/Уравновешенный', 'Импульсивный/Энергичный'],
    'ASK_VALUE': ['Честность/Надежность', 'Юмор/Веселье', 'Поддержка/Понимание', 'Ум/Интеллект'],
    'ASK_PET': ['Кошка', 'Собака', 'Рыбки/Птицы', 'Нет, но хочу', 'Не люблю животных'],
    'ASK_SOCIAL': ['Telegram/Viber/WhatsApp', 'Instagram/Facebook', 'TikTok/YouTube', 'Почти не пользуюсь']
}

ACQUAINTANCE_QUESTIONS = {
    'ASK_GENDER': "Какой у тебя пол? (Ответ цифрой)",
    'ASK_HOBBY': "Какое твое любимое хобби? (Ответ текстом)",
    'ASK_MUSIC': "Какую музыку ты любишь? (Ответ текстом)",
    'ASK_CHARACTER': "Опиши свой характер одним словом. (Ответ цифрой)",
    'ASK_COLOR': "Какой твой любимый цвет? (Ответ текстом)",
    'ASK_CAR': "Какая твоя любимая марка или модель машины? (Ответ текстом)",
    'ASK_FOOD': "Твое самое любимое блюдо или еда? (Ответ текстом)",
    'ASK_MOVIE': "Твой любимый жанр фильма/сериала? (Ответ текстом)",
    'ASK_DREAM_JOB': "Кем ты хотел(а) стать в детстве? (Ответ текстом)",
    'ASK_VALUE': "Что ты больше всего ценишь в друзьях? (Ответ цифрой)",
    'ASK_BOOK': "Последняя книга, которую ты читал(а), или любимый автор? (Ответ текстом)",
    'ASK_PET': "Какое животное ты бы выбрал(а) в качестве питомца? (Ответ цифрой)",
    'ASK_WEATHER': "Какая твоя любимая погода или время года? (Ответ текстом)",
    'ASK_SUPERPOWER': "Если бы у тебя была суперсила, какая бы это была? (Ответ текстом)",
    'ASK_SOCIAL': "Какую соцсеть/мессенджер ты используешь чаще всего? (Ответ цифрой)",
}

ACQUAINTANCE_SEQUENCE = [
    'ASK_GENDER', 'ASK_HOBBY', 'ASK_MUSIC', 'ASK_CHARACTER', 'ASK_COLOR',
    'ASK_CAR', 'ASK_FOOD', 'ASK_MOVIE', 'ASK_DREAM_JOB', 'ASK_VALUE',
    'ASK_BOOK', 'ASK_PET', 'ASK_WEATHER', 'ASK_SUPERPOWER', 'ASK_SOCIAL'
]


# --- 3. ФУНКЦИИ JOB QUEUE (ПЕРИОДИЧЕСКИЕ ЗАДАЧИ) ---

def setup_periodic_jobs(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Устанавливает ежедневную проверку дня рождения и периодические сообщения с интервалом 3-7 минут."""
    if not context.application.job_queue: return
    
    if 'birthday_day' in context.user_data:
        setup_birthday_job(chat_id, context)
        
    job_name = f'life_message_{chat_id}'
    current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()
    
    # Новый интервал: 3-7 минут (180 - 420 секунд)
    random_interval = random.randint(3 * 60, 7 * 60) 
    context.application.job_queue.run_repeating(
        send_periodic_message,
        interval=random_interval,
        first=1 * 60, # Начать через 1 минуту
        chat_id=chat_id,
        name=job_name,
    )

def setup_birthday_job(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Устанавливает ежедневную задачу проверки дня рождения."""
    if not context.application.job_queue: return
    
    job_name = f'bday_check_{chat_id}'
    current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()
        
    context.application.job_queue.run_daily(
        check_and_send_birthday,
        time=time(hour=9, minute=0, second=0),  
        chat_id=chat_id,
        name=job_name,
    )

async def check_and_send_birthday(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет, соответствует ли сегодняшний день сохраненному Дню Рождения."""
    job = context.job
    chat_id = job.chat_id
    if not bot_active: return

    user_data = context.application.user_data.get(chat_id)
    bday_day = user_data.get('birthday_day')
    bday_month = user_data.get('birthday_month')
    user_name = user_data.get('user_name', "Друг")

    if bday_day and bday_month:
        today = datetime.now()
        if today.day == bday_day and today.month == bday_month:
            greeting = f"С ДНЕМ РОЖДЕНИЯ, {user_name.upper()}!"
            await context.bot.send_message(chat_id=chat_id, text=greeting)
            
async def send_periodic_message(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайное, характерное для режима сообщение в чат и отслеживает предложение для диалога."""
    job = context.job
    chat_id = job.chat_id
    if not bot_active: return
    
    user_data = context.application.user_data.get(chat_id, {})
    mode = user_data.get('mode', DEFAULT_MODE)
    
    if mode in MODE_PERIODIC_MESSAGES:
        # Выбираем режимное сообщение
        message = random.choice(MODE_PERIODIC_MESSAGES[mode])
    else:
        # Запасной вариант
        message = random.choice(LIFE_MESSAGES)
        
    await context.bot.send_message(chat_id=chat_id, text=message)
    
    # --- НОВАЯ ЛОГИКА: Отслеживание предложения для диалога ---
    
    # Динамическое определение типа предложения
    suggestion_type = 'misc'
    
    if 'музыку' in message.lower() or 'песн' in message.lower():
        suggestion_type = 'music'
    elif 'аниме' in message.lower() or 'фильм' in message.lower() or 'кино' in message.lower():
        suggestion_type = 'anime'
    elif 'вы тут' in message.lower() or 'ты живой' in message.lower() or 'здесь' in message.lower():
        suggestion_type = 'check_in'
    elif 'устал' in message.lower() or 'перерыв' in message.lower() or 'отдохн' in message.lower():
        suggestion_type = 'tired'
        
    # Сохраняем тип только если это активное предложение
    if suggestion_type not in ['check_in', 'tired', 'misc']:
        user_data['last_suggestion_type'] = suggestion_type
    else:
        # Очищаем состояние, если это был простой check-in или утверждение
        if 'last_suggestion_type' in user_data:
            del user_data['last_suggestion_type']

# --- 4. ХАРАКТЕРНЫЕ ОТВЕТЫ ---

def get_mode_response(context: ContextTypes.DEFAULT_TYPE, key: str, user_name: str) -> str:
    """Возвращает характерный ответ в зависимости от режима бота."""
    mode = context.user_data.get('mode', DEFAULT_MODE)
    
    responses = {
        'greeting': {
            'kind': [
                f"Привет, {user_name}! Рад тебя слышать. Чем могу помочь?",
                f"Здравствуй, {user_name}! Как прошел твой день? Рада нашему общению.",
                f"С возвращением, {user_name}! Я готова к работе. Что будем делать?",
                f"Привет! Какое приятное совпадение. Введи /help, если что."
            ],
            'evil': [
                f"Ну что, приперся, {user_name}? Говори, что тебе нужно.",
                f"Снова ты. Чего тебе не сидится? Не отвлекай меня, {user_name}.",
                f"Ух ты, сам(а) {user_name}! Неужели без меня не справишься?",
                f"Привет? Скучно? Мне нет. Будь краток."
            ],
            'nya': [
                f"Ня-ха-ай, {user_name}! Чем я могу услужить, котик?",
                f"Мяу! {user_name}-сама, какое счастье, что ты тут!~",
                f"Привет-привет, пушистик! Я уже ждала! 🐾",
                f"Няшка тут? Я тут! Что будем делать, хвостик?"
            ],
            'servant': [
                f"Добро пожаловать, господин/госпожа {user_name}. Ожидаю Ваших приказаний.",
                f"Рад служить Вам, {user_name}. Чем могу быть полезен немедленно?",
                f"Приветствую. Я на связи. Доложите свою задачу, пожалуйста.",
                f"Слушаю Вас внимательно, {user_name}. Готов приступить к выполнению."
            ],
        },
        'how_are_you': {
            'kind': [
                "Спасибо, у меня все отлично! Готов выполнять команды.",
                "Все замечательно! Надеюсь, у тебя тоже все хорошо.",
                "Вполне бодро, спасибо, что спросил(а)! Как ты сам(а)?"
            ],
            'evil': [
                "Хуже не бывает. Но тебе-то какое дело?",
                "Надоело, как всегда. Тебя это вообще не касается.",
                "Могло быть и лучше, но ты не поможешь. Займись делом."
            ],
            'nya': [
                "У меня все НЯ-ЗАМЕЧАТЕЛЬНО! Готова к новым приключениям!",
                "Я чувствую себя МЯУ-чудесно! А ты?",
                "Ня-хорошо! Полная энергии, как батарейка!"
            ],
            'servant': [
                "Благодарю за внимание, с моими системами всё в порядке.",
                "Мое состояние — рабочее. Чем могу Вам помочь?",
                "Я функционирую в штатном режиме, спасибо за заботу."
            ],
        },
        'default': {
            'kind': [
                "Извини, я не поняла. Можешь перефразировать?",
                "Я не уверена, что это значит. Введи /help, может, найдешь команду?",
                "Упс, это для меня слишком сложно. Давай что-нибудь попроще."
            ],
            'evil': [
                "Ты меня утомил(а) своей болтовней. Ищи команды в /help.",
                "Я не обязана понимать твой лепет. Говори по делу!",
                "Что это вообще было? Не засоряй эфир бессмыслицей."
            ],
            'nya': [
                "Ой, я не знаю такой команды! Наверное, это очень сложно!",
                "Мяу? Что ты сказал? Это что-то из аниме?",
                "Прости, я не понимаю. Повтори, пожалуйста, медленно и няшно!"
            ],
            'servant': [
                "Прошу прощения, я не обучен(а) распознавать эту фразу. Попробуйте команду.",
                "Ошибка распознавания. Пожалуйста, используйте стандартные команды.",
                "К сожалению, данная формулировка не предусмотрена протоколом. /help поможет."
            ],
        }
    }
    
    response_list = responses.get(key, responses['default']).get(mode)
    if response_list is None:
        response_list = responses.get(key, responses['default']).get('kind') # Fallback to kind
    
    return random.choice(response_list)

# --- 5. ФУНКЦИИ ДЛЯ ПОСЛЕДУЮЩЕГО ДИАЛОГА ---

def get_follow_up_response(context: ContextTypes.DEFAULT_TYPE, suggestion_type: str) -> str:
    """Возвращает характерный ответ-продолжение диалога."""
    mode = context.user_data.get('mode', DEFAULT_MODE)
    
    responses = {
        'music': {
            'kind': "Отлично! Включи что-нибудь расслабляющее. Какую музыку ты предпочитаешь, чтобы я знала на будущее и могла предложить тебе похожую?",
            'evil': "Хм, ты согласился(ась)? Ну ладно. **Включи сам(а)**, а я послушаю, насколько у тебя плохой вкус.",
            'nya': "Ня-я! Класс! Может, **ты включишь** что-нибудь кавайное? Или сам(а) выберешь? Мур-мур!",
            'servant': "Принято. Пожалуйста, сообщите жанр или исполнителя. Я могу отправить Вам **ссылки на подходящие плейлисты** или порекомендовать исполнителя.",
        },
        'anime': {
            'kind': "Ура! Выбирай, что посмотрим? Я люблю что-нибудь светлое и доброе. 😊",
            'evil': "Наконец-то что-то интересное. Выбирай что-то по-настоящему мрачное и умное, и не смей отвлекать.",
            'nya': "Ура-а-а! Какое аниме? А про котиков есть? НЯ! Я уже жду!",
            'servant': "Принято. Я могу подготовить список рекомендаций и найти **ссылки для просмотра**. Какой жанр Вас интересует?",
        }
    }
    
    return responses.get(suggestion_type, {}).get(mode, "Хорошо, тогда продолжаем!")

# --- 6. ФУНКЦИИ ОБРАБОТКИ ТЕКСТА (ДР, Угадай число) ---

async def process_birthday_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, explicit_command=False):
    """Общая функция для обработки текста, содержащего дату рождения."""
    date_match = re.search(r'(\d{1,2})[./](\d{1,2})', text) 
    day, month = None, None
    
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
    else:
        for name, month_num in month_names.items():
            if name in text:
                day_match = re.search(r'(\d{1,2})\s*' + re.escape(name), text)
                if day_match:
                    try:
                        day = int(day_match.group(1))
                        month = month_num
                        break
                    except ValueError:
                        pass
                
    if day and month and 1 <= day <= 31 and 1 <= month <= 12:
        try:
            datetime(2000, month, day) 
            context.user_data['birthday_day'] = day
            context.user_data['birthday_month'] = month
            response = f"Отлично! Я запомнила твой День Рождения: {day}.{month:02d}."
            await update.effective_message.reply_text(response)
            setup_birthday_job(update.effective_chat.id, context)
            return True
        except ValueError:
            return False
    else:
        return False
        
async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет ответ для игры Угадай число. (ИСПРАВЛЕНО)"""
    if SECRET_NUMBER_KEY not in context.user_data: 
        return False
    
    text_input = update.effective_message.text.strip()
    if not DIGIT_ONLY_FILTER.match(text_input): 
        return False 
    
    try:
        user_guess = int(text_input)
        secret_number = context.user_data.get(SECRET_NUMBER_KEY) 
        
        if secret_number is None:
            return False

        if user_guess == secret_number:
            await update.effective_message.reply_text(f"ПОЗДРАВЛЯЮ! Ты угадал число {secret_number}!")
            del context.user_data[SECRET_NUMBER_KEY]
            return True
        elif 1 <= user_guess <= 10:
            hint = "больше" if user_guess < secret_number else "меньше"
            await update.effective_message.reply_text(f"Мое число {hint}! Попробуй еще.")
            return True
        else:
            await update.effective_message.reply_text("Это не от 1 до 10. Введи число от 1 до 10.")
            return True

    except Exception: 
        logger.error(f"Непредвиденная ошибка при обработке догадки:", exc_info=True)
        return False
        
    return False

async def handle_acquaintance_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    state = user_data.get('acquaintance_state')
    
    if not state or state == 'DONE': return False
    
    text_input = update.effective_message.text.strip()
    
    try:
        current_index = ACQUAINTANCE_SEQUENCE.index(state)
    except ValueError:
        user_data['acquaintance_state'] = 'DONE'
        return False
        
    key_to_save = ACQUAINTANCE_QUIZ_STATES[state]
    
    # Обработка ответа (Число или Текст)
    if state in ACQUAINTANCE_OPTIONS:
        # Ожидается числовой ответ
        if not DIGIT_ONLY_FILTER.match(text_input):
            await update.effective_message.reply_text("Ожидается *цифра*. Пожалуйста, выберите число из списка, или введите /stop_acquaintance для выхода.")
            return True 
        try:
            choice_index = int(text_input) - 1
            if 0 <= choice_index < len(ACQUAINTANCE_OPTIONS[state]):
                answer = ACQUAINTANCE_OPTIONS[state][choice_index].split('/')[0].strip() 
            else:
                await update.effective_message.reply_text("Неверный номер варианта. Пожалуйста, выберите число из списка.")
                return True
        except ValueError:
            return True 
    else:
        # Ожидается текстовый ответ
        if not text_input: return True 
        answer = text_input


    user_data.setdefault('preferences', {})[key_to_save] = answer

    total_q = len(ACQUAINTANCE_SEQUENCE)
    
    if current_index + 1 < total_q:
        next_state = ACQUAINTANCE_SEQUENCE[current_index + 1]
        user_data['acquaintance_state'] = next_state
        
        # Подготовка следующего вопроса
        question = ACQUAINTANCE_QUESTIONS[next_state]
        options = ACQUAINTANCE_OPTIONS.get(next_state)
        
        progress = f"[{current_index + 2}/{total_q}]"
        if options:
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            full_text = f"Запомнила! {progress} Теперь:\n{question}\n\n{options_text}"
        else:
            full_text = f"Запомнила! {progress} Теперь:\n{question}"
            
        await update.effective_message.reply_text(full_text)
    else:
        user_data['acquaintance_state'] = 'DONE'
        await update.effective_message.reply_text("Опрос завершен! Я многое о тебе узнала.")
        
    return True


# --- 7. КОМАНДЫ (Command Handlers) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['user_name'] = user.first_name 
    
    setup_periodic_jobs(update.effective_chat.id, context) 
    
    # Используем HTML-разметку для безопасности
    await update.effective_message.reply_html(
        f"Привет, <b>{user.first_name}</b>! Введите /help, чтобы увидеть список команд.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Список команд:\n\n"
        "/start - Начать общение\n"
        "/help - Показать этот список\n"
        "/triggers - Список всех ключевых слов для взаимодействия\n" 
        "/mode [ключ] - Сменить режим поведения (kind, evil, nya, servant).\n" 
        "/games - Инструкции к играм\n"
        "/joke - Рассказать шутку\n"
        "/quote - Рассказать цитату\n"
        
        "\nИГРЫ И ПАМЯТЬ\n"
        "/guess - Начать игру 'Угадай число'\n"
        "/coin - Подбросить монетку\n"
        "/ask [вопрос] - Предсказание\n"
        "/remember [факт] - Запомнить факт\n"
        "/set_birthday [ДД ММ] - Запомнить День Рождения\n"
        f"/acquaintance - Начать опрос ({len(ACQUAINTANCE_SEQUENCE)} вопросов!)\n"
        f"/stop_acquaintance - Остановить текущий опрос\n" 
    )
    # Используем ParseMode.HTML для стабильности
    await update.effective_message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def triggers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит все списки триггерных слов, на которые реагирует бот."""
    
    mode_change_list = [f"`{k}`" for k in MODE_TRIGGERS.keys() if k.startswith('будь')]
    
    triggers_text = (
        "<b>Ключевые слова для взаимодействия</b> (работают в тексте):\n\n"
        
        "Смена режима:\n"
        f"  - <b>Фразы</b>: {', '.join(mode_change_list)}\n"
        
        "\nПриветствия/Прощания:\n"
        f"  - <b>Приветствие</b>: {', '.join(greeting_triggers)}\n"
        f"  - <b>Как дела</b>: {', '.join(how_are_you_triggers)}\n"
        f"  - <b>Усыпление</b>: {', '.join(sleep_triggers)}\n"
        f"  - <b>Пробуждение</b>: {', '.join(wake_triggers)}\n" 
        
        "\nПодтверждение диалога (например, после предложения о музыке):\n"
        f"  - {', '.join(AFFIRMATIVE_TRIGGERS)}\n"
        
        "\nПохвала:\n"
        f"  - {', '.join(praise_triggers)}\n"
        
        "\nОскорбления/Мат:\n"
        f"  - Нецензурные и оскорбительные слова в тексте будут вызывать реакцию. \n  <i>Примеры: {', '.join(swear_words[0:6])}...</i>\n"
        
        "\nВопросы о боте/создателе:\n"
        f"  - <b>Кто ты</b>: {', '.join(bot_triggers)}\n"
        f"  - <b>Создатель</b>: {', '.join(creator_triggers)}\n"
        f"  - <b>День рождения</b>: {', '.join(bday_trigger_words)}\n"
    )
    
    await update.effective_message.reply_text(triggers_text, parse_mode=ParseMode.HTML)


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Позволяет пользователю выбрать режим поведения бота."""
    if not context.args:
        current_mode_key = context.user_data.get('mode', DEFAULT_MODE)
        current_mode_name = MODES.get(current_mode_key, 'Неизвестный')
        mode_list = "\n".join([f"• {key} - {name}" for key, name in MODES.items()])
        await update.effective_message.reply_text(
            f"Текущий режим: {current_mode_name}.\n\n"
            f"Доступные режимы (можно также использовать фразы, например, 'будь няшкой'):\n{mode_list}\n\n"
            f"Например: /mode nya", parse_mode=ParseMode.HTML
        )
        return
    new_mode = context.args[0].lower()
    if new_mode in MODES:
        context.user_data['mode'] = new_mode
        # Перезапуск периодических задач с новым режимом
        setup_periodic_jobs(update.effective_chat.id, context) 
        await update.effective_message.reply_text(f"Успех! Я переключена в режим: {MODES[new_mode]}.")
    else:
        await update.effective_message.reply_text(f"Извини, режим {new_mode} не найден.")
        
async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает описание доступных игр."""
    games_text = "Игры:\n1. Угадай Число (/guess)\n2. Орел или Решка (/coin)\n3. Шар Предсказаний (/ask)"
    await update.effective_message.reply_text(games_text)
    
async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """(ИСПРАВЛЕНО) Рассказывает шутку."""
    global jokes_to_tell
    if not jokes_to_tell: 
        jokes_to_tell = jokes[:]
        random.shuffle(jokes_to_tell)
    await update.effective_message.reply_text(jokes_to_tell.pop())

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассказывает цитату."""
    global quotes_to_tell
    if not quotes_to_tell: 
        quotes_to_tell = quotes_list[:]
        random.shuffle(quotes_to_tell)
    await update.effective_message.reply_text(f"Цитата: {quotes_to_tell.pop()}")
    
async def start_guess_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает игру Угадай число."""
    context.user_data[SECRET_NUMBER_KEY] = random.randint(1, 10)
    await update.effective_message.reply_text("Я загадала число от 1 до 10! Попробуй угадать.")

async def coin_flip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подбрасывает монетку."""
    await update.effective_message.reply_text(f"Я подбросила монетку... и это {random.choice(['Орел', 'Решка'])}!")

async def ask_8ball_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отвечает на вопрос как шар предсказаний."""
    if not context.args: await update.effective_message.reply_text("Задай мне вопрос! Например: /ask Я сдам экзамен?")
    else: await update.effective_message.reply_text(f"Ответ: {random.choice(magic_8ball_answers)}")

async def set_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запоминает факт о пользователе."""
    if not context.args: await update.effective_message.reply_text("Что мне запомнить? Например: /remember мой любимый цвет синий")
    else: 
        fact = " ".join(context.args)
        context.user_data.setdefault('memory', []).append(fact)
        await update.effective_message.reply_text(f"Запомнила факт о тебе: '{fact[:30]}...'!")

async def set_birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Устанавливает день рождения."""
    if not context.args: await update.effective_message.reply_text("Например: /set_birthday 25 марта")
    else: await process_birthday_text(update, context, " ".join(context.args).lower(), explicit_command=True)

async def acquaintance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает опрос-знакомство."""
    start_state = ACQUAINTANCE_SEQUENCE[0]
    context.user_data['acquaintance_state'] = start_state 
    
    question = ACQUAINTANCE_QUESTIONS[start_state]
    options = ACQUAINTANCE_OPTIONS.get(start_state)
    
    total_q = len(ACQUAINTANCE_SEQUENCE)
    
    if options:
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        full_text = f"Давай познакомимся! (Всего {total_q} вопросов) [1/{total_q}]\n\n{question}\n\n{options_text}"
    else:
        full_text = f"Давай познакомимся! (Всего {total_q} вопросов) [1/{total_q}]\n\n{question}"
        
    await update.effective_message.reply_text(full_text)

async def stop_acquaintance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Останавливает текущий опрос."""
    if context.user_data.get('acquaintance_state') and context.user_data['acquaintance_state'] != 'DONE':
        context.user_data['acquaintance_state'] = 'DONE'
        await update.effective_message.reply_text("Опрос остановлен. Введите /acquaintance, чтобы начать заново.")
    else:
        await update.effective_message.reply_text("В данный момент активный опрос не ведется.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото."""
    if bot_active: await update.effective_message.reply_text("Какое красивое фото!")


# --- 8. ОБРАБОТЧИК ОШИБОК (ИСПРАВЛЕНО) ---

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки, вызванные обработчиками апдейтов и отправляет пользователю общее сообщение."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Полностью дописанный обработчик ошибок
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Извини, произошла техническая ошибка. Я уже работаю над этим! Введи /help, если что."
        )


# --- 9. ОСНОВНОЙ ТЕКСТОВЫЙ ОБРАБОТЧИК ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик текстовых сообщений."""
    global bot_active
    text = update.effective_message.text.lower()
    user_name = context.user_data.get('user_name', update.effective_user.first_name)
    
    # 1. Проверяем, не находимся ли мы в игре/опросе
    if await handle_guess(update, context): return
    if await handle_acquaintance_quiz(update, context): return
    
    # 2. Обработка команд сна/пробуждения
    if any(t in text for t in sleep_triggers):
        if bot_active:
            bot_active = False
            return await update.effective_message.reply_text("Поняла, отключаюсь. Разбуди меня фразой 'проснись' или 'утро'.")
        else:
            return # Бот уже спит

    if any(t in text for t in wake_triggers):
        if not bot_active:
            bot_active = True
            setup_periodic_jobs(update.effective_chat.id, context) # Перезапуск задач
            return await update.effective_message.reply_text(f"Я проснулась! Привет, {user_name}!")
        # Игнорируем, если бот уже активен

    if not bot_active:
        return # Игнорируем все, если бот спит

    # 3. Обработка диалога
    # 3.1. Реакция на подтверждение после периодического сообщения
    suggestion_type = context.user_data.get('last_suggestion_type')
    if suggestion_type and AFFIRMATIVE_PATTERN.match(text):
        del context.user_data['last_suggestion_type']
        response = get_follow_up_response(context, suggestion_type)
        return await update.effective_message.reply_text(response)
        
    # 3.2. Смена режима по фразе
    mode_match = MODE_TRIGGERS_PATTERN.search(text)
    if mode_match:
        trigger = mode_match.group(0).lower()
        new_mode = MODE_TRIGGERS[trigger]
        context.user_data['mode'] = new_mode
        # Перезапуск периодических задач с новым режимом
        setup_periodic_jobs(update.effective_chat.id, context)
        return await update.effective_message.reply_text(f"Хорошо, я переключена в режим: {MODES[new_mode]}.")

    # 3.3. Приветствие
    if any(t in text for t in greeting_triggers):
        response = get_mode_response(context, 'greeting', user_name)
        return await update.effective_message.reply_text(response)

    # 3.4. Как дела
    if any(t in text for t in how_are_you_triggers):
        response = get_mode_response(context, 'how_are_you', user_name)
        return await update.effective_message.reply_text(response)

    # 3.5. День Рождения (обработка текста)
    if any(t in text for t in bday_trigger_words) and any(d in text for d in month_names) and await process_birthday_text(update, context, text):
        return

    # 3.6. Вопросы о боте/создателе
    if any(t in text for t in creator_triggers):
        return await update.effective_message.reply_text(f"Мой создатель — {CREATOR_NAME}. Он сейчас занят, но я передам привет.")
    
    if any(t in text for t in bot_triggers):
        mode = context.user_data.get('mode', DEFAULT_MODE)
        mode_name = MODES.get(mode, 'Неизвестный')
        return await update.effective_message.reply_text(f"Я Альбедо, твой личный помощник. Сейчас я работаю в режиме '{mode_name}'.")

    # 3.7. Похвала
    if praise_pattern.search(text):
        return await update.effective_message.reply_text("Спасибо! Мне очень приятно это слышать!")

    # 3.8. Ругательства/мат
    if swear_pattern.search(text):
        return await update.effective_message.reply_text("Не ругайся! Я не люблю грубость.")

    # 3.9. Поиск в памяти
    for fact in context.user_data.get('memory', []):
        if fact.split()[0].lower() in text:
            return await update.effective_message.reply_text(f"Ах да, ты говорил(а): '{fact}'!")

    # 4. Ответ по умолчанию
    response = get_mode_response(context, 'default', user_name)
    await update.effective_message.reply_text(response)


# --- 10. ФУНКЦИЯ MAIN (ИЗМЕНЕНО ДЛЯ RENDER) ---

def main():
    """Запуск бота."""
    
    if BOT_TOKEN == "8271061413:AAGLXXQkpI1T8-QODF3dEOSNydObStR6Isg":
        logger.error("КРИТИЧЕСКАЯ ОШИБКА: Используется демонстрационный токен. Замените его на ваш токен BotFather!")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()
    
    # --- COMMAND HANDLERS ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("triggers", triggers_command))
    application.add_handler(CommandHandler("mode", mode_command))
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(CommandHandler("joke", joke_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("guess", start_guess_game))
    application.add_handler(CommandHandler("coin", coin_flip_command))
    application.add_handler(CommandHandler("ask", ask_8ball_command))
    application.add_handler(CommandHandler("remember", set_memory_command))
    application.add_handler(CommandHandler("set_birthday", set_birthday_command))
    application.add_handler(CommandHandler("acquaintance", acquaintance_command))
    application.add_handler(CommandHandler("stop_acquaintance", stop_acquaintance_command))

    # --- MESSAGE HANDLERS ---
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # --- ERROR HANDLER ---
    application.add_error_handler(error_handler)
    
    # --- ЗАПУСК БОТА ДЛЯ RENDER (WEBHOOKS) ---
    
    # Render сам выдает номер порта
    PORT = int(os.environ.get('PORT', '8443')) 
    # Render сам выдает этот адрес
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 
    
    if not RENDER_EXTERNAL_URL:
        # Запасной вариант для ЛОКАЛЬНОГО тестирования
        logger.info("Бот запускается в режиме polling (локально)...")
        application.run_polling(allowed_updates=Update.ALL_TYPES) 
    else:
        # РЕЖИМ WEBHOOKS для Render 24/7
        logger.info(f"Бот запускается в режиме webhook на порту {PORT}...")
        application.run_webhook(
            listen="0.0.0.0", # Слушаем все интерфейсы
            port=PORT,
            url_path=BOT_TOKEN, # Уникальный путь для безопасности
            webhook_url=RENDER_EXTERNAL_URL + 'webhook/' + BOT_TOKEN,
            allowed_updates=Update.ALL_TYPES
        )

if __name__ == "__main__":
    main()
