import schedule
import time
import threading
import logging
from data_manager import read_user_data
from messages import escape_markdown_v2
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def send_daily_notifications(bot_instance):
    users = read_user_data()

    for user_id, user_info in users.items():
        user_language = user_info.get("language", "English")

        reminder_messages = {
            "English": "🌟 Time to improve your English! Let's learn together! 🚀",
            "Russian": "🌟 Время улучшать ваш английский! Давайте учиться вместе! 🚀",
            "Kazakh": "🌟 Ағылшын тіліңізді жетілдіретін уақыт келді! Бірге оқиық! 🚀",
            "Uzbek": "🌟 Ingliz tilingizni yaxshilash vaqti keldi! Keling, birga o‘rganamiz! 🚀",
            "Kyrgyz": "🌟 Англис тилин жакшыртуу убактысы келди! Келгиле, бирге окуйлу! 🚀"
        }

        message_text = reminder_messages.get(user_language, reminder_messages["English"])
        lesson_keyboard = InlineKeyboardMarkup()
        lesson_keyboard.add(
            InlineKeyboardButton("🎧 Listening", callback_data="start_listening"),
            InlineKeyboardButton("📖 Reading", callback_data="start_reading"),
            InlineKeyboardButton("📝 ESSAY practice", callback_data="start_vocab")
        )

        try:
            bot_instance.send_message(user_id, escape_markdown_v2(message_text), reply_markup=lesson_keyboard)
            logging.info(f"Sent daily lesson reminder to {user_id}")
        except Exception as e:
            logging.error(f"Failed to send notification to {user_id}: {e}")


def schedule_notifications(bot_instance):
    """
    Schedule daily notifications at 14:00.
    """
    schedule.every().day.at("14:00").do(send_daily_notifications, bot_instance)

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)

    t = threading.Thread(target=run_schedule, daemon=True)
    t.start()
