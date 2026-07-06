
import random

from aiogram.types import FSInputFile
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (
    get_random_word_by_level,
    get_wrong_options_by_level,
    update_user_stats,
    set_user_level,
    get_user_level,
)
from aiogram.filters import Command

PHOTO_URL = FSInputFile("Big-Ben.jpg")
router = Router()

TEST_LENGTH = 10


class TestStates(StatesGroup):
    testing = State()


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пройти тест")],
        [KeyboardButton(text="Сменить уровень")],
        [KeyboardButton(text="Моя статистика")],
    ],
    resize_keyboard=True,
)

level_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="A (Beginner)", callback_data="lvl_A"),
            InlineKeyboardButton(text="B (Intermediate)", callback_data="lvl_B"),
            InlineKeyboardButton(text="C (Advanced)", callback_data="lvl_C"),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="back_to_main")
        ]
    ]
)

def get_level_buttons():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A (Beginner)", callback_data="set_lvl_A"),
                InlineKeyboardButton(text="B (Intermediate)", callback_data="set_lvl_B"),
                InlineKeyboardButton(text="C (Advanced)", callback_data="set_lvl_C"),
            ]
        ]
    )


async def send_question(message: Message, level: str, question_num: int):
    word = get_random_word_by_level(level)
    if not word:
        await message.answer("На этом уровне пока нет слов. Попробуйте другой уровень.")
        return None

    correct_ru = word['russian']
    wrongs = get_wrong_options_by_level(word['id'], level)
    options = [correct_ru] + wrongs
    random.shuffle(options)

    english_display = word['english'].capitalize()
    buttons = [
        [InlineKeyboardButton(text=opt.capitalize(), callback_data=opt)]
        for opt in options
    ]
    quiz_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"Вопрос {question_num} из {TEST_LENGTH}\n"
        f"Как переводится слово: <b>{english_display}</b>?",
        parse_mode="HTML",
        reply_markup=quiz_kb,
    )
    return correct_ru, word['id'], level


@router.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "👋 Привет! Это бот для изучения английских слов.\n\n"
        "1. Выбирай уровень сложности (A, B, C).\n"
        "2. Проходи тесты — выбирай правильный перевод.\n"
        "3. Следи за своей статистикой и расти вместе с нами!\n\n"
        "Погнали учить английский вместе! 🇬🇧\n\n"
        "⬇ Выбери уровень для начала:"
    )
    buttons = [
        [
            InlineKeyboardButton(text="A (Beginner)", callback_data="set_lvl_A"),
            InlineKeyboardButton(text="B (Intermediate)", callback_data="set_lvl_B"),
            InlineKeyboardButton(text="C (Advanced)", callback_data="set_lvl_C"),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer_photo(photo=PHOTO_URL, caption=text, reply_markup=markup)

@router.callback_query(F.data.in_({"set_lvl_A", "set_lvl_B", "set_lvl_C"}))
async def process_level_start(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    level = callback.data[-1]
    set_user_level(telegram_id, level)
    await callback.message.answer(f"✅ Уровень {level} выбран. Для старта нажми на кнопку 'Пройти тест'!", reply_markup=main_kb)
    await callback.answer()

@router.message(F.text == "Пройти тест")
async def start_test(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    level = get_user_level(telegram_id)

    await state.set_state(TestStates.testing)
    await state.update_data(question=1, correct=0, level=level)

    result = await send_question(message, level, question_num=1)
    if result is None:
        await state.clear()
        return

    correct_ru, word_id, level = result
    await state.update_data(correct_ru=correct_ru, word_id=word_id, level=level)

@router.callback_query(TestStates.testing)
async def handle_test_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    correct_ru = data.get("correct_ru")
    question = data.get("question", 1)
    correct_count = data.get("correct", 0)
    level = data.get("level")

    if correct_ru is None:
        await callback.answer("Начните тест заново через кнопку 'Пройти тест'")
        return

    user_answer = callback.data
    is_correct = user_answer == correct_ru

    if is_correct:
        correct_count += 1
        feedback = "✅ Верно! Молодец!"
    else:
        feedback = f"❌ Неправильно. Правильный ответ: {correct_ru.capitalize()}"

    update_user_stats(callback.from_user.id, is_correct=is_correct)

    try:
        await callback.message.edit_text(feedback)
    except Exception:
        await callback.message.answer(feedback)

    await callback.answer()

    if question >= TEST_LENGTH:
        final_text = (
            f"🏁 Тест завершён!\n"
            f"Ваш результат: {correct_count} из {TEST_LENGTH} правильных ответов."
        )
        await callback.message.answer(final_text, reply_markup=main_kb)
        await state.clear()
        return

    next_question = question + 1
    await state.update_data(question=next_question, correct=correct_count)

    result = await send_question(callback.message, level, question_num=next_question)
    if result is None:
        await state.clear()
        return

    correct_ru, word_id, level = result
    await state.update_data(correct_ru=correct_ru, word_id=word_id, level=level)

@router.message(F.text == "Сменить уровень")
async def choose_level(message: Message):
    await message.answer("Выбери уровень изучения:", reply_markup=level_kb)

@router.message(F.text.in_(["A", "B", "C"]))
async def set_level(message: Message):
    telegram_id = message.from_user.id
    new_level = message.text
    set_user_level(telegram_id, new_level)
    await message.answer(f"Уровень успешно изменён на {new_level}!", reply_markup=main_kb)

@router.message(F.text == "Назад")
async def go_main_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_kb)

@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Главное меню:", reply_markup=main_kb)
    await callback.answer()

@router.message(F.text == "Моя статистика")
async def statistics(message: Message):
    from database import get_conn
    telegram_id = message.from_user.id
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT score_correct, score_incorrect FROM users WHERE telegram_id=?",
        (telegram_id,),
    )
    row = c.fetchone()
    conn.close()

    correct = row[0] if row else 0
    wrong = row[1] if row else 0
    total = correct + wrong
    if total > 0:
        percent = int(round((correct / total) * 100))
    else:
        percent = 0

    # Определим цвет строки прогресса
    if percent >= 70:
        color = "🟩"
    elif percent >= 40:
        color = "🟨"
    else:
        color = "🟥"
    filled_blocks = max(1, percent // 10) if total > 0 else 0
    blocks = color * filled_blocks + "⬛" * (10 - filled_blocks)
    stat_text = (
        "📊 Ваша статистика:\n"
        f"✅ Правильно: {correct}\n"
        f"❌ Ошибок: {wrong}\n"
        f"Успеваемость: {percent}%\n"
        f"[{blocks}]"
    )
    await message.answer(stat_text, reply_markup=main_kb)
