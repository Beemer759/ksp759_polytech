"""
Backend лабораторной работы (вариант 18: Онлайн-переводчик).

REST API, которое:
  * связывает Frontend с внутренней СУБД (PostgreSQL) — CRUD с историей переводов;
  * интегрируется с отдельным Web-сервисом переводчика (container "web-service").

Эндпоинты:
  GET  /api/health      — проверка готовности (backend + БД)
  GET  /api/languages   — список поддерживаемых языков (проброс от web-сервиса)
  POST /api/translate   — перевод текста через web-сервис + сохранение в БД
  GET  /api/history     — история переводов из БД
  DELETE /api/history   — очистка истории
"""

import os
import time

import requests
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "host=db port=5432 dbname=translator_db user=postgres password=postgres",
)
WEB_SERVICE_URL = os.environ.get("WEB_SERVICE_URL", "http://web-service:5001")

app = Flask(__name__)

# ---------------- Пул соединений с СУБД (с ожиданием готовности БД) ----------------

pool = None
for attempt in range(60):
    try:
        pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
        print("[backend] Подключение к БД установлено")
        break
    except Exception as exc:  # БД ещё стартует
        print(f"[backend] Ожидание БД ({attempt + 1}/60): {exc}")
        time.sleep(2)

if pool is None:
    raise RuntimeError("Не удалось подключиться к БД")


def query(sql: str, params=None, fetch: bool = True, commit: bool = False):
    """Выполняет SQL-запрос через пул соединений."""
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            result = cur.fetchall() if fetch else None
        if commit:
            conn.commit()
        return result
    finally:
        pool.putconn(conn)


# ---------------- Эндпоинты REST API ----------------

@app.get("/api/health")
def health():
    """Проверка готовности backend и БД."""
    try:
        query("SELECT 1")
        db_ok = True
    except Exception as exc:
        db_ok = False
        return jsonify({"status": "degraded", "db": str(exc)}), 503
    return jsonify({"status": "ok", "db": "ok" if db_ok else "fail"}), 200


@app.get("/api/languages")
def languages():
    """Список поддерживаемых целевых языков (данные web-сервиса)."""
    try:
        resp = requests.get(f"{WEB_SERVICE_URL}/languages", timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as exc:
        return jsonify({"error": f"Web-сервис недоступен: {exc}"}), 502


@app.post("/api/translate")
def translate():
    """
    Перевод текста: Frontend -> Backend -> Web-сервис -> Backend -> БД.
    Сохраняет запись в таблицу translations и возвращает перевод.
    """
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    target_lang = (payload.get("target_lang") or "").lower()

    if not text:
        return jsonify({"error": "Поле 'text' обязательно"}), 400
    if not target_lang:
        return jsonify({"error": "Поле 'target_lang' обязательно"}), 400

    # Запрос к отдельному Web-сервису (по варианту 18 — переводчик)
    try:
        resp = requests.post(
            f"{WEB_SERVICE_URL}/translate",
            json={"text": text, "target_lang": target_lang},
            timeout=15,
        )
        resp.raise_for_status()
        translation = resp.json()
    except requests.RequestException as exc:
        return jsonify({"error": f"Web-сервис недоступен: {exc}"}), 502

    # Сохранение перевода в БД (CRUD: Create)
    row = query(
        """
        INSERT INTO translations (original_text, translated_text, source_lang, target_lang)
        VALUES (%s, %s, %s, %s)
        RETURNING id, original_text, translated_text, source_lang, target_lang, created_at
        """,
        (
            translation["original_text"],
            translation["translated_text"],
            translation["source_lang"],
            translation["target_lang"],
        ),
        commit=True,
    )[0]

    return jsonify({
        "id": row["id"],
        "original_text": row["original_text"],
        "translated_text": row["translated_text"],
        "source_lang": row["source_lang"],
        "target_lang": row["target_lang"],
        "created_at": row["created_at"].isoformat(),
        "engine": translation.get("engine", "unknown"),
    }), 201


@app.get("/api/history")
def history():
    """История переводов из БД (новые записи сверху)."""
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = query(
        """
        SELECT id, original_text, translated_text, source_lang, target_lang, created_at
        FROM translations
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (limit,),
    )
    return jsonify({
        "count": len(rows),
        "items": [
            {**row, "created_at": row["created_at"].isoformat()} for row in rows
        ],
    })


@app.delete("/api/history")
def clear_history():
    """
    Очистка истории переводов.
    Если передан параметр ?id=N — удаляется только указанная запись,
    иначе удаляется вся история.
    """
    record_id = request.args.get("id", type=int)
    if record_id is not None:
        query(
            "DELETE FROM translations WHERE id = %s",
            (record_id,),
            fetch=False,
            commit=True,
        )
        return jsonify({"status": "ok", "deleted_id": record_id}), 200
    query("DELETE FROM translations", fetch=False, commit=True)
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
