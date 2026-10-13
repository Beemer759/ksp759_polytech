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

// ---------------- Словарь: список слов, доступных для перевода ----------------
// Данные приходят от Web-сервиса через Backend (/api/vocabulary)
let vocabulary = []; // [{source, target, type, source_lang, target_lang}]

async function loadVocabulary() {
  const errorBox = $('vocabError');
  const body = $('vocabBody');
  errorBox.classList.add('hidden');

  try {
    const resp = await fetch('/api/vocabulary');
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);

    // Собираем плоский список и заполняем фильтр направлений
    const filter = $('vocabFilter');
    const pairs = Object.entries(data.pairs || {});
    for (const [pairKey, pair] of pairs) {
      for (const item of pair.items) {
        vocabulary.push({
          ...item,
          source_lang: pair.source_lang,
          target_lang: pair.target_lang,
          pair: pairKey,
        });
      }
      const option = document.createElement('option');
      option.value = pairKey;
      option.textContent = `${pair.source_lang.toUpperCase()} → ${pair.target_lang.toUpperCase()}`;
      filter.appendChild(option);
    }

    $('vocabCount').textContent =
      `Всего позиций в словаре: ${data.count} (направлений перевода: ${pairs.length})`;
    renderVocabulary();
  } catch (err) {
    body.innerHTML = '';
    errorBox.textContent = `Ошибка загрузки словаря: ${err.message}`;
    errorBox.classList.remove('hidden');
  }
}

function renderVocabulary() {
  const body = $('vocabBody');
  const pairFilter = $('vocabFilter').value;
  const search = $('vocabSearch').value.trim().toLowerCase();

  const rows = vocabulary.filter((item) => {
    if (pairFilter !== 'all' && item.pair !== pairFilter) return false;
    if (search && !item.source.toLowerCase().includes(search)
              && !item.target.toLowerCase().includes(search)) return false;
    return true;
  });

  body.innerHTML = '';

  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="4" class="empty">Ничего не найдено</td></tr>';
    return;
  }

  for (const item of rows) {
    const tr = document.createElement('tr');
    tr.className = 'clickable';
    tr.title = 'Нажмите, чтобы подставить слово в поле перевода';

    const source = document.createElement('td');
    source.textContent = item.source;

    const target = document.createElement('td');
    target.textContent = item.target;

    const pair = document.createElement('td');
    pair.textContent = `${item.source_lang} → ${item.target_lang}`;

    const type = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = 'badge' + (item.type === 'phrase' ? ' badge-phrase' : '');
    badge.textContent = item.type === 'phrase' ? 'фраза' : 'слово';
    type.appendChild(badge);

    // Клик по строке: подставляем слово и выбираем направление перевода
    tr.addEventListener('click', () => {
      $('sourceText').value = item.source;
      $('targetLang').value = item.target_lang;
      $('result').classList.add('hidden');
      $('sourceText').focus();
    });

    tr.append(source, target, pair, type);
    body.appendChild(tr);
  }
}

$('vocabFilter').addEventListener('change', renderVocabulary);
$('vocabSearch').addEventListener('input', renderVocabulary);

// Первичная загрузка словаря при открытии страницы
loadVocabulary();

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
