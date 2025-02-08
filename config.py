import os
import logging

# ==========================
#  TELEGRAM & OPENAI CONFIG
# ==========================

# NOTE: Replace placeholder tokens with your actual credentials
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# ==========================
#         LOGGING
# ==========================
logging.basicConfig(
    filename="bot_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# ==========================
#         FILENAMES
# ==========================
USER_DATA_FILE = 'users.csv'
PLAN_DATA_FILE = 'plans.csv'
ESSAY_TOPICS_FILE = 'essay_topics.csv'

# Ensure CSV files exist
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
        pass

if not os.path.exists(PLAN_DATA_FILE):
    with open(PLAN_DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
        pass

if not os.path.exists(ESSAY_TOPICS_FILE):
    with open(ESSAY_TOPICS_FILE, mode='w', newline='', encoding='utf-8') as file:
        pass
