"""
Веб-сервис по варианту 18 — "Онлайн-переводчик" (локальный микросервис-эмулятор).

Предоставляет REST-эндпоинты:
    GET  /health     — проверка готовности сервиса
    GET  /languages  — список поддерживаемых целевых языков
    POST /translate  — перевод переданного текста на выбранный язык

Реализация намеренно не зависит от внешних библиотек (только stdlib),
чтобы образ собирался быстро и без доступа к PyPI.
"""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os

PORT = int(os.environ.get("SERVICE_PORT", "5001"))

# ---------------- Словари перевода (эмулятор машинного перевода) ----------------

PHRASES = {
    "ru->en": {
        "здравствуйте": "hello",
        "привет": "hi",
        "добрый день": "good afternoon",
        "доброе утро": "good morning",
        "добрый вечер": "good evening",
        "к дела": "how are you",
        "спасибо": "thank you",
        "спасибо за помощь": "thank you for help",
        "до свидания": "goodbye",
        "пожалуйста": "you are welcome",
        "меня зовут": "my name is",
        "хорошего дня": "have a nice day",
    },
    "ru->de": {
        "здравствуйте": "hallo",
        "привет": "hallo",
        "добрый день": "guten tag",
        "доброе утро": "guten morgen",
        "добрый вечер": "guten abend",
        "спасибо": "danke",
        "спасибо за помощь": "danke für die hilfe",
        "до свидания": "auf wiedersehen",
        "пожалуйста": "bitte",
    },
    "ru->fr": {
        "здравствуйте": "bonjour",
        "привет": "salut",
        "добрый день": "bonjour",
        "доброе утро": "bonjour",
        "добрый вечер": "bonsoir",
        "спасибо": "merci",
        "до свидания": "au revoir",
        "пожалуйста": "je vous en prie",
    },
    "ru->es": {
        "здравствуйте": "hola",
        "привет": "hola",
        "добрый день": "buenos días",
        "доброе утро": "buenos días",
        "добрый вечер": "buenas noches",
        "спасибо": "gracias",
        "до свидания": "adiós",
        "пожалуйста": "de nada",
    },
    "en->ru": {
        "hello": "привет",
        "hi": "привет",
        "good morning": "доброе утро",
        "good afternoon": "добрый день",
        "good evening": "добрый вечер",
        "how are you": "как дела",
        "thank you": "спасибо",
        "thank you for help": "спасибо за помощь",
        "goodbye": "до свидания",
        "have a nice day": "хорошего дня",
        "my name is": "меня зовут",
    },
}

WORDS = {
    "ru->en": {
        "мир": "world", "человек": "person", "люди": "people", "день": "day",
        "ночь": "night", "время": "time", "год": "year", "дело": "business",
        "язык": "language", "слово": "word", "текст": "text", "перевод": "translation",
        "компьютер": "computer", "программа": "program", "данные": "data",
        "база": "database", "данных": "of data", "собака": "dog", "кот": "cat",
        "книга": "book", "город": "city", "дом": "house", "вода": "water",
        "еда": "food", "музыка": "music", "фильм": "movie", "работа": "work",
        "друг": "friend", "семья": "family", "школа": "school", "студент": "student",
        "и": "and", "или": "or", "я": "i", "мы": "we", "вы": "you", "он": "he",
        "она": "she", "это": "this", "не": "not", "да": "yes", "нет": "no",
    },
    "en->ru": {
        "world": "мир", "person": "человек", "people": "люди", "day": "день",
        "night": "ночь", "time": "время", "year": "год", "language": "язык",
        "word": "слово", "text": "текст", "translation": "перевод",
        "computer": "компьютер", "program": "программа", "data": "данные",
        "database": "база данных", "dog": "собака", "cat": "кот",
        "book": "книга", "city": "город", "house": "дом", "water": "вода",
        "food": "еда", "music": "музыка", "movie": "фильм", "work": "работа",
        "friend": "друг", "family": "семья", "school": "школа", "student": "студент",
        "docker": "докер", "application": "приложение", "service": "сервис",
        "and": "и", "or": "или", "i": "я", "we": "мы", "you": "вы",
        "he": "он", "she": "она", "this": "это", "not": "не", "yes": "да", "no": "нет",
        "my": "мой", "your": "твой", "is": "есть", "are": "есть",
    },
    "ru->de": {
        "мир": "welt", "человек": "mensch", "день": "tag", "ночь": "nacht",
        "время": "zeit", "год": "jahr", "язык": "sprache", "слово": "wort",
        "текст": "text", "книга": "buch", "город": "stadt", "дом": "haus",
        "вода": "wasser", "друг": "freund", "работа": "arbeit", "музыка": "musik",
    },
    "ru->fr": {
        "мир": "monde", "человек": "personne", "день": "jour", "ночь": "nuit",
        "время": "temps", "год": "an", "язык": "langue", "слово": "mot",
        "текст": "texte", "книга": "livre", "город": "ville", "дом": "maison",
        "вода": "eau", "друг": "ami", "работа": "travail", "музыка": "musique",
        "кошка": "chat", "собака": "chien", "и": "et", "я": "je", "мы": "nous",
    },
    "ru->es": {
        "мир": "mundo", "человек": "persona", "день": "día", "ночь": "noche",
        "время": "tiempo", "год": "año", "язык": "idioma", "слово": "palabra",
        "текст": "texto", "книга": "libro", "город": "ciudad", "дом": "casa",
        "вода": "agua", "друг": "amigo", "работа": "trabajo", "музыка": "música",
    },
}

SUPPORTED_LANGUAGES = {
    "en": "Английский",
    "de": "Немецкий",
    "fr": "Французский",
    "es": "Испанский",
    "ru": "Русский",
}


def detect_language(text: str) -> str:
    """Простейшее определение языка: кириллица -> ru, иначе -> en."""
    cyr = len(re.findall(r"[а-яё]", text.lower()))
    lat = len(re.findall(r"[a-z]", text.lower()))
    return "ru" if cyr >= lat else "en"


def translate_text(text: str, target_lang: str) -> tuple[str, str]:
    """Перевод текста на целевой язык. Возвращает (перевод, язык_оригинала)."""
    source_lang = detect_language(text)
    if target_lang == source_lang:
        return text, source_lang

    # Если перевод между неподдерживаемой парой языков — идём через русский/английский
    pair = f"{source_lang}->{target_lang}"
    if pair not in PHRASES and pair not in WORDS:
        if source_lang == "ru" and target_lang != "en":
            mid, _ = translate_text(text, "en")
            return translate_text(mid, target_lang)[0], source_lang
        if target_lang == "ru" and source_lang != "en":
            mid, _ = translate_text(text, "ru")
            return translate_text(mid, "en")[0], source_lang
        return text, source_lang

    lowered = text.lower().strip()

    # 1) Ищем целое словосочетание в словаре фраз (сначала — самые длинные)
    for phrase, translated in sorted(
        PHRASES.get(pair, {}).items(), key=lambda item: len(item[0]), reverse=True
    ):
        if phrase in lowered:
            # Заменяем найденную фразу, сохраняя регистр первого символа исходника
            idx = lowered.index(phrase)
            replacement = translated.capitalize() if text[idx:idx + 1].isupper() else translated
            text = text[:idx] + replacement + text[idx + len(phrase):]
            lowered = text.lower()

    # 2) Пословно переводим слова из словаря
    word_map = WORDS.get(pair, {})

    def replace_word(match: "re.Match[str]") -> str:
        raw = match.group(0)
        key = raw.lower()
        if key in word_map:
            translated = word_map[key]
            return translated.capitalize() if raw[:1].isupper() else translated
        return raw

    result = re.sub(r"[А-Яа-яA-Za-z]+", replace_word, text)
    return result, source_lang


# ---------------- HTTP-сервер (эндпоинты сервиса) ----------------

class TranslateHandler(BaseHTTPRequestHandler):
    server_version = "TranslatorWebService/1.0"

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # Разрешаем обращения с других контейнеров/браузера
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # CORS preflight
        self._send_json(204, {})

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "translator-web-service"})
        elif self.path == "/languages":
            self._send_json(200, {"languages": SUPPORTED_LANGUAGES})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/translate":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "Некорректный JSON"})
            return

        text = (data.get("text") or "").strip()
        target_lang = (data.get("target_lang") or "").lower()
        if not text:
            self._send_json(400, {"error": "Поле 'text' обязательно"})
            return
        if target_lang not in SUPPORTED_LANGUAGES:
            self._send_json(400, {
                "error": f"Неподдерживаемый язык: '{target_lang}'",
                "supported": list(SUPPORTED_LANGUAGES.keys()),
            })
            return

        translated, source_lang = translate_text(text, target_lang)
        self._send_json(200, {
            "original_text": text,
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "engine": "local-emulator v1.0",
        })

    def log_message(self, fmt: str, *args) -> None:
        print(f"[web-service] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), TranslateHandler)
    print(f"Web-сервис переводчика запущен на порту {PORT}")
    server.serve_forever()
