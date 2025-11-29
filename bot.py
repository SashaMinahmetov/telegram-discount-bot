import os
TOKEN = os.getenv("TOKEN")
import asyncio
import logging
import re
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Состояния диалога
(
    ВЫБОР_ЯЗЫКА,
    ВЫБОР_ТИПА_СКИДКИ,
    ОЖИДАНИЕ_СВОЕЙ_СКИДКИ,
    ОЖИДАНИЕ_ЦЕНЫ,
    ОЖИДАНИЕ_N,
    ОЖИДАНИЕ_X,
    ОЖИДАНИЕ_ЦЕНЫ_NX,
    ОЖИДАНИЕ_ЦЕНЫ_ВЕС,
    ОЖИДАНИЕ_ГРАММОВ,
    ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ,
    ОЖИДАНИЕ_ПРОЦЕНТА_СКИДКИ,
    НАСТРОЙКИ,
    PRO_MENU,
    PRO_AUTOMODE_INPUT,
    PRO_FIXED_PRICE,
    PRO_FIXED_DISCOUNT,
    PRO_LOYAL_ORIGINAL,
    PRO_LOYAL_CARD,
    PRO_DOUBLE_PRICE,
    PRO_DOUBLE_DISC1,
    PRO_DOUBLE_DISC2,
    PRO_COMPARE_FIRST_PRICE,
    PRO_COMPARE_FIRST_WEIGHT,
    PRO_COMPARE_SECOND_PRICE,
    PRO_COMPARE_SECOND_WEIGHT,
    PRO_PROMO_OLD,
    PRO_PROMO_NEW,
    PRO_MARGIN_COST,
    PRO_MARGIN_SHELF,
) = range(29)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Словари с локализацией
LOCALIZATION = {
    'ru': {
        'welcome': "👋 Добро пожаловать! Выберите язык:",
        'main_menu': "👋 Добро пожаловать! Выберите опцию для расчета:",
        'select_discount': "📦 Выберите процент скидки:",
        'enter_custom_discount': "🎯 Введите свой процент скидки (например, 14.44):",
        'enter_price': "🔢 Введите цену на полке (например, 545.44):",
        'price_result': "{title}\n\n💰 Цена на полке: {price:.2f} грн\n🎯 Скидка: {discount}%{extra}\n✅ Цена со скидкой: {discounted_price:.2f} грн",
        'invalid_discount': "❌ Ошибка. Скидка должна быть от 0% до 100%.",
        'invalid_price': "❌ Ошибка. Введите цену корректно, например: 545.44.",
        'enter_n': "🔢 Введите количество товаров, которые нужно купить (N):\n\nМожете выбрать цифру кнопками ниже.",
        'enter_x': "🎯 Введите количество бесплатных товаров (X):\n\nМожете выбрать цифру кнопками ниже.",
        'enter_nx_price': "💰 Введите цену одного товара (например, 99.99):",
        'nx_result': "{title}\n\n🛒 Акция: {n}+{x}\n💰 Цена одного товара: {price:.2f} грн\n💸 Общая сумма: {total:.2f} грн\n🎯 Фактичная скидка: {discount:.2f}%\n✅ Цена за единицу с учетом акции: {unit_price:.2f} грн",
        'enter_weight_price': "💰 Введите цену товара (например, 50.75):",
        'enter_weight': "⚖️ Введите количество грамм/мл в упаковке (например, 125):",
        'weight_result': '{title}\n\n💰 Цена: {price:.2f} грн\n⚖️ Вес: {weight:.2f} г/мл\n📊 Цена за 1 кг/л: {kg_price:.2f} грн\n📏 Цена за 100 г/мл: {price_100g:.2f} грн',
        'enter_price_short': 'Введите цену товара:',
        'enter_weight_short': 'Введите вес/объем (в граммах или мл):',
        'invalid_number': 'Пожалуйста, введите корректное число (больше 0).',
        'error': '❌ Произошла ошибка. Попробуйте снова или введите /start для перезапуска.',
        'cancel': "❌ Операция отменена. Введите /start для начала работы.",
        'restart': "🔄 Бот перезапущен!\n👋 Добро пожаловать! Выберите опцию для расчета:",
        'unexpected_text': "❌ Пожалуйста, используйте кнопки меню для выбора. Если вы хотите ввести свое значение, сначала выберите 'Другая %'.",
        'settings_menu': "⚙️ Настройки\nВыберите опцию:",
        'change_language': "🔄 Сменить язык",
        'back': "🔙 Назад",
        'next_action_prompt': "📊 Выберите следующее действие:",
        'restart_btn': "🔁 Перезапустить бот",
        # Сообщение при выборе раздела
        'mode_shelf': "📦 Вы выбрали: «Сколько стоит со скидкой»",
        'mode_nx': "🎯 Вы выбрали: «Скидка по акции N+X»",
        'mode_per_kg': "⚖️ Вы выбрали: «Сколько за кг/литр»",
        'mode_original_price': "💼 Вы выбрали: «Узнать регулярную цену без скидки»",
        # Заголовки расчётов
        'calc_title_shelf': "📦 Сколько стоит со скидкой",
        'calc_title_nx': "🎯 Скидка по акции N+X",
        'calc_title_per_kg': "⚖️ Сколько за кг/литр",
        'calc_title_original_price': "💼 Узнать регулярную цену без скидки",
        # Названия в главном меню
        'main_menu_btn': [
            ("📦 Сколько стоит со скидкой", "menu_shelf_discount"),
            ("🎯 Скидка по акции N+X", "menu_nx"),
            ("⚖️ Сколько за кг/литр", "menu_per_kg"),
            ("💼 Узнать регулярную цену без скидки", "menu_original_price"),
            ("🌟 PRO режим", "menu_pro"),
            ("⚙️ Настройки", "настройки"),
        ],
        'discount_buttons': [
            [("5%", "5"), ("10%", "10"), ("15%", "15"), ("20%", "20")],
            [("25%", "25"), ("30%", "30"), ("35%", "35"), ("40%", "40")],
            [("45%", "45"), ("50%", "50"), ("Другая %", "другая_скидка")]
        ],
        # PRO-режим — сообщения режима
        'mode_pro_auto': "🌟 PRO: Авто-режим",
        'mode_pro_fixed': "🌟 PRO: Фиксированная скидка (грн)",
        'mode_pro_loyal': "🌟 PRO: Цена по карте лояльности",
        'mode_pro_double': "🌟 PRO: Двойная скидка",
        'mode_pro_compare': "🌟 PRO: Сравнение 2 товаров",
        'mode_pro_promo': "🌟 PRO: Сравнение промо и обычной цены",
        'mode_pro_margin': "🌟 PRO: Маржа и наценка",
        'mode_pro_history': "🌟 PRO: История расчетов",
        'pro_menu_title': "🌟 PRO режим. Выберите функцию:",
        'pro_btn_auto': "🤖 Авто-режим",
        'pro_btn_fixed': "💸 Фиксированная скидка (грн)",
        'pro_btn_loyal': "💳 Цена по карте лояльности",
        'pro_btn_double': "🔁 Двойная скидка",
        'pro_btn_compare': "⚖️ Сравнить 2 товара",
        'pro_btn_promo': "📉 Сравнить промо и обычную цену",
        'pro_btn_margin': "📊 Маржа и наценка",
        'pro_btn_history': "📜 История расчётов",
        'pro_enter_expression': "✍️ Отправьте выражение одним сообщением.\nПримеры:\n• 299 - 40%\n• 2+1 цена 60\n• 350 г за 42",
        'pro_fixed_enter_price': "💰 Введите цену товара:",
        'pro_fixed_enter_discount_sum': "💸 Введите размер скидки в гривнах:",
        'pro_loyal_enter_regular': "💰 Введите обычную цену (без карты):",
        'pro_loyal_enter_card': "💳 Введите цену по карте лояльности:",
        'pro_double_enter_price': "💰 Введите цену товара:",
        'pro_double_enter_first': "🔁 Введите первую скидку в процентах:",
        'pro_double_enter_second': "🔁 Введите вторую скидку в процентах:",
        'pro_compare_first_price': "1️⃣ Введите цену первого товара:",
        'pro_compare_first_weight': "1️⃣ Введите вес/объем первого товара (в граммах или мл):",
        'pro_compare_second_price': "2️⃣ Введите цену второго товара:",
        'pro_compare_second_weight': "2️⃣ Введите вес/объем второго товара (в граммах или мл):",
        'pro_promo_old_price': "💵 Введите обычную цену (до скидки):",
        'pro_promo_new_price': "💸 Введите акционную цену (со скидкой):",
        'pro_margin_cost': "💼 Введите закупочную цену товара:",
        'pro_margin_shelf': "🏷️ Введите цену товара на полке:",
        'pro_history_empty': "Пока нет сохранённых расчётов.",
        'pro_history_title': "📜 История последних расчётов:",
        'pro_invalid_number': "❌ Некорректное значение. Введите число, например 123.45",
        'pro_auto_unknown': "⚠️ Не удалось распознать выражение.\nПопробуйте другой формат или используйте стандартные режимы.",
    },
    'uk': {
        'welcome': "👋 Ласкаво просимо! Оберіть мову:",
        'main_menu': "👋 Ласкаво просимо! Оберіть опцію для розрахунку:",
        'select_discount': "📦 Оберіть відсоток знижки:",
        'enter_custom_discount': "🎯 Введіть свій відсоток знижки (наприклад, 14.44):",
        'enter_price': "🔢 Введіть ціну на полиці (наприклад, 545.44):",
        'price_result': "{title}\n\n💰 Ціна на полиці: {price:.2f} грн\n🎯 Знижка: {discount}%{extra}\n✅ Ціна зі знижкою: {discounted_price:.2f} грн",
        'invalid_discount': "❌ Помилка. Знижка має бути від 0% до 100%.",
        'invalid_price': "❌ Помилка. Введіть ціну коректно, наприклад: 545.44.",
        'enter_n': "🔢 Введіть кількість товарів, які потрібно купити (N):\n\nМожете обрати цифру кнопками нижче.",
        'enter_x': "🎯 Введіть кількість безкоштовних товарів (X):\n\nМожете обрати цифру кнопками нижче.",
        'enter_nx_price': "💰 Введіть ціну одного товару (наприклад, 99.99):",
        'nx_result': "{title}\n\n🛒 Акція: {n}+{x}\n💰 Ціна одного товару: {price:.2f} грн\n💸 Загальна сума: {total:.2f} грн\n🎯 Фактична знижка: {discount:.2f}%\n✅ Ціна за одиницю з урахуванням акції: {unit_price:.2f} грн",
        'enter_weight_price': "💰 Введіть ціну товару (наприклад, 50.75):",
        'enter_weight': "⚖️ Введіть кількість грамів/мл в упаковці (наприклад, 125):",
        'weight_result': '{title}\n\n💰 Ціна: {price:.2f} грн\n⚖️ Вага: {weight:.2f} г/мл\n📊 Ціна за 1 кг/л: {kg_price:.2f} грн\n📏 Ціна за 100 г/мл: {price_100g:.2f} грн',
        'enter_price_short': 'Введіть ціну товару:',
        'enter_weight_short': 'Введіть вагу/об’єм (у грамах або мл):',
        'invalid_number': 'Будь ласка, введіть коректне число (більше 0).',
        'error': '❌ Сталася помилка. Спробуйте ще раз або введіть /start для перезапуску.',
        'cancel': "❌ Операцію скасовано. Введіть /start для початку роботи.",
        'restart': "🔄 Бот перезапущено!\n👋 Ласкаво просимо! Оберіть опцію для розрахунку:",
        'unexpected_text': "❌ Будь ласка, використовуйте кнопки меню для вибору. Якщо хочете ввести власне значення, спочатку оберіть 'Інший %'.",
        'settings_menu': "⚙️ Налаштування\nОберіть опцію:",
        'change_language': "🔄 Змінити мову",
        'back': "🔙 Назад",
        'next_action_prompt': "📊 Оберіть наступну дію:",
        'restart_btn': "🔁 Перезапустити бота",
        'mode_shelf': "📦 Ви обрали: «Скільки коштує зі знижкою»",
        'mode_nx': "🎯 Ви обрали: «Знижка по акції N+X»",
        'mode_per_kg': "⚖️ Ви обрали: «Скільки за кг/літр»",
        'mode_original_price': "💼 Ви обрали: «Дізнатись регулярну ціну без знижки»",
        'calc_title_shelf': "📦 Скільки коштує зі знижкою",
        'calc_title_nx': "🎯 Знижка по акції N+X",
        'calc_title_per_kg': "⚖️ Скільки за кг/літр",
        'calc_title_original_price': "💼 Дізнатись регулярну ціну без знижки",
        'main_menu_btn': [
            ("📦 Скільки коштує зі знижкою", "menu_shelf_discount"),
            ("🎯 Знижка по акції N+X", "menu_nx"),
            ("⚖️ Скільки за кг/літр", "menu_per_kg"),
            ("💼 Дізнатись регулярну ціну без знижки", "menu_original_price"),
            ("🌟 PRO режим", "menu_pro"),
            ("⚙️ Налаштування", "настройки"),
        ],
        'discount_buttons': [
            [("5%", "5"), ("10%", "10"), ("15%", "15"), ("20%", "20")],
            [("25%", "25"), ("30%", "30"), ("35%", "35"), ("40%", "40")],
            [("45%", "45"), ("50%", "50"), ("Інший %", "інша_знижка")]
        ],
        'mode_pro_auto': "🌟 PRO: Авто-режим",
        'mode_pro_fixed': "🌟 PRO: Фіксована знижка (грн)",
        'mode_pro_loyal': "🌟 PRO: Ціна за карткою лояльності",
        'mode_pro_double': "🌟 PRO: Подвійна знижка",
        'mode_pro_compare': "🌟 PRO: Порівняння 2 товарів",
        'mode_pro_promo': "🌟 PRO: Порівняння промо та звичайної ціни",
        'mode_pro_margin': "🌟 PRO: Маржа та націнка",
        'mode_pro_history': "🌟 PRO: Історія розрахунків",
        'pro_menu_title': "🌟 PRO режим. Оберіть функцію:",
        'pro_btn_auto': "🤖 Авто-режим",
        'pro_btn_fixed': "💸 Фіксована знижка (грн)",
        'pro_btn_loyal': "💳 Ціна за карткою лояльності",
        'pro_btn_double': "🔁 Подвійна знижка",
        'pro_btn_compare': "⚖️ Порівняти 2 товари",
        'pro_btn_promo': "📉 Порівняти промо та звичайну ціну",
        'pro_btn_margin': "📊 Маржа та націнка",
        'pro_btn_history': "📜 Історія розрахунків",
        'pro_enter_expression': "✍️ Надішліть вираз одним повідомленням.\nПриклади:\n• 299 - 40%\n• 2+1 ціна 60\n• 350 г за 42",
        'pro_fixed_enter_price': "💰 Введіть ціну товару:",
        'pro_fixed_enter_discount_sum': "💸 Введіть розмір знижки в гривнях:",
        'pro_loyal_enter_regular': "💰 Введіть звичайну ціну (без картки):",
        'pro_loyal_enter_card': "💳 Введіть ціну за карткою лояльності:",
        'pro_double_enter_price': "💰 Введіть ціну товару:",
        'pro_double_enter_first': "🔁 Введіть першу знижку у відсотках:",
        'pro_double_enter_second': "🔁 Введіть другу знижку у відсотках:",
        'pro_compare_first_price': "1️⃣ Введіть ціну першого товару:",
        'pro_compare_first_weight': "1️⃣ Введіть вагу/об’єм першого товару (у грамах або мл):",
        'pro_compare_second_price': "2️⃣ Введіть ціну другого товару:",
        'pro_compare_second_weight': "2️⃣ Введіть вагу/об’єм другого товару (у грамах або мл):",
        'pro_promo_old_price': "💵 Введіть звичайну ціну (до знижки):",
        'pro_promo_new_price': "💸 Введіть акційну ціну (зі знижкою):",
        'pro_margin_cost': "💼 Введіть закупівельну ціну товару:",
        'pro_margin_shelf': "🏷️ Введіть ціну товару на полиці:",
        'pro_history_empty': "Поки що немає збережених розрахунків.",
        'pro_history_title': "📜 Історія останніх розрахунків:",
        'pro_invalid_number': "❌ Некоректне значення. Введіть число, наприклад 123.45",
        'pro_auto_unknown': "⚠️ Не вдалося розпізнати вираз.\nСпробуйте інший формат або використайте стандартні режими.",
    }
}

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def get_language(context: ContextTypes.DEFAULT_TYPE | None) -> str:
    """Безопасно достаём язык. Если context/user_data нет — отдаём 'ru'."""
    try:
        if context is not None and getattr(context, "user_data", None) is not None:
            return context.user_data.get('language', 'ru')
    except Exception:
        pass
    return 'ru'


def add_to_history(context: ContextTypes.DEFAULT_TYPE, entry: str) -> None:
    """Добавляем запись в историю (максимум 10 последних)."""
    history = context.user_data.get("history", [])
    history.append(entry)
    if len(history) > 10:
        history = history[-10:]
    context.user_data["history"] = history


async def send_clean_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup=None,
    keep_result: bool = False,
):
    """
    Удаляет прошлые служебные сообщения бота и сообщение-триггер,
    отправляет новое и (опционально) помечает его на будущее удаление.
    """
    bot = context.bot

    if update.callback_query:
        chat = update.callback_query.message.chat
        trigger_message_id = update.callback_query.message.message_id
    else:
        chat = update.message.chat
        trigger_message_id = update.message.message_id

    # Удаляем предыдущие "служебные" сообщения бота
    old_ids = context.user_data.get("messages_to_delete", [])
    for mid in old_ids:
        try:
            await bot.delete_message(chat_id=chat.id, message_id=mid)
        except Exception:
            pass
    context.user_data["messages_to_delete"] = []

    # Удаляем сообщение-триггер
    try:
        await bot.delete_message(chat.id, trigger_message_id)
    except Exception:
        pass

    # Отправляем новое сообщение
    sent = await bot.send_message(chat_id=chat.id, text=text, reply_markup=reply_markup)

    # Запоминаем все сообщения бота — для полного очищения при "перезапустить бот"
    all_bot = context.user_data.get("all_bot_messages", [])
    all_bot.append(sent.message_id)
    context.user_data["all_bot_messages"] = all_bot

    # Если это не "результат" — помечаем для удаления на следующем шаге
    if not keep_result:
        context.user_data["messages_to_delete"].append(sent.message_id)

    return sent


async def delete_mode_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляем сообщение с текстом 'Вы выбрали ...', если оно есть."""
    mode_id = context.user_data.pop('mode_message_id', None)
    if not mode_id:
        return
    chat = update.effective_chat
    if not chat:
        return
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=mode_id)
    except Exception:
        pass


def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("Українська", callback_data="lang_uk")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard(context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(context)
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data)]
        for text, data in LOCALIZATION[lang]['main_menu_btn']
    ]
    return InlineKeyboardMarkup(keyboard)


def get_next_actions_keyboard(context: ContextTypes.DEFAULT_TYPE):
    """Клавиатура после результата: главное меню + перезапуск."""
    lang = get_language(context)
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data)]
        for text, data in LOCALIZATION[lang]['main_menu_btn']
    ]
    keyboard.append([
        InlineKeyboardButton(
            LOCALIZATION[lang]['restart_btn'],
            callback_data="перезапустить_бот"
        )
    ])
    return InlineKeyboardMarkup(keyboard)


def get_discount_keyboard(context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(context)
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data) for text, data in row]
        for row in LOCALIZATION[lang]['discount_buttons']
    ]
    keyboard.append([InlineKeyboardButton(LOCALIZATION[lang]['back'], callback_data="назад")])
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(context)
    keyboard = [
        [InlineKeyboardButton(LOCALIZATION[lang]['change_language'], callback_data="сменить_язык")],
        [InlineKeyboardButton(LOCALIZATION[lang]['back'], callback_data="назад")],
        [InlineKeyboardButton(LOCALIZATION[lang]['restart_btn'], callback_data="перезапустить_бот")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_numeric_reply_keyboard():
    keyboard = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["10"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_pro_menu_keyboard(context: ContextTypes.DEFAULT_TYPE):
    lang = get_language(context)
    L = LOCALIZATION[lang]
    keyboard = [
        [InlineKeyboardButton(L['pro_btn_auto'], callback_data="pro_auto")],
        [InlineKeyboardButton(L['pro_btn_fixed'], callback_data="pro_fixed")],
        [InlineKeyboardButton(L['pro_btn_loyal'], callback_data="pro_loyal")],
        [InlineKeyboardButton(L['pro_btn_double'], callback_data="pro_double")],
        [InlineKeyboardButton(L['pro_btn_compare'], callback_data="pro_compare")],
        [InlineKeyboardButton(L['pro_btn_promo'], callback_data="pro_promo")],
        [InlineKeyboardButton(L['pro_btn_margin'], callback_data="pro_margin")],
        [InlineKeyboardButton(L['pro_btn_history'], callback_data="pro_history")],
        [InlineKeyboardButton(L['back'], callback_data="назад")],
        [InlineKeyboardButton(LOCALIZATION[lang]['restart_btn'], callback_data="перезапустить_бот")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== ОБРАБОТЧИКИ КОМАНД И ОБЩИЕ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'language' not in context.user_data:
        context.user_data['попередній_стан'] = ВЫБОР_ЯЗЫКА
        await send_clean_message(
            update,
            context,
            "👋 Выберите язык / Оберіть мову:",
            reply_markup=get_language_keyboard()
        )
        return ВЫБОР_ЯЗЫКА

    lang = get_language(context)
    saved_lang = lang
    context.user_data.clear()
    context.user_data['language'] = saved_lang
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    keyboard = get_main_menu_keyboard(context)

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['main_menu'],
        reply_markup=keyboard
    )
    return ВЫБОР_ТИПА_СКИДКИ


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['language'] = lang
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    keyboard = get_main_menu_keyboard(context)

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['main_menu'],
        reply_markup=keyboard
    )
    return ВЫБОР_ТИПА_СКИДКИ


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    await update.callback_query.answer()

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['settings_menu'],
        reply_markup=get_settings_keyboard(context)
    )
    return НАСТРОЙКИ


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data['попередній_стан'] = НАСТРОЙКИ
    await send_clean_message(
        update,
        context,
        "👋 Выберите язык / Оберіть мову:",
        reply_markup=get_language_keyboard()
    )
    return ВЫБОР_ЯЗЫКА

# ===== БАЗОВЫЕ РЕЖИМЫ =====

async def calculate_shelf_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    context.user_data['текущее_действие'] = 'menu_shelf_discount'
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    if update.callback_query:
        await update.callback_query.answer()

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_shelf'],
        reply_markup=None,
        keep_result=True,
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['select_discount'],
        reply_markup=get_discount_keyboard(context)
    )
    return ВЫБОР_ТИПА_СКИДКИ


async def handle_fixed_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    await update.callback_query.answer()
    discount = float(update.callback_query.data)
    context.user_data['скидка'] = discount
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_price'],
        reply_markup=None
    )
    return ОЖИДАНИЕ_ЦЕНЫ


async def custom_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    await update.callback_query.answer()

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_custom_discount'],
        reply_markup=None
    )
    return ОЖИДАНИЕ_СВОЕЙ_СКИДКИ


async def handle_discount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    try:
        text = update.message.text.replace(',', '.')
        if not all(c.isdigit() or c == '.' for c in text):
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
            return ОЖИДАНИЕ_СВОЕЙ_СКИДКИ

        discount = float(text)
        if discount <= 0 or discount >= 100:
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
            return ОЖИДАНИЕ_СВОЕЙ_СКИДКИ

        context.user_data['скидка'] = discount
        context.user_data['попередній_стан'] = ОЖИДАНИЕ_СВОЕЙ_СКИДКИ

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['enter_price'],
            reply_markup=None
        )
        return ОЖИДАНИЕ_ЦЕНЫ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
        return ОЖИДАНИЕ_СВОЕЙ_СКИДКИ
    except Exception as e:
        logger.error(f"Unexpected error in handle_discount_input: {e}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ОЖИДАНИЕ_СВОЕЙ_СКИДКИ


async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    try:
        text = update.message.text.replace(',', '.')
        if not all(c.isdigit() or c == '.' for c in text):
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
            return ОЖИДАНИЕ_ЦЕНЫ

        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
            return ОЖИДАНИЕ_ЦЕНЫ

        discount = context.user_data.get('скидка', 0)
        discounted_price = price * (1 - discount / 100)
        extra = f" ({context.user_data.get('extra_discount_info', '')})" if context.user_data.get('extra_discount_info') else ""

        await delete_mode_message(update, context)
        title = LOCALIZATION[lang]['calc_title_shelf']

        result_text = LOCALIZATION[lang]['price_result'].format(
            title=title,
            price=price,
            discount=discount,
            extra=extra,
            discounted_price=discounted_price
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True,
        )
        add_to_history(context, result_text)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
        return ОЖИДАНИЕ_ЦЕНЫ
    except Exception as e:
        logger.error(f"Unexpected error in handle_price_input: {e}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ОЖИДАНИЕ_ЦЕНЫ

# ===== АКЦИЯ N+X =====

async def calculate_n_plus_x(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    context.user_data['текущее_действие'] = 'menu_nx'
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    context.user_data.pop('n', None)
    context.user_data.pop('x', None)

    if update.callback_query:
        await update.callback_query.answer()

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_nx'],
        reply_markup=None,
        keep_result=True,
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_n'],
        reply_markup=get_numeric_reply_keyboard()
    )
    return ОЖИДАНИЕ_N


async def handle_n_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.strip()

    if not text.isdigit():
        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['invalid_number'],
            reply_markup=get_numeric_reply_keyboard()
        )
        return ОЖИДАНИЕ_N

    n = int(text)
    if n <= 0:
        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['invalid_number'],
            reply_markup=get_numeric_reply_keyboard()
        )
        return ОЖИДАНИЕ_N

    context.user_data['n'] = n
    context.user_data['попередній_стан'] = ОЖИДАНИЕ_N

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_x'],
        reply_markup=get_numeric_reply_keyboard()
    )
    return ОЖИДАНИЕ_X


async def handle_x_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.strip()

    if not text.isdigit():
        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['invalid_number'],
            reply_markup=get_numeric_reply_keyboard()
        )
        return ОЖИДАНИЕ_X

    x = int(text)
    if x <= 0:
        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['invalid_number'],
            reply_markup=get_numeric_reply_keyboard()
        )
        return ОЖИДАНИЕ_X

    context.user_data['x'] = x
    context.user_data['попередній_стан'] = ОЖИДАНИЕ_X

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_nx_price'],
        reply_markup=ReplyKeyboardRemove()
    )
    return ОЖИДАНИЕ_ЦЕНЫ_NX


async def handle_nx_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
            return ОЖИДАНИЕ_ЦЕНЫ_NX

        n = context.user_data.get('n')
        x = context.user_data.get('x')
        if n is None or x is None:
            logger.error(f"Missing n or x: n={n}, x={x}")
            await send_clean_message(update, context, LOCALIZATION[lang]['error'])
            return ВЫБОР_ТИПА_СКИДКИ

        total_quantity = n + x
        discount_percent = (x / total_quantity) * 100
        unit_price = price * n / total_quantity
        total_price = price * n

        await delete_mode_message(update, context)
        title = LOCALIZATION[lang]['calc_title_nx']

        result_text = LOCALIZATION[lang]['nx_result'].format(
            title=title,
            n=n,
            x=x,
            price=price,
            total=total_price,
            discount=discount_percent,
            unit_price=unit_price
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True,
        )
        add_to_history(context, result_text)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
        return ОЖИДАНИЕ_ЦЕНЫ_NX
    except Exception as e:
        logger.error(f"Error in handle_nx_price_input: {e}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ВЫБОР_ТИПА_СКИДКИ

# ===== ЦЕНА ЗА КГ / ЛИТР =====

async def calculate_price_per_kg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    context.user_data['текущее_действие'] = 'menu_per_kg'
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ
    context.user_data.pop('цена_веса', None)

    if update.callback_query:
        await update.callback_query.answer()

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_per_kg'],
        reply_markup=None,
        keep_result=True,
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_weight_price'],
        reply_markup=None
    )
    return ОЖИДАНИЕ_ЦЕНЫ_ВЕС


async def handle_weight_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    logger.info(f"handle_weight_price_input: input={text}, user_data={context.user_data}")
    try:
        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
            return ОЖИДАНИЕ_ЦЕНЫ_ВЕС

        context.user_data['цена_веса'] = price
        context.user_data['попередній_стан'] = ОЖИДАНИЕ_ЦЕНЫ_ВЕС

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['enter_weight'],
            reply_markup=None
        )
        return ОЖИДАНИЕ_ГРАММОВ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
        return ОЖИДАНИЕ_ЦЕНЫ_ВЕС
    except Exception as e:
        logger.error(f"Error in handle_weight_price_input: {e}, input={text}, user_data={context.user_data}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ОЖИДАНИЕ_ЦЕНЫ_ВЕС


async def handle_weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    logger.info(f"handle_weight_input: input={text}, user_data={context.user_data}")
    try:
        weight = float(text)
        if weight <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_number'])
            return ОЖИДАНИЕ_ГРАММОВ

        price = context.user_data.get('цена_веса')
        if not isinstance(price, (int, float)) or price <= 0:
            logger.error(f"Invalid or missing price: price={price}, user_data={context.user_data}")
            await send_clean_message(update, context, LOCALIZATION[lang]['error'])
            return ОЖИДАНИЕ_ЦЕНЫ_ВЕС

        kg_price = (price / weight) * 1000
        price_100g = (price / weight) * 100

        await delete_mode_message(update, context)
        title = LOCALIZATION[lang]['calc_title_per_kg']

        result_text = LOCALIZATION[lang]['weight_result'].format(
            title=title,
            price=price,
            weight=weight,
            kg_price=kg_price,
            price_100g=price_100g
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True,
        )
        add_to_history(context, result_text)

        context.user_data.pop('цена_веса', None)
        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_number'])
        return ОЖИДАНИЕ_ГРАММОВ
    except Exception as e:
        logger.error(f"Error in handle_weight_input: {e}, input={text}, user_data={context.user_data}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ОЖИДАНИЕ_ЦЕНЫ_ВЕС

# ===== ОБРАТНЫЙ РАСЧЁТ РЕГУЛЯРНОЙ ЦЕНЫ =====

async def calculate_original_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    context.user_data['текущее_действие'] = 'menu_original_price'
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ

    if update.callback_query:
        await update.callback_query.answer()

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_original_price'],
        reply_markup=None,
        keep_result=True,
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['enter_price'],
        reply_markup=None
    )
    return ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ


async def handle_discounted_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
            return ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ

        context.user_data['цена_со_скидкой'] = price
        context.user_data['попередній_стан'] = ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['enter_custom_discount'],
            reply_markup=None
        )
        return ОЖИДАНИЕ_ПРОЦЕНТА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_price'])
        return ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ
    except Exception as e:
        logger.error(f"Error in handle_discounted_price: {e}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ВЫБОР_ТИПА_СКИДКИ


async def calculate_original_price_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        discount_percent = float(text)
        if not (0 < discount_percent < 100):
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
            return ОЖИДАНИЕ_ПРОЦЕНТА_СКИДКИ

        discounted_price = context.user_data.get('цена_со_скидкой', 0)
        if discounted_price <= 0:
            logger.error(f"Invalid discounted_price: {discounted_price}")
            await send_clean_message(update, context, LOCALIZATION[lang]['error'])
            return ВЫБОР_ТИПА_СКИДКИ

        original_price = discounted_price / (1 - discount_percent / 100)

        await delete_mode_message(update, context)
        title = LOCALIZATION[lang]['calc_title_original_price']

        result_text = LOCALIZATION[lang]['price_result'].format(
            title=title,
            price=original_price,
            discount=discount_percent,
            extra="",
            discounted_price=discounted_price
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True,
        )
        add_to_history(context, result_text)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
        return ОЖИДАНИЕ_ПРОЦЕНТА_СКИДКИ
    except Exception as e:
        logger.error(f"Error in calculate_original_price_result: {e}")
        await send_clean_message(update, context, LOCALIZATION[lang]['error'])
        return ВЫБОР_ТИПА_СКИДКИ

# ===== PRO МЕНЮ И ФУНКЦИИ =====

async def open_pro_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_menu_title'],
        reply_markup=get_pro_menu_keyboard(context)
    )
    return PRO_MENU

# --- PRO: Авто-режим ---

def parse_automode_expression(text: str):
    """
    Простейший парсер авто-режима.
    Возвращает dict с полями:
    {'type': 'percent', 'price': ..., 'discount': ...}
    и т.п. либо None, если не распознано.
    """

    t = text.lower().replace(',', '.').strip()

    # 1) "299 - 40%" или "299-40%"
    m = re.search(r'(\d+(?:\.\d+)?)\s*[-−]\s*(\d+(?:\.\d+)?)\s*%', t)
    if m:
        price = float(m.group(1))
        disc = float(m.group(2))
        if price > 0 and 0 < disc < 100:
            return {'type': 'percent', 'price': price, 'discount': disc}

    # 2) "2+1 цена 60" или "2+1 60"
    m = re.search(r'(\d+)\s*\+\s*(\d+)', t)
    if m:
        n = int(m.group(1))
        x = int(m.group(2))
        m_price = re.search(r'(\d+(?:\.\d+)?)', t[m.end():])
        if m_price:
            price = float(m_price.group(1))
            if n > 0 and x > 0 and price > 0:
                return {'type': 'nx', 'n': n, 'x': x, 'price': price}

    # 3) "350 г за 42" / "350гр за 42" / "350 ml за 42"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(г|гр|грамм|грамів|мл|ml)\s*(за|x|×)\s*(\d+(?:\.\d+)?)', t)
    if m:
        weight = float(m.group(1))
        price = float(m.group(4))
        if weight > 0 and price > 0:
            return {'type': 'per_kg', 'weight': weight, 'price': price}

    # 4) "42 за 350 г"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(за)\s*(\d+(?:\.\d+)?)\s*(г|гр|грамм|грамів|мл|ml)', t)
    if m:
        price = float(m.group(1))
        weight = float(m.group(3))
        if weight > 0 and price > 0:
            return {'type': 'per_kg', 'weight': weight, 'price': price}

    return None


async def pro_auto_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    # Сообщение с названием режима
    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_auto'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_enter_expression'],
        reply_markup=None
    )
    return PRO_AUTOMODE_INPUT


async def pro_handle_automode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    parsed = parse_automode_expression(update.message.text)
    if not parsed:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_auto_unknown'])
        return PRO_AUTOMODE_INPUT

    await delete_mode_message(update, context)

    result_text = ""
    if parsed['type'] == 'percent':
        price = parsed['price']
        disc = parsed['discount']
        new_price = price * (1 - disc / 100)
        result_text = (
            f"🤖 Авто-режим: скидка в процентах\n\n"
            f"💰 Цена: {price:.2f} грн\n"
            f"🎯 Скидка: {disc:.2f}%\n"
            f"✅ Итоговая цена: {new_price:.2f} грн"
        )
    elif parsed['type'] == 'nx':
        n = parsed['n']
        x = parsed['x']
        price = parsed['price']
        total_quantity = n + x
        discount_percent = (x / total_quantity) * 100
        unit_price = price * n / total_quantity
        total_price = price * n
        result_text = (
            f"🤖 Авто-режим: акция {n}+{x}\n\n"
            f"💰 Цена одного товара: {price:.2f} грн\n"
            f"🛒 Всего товаров (с бесплатными): {total_quantity}\n"
            f"💸 Общая сумма: {total_price:.2f} грн\n"
            f"🎯 Фактичная скидка: {discount_percent:.2f}%\n"
            f"✅ Цена за единицу: {unit_price:.2f} грн"
        )
    elif parsed['type'] == 'per_kg':
        price = parsed['price']
        weight = parsed['weight']
        kg_price = (price / weight) * 1000
        price_100g = (price / weight) * 100
        result_text = (
            f"🤖 Авто-режим: цена за кг/л\n\n"
            f"💰 Цена: {price:.2f} грн\n"
            f"⚖️ Вес: {weight:.2f} г/мл\n"
            f"📊 Цена за 1 кг/л: {kg_price:.2f} грн\n"
            f"📏 Цена за 100 г/мл: {price_100g:.2f} грн"
        )

    await send_clean_message(
        update,
        context,
        result_text,
        reply_markup=None,
        keep_result=True
    )
    add_to_history(context, result_text)

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['next_action_prompt'],
        reply_markup=get_next_actions_keyboard(context),
    )
    return ВЫБОР_ТИПА_СКИДКИ

# --- PRO: фиксированная скидка в грн ---

async def pro_fixed_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_fixed'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_fixed_enter_price'],
        reply_markup=None
    )
    return PRO_FIXED_PRICE


async def pro_fixed_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_FIXED_PRICE
        context.user_data['pro_fixed_price'] = price
        context.user_data['попередній_стан'] = PRO_FIXED_PRICE

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_fixed_enter_discount_sum'],
            reply_markup=None
        )
        return PRO_FIXED_DISCOUNT
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_FIXED_PRICE


async def pro_fixed_discount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        discount_sum = float(text)
        price = context.user_data.get('pro_fixed_price', 0)
        if discount_sum <= 0 or discount_sum >= price:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_FIXED_DISCOUNT

        await delete_mode_message(update, context)

        final_price = price - discount_sum
        result_text = (
            f"💸 Фиксированная скидка в гривнах\n\n"
            f"💰 Цена товара: {price:.2f} грн\n"
            f"⬇️ Скидка: {discount_sum:.2f} грн\n"
            f"✅ Итоговая цена: {final_price:.2f} грн"
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True
        )
        add_to_history(context, result_text)
        context.user_data.pop('pro_fixed_price', None)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_FIXED_DISCOUNT

# --- PRO: карта лояльности ---

async def pro_loyal_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_loyal'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_loyal_enter_regular'],
        reply_markup=None
    )
    return PRO_LOYAL_ORIGINAL


async def pro_loyal_original_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_LOYAL_ORIGINAL

        context.user_data['pro_loyal_original'] = price
        context.user_data['попередній_стан'] = PRO_LOYAL_ORIGINAL

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_loyal_enter_card'],
            reply_markup=None
        )
        return PRO_LOYAL_CARD
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_LOYAL_ORIGINAL


async def pro_loyal_card_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        card_price = float(text)
        original = context.user_data.get('pro_loyal_original', 0)
        if card_price <= 0 or card_price >= original:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_LOYAL_CARD

        await delete_mode_message(update, context)

        diff = original - card_price
        disc_percent = diff / original * 100

        result_text = (
            f"💳 Цена по карте лояльности\n\n"
            f"💰 Обычная цена: {original:.2f} грн\n"
            f"💳 Цена по карте: {card_price:.2f} грн\n"
            f"⬇️ Экономия: {diff:.2f} грн ({disc_percent:.2f}%)"
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True
        )
        add_to_history(context, result_text)
        context.user_data.pop('pro_loyal_original', None)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_LOYAL_CARD

# --- PRO: двойная скидка ---

async def pro_double_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_double'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_double_enter_price'],
        reply_markup=None
    )
    return PRO_DOUBLE_PRICE


async def pro_double_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price = float(text)
        if price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_DOUBLE_PRICE

        context.user_data['pro_double_price'] = price
        context.user_data['попередній_стан'] = PRO_DOUBLE_PRICE

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_double_enter_first'],
            reply_markup=None
        )
        return PRO_DOUBLE_DISC1
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_DOUBLE_PRICE


async def pro_double_disc1_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        disc1 = float(text)
        if not (0 < disc1 < 100):
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
            return PRO_DOUBLE_DISC1

        context.user_data['pro_double_disc1'] = disc1
        context.user_data['попередній_стан'] = PRO_DOUBLE_DISC1

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_double_enter_second'],
            reply_markup=None
        )
        return PRO_DOUBLE_DISC2
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
        return PRO_DOUBLE_DISC1


async def pro_double_disc2_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        disc2 = float(text)
        if not (0 < disc2 < 100):
            await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
            return PRO_DOUBLE_DISC2

        price = context.user_data.get('pro_double_price', 0)
        disc1 = context.user_data.get('pro_double_disc1', 0)
        if price <= 0 or not (0 < disc1 < 100):
            await send_clean_message(update, context, LOCALIZATION[lang]['error'])
            return ВЫБОР_ТИПА_СКИДКИ

        await delete_mode_message(update, context)

        price_after_first = price * (1 - disc1 / 100)
        price_after_second = price_after_first * (1 - disc2 / 100)
        effective_disc = (1 - price_after_second / price) * 100

        result_text = (
            f"🔁 Двойная скидка\n\n"
            f"💰 Начальная цена: {price:.2f} грн\n"
            f"1️⃣ Первая скидка: {disc1:.2f}% → {price_after_first:.2f} грн\n"
            f"2️⃣ Вторая скидка: {disc2:.2f}% → {price_after_second:.2f} грн\n"
            f"🎯 Итоговая эффективная скидка: {effective_disc:.2f}%"
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True
        )
        add_to_history(context, result_text)
        context.user_data.pop('pro_double_price', None)
        context.user_data.pop('pro_double_disc1', None)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['invalid_discount'])
        return PRO_DOUBLE_DISC2

# --- PRO: сравнение 2 товаров ---

async def pro_compare_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_compare'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_compare_first_price'],
        reply_markup=None
    )
    return PRO_COMPARE_FIRST_PRICE


async def pro_compare_first_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price1 = float(text)
        if price1 <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_COMPARE_FIRST_PRICE

        context.user_data['pro_cmp_price1'] = price1
        context.user_data['попередній_стан'] = PRO_COMPARE_FIRST_PRICE

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_compare_first_weight'],
            reply_markup=None
        )
        return PRO_COMPARE_FIRST_WEIGHT
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_COMPARE_FIRST_PRICE


async def pro_compare_first_weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        w1 = float(text)
        if w1 <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_COMPARE_FIRST_WEIGHT

        context.user_data['pro_cmp_weight1'] = w1
        context.user_data['попередній_стан'] = PRO_COMPARE_FIRST_WEIGHT

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_compare_second_price'],
            reply_markup=None
        )
        return PRO_COMPARE_SECOND_PRICE
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_COMPARE_FIRST_WEIGHT


async def pro_compare_second_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        price2 = float(text)
        if price2 <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_COMPARE_SECOND_PRICE

        context.user_data['pro_cmp_price2'] = price2
        context.user_data['попередній_стан'] = PRO_COMPARE_SECOND_PRICE

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_compare_second_weight'],
            reply_markup=None
        )
        return PRO_COMPARE_SECOND_WEIGHT
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_COMPARE_SECOND_PRICE


async def pro_compare_second_weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        w2 = float(text)
        if w2 <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_COMPARE_SECOND_WEIGHT

        price1 = context.user_data.get('pro_cmp_price1', 0)
        w1 = context.user_data.get('pro_cmp_weight1', 0)
        price2 = context.user_data.get('pro_cmp_price2', 0)
        if price1 <= 0 or w1 <= 0 or price2 <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['error'])
            return ВЫБОР_ТИПА_СКИДКИ

        await delete_mode_message(update, context)

        kg1 = (price1 / w1) * 1000
        kg2 = (price2 / w2) * 1000
        if kg1 < kg2:
            better = "1️⃣ первый товар"
        elif kg2 < kg1:
            better = "2️⃣ второй товар"
        else:
            better = "оба товара одинаковы по цене за кг"

        result_text = (
            f"⚖️ Сравнение двух товаров\n\n"
            f"1️⃣ Цена: {price1:.2f} грн, вес: {w1:.2f} г → {kg1:.2f} грн/кг\n"
            f"2️⃣ Цена: {price2:.2f} грн, вес: {w2:.2f} г → {kg2:.2f} грн/кг\n\n"
            f"✅ Выгоднее: {better}"
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True
        )
        add_to_history(context, result_text)

        context.user_data.pop('pro_cmp_price1', None)
        context.user_data.pop('pro_cmp_weight1', None)
        context.user_data.pop('pro_cmp_price2', None)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_COMPARE_SECOND_WEIGHT

# --- PRO: сравнение промо vs обычной цены ---

async def pro_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_promo'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_promo_old_price'],
        reply_markup=None
    )
    return PRO_PROMO_OLD


async def pro_promo_old_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        old_price = float(text)
        if old_price <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_PROMO_OLD

        context.user_data['pro_promo_old'] = old_price
        context.user_data['попередній_стан'] = PRO_PROMO_OLD

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_promo_new_price'],
            reply_markup=None
        )
        return PRO_PROMO_NEW
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_PROMO_OLD


async def pro_promo_new_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        new_price = float(text)
        old_price = context.user_data.get('pro_promo_old', 0)
        if new_price <= 0 or new_price >= old_price:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_PROMO_NEW

        await delete_mode_message(update, context)

        diff = old_price - new_price
        disc_percent = diff / old_price * 100

        result_text = (
            f"📉 Сравнение промо и обычной цены\n\n"
            f"💵 Обычная цена: {old_price:.2f} грн\n"
            f"💸 Промо цена: {new_price:.2f} грн\n"
            f"⬇️ Скидка: {diff:.2f} грн ({disc_percent:.2f}%)"
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True
        )
        add_to_history(context, result_text)
        context.user_data.pop('pro_promo_old', None)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_PROMO_NEW

# --- PRO: маржа и наценка ---

async def pro_margin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data['попередній_стан'] = PRO_MENU

    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_margin'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['pro_margin_cost'],
        reply_markup=None
    )
    return PRO_MARGIN_COST


async def pro_margin_cost_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        cost = float(text)
        if cost <= 0:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_MARGIN_COST

        context.user_data['pro_margin_cost'] = cost
        context.user_data['попередній_стан'] = PRO_MARGIN_COST

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['pro_margin_shelf'],
            reply_markup=None
        )
        return PRO_MARGIN_SHELF
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_MARGIN_COST


async def pro_margin_shelf_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    text = update.message.text.replace(',', '.')
    try:
        shelf = float(text)
        cost = context.user_data.get('pro_margin_cost', 0)
        if shelf <= 0 or shelf <= cost:
            await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
            return PRO_MARGIN_SHELF

        await delete_mode_message(update, context)

        profit = shelf - cost
        markup_percent = (shelf / cost - 1) * 100
        margin_percent = profit / shelf * 100

        result_text = (
            f"📊 Маржа и наценка\n\n"
            f"💼 Закупочная цена: {cost:.2f} грн\n"
            f"🏷️ Цена на полке: {shelf:.2f} грн\n"
            f"💰 Прибыль с единицы: {profit:.2f} грн\n"
            f"📈 Наценка: {markup_percent:.2f}%\n"
            f"📉 Маржа: {margin_percent:.2f}%"
        )
        await send_clean_message(
            update,
            context,
            result_text,
            reply_markup=None,
            keep_result=True
        )
        add_to_history(context, result_text)
        context.user_data.pop('pro_margin_cost', None)

        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['next_action_prompt'],
            reply_markup=get_next_actions_keyboard(context),
        )
        return ВЫБОР_ТИПА_СКИДКИ
    except ValueError:
        await send_clean_message(update, context, LOCALIZATION[lang]['pro_invalid_number'])
        return PRO_MARGIN_SHELF

# --- PRO: история ---

async def pro_show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    if update.callback_query:
        await update.callback_query.answer()

    # Покажем, что сейчас режим "история"
    mode_msg = await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['mode_pro_history'],
        reply_markup=None,
        keep_result=True
    )
    context.user_data['mode_message_id'] = mode_msg.message_id

    history = context.user_data.get("history", [])
    if not history:
        text = LOCALIZATION[lang]['pro_history_empty']
    else:
        text = LOCALIZATION[lang]['pro_history_title'] + "\n\n" + "\n\n".join(history)

    await delete_mode_message(update, context)

    await send_clean_message(
        update,
        context,
        text,
        reply_markup=None,
        keep_result=True
    )

    await send_clean_message(
        update,
        context,
        LOCALIZATION[lang]['next_action_prompt'],
        reply_markup=get_next_actions_keyboard(context),
    )
    return ВЫБОР_ТИПА_СКИДКИ

# ===== НАЗАД =====

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    previous_state = context.user_data.get('попередній_стан', ВЫБОР_ТИПА_СКИДКИ)
    logger.info(f"Back pressed: previous_state={previous_state}, user_data={context.user_data}")

    state_map = {
        ВЫБОР_ТИПА_СКИДКИ: start,
        ОЖИДАНИЕ_СВОЕЙ_СКИДКИ: calculate_shelf_discount,
        ОЖИДАНИЕ_ЦЕНЫ: calculate_shelf_discount,
        ОЖИДАНИЕ_N: start,
        ОЖИДАНИЕ_X: calculate_n_plus_x,
        ОЖИДАНИЕ_ЦЕНЫ_NX: handle_x_input,
        ОЖИДАНИЕ_ЦЕНЫ_ВЕС: start,
        ОЖИДАНИЕ_ГРАММОВ: calculate_price_per_kg,
        ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ: calculate_original_price,
        ОЖИДАНИЕ_ПРОЦЕНТА_СКИДКИ: handle_discounted_price,
        НАСТРОЙКИ: start,
        ВЫБОР_ЯЗЫКА: start,
        PRO_MENU: start,
        PRO_AUTOMODE_INPUT: open_pro_menu,
        PRO_FIXED_PRICE: open_pro_menu,
        PRO_FIXED_DISCOUNT: open_pro_menu,
        PRO_LOYAL_ORIGINAL: open_pro_menu,
        PRO_LOYAL_CARD: open_pro_menu,
        PRO_DOUBLE_PRICE: open_pro_menu,
        PRO_DOUBLE_DISC1: open_pro_menu,
        PRO_DOUBLE_DISC2: open_pro_menu,
        PRO_COMPARE_FIRST_PRICE: open_pro_menu,
        PRO_COMPARE_FIRST_WEIGHT: open_pro_menu,
        PRO_COMPARE_SECOND_PRICE: open_pro_menu,
        PRO_COMPARE_SECOND_WEIGHT: open_pro_menu,
        PRO_PROMO_OLD: open_pro_menu,
        PRO_PROMO_NEW: open_pro_menu,
        PRO_MARGIN_COST: open_pro_menu,
        PRO_MARGIN_SHELF: open_pro_menu,
    }

    try:
        handler = state_map.get(previous_state, start)
        return await handler(update, context)
    except Exception as e:
        logger.error(f"Error in back handler: {e}, previous_state={previous_state}")
        await send_clean_message(
            update,
            context,
            LOCALIZATION[lang]['error'],
            reply_markup=get_main_menu_keyboard(context)
        )
        return ВЫБОР_ТИПА_СКИДКИ

# ===== ОБЩИЕ ОБРАБОТЧИКИ =====

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE | None) -> None:
    """Глобальный обработчик ошибок."""
    lang = get_language(context)
    logger.error(f"Error occurred: {getattr(context, 'error', None)}, update={update}")

    try:
        if update and hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text(LOCALIZATION[lang]['error'])
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    await send_clean_message(update, context, LOCALIZATION[lang]['cancel'], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Перезапуск: удаляем все сообщения бота в этом чате и показываем меню заново."""
    if update.callback_query:
        await update.callback_query.answer()

    lang = get_language(context)

    # Удаляем все сообщения бота, которые мы когда-либо отправляли
    chat = update.effective_chat
    if chat:
        all_ids = context.user_data.get("all_bot_messages", [])
        for mid in all_ids:
            try:
                await context.bot.delete_message(chat_id=chat.id, message_id=mid)
            except Exception:
                pass

    # Полная очистка user_data, кроме языка
    context.user_data.clear()
    context.user_data['language'] = lang
    context.user_data['попередній_стан'] = ВЫБОР_ТИПА_СКИДКИ

    keyboard = get_main_menu_keyboard(context)

    msg = await update.effective_chat.send_message(
        text=LOCALIZATION[lang]['restart'],
        reply_markup=keyboard
    )
    context.user_data["all_bot_messages"] = [msg.message_id]
    context.user_data["messages_to_delete"] = [msg.message_id]

    return ВЫБОР_ТИПА_СКИДКИ


async def handle_unexpected_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_language(context)
    await send_clean_message(update, context, LOCALIZATION[lang]['unexpected_text'])
    return ВЫБОР_ТИПА_СКИДКИ

# ===== MAIN =====

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ВЫБОР_ЯЗЫКА: [
                CallbackQueryHandler(choose_language, pattern="^lang_(ru|uk)$"),
                CommandHandler("start", start),
                CallbackQueryHandler(back, pattern="^назад$"),
            ],
            ВЫБОР_ТИПА_СКИДКИ: [
                CallbackQueryHandler(calculate_shelf_discount, pattern="^menu_shelf_discount$"),
                CallbackQueryHandler(calculate_n_plus_x, pattern="^menu_nx$"),
                CallbackQueryHandler(calculate_price_per_kg, pattern="^menu_per_kg$"),
                CallbackQueryHandler(calculate_original_price, pattern="^menu_original_price$"),
                CallbackQueryHandler(open_pro_menu, pattern="^menu_pro$"),
                CallbackQueryHandler(handle_fixed_discount, pattern="^(5|10|15|20|25|30|35|40|45|50)$"),
                CallbackQueryHandler(custom_discount, pattern="^(другая_скидка|інша_знижка)$"),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(settings_menu, pattern="^настройки$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unexpected_text),
            ],
            ОЖИДАНИЕ_СВОЕЙ_СКИДКИ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_discount_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_ЦЕНЫ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_N: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_n_input),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_X: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_x_input),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_ЦЕНЫ_NX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nx_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_ЦЕНЫ_ВЕС: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weight_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_ГРАММОВ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weight_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_ЦЕНЫ_СО_СКИДКОЙ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_discounted_price),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            ОЖИДАНИЕ_ПРОЦЕНТА_СКИДКИ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_original_price_result),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            НАСТРОЙКИ: [
                CallbackQueryHandler(change_language, pattern="^сменить_язык$"),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_MENU: [
                CallbackQueryHandler(pro_auto_start, pattern="^pro_auto$"),
                CallbackQueryHandler(pro_fixed_start, pattern="^pro_fixed$"),
                CallbackQueryHandler(pro_loyal_start, pattern="^pro_loyal$"),
                CallbackQueryHandler(pro_double_start, pattern="^pro_double$"),
                CallbackQueryHandler(pro_compare_start, pattern="^pro_compare$"),
                CallbackQueryHandler(pro_promo_start, pattern="^pro_promo$"),
                CallbackQueryHandler(pro_margin_start, pattern="^pro_margin$"),
                CallbackQueryHandler(pro_show_history, pattern="^pro_history$"),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_AUTOMODE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_handle_automode),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_FIXED_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_fixed_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_FIXED_DISCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_fixed_discount_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_LOYAL_ORIGINAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_loyal_original_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_LOYAL_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_loyal_card_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_DOUBLE_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_double_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_DOUBLE_DISC1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_double_disc1_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_DOUBLE_DISC2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_double_disc2_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_COMPARE_FIRST_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_compare_first_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_COMPARE_FIRST_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_compare_first_weight_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_COMPARE_SECOND_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_compare_second_price_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_COMPARE_SECOND_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_compare_second_weight_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_PROMO_OLD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_promo_old_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_PROMO_NEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_promo_new_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_MARGIN_COST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_margin_cost_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
            PRO_MARGIN_SHELF: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_margin_shelf_input),
                CallbackQueryHandler(back, pattern="^назад$"),
                CallbackQueryHandler(restart, pattern="^перезапустить_бот$"),
                CommandHandler("start", restart),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", restart),
        ],
        per_chat=True
    )

    app.add_handler(conv_handler)
    logger.info("🚀 Бот запущен через Polling")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    try:
        import os, sys, psutil
        current_pid = os.getpid()
        current_process = psutil.Process(current_pid)
        process_name = current_process.name()

        count = 0
        for process in psutil.process_iter(['pid', 'name']):
            try:
                if process.info['name'] == process_name and process.info['pid'] != current_pid:
                    count += 1
            except psutil.NoSuchProcess:
                pass

        if count > 0:
            print(f"⚠️ Уже запущено {count} экземпляров бота. Текущий PID: {current_pid}")
            sys.exit(0)

        try:
            import nest_asyncio
            nest_asyncio.apply()
            print("🔄 nest_asyncio применен")
        except ImportError:
            print("⚠️ nest_asyncio не установлен")

        print(f"🚀 Запуск бота, PID: {current_pid}")
        asyncio.run(main())

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
