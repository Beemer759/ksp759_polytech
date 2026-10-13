-- ============================================================
-- Вариант 18: Онлайн-переводчик
-- Первичная инициализация схемы и начальных данных БД
-- ============================================================

-- Таблица истории переводов
CREATE TABLE IF NOT EXISTS translations (
    id              SERIAL PRIMARY KEY,
    original_text   TEXT NOT NULL,                       -- Исходный текст
    translated_text TEXT NOT NULL,                       -- Перевод
    source_lang     VARCHAR(10) NOT NULL DEFAULT 'auto', -- Язык оригинала
    target_lang     VARCHAR(10) NOT NULL,                -- Целевой язык
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()   -- Время перевода
);

-- Индекс для быстрой выборки истории (новые сверху)
CREATE INDEX IF NOT EXISTS idx_translations_created_at
    ON translations (created_at DESC);

-- Начальные (первичные) данные — примеры сохранённых переводов
INSERT INTO translations (original_text, translated_text, source_lang, target_lang) VALUES
    ('Добрый день!',            'Good afternoon!',       'ru', 'en'),
    ('Как дела?',               'How are you?',          'ru', 'en'),
    ('Спасибо за помощь',       'Thank you for help',    'ru', 'en'),
    ('Good morning',            'Доброе утро',           'en', 'ru'),
    ('Docker Compose is great', 'Docker Compose — отлично', 'en', 'ru');
