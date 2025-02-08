import csv
import os
import re
import logging
from config import USER_DATA_FILE, PLAN_DATA_FILE, ESSAY_TOPICS_FILE
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def read_user_data():
    users = {}
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[int(row['user_id'])] = {
                    'user_id': row['user_id'],
                    'language': row.get('language', ''),
                    'english_level': row.get('english_level', ''),
                    'name': row.get('name', ''),
                    'age': row.get('age', ''),
                    'score': int(row.get('score', 0))
                }
    return users


def write_user_data(user_id, language=None, english_level=None, name=None, age=None, score=None, bot_instance=None):
    users = read_user_data()
    previous = users.get(user_id, {})
    previous_language = previous.get('language', 'English')
    user_language = language or previous_language
    previous_level = previous.get('english_level', '')
    previous_name = previous.get('name', '')
    previous_age = previous.get('age', '')
    previous_score = previous.get('score', 0)

    new_language = language or previous_language
    new_level = english_level or previous_level
    new_name = name or previous_name
    new_age = age or previous_age
    new_score = score if score is not None else previous_score

    users[user_id] = {
        'user_id': user_id,
        'language': new_language,
        'english_level': new_level,
        'name': new_name,
        'age': new_age,
        'score': new_score
    }

    with open(USER_DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['user_id', 'language', 'english_level', 'name', 'age', 'score'])
        writer.writeheader()
        for row in users.values():
            writer.writerow(row)

    # If you'd like to show a short update message to the user, you'd do it here:
    # But to keep it decoupled, we typically handle feedback in the main bot code.

def read_plan_data():
    plans = {}
    if os.path.exists(PLAN_DATA_FILE):
        with open(PLAN_DATA_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                plans[int(row['user_id'])] = row['plan']
    return plans


def write_plan_data(user_id, plan_text):
    plans = read_plan_data()
    plans[user_id] = plan_text
    with open(PLAN_DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['user_id', 'plan'])
        writer.writeheader()
        for uid, plan in plans.items():
            writer.writerow({'user_id': uid, 'plan': plan})


def get_user_level(user_id):
    users = read_user_data()
    return users.get(user_id, {}).get("english_level", "Unknown")


def update_user_score(user_id, additional_points):
    users = read_user_data()
    user = users.get(user_id, {})
    current_score = int(user.get("score", 0))
    new_score = current_score + additional_points
    write_user_data(user_id,
                    language=user.get("language"),
                    english_level=user.get("english_level"),
                    name=user.get("name"),
                    age=user.get("age"),
                    score=new_score)
    logging.info(f"User {user_id} awarded {additional_points} points. New score: {new_score}")


def get_persistent_keyboard(user_language):
    new_lesson_text = {
        "English": "📚 Start a New Lesson",
        "Russian": "📚 Начать новый урок",
        "Kazakh": "📚 Жаңа сабақты бастау",
        "Uzbek": "📚 Yangi darsni boshlash",
        "Kyrgyz": "📚 Жаңы сабакты баштоо"
    }.get(user_language, "📚 Start a New Lesson")

    persistent_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    persistent_keyboard.add(KeyboardButton(new_lesson_text))
    return persistent_keyboard


def read_essay_topics():
    topics = []
    if os.path.exists(ESSAY_TOPICS_FILE):
        with open(ESSAY_TOPICS_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                topics.append({
                    'essay_id': int(row['essay_id']),
                    'user_id': int(row['user_id']),
                    'topic': row['topic'],
                    'status': row['status']
                })
    return topics


def write_essay_topics(topics):
    with open(ESSAY_TOPICS_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['essay_id', 'user_id', 'topic', 'status'])
        writer.writeheader()
        for row in topics:
            writer.writerow({
                'essay_id': row['essay_id'],
                'user_id': row['user_id'],
                'topic': row['topic'],
                'status': row['status']
            })


def add_essay_topic(user_id, topic, status="assigned"):
    topics = read_essay_topics()
    if topics:
        new_id = max(t['essay_id'] for t in topics) + 1
    else:
        new_id = 1
    new_topic = {'essay_id': new_id, 'user_id': user_id, 'topic': topic, 'status': status}
    topics.append(new_topic)
    write_essay_topics(topics)
    return new_topic


def get_user_active_essays(user_id):
    topics = read_essay_topics()
    return [t for t in topics if t['user_id'] == user_id and t['status'] == "assigned"]


def update_essay_topic_status(essay_id, new_status):
    topics = read_essay_topics()
    for t in topics:
        if t['essay_id'] == essay_id:
            t['status'] = new_status
            break
    write_essay_topics(topics)
