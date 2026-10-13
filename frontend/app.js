// Фронтенд переводчика (вариант 18).
// Все запросы идут на Backend через nginx-прокси /api -> http://backend:8000

const $ = (id) => document.getElementById(id);

// ---------------- Кнопка 2: перевод через Web-сервис (через Backend) ----------------
$('translateBtn').addEventListener('click', async () => {
  const text = $('sourceText').value.trim();
  const targetLang = $('targetLang').value;
  const errorBox = $('translateError');
  errorBox.classList.add('hidden');

  if (!text) {
    errorBox.textContent = 'Введите текст для перевода.';
    errorBox.classList.remove('hidden');
    return;
  }

  const btn = $('translateBtn');
  btn.disabled = true;
  btn.textContent = 'Переводим…';

  try {
    const resp = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target_lang: targetLang }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);

    $('resultText').textContent = data.translated_text;
    $('resultMeta').textContent =
      `Язык оригинала: ${data.source_lang} · Целевой язык: ${data.target_lang} · ` +
      `Запись #${data.id} сохранена в БД · Engine: ${data.engine}`;
    $('result').classList.remove('hidden');
  } catch (err) {
    errorBox.textContent = `Ошибка перевода: ${err.message}`;
    errorBox.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Перевести';
  }
});

// ---------------- Кнопка 1: история переводов из БД (через Backend) ----------------
async function loadHistory() {
  const errorBox = $('historyError');
  const list = $('historyList');
  errorBox.classList.add('hidden');
  list.innerHTML = '<p class="empty">Загрузка…</p>';

  try {
    const resp = await fetch('/api/history');
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);

    $('historyCount').textContent = `Записей в базе: ${data.count}`;
    list.innerHTML = '';

    if (!data.items.length) {
      list.innerHTML = '<p class="empty">История пуста — выполните первый перевод.</p>';
      return;
    }

    for (const item of data.items) {
      const el = document.createElement('div');
      el.className = 'history-item';

      const pair = document.createElement('div');
      pair.className = 'pair';

      const original = document.createElement('div');
      original.className = 'original';
      original.textContent = item.original_text;

      const translated = document.createElement('div');
      translated.className = 'translated';
      translated.textContent = item.translated_text;

      const when = document.createElement('div');
      when.className = 'when';
      when.textContent =
        `${item.source_lang} → ${item.target_lang} · ${new Date(item.created_at).toLocaleString('ru-RU')}`;

      pair.append(original, translated, when);

      // Удаление конкретной записи (CRUD: Delete)
      const del = document.createElement('button');
      del.className = 'btn btn-danger';
      del.textContent = 'Удалить';
      del.addEventListener('click', async () => {
        await fetch(`/api/history?id=${item.id}`, { method: 'DELETE' });
        loadHistory();
      });

      el.append(pair, del);
      list.appendChild(el);
    }
  } catch (err) {
    list.innerHTML = '';
    errorBox.textContent = `Ошибка загрузки истории: ${err.message}`;
    errorBox.classList.remove('hidden');
  }
}

$('historyBtn').addEventListener('click', loadHistory);

// Первичная загрузка истории при открытии страницы
loadHistory();
