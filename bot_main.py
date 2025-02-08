import telebot
import re
import json
import logging

from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import BOT_TOKEN
from data_manager import (
    read_user_data, write_user_data, update_user_score,
    get_user_level, get_persistent_keyboard,
    add_essay_topic, get_user_active_essays, update_essay_topic_status,
    read_essay_topics, write_essay_topics, write_plan_data
)
from messages import MESSAGES, escape_markdown_v2
from openai_client_wrapper import call_llm, extract_json
from scheduler import schedule_notifications

# ===========================================
#     GLOBAL VARIABLES / IN-MEMORY STORAGE
# ===========================================
USER_PARAGRAPHS = {}
USER_STATES = {}
LESSON_SESSIONS = {}
LLM_CHAT_HISTORY = {}
LESSON_RESPONSES = {}
ESSAY_ASSIGNMENT_STATE = {}

# State constants
LANGUAGE_SELECTION = "LANGUAGE"
ASSESSMENT = "ASSESSMENT"
INTRODUCTION = "INTRODUCTION"
LEARNING_MODE = "LEARNING_MODE"
ESSAY_EVALUATION = "ESSAY_EVALUATION"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="MarkdownV2")


@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    user_data = read_user_data()

    # If user already introduced name & age, skip setup
    if user_id in user_data and user_data[user_id].get('name') and user_data[user_id].get('age'):
        user_language = user_data[user_id].get('language', 'English')
        messages = {
            "English": "✅ *You have already completed the setup!* No need to restart. You can continue learning.",
            "Russian": "✅ *Вы уже завершили настройку!* Вы можете продолжить обучение.",
            "Kazakh": "✅ *Сіз орнатуды аяқтадыңыз!* Оқуды жалғастыра аласыз.",
            "Uzbek": "✅ *Siz allaqachon sozlamalarni tugatgansiz!* Davom etishingiz mumkin.",
            "Kyrgyz": "✅ *Орнотуу бүткөн!* Окууну уланта берсеңиз болот."
        }
        bot.send_message(message.chat.id, escape_markdown_v2(messages[user_language]))
        return

    USER_STATES[user_id] = LANGUAGE_SELECTION
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(
        KeyboardButton("Russian"),
        KeyboardButton("Kazakh"),
        KeyboardButton("English"),
        KeyboardButton("Uzbek"),
        KeyboardButton("Kyrgyz")
    )

    bot.send_message(
        message.chat.id,
        escape_markdown_v2(MESSAGES["welcome"]["English"]),
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda message: USER_STATES.get(message.from_user.id) == LANGUAGE_SELECTION)
def process_language(message):
    user_id = message.from_user.id
    language_choice = message.text.strip() if message.text else ""
    allowed_languages = ["English", "Russian", "Kazakh", "Uzbek", "Kyrgyz"]

    if language_choice not in allowed_languages:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for lang in allowed_languages:
            keyboard.add(KeyboardButton(lang))

        bot.send_message(
            message.chat.id,
            escape_markdown_v2("Invalid selection. Please choose one of the provided languages."),
            reply_markup=keyboard
        )
        return

    write_user_data(user_id, language=language_choice)
    bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["send_paragraph"][language_choice]), reply_markup=ReplyKeyboardRemove())
    USER_STATES[user_id] = ASSESSMENT


@bot.message_handler(func=lambda message: USER_STATES.get(message.from_user.id) == ASSESSMENT)
def process_assessment(message):
    user_id = message.from_user.id
    user_text = message.text
    USER_PARAGRAPHS[user_id] = user_text

    user_language = read_user_data().get(user_id, {}).get('language', 'English')
    system_prompt = (
        "You are an expert in English proficiency assessment. Use emojis. "
        "Analyze errors in the user's text, provide improvement suggestions, "
        "and ensure that only the final English level is enclosed inside triple backticks like this: ```B2```. "
        f"Respond in {user_language}.\n\n"
        "Assess the following text:\n"
        + user_text
    )

    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["assessing"][user_language]))

    # We’re going to do a single-call here. 
    # If you want streaming, you can adapt it from your original code.
    try:
        response = call_llm(system_prompt)
        bot.delete_message(message.chat.id, msg.message_id)

        # Extract the proficiency level
        proficiency_level_match = re.search(r'```(.*?)```', response, re.DOTALL)
        proficiency_level = proficiency_level_match.group(1).strip() if proficiency_level_match else "Unknown"

        # Remove the triple backticks content from the text
        assessment_text_without_level = re.sub(r'```.*?```', '', response).strip()

        # Update user data with the assessed level
        write_user_data(user_id, english_level=proficiency_level)

        final_message = (
            f"{escape_markdown_v2(MESSAGES['assessment_results'][user_language])}"
            f"{escape_markdown_v2(assessment_text_without_level)}\n\n"
            f"{escape_markdown_v2(MESSAGES['proficiency_level'][user_language])}*{escape_markdown_v2(proficiency_level)}*"
        )
        bot.send_message(message.chat.id, final_message)

        # Add a keyboard to retake or continue
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        retake_test = {
            "English": "🔄 Retake Test",
            "Russian": "🔄 Пересдать тест",
            "Kazakh": "🔄 Тестті қайта тапсыру",
            "Uzbek": "🔄 Testni qayta topshirish",
            "Kyrgyz": "🔄 Тестти кайрадан берүү"
        }.get(user_language, "🔄 Retake Test")

        continue_setup = {
            "English": "➡️ Continue Setup",
            "Russian": "➡️ Продолжить настройку",
            "Kazakh": "➡️ Орнатуды жалғастыру",
            "Uzbek": "➡️ Sozlamani davom ettirish",
            "Kyrgyz": "➡️ Орнотууну улантуу"
        }.get(user_language, "➡️ Continue Setup")

        keyboard.add(KeyboardButton(retake_test), KeyboardButton(continue_setup))

        bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["choose_option"][user_language]), reply_markup=keyboard)
    except Exception as e:
        logging.error(str(e))
        bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["error"][user_language]))


@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    user_id = message.from_user.id
    if user_id in USER_STATES:
        USER_STATES.pop(user_id)
    bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["cancel"]["English"]), reply_markup=ReplyKeyboardRemove())


@bot.message_handler(
    func=lambda message: message.text in [
        "➡️ Continue Setup", "➡️ Продолжить настройку", "➡️ Орнатуды жалғастыру",
        "➡️ Sozlamani davom ettirish", "➡️ Орнотууну улантуу"
    ]
)
def handle_continue_setup(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, escape_markdown_v2("⏳"))
    process_continue_setup(user_id, message.chat.id)


@bot.message_handler(
    func=lambda message: message.text in [
        "🔄 Retake Test", "🔄 Пересдать тест", "🔄 Тестті қайта тапсыру",
        "🔄 Testni qayta topshirish", "🔄 Тестти кайрадан берүү"
    ]
)
def handle_retake_test(message):
    user_id = message.from_user.id
    user_language = read_user_data().get(user_id, {}).get('language', 'English')
    text_msg = {
        "English": "🔄 *You chose to retake the test.* Please send another paragraph in English.",
        "Russian": "🔄 *Вы выбрали пересдать тест.* Отправьте другой абзац на английском языке.",
        "Kazakh": "🔄 *Сіз тестті қайта тапсыруды таңдадыңыз.* Ағылшын тілінде басқа абзац жіберіңіз.",
        "Uzbek": "🔄 *Siz testni qayta topshirishni tanladingiz.* Ingliz tilida yana bir parcha yuboring.",
        "Kyrgyz": "🔄 *Сиз тестти кайрадан берүүнү тандадыңыз.* Англис тилинде башка бир абзац жиберип көрүңүз."
    }.get(user_language, "Please send another paragraph in English.")

    bot.send_message(message.chat.id, escape_markdown_v2(text_msg), reply_markup=ReplyKeyboardRemove())
    USER_STATES[user_id] = ASSESSMENT


def process_continue_setup(user_id, chat_id):
    user_data = read_user_data()
    user_language = user_data.get(user_id, {}).get('language', 'English')
    user_paragraph = USER_PARAGRAPHS.get(user_id, "No paragraph provided.")
    level = user_data.get(user_id, {}).get("english_level", "Unknown")

    topics_prompt = (
        "You are an expert in language learning. "
        "Based on the following paragraph provided by the user:\n\n"
        f"{user_paragraph}\n\n"
        f"{level} is their current English proficiency level. "
        "If the user's English level is A1 or A2, mention that these tasks might be too advanced. "
        "Generate a personalized list of topics the user should learn to improve. "
        f"Respond in {user_language}."
    )

    loading_msg = bot.send_message(chat_id, escape_markdown_v2("⏳ Generating your personalized list of topics..."))
    response = call_llm(topics_prompt)
    bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                          text=escape_markdown_v2("✅ Personalized topics generated!"))

    bot.send_message(chat_id, f"{escape_markdown_v2(MESSAGES['personalized_topics'].get(user_language))}\n\n{escape_markdown_v2(response)}")

    # Save to plan data
    write_plan_data(user_id, response)

    # Ask user to introduce themselves
    intro_prompts = {
        "English": "Please introduce yourself briefly (include your name and age).",
        "Russian": "Пожалуйста, кратко представьтесь (укажите имя и возраст).",
        "Kazakh": "Өзіңізді қысқаша таныстырыңыз (аты-жөніңізді және жасыңызды көрсетіңіз).",
        "Uzbek": "O'zingizni qisqacha tanishtiring (ism va yoshni kiriting).",
        "Kyrgyz": "Кыскача тааныштырып коюңуз (аты-жөнүңүздү жана жашыңызды)."
    }
    bot.send_message(chat_id, escape_markdown_v2(intro_prompts.get(user_language, intro_prompts["English"])))
    USER_STATES[user_id] = INTRODUCTION


@bot.message_handler(func=lambda message: USER_STATES.get(message.from_user.id) == INTRODUCTION)
def process_introduction(message):
    user_id = message.from_user.id
    user_language = read_user_data().get(user_id, {}).get('language', 'English')
    user_intro = message.text

    if not user_intro:
        bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["introduction_error"][user_language]))
        return

    extraction_prompt = (
        "You are an assistant that extracts the user's name and age from this text. "
        "Return them as two strings separated by space: Name Age. "
        "If you cannot find both name and age, return exactly `INVALID_INPUT`."
    )

    response = call_llm(extraction_prompt + "\n\n" + user_intro)
    if "INVALID_INPUT" in response:
        bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["introduction_error"][user_language]))
        return

    parts = response.split()
    if len(parts) >= 2 and parts[1].isdigit():
        name, age = parts[0], parts[1]
        write_user_data(user_id, name=name, age=age)
        confirmation = MESSAGES["introduction_recorded"][user_language].format(name=name, age=age)
        bot.send_message(message.chat.id, escape_markdown_v2(confirmation))
    else:
        bot.send_message(message.chat.id, escape_markdown_v2(MESSAGES["introduction_error"][user_language]))
        return

    # Next step: Show "Finish Setup" button
    finish_button_text = {
        "English": "➡️ Finish setup",
        "Russian": "➡️ Завершить настройку",
        "Kazakh": "➡️ Орнатуды аяқтау",
        "Uzbek": "➡️ Sozlamani tugatish",
        "Kyrgyz": "➡️ Орнотууну бүтүрүү"
    }.get(user_language, "➡️ Finish setup")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(finish_button_text, callback_data="finish_setup"))
    bot.send_message(message.chat.id, escape_markdown_v2("Please proceed to the learning mode when you are ready:"), reply_markup=markup)
    USER_STATES[user_id] = LEARNING_MODE


@bot.callback_query_handler(func=lambda call: call.data == "finish_setup")
def handle_finish_setup(call):
    user_id = call.from_user.id
    user_language = read_user_data().get(user_id, {}).get('language', 'English')

    messages = {
        "English": (
            "✅ *Setup Complete!* You are now ready to begin your learning journey.\n\n"
            "⏰ Every day at *2 PM*, you will receive a reminder.\n\n"
            "💬 You also have a free conversation mode.\n\n"
            "🎯 *Start your first task:*"
        ),
        "Russian": (
            "✅ *Настройка завершена!* Теперь вы готовы начать обучение.\n\n"
            "⏰ Каждый день в *14:00* вы будете получать напоминание.\n\n"
            "💬 У вас есть режим свободного общения.\n\n"
            "🎯 *Начните свое первое задание:*"
        )
    }
    text = messages.get(user_language, messages["English"])

    task_keyboard = InlineKeyboardMarkup()
    task_keyboard.add(
        InlineKeyboardButton("🎧 Listening", callback_data="start_listening"),
        InlineKeyboardButton("📖 Reading", callback_data="start_reading"),
        InlineKeyboardButton("📝 ESSAY practice", callback_data="generate_new_essay"),
        InlineKeyboardButton("✍️ Writing Assignment", callback_data="start_writing_assignment")
    )

    cancel_reg_text = {
        "English": "❌ Cancel Registration",
        "Russian": "❌ Перепройти регистрацию",
        "Kazakh": "❌ Тіркеуді қайталау",
        "Uzbek": "❌ Ro'yxatdan o'tishni bekor qilish",
        "Kyrgyz": "❌ Каттоону кайра өткөрүү"
    }.get(user_language, "❌ Cancel Registration")

    task_keyboard.add(InlineKeyboardButton(cancel_reg_text, callback_data="cancel_registration"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=escape_markdown_v2(text),
        reply_markup=task_keyboard
    )
    USER_STATES.pop(user_id, None)


@bot.callback_query_handler(func=lambda call: call.data == "cancel_registration")
def handle_cancel_registration(call):
    user_id = call.from_user.id
    user_data = read_user_data()
    user_language = user_data.get(user_id, {}).get("language", "English")

    if user_id in user_data:
        del user_data[user_id]
        # Overwrite the entire CSV
        with open("users.csv", mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['user_id', 'language', 'english_level', 'name', 'age', 'score'])
            writer.writeheader()
            for row in user_data.values():
                writer.writerow(row)

    USER_STATES[user_id] = LANGUAGE_SELECTION

    localized_cancel_msg = {
        "English": "✅ *Your registration has been canceled and all data has been deleted.*",
        "Russian": "✅ *Ваша регистрация отменена и все данные удалены.*"
    }
    bot.send_message(call.message.chat.id, escape_markdown_v2(localized_cancel_msg.get(user_language, localized_cancel_msg["English"])))
    # Start again
    cmd_start(call.message)


# ===========================================
#  EXAMPLE: SCHEDULER START (in separate file)
# ===========================================
@bot.message_handler(commands=['run_scheduler'])
def run_scheduler_cmd(message):
    # Start the daily reminder thread
    schedule_notifications(bot)
    bot.send_message(message.chat.id, "Daily notifications have been scheduled at 14:00!")


# (Below would follow your reading lesson, listening lesson logic, essay submission, etc.)
# For brevity, not repeating the entire code block from your original script.
# Add your handlers for "start_listening", "start_reading", "start_vocab", "start_writing_assignment" etc. 
# All are consistent with your original code.

def start_bot():
    print("🚀 Bot is running...")
    schedule_notifications(bot)  # Optional to start automatically
    bot.infinity_polling()

if __name__ == "__main__":
    start_bot()
