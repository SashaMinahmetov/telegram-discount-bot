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

# Константы для состояний диалога
(
    LANGUAGE_SELECTION,
    MAIN_MENU,
    DISCOUNT_PRICE,
    DISCOUNT_PERCENT,
    N_PLUS_X_N,
    N_PLUS_X_X,
    N_PLUS_X_PRICE,
    PRICE_PER_KG_PRICE,
    PRICE_PER_KG_WEIGHT,
    ORIGINAL_PRICE_DISCOUNTED_PRICE,
    ORIGINAL_PRICE_DISCOUNT_PERCENT,
    PRO_MENU,
    PRO_AUTO_MODE,
    PRO_AUTO_INPUT,
    PRO_FIXED_DISCOUNT_PRICE,
    PRO_FIXED_DISCOUNT_AMOUNT,
    PRO_LOYALTY_BASE_PRICE,
    PRO_LOYALTY_CARD_PRICE,
    PRO_DOUBLE_DISC1_PRICE,
    PRO_DOUBLE_DISC1_FIRST,
    PRO_DOUBLE_DISC1_SECOND,
    PRO_DOUBLE_DISC2_PRICE,
    PRO_DOUBLE_DISC2_FIRST,
    PRO_DOUBLE_DISC2_SECOND,
    PRO_COMPARE_FIRST_PRICE,
    PRO_COMPARE_FIRST_WEIGHT,
    PRO_COMPARE_SECOND_PRICE,
    PRO_COMPARE_SECOND_WEIGHT,
    PRO_PROMO_OLD,
    PRO_PROMO_NEW,
    PRO_MARGIN_COST,
    PRO_MARGIN_SHELF,
) = range(32)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Поддерживаемые языки
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "uk": "🇺🇦 Українська",
}

# Переводы текстов
TEXTS = {
    "ru": {
        "start": "👋 Привет! Я бот для расчёта цен, скидок и выгодных акций.\n\n"
                 "Выбери язык:",
        "language_selected": "Язык установлен: {language}\n\nВыбери режим:",
        "main_menu_title": "📊 Основной режим",
        "pro_menu_title": "💼 PRO режим",
        "main_menu": "Выберите, что хотите посчитать:",
        "pro_menu": "Выберите профессиональный инструмент:",
        "btn_basic_mode": "📊 Основной режим",
        "btn_pro_mode": "💼 PRO режим",
        "btn_back_to_main": "⬅️ Назад в основное меню",
        "btn_restart": "🔁 Перезапустить бота",
        "btn_history": "📜 История расчётов (TOP-10)",

        # Основные функции
        "btn_discount_price": "💰 Цена со скидкой",
        "btn_n_plus_x": "🎯 Акция N+X (2+1, 3+2...)",
        "btn_price_per_kg": "⚖️ Цена за кг/литр",
        "btn_original_price": "💼 Узнать цену до скидки",

        # PRO функции
        "btn_auto_mode": "🤖 Авто-режим (299−40%, 2+1 цена 60...)",
        "btn_fixed_discount": "💸 Фиксированная скидка (в грн)",
        "btn_loyalty_price": "💳 Цена по карте лояльности",
        "btn_double_discount": "🔁 Двойная скидка (2 скидки подряд)",
        "btn_compare_products": "⚖️ Сравнение двух товаров",
        "btn_promo_vs_regular": "📉 Промо vs обычная цена",
        "btn_margin_calc": "📊 Маржа и наценка",

        "enter_price": "Введите цену товара (например, 199.99):",
        "enter_discount_percent": "Введите размер скидки в % (например, 15 или 14.44):",
        "enter_discount_percent_or_choose": "Выберите готовый размер скидки или введите свой %:",
        "enter_n": "Введите количество покупаемых товаров (N):",
        "enter_x": "Введите количество товаров в подарок (X):",
        "enter_weight": "Введите вес/объём товара (в граммах или мл):",
        "enter_discounted_price": "Введите акционную цену (со скидкой):",
        "enter_two_discounts": "Введите две скидки подряд в формате: 20+15 (без пробелов):",
        "enter_first_product_price": "Введите цену первого товара:",
        "enter_first_product_weight": "Введите вес/объём первого товара (в граммах или мл):",
        "enter_second_product_price": "Введите цену второго товара:",
        "enter_second_product_weight": "Введите вес/объём второго товара (в граммах или мл):",
        "enter_promo_price": "Введите промо-цену товара:",
        "enter_regular_price": "Введите регулярную (обычную) цену товара:",
        "enter_cost_price": "Введите закупочную цену товара:",
        "enter_shelf_price": "Введите цену на полке (продажную):",

        "result_discount_price": "🎯 *Расчёт: цена со скидкой*\n\n"
                                 "Исходная цена: *{original:.2f}*\n"
                                 "Скидка: *{discount:.2f}%*\n"
                                 "Цена со скидкой: *{final:.2f}*",
        "result_n_plus_x": "🎯 *Расчёт: акция N+X*\n\n"
                           "Покупаем: *{n}* шт.\n"
                           "Получаем в подарок: *{x}* шт.\n"
                           "Цена за единицу по акции: *{unit_price:.2f}*\n"
                           "Фактическая скидка: *{discount_percent:.2f}%*",
        "result_price_per_kg": "⚖️ *Расчёт: цена за кг/литр*\n\n"
                               "Цена: *{price:.2f}*\n"
                               "Вес/объём: *{weight}* г/мл\n"
                               "Цена за 1 кг/л: *{per_kg:.2f}*\n"
                               "Цена за 100 г/мл: *{per_100:.2f}*",
        "result_original_price": "💼 *Расчёт: цена до скидки*\n\n"
                                 "Акционная цена: *{discounted:.2f}*\n"
                                 "Скидка: *{discount:.2f}%*\n"
                                 "Цена до скидки: *{original:.2f}*",
        "result_fixed_discount": "💸 *Расчёт: фиксированная скидка*\n\n"
                                 "Исходная цена: *{price:.2f}*\n"
                                 "Скидка: *{discount:.2f}*\n"
                                 "Цена со скидкой: *{final:.2f}*",
        "result_loyalty_price": "💳 *Расчёт: карта лояльности*\n\n"
                                "Обычная цена: *{base:.2f}*\n"
                                "Цена по карте: *{card:.2f}*\n"
                                "Экономия: *{save:.2f}* (*{percent:.2f}%*)",
        "result_double_discount": "🔁 *Расчёт: двойная скидка*\n\n"
                                  "Исходная цена: *{price:.2f}*\n"
                                  "Первая скидка: *{d1:.2f}%*\n"
                                  "Вторая скидка: *{d2:.2f}%*\n"
                                  "Промежуточная цена: *{mid:.2f}*\n"
                                  "Итоговая цена: *{final:.2f}*\n"
                                  "Эффективная скидка: *{eff:.2f}%*",
        "result_compare": "⚖️ *Сравнение двух товаров*\n\n"
                          "Товар 1: *{p1:.2f}* за *{w1}* г/мл → *{per1:.2f}* за 1 кг/л\n"
                          "Товар 2: *{p2:.2f}* за *{w2}* г/мл → *{per2:.2f}* за 1 кг/л\n\n"
                          "{better}",
        "result_promo_vs_regular": "📉 *Промо vs обычная цена*\n\n"
                                   "Обычная цена: *{regular:.2f}*\n"
                                   "Промо-цена: *{promo:.2f}*\n"
                                   "Экономия: *{save:.2f}* (*{percent:.2f}%*)",
        "result_margin": "📊 *Маржа и наценка*\n\n"
                         "Закупочная цена: *{cost:.2f}*\n"
                         "Цена на полке: *{shelf:.2f}*\n"
                         "Наценка: *{markup:.2f}%*\n"
                         "Маржа: *{margin:.2f}%*\n"
                         "Прибыль с единицы: *{profit:.2f}*",
        "history_empty": "Пока нет сохранённых расчётов.",
        "history_header": "📜 *10 последних расчётов:*",
        "back_to_menu": "⬅️ Вернуться в меню",
        "invalid_number": "❌ Некорректный ввод. Пожалуйста, введите число (можно с точкой).",
        "invalid_format": "❌ Некорректный формат. Попробуйте ещё раз.",
        "action_cancelled": "Действие отменено.",
        "current_mode_basic": "📊 Сейчас: *Основной режим*\n\nВыберите функцию:",
        "current_mode_pro": "💼 Сейчас: *PRO режим*\n\nВыберите инструмент:",
        "mode_discount_price": "💰 *Режим: Цена со скидкой*",
        "mode_n_plus_x": "🎯 *Режим: Акция N+X*",
        "mode_price_per_kg": "⚖️ *Режим: Цена за кг/литр*",
        "mode_original_price": "💼 *Режим: Цена до скидки*",
        "mode_fixed_discount": "💸 *Режим: Фиксированная скидка*",
        "mode_loyalty": "💳 *Режим: Цена по карте лояльности*",
        "mode_double_discount": "🔁 *Режим: Двойная скидка*",
        "mode_compare": "⚖️ *Режим: Сравнение товаров*",
        "mode_promo_vs_regular": "📉 *Режим: Промо vs обычная цена*",
        "mode_margin": "📊 *Режим: Маржа и наценка*",
        "pro_auto_prompt": "🤖 Введите выражение, например:\n"
                           "- `299-40%`\n"
                           "- `2+1 цена 60`\n"
                           "- `350 г за 42`\n\n"
                           "Я попробую сам определить тип расчёта.",
        "btn_cancel": "❌ Отмена",
        "btn_main_menu": "🏠 В главное меню",
        "error": "❌ Произошла ошибка. Попробуйте снова или введите /start для перезапуска.",
    },
    "uk": {
        "start": "👋 Привіт! Я бот для розрахунку цін, знижок та вигідних акцій.\n\n"
                 "Оберіть мову:",
        "language_selected": "Мову встановлено: {language}\n\nОберіть режим:",
        "main_menu_title": "📊 Основний режим",
        "pro_menu_title": "💼 PRO режим",
        "main_menu": "Оберіть, що хочете порахувати:",
        "pro_menu": "Оберіть професійний інструмент:",
        "btn_basic_mode": "📊 Основний режим",
        "btn_pro_mode": "💼 PRO режим",
        "btn_back_to_main": "⬅️ Назад до основного меню",
        "btn_restart": "🔁 Перезапустити бота",
        "btn_history": "📜 Історія розрахунків (TOP-10)",

        "btn_discount_price": "💰 Ціна зі знижкою",
        "btn_n_plus_x": "🎯 Акція N+X (2+1, 3+2...)",
        "btn_price_per_kg": "⚖️ Ціна за кг/літр",
        "btn_original_price": "💼 Дізнатися ціну до знижки",

        "btn_auto_mode": "🤖 Авто-режим (299−40%, 2+1 ціна 60...)",
        "btn_fixed_discount": "💸 Фіксована знижка (в грн)",
        "btn_loyalty_price": "💳 Ціна за картою лояльності",
        "btn_double_discount": "🔁 Подвійна знижка",
        "btn_compare_products": "⚖️ Порівняння двох товарів",
        "btn_promo_vs_regular": "📉 Промо vs звичайна ціна",
        "btn_margin_calc": "📊 Маржа та націнка",

        "enter_price": "Введіть ціну товару (наприклад, 199.99):",
        "enter_discount_percent": "Введіть розмір знижки в % (наприклад, 15 або 14.44):",
        "enter_discount_percent_or_choose": "Оберіть готовий розмір знижки або введіть свій %:",
        "enter_n": "Введіть кількість товарів, що купуються (N):",
        "enter_x": "Введіть кількість товарів у подарунок (X):",
        "enter_weight": "Введіть вагу/об'єм товару (у грамах або мл):",
        "enter_discounted_price": "Введіть акційну ціну (зі знижкою):",
        "enter_two_discounts": "Введіть дві знижки підряд у форматі: 20+15 (без пробілів):",
        "enter_first_product_price": "Введіть ціну першого товару:",
        "enter_first_product_weight": "Введіть вагу/об'єм першого товару (у грамах або мл):",
        "enter_second_product_price": "Введіть ціну другого товару:",
        "enter_second_product_weight": "Введіть вагу/об'єм другого товару (у грамах або мл):",
        "enter_promo_price": "Введіть промо-ціну товару:",
        "enter_regular_price": "Введіть звичайну (регулярну) ціну товару:",
        "enter_cost_price": "Введіть закупівельну ціну товару:",
        "enter_shelf_price": "Введіть ціну на полиці (продажну):",

        "result_discount_price": "🎯 *Розрахунок: ціна зі знижкою*\n\n"
                                 "Початкова ціна: *{original:.2f}*\n"
                                 "Знижка: *{discount:.2f}%*\n"
                                 "Ціна зі знижкою: *{final:.2f}*",
        "result_n_plus_x": "🎯 *Розрахунок: акція N+X*\n\n"
                           "Купуємо: *{n}* шт.\n"
                           "Отримуємо в подарунок: *{x}* шт.\n"
                           "Ціна за одиницю по акції: *{unit_price:.2f}*\n"
                           "Фактична знижка: *{discount_percent:.2f}%*",
        "result_price_per_kg": "⚖️ *Розрахунок: ціна за кг/літр*\n\n"
                               "Ціна: *{price:.2f}*\n"
                               "Вага/об'єм: *{weight}* г/мл\n"
                               "Ціна за 1 кг/л: *{per_kg:.2f}*\n"
                               "Ціна за 100 г/мл: *{per_100:.2f}*",
        "result_original_price": "💼 *Розрахунок: ціна до знижки*\n\n"
                                 "Акційна ціна: *{discounted:.2f}*\n"
                                 "Знижка: *{discount:.2f}%*\n"
                                 "Ціна до знижки: *{original:.2f}*",
        "result_fixed_discount": "💸 *Розрахунок: фіксована знижка*\n\n"
                                 "Початкова ціна: *{price:.2f}*\n"
                                 "Знижка: *{discount:.2f}*\n"
                                 "Ціна зі знижкою: *{final:.2f}*",
        "result_loyalty_price": "💳 *Розрахунок: карта лояльності*\n\n"
                                "Звичайна ціна: *{base:.2f}*\n"
                                "Ціна за картою: *{card:.2f}*\n"
                                "Економія: *{save:.2f}* (*{percent:.2f}%*)",
        "result_double_discount": "🔁 *Розрахунок: подвійна знижка*\n\n"
                                  "Початкова ціна: *{price:.2f}*\n"
                                  "Перша знижка: *{d1:.2f}%*\n"
                                  "Друга знижка: *{d2:.2f}%*\n"
                                  "Проміжна ціна: *{mid:.2f}*\n"
                                  "Кінцева ціна: *{final:.2f}*\n"
                                  "Ефективна знижка: *{eff:.2f}%*",
        "result_compare": "⚖️ *Порівняння двох товарів*\n\n"
                          "Товар 1: *{p1:.2f}* за *{w1}* г/мл → *{per1:.2f}* за 1 кг/л\n"
                          "Товар 2: *{p2:.2f}* за *{w2}* г/мл → *{per2:.2f}* за 1 кг/л\n\n"
                          "{better}",
        "result_promo_vs_regular": "📉 *Промо vs звичайна ціна*\n\n"
                                   "Звичайна ціна: *{regular:.2f}*\n"
                                   "Промо-ціна: *{promo:.2f}*\n"
                                   "Економія: *{save:.2f}* (*{percent:.2f}%*)",
        "result_margin": "📊 *Розрахунок: маржа та націнка*\n\n"
                         "Закупівельна ціна: *{cost:.2f}*\n"
                         "Ціна на полиці: *{shelf:.2f}*\n"
                         "Націнка: *{markup:.2f}%*\n"
                         "Маржа: *{margin:.2f}%*\n"
                         "Прибуток з одиниці: *{profit:.2f}*",
        "history_empty": "Поки що немає збережених розрахунків.",
        "history_header": "📜 *10 останніх розрахунків:*",
        "back_to_menu": "⬅️ Повернутися в меню",
        "invalid_number": "❌ Некоректне введення. Будь ласка, введіть число (можна з крапкою).",
        "invalid_format": "❌ Некоректний формат. Спробуйте ще раз.",
        "action_cancelled": "Дію скасовано.",
        "current_mode_basic": "📊 Зараз: *Основний режим*\n\nОберіть функцію:",
        "current_mode_pro": "💼 Зараз: *PRO режим*\n\nОберіть інструмент:",
        "mode_discount_price": "💰 *Режим: Ціна зі знижкою*",
        "mode_n_plus_x": "🎯 *Режим: Акція N+X*",
        "mode_price_per_kg": "⚖️ *Режим: Ціна за кг/літр*",
        "mode_original_price": "💼 *Режим: Ціна до знижки*",
        "mode_fixed_discount": "💸 *Режим: Фіксована знижка*",
        "mode_loyalty": "💳 *Режим: Ціна за картою лояльності*",
        "mode_double_discount": "🔁 *Режим: Подвійна знижка*",
        "mode_compare": "⚖️ *Режим: Порівняння товарів*",
        "mode_promo_vs_regular": "📉 *Режим: Промо vs звичайна ціна*",
        "mode_margin": "📊 *Режим: Маржа та націнка*",
        "pro_auto_prompt": "🤖 Введіть вираз, наприклад:\n"
                           "- `299-40%`\n"
                           "- `2+1 ціна 60`\n"
                           "- `350 г за 42`\n\n"
                           "Я спробую сам визначити тип розрахунку.",
        "btn_cancel": "❌ Скасувати",
        "btn_main_menu": "🏠 В головне меню",
        "error": "❌ Сталася помилка. Спробуйте ще раз або введіть /start для перезапуску.",
    },
}

# Хранилище истории в памяти (по user_id)
USER_HISTORY = {}

# ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------


def get_language(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("language", "ru")


def t(context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    lang = get_language(context)
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, "")
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def add_to_history(user_id: int, text: str):
    """Сохраняем последние 10 расчётов для пользователя"""
    if user_id not in USER_HISTORY:
        USER_HISTORY[user_id] = []
    USER_HISTORY[user_id].insert(0, text)
    USER_HISTORY[user_id] = USER_HISTORY[user_id][:10]


def is_valid_number(value: str) -> bool:
    try:
        float(value.replace(",", "."))
        return True
    except ValueError:
        return False


def parse_number(value: str) -> float:
    return float(value.replace(",", "."))


def get_main_keyboard(context: ContextTypes.DEFAULT_TYPE):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t(context, "btn_basic_mode"), callback_data="mode_basic"
                ),
                InlineKeyboardButton(
                    t(context, "btn_pro_mode"), callback_data="mode_pro"
                ),
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_history"), callback_data="history"
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_restart"), callback_data="restart"
                )
            ],
        ]
    )


def get_basic_menu_keyboard(context: ContextTypes.DEFAULT_TYPE):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t(context, "btn_discount_price"),
                    callback_data="discount_price",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_n_plus_x"), callback_data="n_plus_x"
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_price_per_kg"),
                    callback_data="price_per_kg",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_original_price"),
                    callback_data="original_price",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_back_to_main"),
                    callback_data="back_to_main",
                )
            ],
        ]
    )


def get_pro_menu_keyboard(context: ContextTypes.DEFAULT_TYPE):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t(context, "btn_auto_mode"), callback_data="pro_auto"
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_fixed_discount"),
                    callback_data="pro_fixed_discount",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_loyalty_price"),
                    callback_data="pro_loyalty_price",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_double_discount"),
                    callback_data="pro_double_discount",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_compare_products"),
                    callback_data="pro_compare_products",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_promo_vs_regular"),
                    callback_data="pro_promo_vs_regular",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_margin_calc"),
                    callback_data="pro_margin_calc",
                )
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_back_to_main"),
                    callback_data="back_to_main",
                )
            ],
        ]
    )


def get_discount_keyboard(context: ContextTypes.DEFAULT_TYPE):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("5%", callback_data="disc_5"),
                InlineKeyboardButton("10%", callback_data="disc_10"),
                InlineKeyboardButton("15%", callback_data="disc_15"),
            ],
            [
                InlineKeyboardButton("20%", callback_data="disc_20"),
                InlineKeyboardButton("25%", callback_data="disc_25"),
                InlineKeyboardButton("30%", callback_data="disc_30"),
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_cancel"), callback_data="cancel"
                )
            ],
        ]
    )


def get_yes_no_keyboard(context: ContextTypes.DEFAULT_TYPE):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✔️", callback_data="yes"),
                InlineKeyboardButton("❌", callback_data="no"),
            ],
            [
                InlineKeyboardButton(
                    t(context, "btn_cancel"), callback_data="cancel"
                )
            ],
        ]
    )


def get_numeric_keyboard():
    # Встроенная клавиатура ввода цифр
    return ReplyKeyboardMarkup(
        [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["0", ",", "."],
            ["⬅️ Назад", "❌ Отмена"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Введите число...",
    )


# ---------------- ОБРАБОТЧИКИ КОМАНД ----------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["language"] = "ru"
    user = update.effective_user
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(LANGUAGES["ru"], callback_data="lang_ru"),
                InlineKeyboardButton(LANGUAGES["uk"], callback_data="lang_uk"),
            ]
        ]
    )
    await update.message.reply_text(
        TEXTS["ru"]["start"],
        reply_markup=keyboard,
    )
    return LANGUAGE_SELECTION


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(LANGUAGES["ru"], callback_data="lang_ru"),
                InlineKeyboardButton(LANGUAGES["uk"], callback_data="lang_uk"),
            ]
        ]
    )
    await query.message.delete()
    await query.message.chat.send_message(
        TEXTS["ru"]["start"],
        reply_markup=keyboard,
    )
    return LANGUAGE_SELECTION


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "lang_ru":
        context.user_data["language"] = "ru"
    elif query.data == "lang_uk":
        context.user_data["language"] = "uk"

    lang = get_language(context)
    await query.message.delete()
    await query.message.chat.send_message(
        t(context, "language_selected", language=LANGUAGES[lang]),
        reply_markup=get_main_keyboard(context),
    )
    return MAIN_MENU


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "mode_basic":
        await query.message.edit_text(
            f"{t(context, 'main_menu_title')}\n\n{t(context, 'current_mode_basic')}",
            reply_markup=get_basic_menu_keyboard(context),
        )
        return MAIN_MENU

    if data == "mode_pro":
        await query.message.edit_text(
            f"{t(context, 'pro_menu_title')}\n\n{t(context, 'current_mode_pro')}",
            reply_markup=get_pro_menu_keyboard(context),
        )
        return PRO_MENU

    if data == "back_to_main":
        await query.message.edit_text(
            t(context, "main_menu"),
            reply_markup=get_main_keyboard(context),
        )
        return MAIN_MENU

    if data == "restart":
        return await restart_callback(update, context)

    if data == "history":
        user_id = update.effective_user.id
        history = USER_HISTORY.get(user_id, [])
        if not history:
            await query.message.reply_text(t(context, "history_empty"))
        else:
            text = t(context, "history_header") + "\n\n" + "\n\n".join(history)
            await query.message.reply_text(text)
        return MAIN_MENU

    if data == "discount_price":
        await query.message.edit_text(
            f"{t(context, 'mode_discount_price')}\n\n{t(context, 'enter_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "discount_price"
        return DISCOUNT_PRICE

    if data == "n_plus_x":
        await query.message.edit_text(
            f"{t(context, 'mode_n_plus_x')}\n\n{t(context, 'enter_n')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "n_plus_x"
        return N_PLUS_X_N

    if data == "price_per_kg":
        await query.message.edit_text(
            f"{t(context, 'mode_price_per_kg')}\n\n{t(context, 'enter_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "price_per_kg"
        return PRICE_PER_KG_PRICE

    if data == "original_price":
        await query.message.edit_text(
            f"{t(context, 'mode_original_price')}\n\n{t(context, 'enter_discounted_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "original_price"
        return ORIGINAL_PRICE_DISCOUNTED_PRICE

    if data == "pro_auto":
        await query.message.edit_text(
            f"{t(context, 'pro_menu_title')}\n\n{t(context, 'pro_auto_prompt')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_auto"
        return PRO_AUTO_INPUT

    if data == "pro_fixed_discount":
        await query.message.edit_text(
            f"{t(context, 'mode_fixed_discount')}\n\n{t(context, 'enter_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_fixed_discount"
        return PRO_FIXED_DISCOUNT_PRICE

    if data == "pro_loyalty_price":
        await query.message.edit_text(
            f"{t(context, 'mode_loyalty')}\n\n{t(context, 'enter_regular_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_loyalty"
        return PRO_LOYALTY_BASE_PRICE

    if data == "pro_double_discount":
        await query.message.edit_text(
            f"{t(context, 'mode_double_discount')}\n\n{t(context, 'enter_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_double_discount_price"
        return PRO_DOUBLE_DISC1_PRICE

    if data == "pro_compare_products":
        await query.message.edit_text(
            f"{t(context, 'mode_compare')}\n\n{t(context, 'enter_first_product_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_compare_first_price"
        return PRO_COMPARE_FIRST_PRICE

    if data == "pro_promo_vs_regular":
        await query.message.edit_text(
            f"{t(context, 'mode_promo_vs_regular')}\n\n{t(context, 'enter_regular_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_promo_regular"
        return PRO_PROMO_OLD

    if data == "pro_margin_calc":
        await query.message.edit_text(
            f"{t(context, 'mode_margin')}\n\n{t(context, 'enter_cost_price')}",
            reply_markup=None,
        )
        context.user_data["current_mode"] = "pro_margin_cost"
        return PRO_MARGIN_COST

    return MAIN_MENU


# ---------------- ОБРАБОТЧИКИ ОСНОВНОГО РЕЖИМА ----------------


async def discount_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return DISCOUNT_PRICE

    price = parse_number(text)
    context.user_data["discount_price_original"] = price

    await update.message.reply_text(
        t(context, "enter_discount_percent_or_choose"),
        reply_markup=get_discount_keyboard(context),
    )
    return DISCOUNT_PERCENT


async def discount_percent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel":
        await query.message.delete()
        await query.message.chat.send_message(
            t(context, "action_cancelled"),
            reply_markup=get_basic_menu_keyboard(context),
        )
        return MAIN_MENU

    if data.startswith("disc_"):
        discount = int(data.split("_")[1])
        original = context.user_data.get("discount_price_original", 0)
        final = original * (1 - discount / 100)

        result_text = t(
            context,
            "result_discount_price",
            original=original,
            discount=discount,
            final=final,
        )
        add_to_history(query.from_user.id, result_text)

        await query.message.delete()
        await query.message.chat.send_message(
            result_text,
            reply_markup=get_main_keyboard(context),
            parse_mode="Markdown",
        )
        return MAIN_MENU

    await query.message.reply_text(t(context, "invalid_format"))
    return DISCOUNT_PERCENT


async def discount_percent_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ["⬅️ Назад", "❌ Отмена"]:
        await update.message.reply_text(
            t(context, "action_cancelled"),
            reply_markup=get_basic_menu_keyboard(context),
        )
        return MAIN_MENU

    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return DISCOUNT_PERCENT

    discount = parse_number(text)
    original = context.user_data.get("discount_price_original", 0)
    final = original * (1 - discount / 100)

    result_text = t(
        context,
        "result_discount_price",
        original=original,
        discount=discount,
        final=final,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def n_plus_x_n_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text(t(context, "invalid_number"))
        return N_PLUS_X_N

    context.user_data["n_plus_x_n"] = int(text)
    await update.message.reply_text(t(context, "enter_x"), reply_markup=get_numeric_keyboard())
    return N_PLUS_X_X


async def n_plus_x_x_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text(t(context, "invalid_number"))
        return N_PLUS_X_X

    context.user_data["n_plus_x_x"] = int(text)
    await update.message.reply_text(
        t(context, "enter_price"),
        reply_markup=ReplyKeyboardRemove(),
    )
    return N_PLUS_X_PRICE


async def n_plus_x_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return N_PLUS_X_PRICE

    price = parse_number(text)
    n = context.user_data.get("n_plus_x_n", 1)
    x = context.user_data.get("n_plus_x_x", 0)
    total_items = n + x
    unit_price = price / total_items
    discount_percent = (x / total_items) * 100

    result_text = t(
        context,
        "result_n_plus_x",
        n=n,
        x=x,
        unit_price=unit_price,
        discount_percent=discount_percent,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def price_per_kg_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRICE_PER_KG_PRICE

    price = parse_number(text)
    context.user_data["price_per_kg_price"] = price

    await update.message.reply_text(t(context, "enter_weight"))
    return PRICE_PER_KG_WEIGHT


async def price_per_kg_weight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRICE_PER_KG_WEIGHT

    weight = parse_number(text)
    price = context.user_data.get("price_per_kg_price", 0)

    per_kg = price / (weight / 1000)
    per_100 = price / (weight / 100)

    result_text = t(
        context,
        "result_price_per_kg",
        price=price,
        weight=weight,
        per_kg=per_kg,
        per_100=per_100,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def original_price_discounted_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return ORIGINAL_PRICE_DISCOUNTED_PRICE

    discounted_price = parse_number(text)
    context.user_data["original_discounted_price"] = discounted_price

    await update.message.reply_text(t(context, "enter_discount_percent"))
    return ORIGINAL_PRICE_DISCOUNT_PERCENT


async def original_price_percent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return ORIGINAL_PRICE_DISCOUNT_PERCENT

    discount = parse_number(text)
    discounted_price = context.user_data.get("original_discounted_price", 0)
    original = discounted_price / (1 - discount / 100)

    result_text = t(
        context,
        "result_original_price",
        discounted=discounted_price,
        discount=discount,
        original=original,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


# ---------------- ОБРАБОТЧИКИ PRO-РЕЖИМА ----------------


async def pro_auto_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 299-40%
    match_disc = re.match(r"(\d+[.,]?\d*)\s*-\s*(\d+[.,]?\d*)\s*%", text)
    if match_disc:
        price = parse_number(match_disc.group(1))
        disc = parse_number(match_disc.group(2))
        final = price * (1 - disc / 100)

        result_text = t(
            context,
            "result_discount_price",
            original=price,
            discount=disc,
            final=final,
        )
        add_to_history(update.effective_user.id, result_text)
        await update.message.reply_text(
            result_text,
            reply_markup=get_main_keyboard(context),
            parse_mode="Markdown",
        )
        return MAIN_MENU

    # 2+1 цена 60
    match_nx = re.match(
        r"(\d+)\s*\+\s*(\d+).*(\d+[.,]?\d*)", text, re.IGNORECASE
    )
    if match_nx:
        n = int(match_nx.group(1))
        x = int(match_nx.group(2))
        price = parse_number(match_nx.group(3))

        total_items = n + x
        unit_price = price / total_items
        discount_percent = (x / total_items) * 100

        result_text = t(
            context,
            "result_n_plus_x",
            n=n,
            x=x,
            unit_price=unit_price,
            discount_percent=discount_percent,
        )
        add_to_history(update.effective_user.id, result_text)
        await update.message.reply_text(
            result_text,
            reply_markup=get_main_keyboard(context),
            parse_mode="Markdown",
        )
        return MAIN_MENU

    # 350 г за 42
    match_weight = re.match(
        r"(\d+[.,]?\d*)\s*[ггг]|грамм|грамів|гр?\.?\s*за\s*(\d+[.,]?\d*)",
        text,
        re.IGNORECASE,
    )
    if match_weight:
        weight = parse_number(match_weight.group(1))
        price = parse_number(match_weight.group(2))

        per_kg = price / (weight / 1000)
        per_100 = price / (weight / 100)

        result_text = t(
            context,
            "result_price_per_kg",
            price=price,
            weight=weight,
            per_kg=per_kg,
            per_100=per_100,
        )
        add_to_history(update.effective_user.id, result_text)
        await update.message.reply_text(
            result_text,
            reply_markup=get_main_keyboard(context),
            parse_mode="Markdown",
        )
        return MAIN_MENU

    await update.message.reply_text(t(context, "invalid_format"))
    return PRO_AUTO_INPUT


async def pro_fixed_discount_price_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_FIXED_DISCOUNT_PRICE

    price = parse_number(text)
    context.user_data["fixed_price"] = price

    await update.message.reply_text(t(context, "enter_discounted_price"))
    return PRO_FIXED_DISCOUNT_AMOUNT


async def pro_fixed_discount_amount_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_FIXED_DISCOUNT_AMOUNT

    discount = parse_number(text)
    price = context.user_data.get("fixed_price", 0)
    final = max(price - discount, 0)

    result_text = t(
        context,
        "result_fixed_discount",
        price=price,
        discount=discount,
        final=final,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def pro_loyalty_base_price_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_LOYALTY_BASE_PRICE

    base = parse_number(text)
    context.user_data["loyalty_base"] = base

    await update.message.reply_text(t(context, "enter_discounted_price"))
    return PRO_LOYALTY_CARD_PRICE


async def pro_loyalty_card_price_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_LOYALTY_CARD_PRICE

    card = parse_number(text)
    base = context.user_data.get("loyalty_base", 0)
    save = max(base - card, 0)
    percent = (save / base * 100) if base else 0

    result_text = t(
        context,
        "result_loyalty_price",
        base=base,
        card=card,
        save=save,
        percent=percent,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def pro_double_disc_price_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_DOUBLE_DISC1_PRICE

    price = parse_number(text)
    context.user_data["double_disc_price"] = price

    await update.message.reply_text(t(context, "enter_two_discounts"))
    return PRO_DOUBLE_DISC1


async def pro_double_disc_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip()
    match = re.match(r"(\d+[.,]?\d*)\s*\+\s*(\d+[.,]?\d*)", text)
    if not match:
        await update.message.reply_text(t(context, "invalid_format"))
        return PRO_DOUBLE_DISC1

    d1 = parse_number(match.group(1))
    d2 = parse_number(match.group(2))
    price = context.user_data.get("double_disc_price", 0)

    mid = price * (1 - d1 / 100)
    final = mid * (1 - d2 / 100)
    effective = (1 - final / price) * 100 if price else 0

    result_text = t(
        context,
        "result_double_discount",
        price=price,
        d1=d1,
        d2=d2,
        mid=mid,
        final=final,
        eff=effective,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def pro_compare_first_price_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_COMPARE_FIRST_PRICE

    price1 = parse_number(text)
    context.user_data["compare_price1"] = price1

    await update.message.reply_text(t(context, "enter_first_product_weight"))
    return PRO_COMPARE_FIRST_WEIGHT


async def pro_compare_first_weight_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_COMPARE_FIRST_WEIGHT

    weight1 = parse_number(text)
    context.user_data["compare_weight1"] = weight1

    await update.message.reply_text(t(context, "enter_second_product_price"))
    return PRO_COMPARE_SECOND_PRICE


async def pro_compare_second_price_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_COMPARE_SECOND_PRICE

    price2 = parse_number(text)
    context.user_data["compare_price2"] = price2

    await update.message.reply_text(t(context, "enter_second_product_weight"))
    return PRO_COMPARE_SECOND_WEIGHT


async def pro_compare_second_weight_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_COMPARE_SECOND_WEIGHT

    weight1 = context.user_data.get("compare_weight1", 0)
    price1 = context.user_data.get("compare_price1", 0)

    weight2 = parse_number(text)
    price2 = context.user_data.get("compare_price2", 0)

    per1 = price1 / (weight1 / 1000) if weight1 else 0
    per2 = price2 / (weight2 / 1000) if weight2 else 0

    if per1 < per2:
        better = "✅ Товар 1 вигідніший"
    elif per2 < per1:
        better = "✅ Товар 2 вигідніший"
    else:
        better = "⚖️ Обидва товари однаково вигідні"

    result_text = t(
        context,
        "result_compare",
        p1=price1,
        w1=weight1,
        per1=per1,
        p2=price2,
        w2=weight2,
        per2=per2,
        better=better,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def pro_promo_old_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_PROMO_OLD

    regular = parse_number(text)
    context.user_data["promo_regular"] = regular

    await update.message.reply_text(t(context, "enter_promo_price"))
    return PRO_PROMO_NEW


async def pro_promo_new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_PROMO_NEW

    promo = parse_number(text)
    regular = context.user_data.get("promo_regular", 0)

    save = max(regular - promo, 0)
    percent = (save / regular * 100) if regular else 0

    result_text = t(
        context,
        "result_promo_vs_regular",
        regular=regular,
        promo=promo,
        save=save,
        percent=percent,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


async def pro_margin_cost_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_MARGIN_COST

    cost = parse_number(text)
    context.user_data["margin_cost"] = cost

    await update.message.reply_text(t(context, "enter_shelf_price"))
    return PRO_MARGIN_SHELF


async def pro_margin_shelf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text(t(context, "invalid_number"))
        return PRO_MARGIN_SHELF

    shelf = parse_number(text)
    cost = context.user_data.get("margin_cost", 0)

    profit = max(shelf - cost, 0)
    markup = (profit / cost * 100) if cost else 0
    margin = (profit / shelf * 100) if shelf else 0

    result_text = t(
        context,
        "result_margin",
        cost=cost,
        shelf=shelf,
        markup=markup,
        margin=margin,
        profit=profit,
    )
    add_to_history(update.effective_user.id, result_text)

    await update.message.reply_text(
        result_text,
        reply_markup=get_main_keyboard(context),
        parse_mode="Markdown",
    )
    return MAIN_MENU


# ---------------- ОБЩИЕ ОБРАБОТЧИКИ ----------------


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        t(context, "action_cancelled"),
        reply_markup=get_main_keyboard(context),
    )
    return MAIN_MENU


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Ошибка: %s", context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            lang = get_language(context)
            await update.effective_message.reply_text(TEXTS[lang]["error"])
    except Exception:
        pass


# ---------------- ЗАПУСК ПРИЛОЖЕНИЯ ----------------


async def main():
    application = (
        ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE_SELECTION: [
                CallbackQueryHandler(
                    language_callback, pattern="^lang_(ru|uk)$"
                )
            ],
            MAIN_MENU: [
                CallbackQueryHandler(
                    main_menu_callback,
                    pattern=(
                        "^(mode_basic|mode_pro|back_to_main|restart|history|"
                        "discount_price|n_plus_x|price_per_kg|original_price|"
                        "pro_auto|pro_fixed_discount|pro_loyalty_price|"
                        "pro_double_discount|pro_compare_products|"
                        "pro_promo_vs_regular|pro_margin_calc)$"
                    ),
                )
            ],
            DISCOUNT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, discount_price_handler)
            ],
            DISCOUNT_PERCENT: [
                CallbackQueryHandler(discount_percent_callback, pattern="^disc_"),
                CallbackQueryHandler(discount_percent_callback, pattern="^cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, discount_percent_manual),
            ],
            N_PLUS_X_N: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, n_plus_x_n_handler)
            ],
            N_PLUS_X_X: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, n_plus_x_x_handler)
            ],
            N_PLUS_X_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, n_plus_x_price_handler)
            ],
            PRICE_PER_KG_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    price_per_kg_price_handler,
                )
            ],
            PRICE_PER_KG_WEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    price_per_kg_weight_handler,
                )
            ],
            ORIGINAL_PRICE_DISCOUNTED_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    original_price_discounted_handler,
                )
            ],
            ORIGINAL_PRICE_DISCOUNT_PERCENT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    original_price_percent_handler,
                )
            ],
            PRO_MENU: [],
            PRO_AUTO_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pro_auto_input_handler)
            ],
            PRO_FIXED_DISCOUNT_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_fixed_discount_price_handler,
                )
            ],
            PRO_FIXED_DISCOUNT_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_fixed_discount_amount_handler,
                )
            ],
            PRO_LOYALTY_BASE_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_loyalty_base_price_handler,
                )
            ],
            PRO_LOYALTY_CARD_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_loyalty_card_price_handler,
                )
            ],
            PRO_DOUBLE_DISC1_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_double_disc_price_handler,
                )
            ],
            PRO_DOUBLE_DISC1: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, pro_double_disc_handler
                )
            ],
            PRO_COMPARE_FIRST_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_compare_first_price_handler,
                )
            ],
            PRO_COMPARE_FIRST_WEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_compare_first_weight_handler,
                )
            ],
            PRO_COMPARE_SECOND_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_compare_second_price_handler,
                )
            ],
            PRO_COMPARE_SECOND_WEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_compare_second_weight_handler,
                )
            ],
            PRO_PROMO_OLD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_promo_old_handler,
                )
            ],
            PRO_PROMO_NEW: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_promo_new_handler,
                )
            ],
            PRO_MARGIN_COST: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_margin_cost_handler,
                )
            ],
            PRO_MARGIN_SHELF: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    pro_margin_shelf_handler,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    logger.info("Бот запущен.")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()


if __name__ == "__main__":
    try:
        if not TOKEN:
            raise RuntimeError("Переменная окружения TOKEN не установлена")

        print("🚀 Запуск бота")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
