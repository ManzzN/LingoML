def escape_markdown_v2(text):
    """
    Escapes special characters for Telegram MarkdownV2 formatting.
    """
    import re
    if not text:
        return ""
    escape_chars = r'_*[\]()~`>#+-=|{}.!'
    return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)


MESSAGES = {
    "welcome": {
        "English": "👋 *Welcome!* Please select your language preference:",
        "Russian": "👋 *Добро пожаловать!* Пожалуйста, выберите предпочитаемый язык:",
        "Kazakh": "👋 *Қош келдіңіз!* Тіл таңдаңыз:",
        "Uzbek": "👋 *Xush kelibsiz!* Iltimos, til tanlovingizni belgilang:",
        "Kyrgyz": "👋 *Кош келиңиз!* Сураныч, өз тилиңизди тандаңыз:"
    },
    "send_paragraph": {
        "English": (
            "📜 *Now, please send a paragraph in English* so I can evaluate your proficiency. "
            "Your paragraph can be on any topic of your choice—introduce yourself, describe your hobbies, "
            "or share a recent experience. Aim for at least 4-5 sentences to demonstrate your grammar, vocabulary, and fluency.\n\n"
        ),
        "Russian": (
            "📜 *Теперь отправьте абзац на английском языке*, чтобы я мог оценить ваш уровень владения языком. "
            "Вы можете выбрать любую тему: представьтесь, расскажите о своих увлечениях или поделитесь недавним опытом. "
            "Постарайтесь написать минимум 4-5 предложений.\n\n"
        ),
        "Kazakh": (
            "📜 *Енді ағылшын тілінде бір абзац жіберіңіз*, мен сіздің деңгейіңізді бағалай аламын. "
            "Кез келген тақырыпты таңдауға болады.\n\n"
        ),
        "Uzbek": (
            "📜 *Iltimos, endi ingliz tilida bir parcha matn yuboring*, shunda men sizning til darajangizni baholay olaman. "
            "Kamida 4-5 jumla yozing.\n\n"
        ),
        "Kyrgyz": (
            "📜 *Эми англис тилинде бир абзац жибериңиз*, ошондо мен сиздин деңгээлиңизди баалай алам. "
            "Кеминде 4-5 сүйлөм жазып көрүңүз.\n\n"
        )
    },
    "assessing": {
        "English": "⏳ *Assessing your English...* Please wait.",
        "Russian": "⏳ *Оцениваю ваш английский...* Пожалуйста, подождите.",
        "Kazakh": "⏳ *Ағылшын тіліңізді бағалап жатырмын...* Күте тұрыңыз.",
        "Uzbek": "⏳ *Ingliz tilingizni baholayapman...* Iltimos, kuting.",
        "Kyrgyz": "⏳ *Англис тилиңизди баалап жатам...* Сураныч, күтүп туруңуз."
    },
    "assessment_results": {
        "English": "📊 *Your English Assessment Result:*\n\n",
        "Russian": "📊 *Результаты оценки:*\n\n",
        "Kazakh": "📊 *Бағалау нәтижелері:*\n\n",
        "Uzbek": "📊 *Sizning ingliz tilini baholash natijalaringiz:*\n\n",
        "Kyrgyz": "📊 *Сиздин англис тили баалоо жыйынтыктары:*\n\n"
    },
    "proficiency_level": {
        "English": "🌍 *Estimated Proficiency Level:* ",
        "Russian": "🌍 *Предположительный уровень:* ",
        "Kazakh": "🌍 *Болжамды деңгей:* ",
        "Uzbek": "🌍 *Taxminiy daraja:* ",
        "Kyrgyz": "🌍 *Болжолдуу деңгээл:* "
    },
    "error": {
        "English": "⚠️ *Error:* Unable to process assessment at this time. Please try again later.",
        "Russian": "⚠️ *Ошибка:* Невозможно обработать оценку сейчас. Попробуйте позже.",
        "Kazakh": "⚠️ *Қате:* Кейінірек қайталап көріңіз.",
        "Uzbek": "⚠️ *Xato:* Keyinroq urinib ko‘ring.",
        "Kyrgyz": "⚠️ *Ката:* Кийинчерээк аракет кылып көрүңүз."
    },
    "cancel": {
        "English": "❌ *Conversation canceled.* Type /start to begin again.",
        "Russian": "❌ *Разговор отменен.* Введите /start, чтобы начать заново.",
        "Kazakh": "❌ *Сөйлесу тоқтатылды.* /start жазыңыз.",
        "Uzbek": "❌ *Suhbat bekor qilindi.* /start ni yozing.",
        "Kyrgyz": "❌ *Сүйлөшүү токтотулду.* /start командасын териңиз."
    },
    "choose_option": {
        "English": "Please choose an option:",
        "Russian": "Пожалуйста, выберите опцию:",
        "Kazakh": "Опцияны таңдаңыз:",
        "Uzbek": "Iltimos, bir variantni tanlang:",
        "Kyrgyz": "Сураныч, вариант тандаңыз:"
    },
    "personalized_topics": {
        "English": "✅ *Your Personalized List of Topics:*",
        "Russian": "✅ *Ваш персонализированный список тем:*",
        "Kazakh": "✅ *Жеке тақырыптарыңыздың тізімі:*",
        "Uzbek": "✅ *Shaxsiy mavzular ro'yxati:*",
        "Kyrgyz": "✅ *Сиздин жеке темалар тизмеси:*"
    },
    "introduction_recorded": {
        "English": "✅ *Your introduction has been recorded.*\n\n👤 Name: {name}\n🎂 Age: {age}",
        "Russian": "✅ *Ваше представление записано.*\n\n👤 Имя: {name}\n🎂 Возраст: {age}",
        "Kazakh": "✅ *Сіздің таныстыруыңыз тіркелді.*\n\n👤 Есім: {name}\n🎂 Жас: {age}",
        "Uzbek": "✅ *Tanishuv yozib olindi.*\n\n👤 Ism: {name}\n🎂 Yosh: {age}",
        "Kyrgyz": "✅ *Тааныштырууңуз жазылды.*\n\n👤 Аты: {name}\n🎂 Жашы: {age}"
    },
    "introduction_error": {
        "English": "⚠️ *Could not extract name and age properly. Please try again.*",
        "Russian": "⚠️ *Не удалось определить имя и возраст.*",
        "Kazakh": "⚠️ *Аты-жөніңіз бен жасыңызды анықтай алмадым.*",
        "Uzbek": "⚠️ *Ism va yoshni aniqlay olmadim.*",
        "Kyrgyz": "⚠️ *Аты-жөнүн жана жашын аныктай алган жокмун.*"
    }
}
