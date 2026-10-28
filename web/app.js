const $ = (selector) => document.querySelector(selector);
const screens = [$('#welcome-screen'), $('#loading-screen'), $('#dashboard-screen'), $('#detail-screen')];
const state = { api: null, data: null, category: null, progressTimer: null };

function show(screen) {
  screens.forEach((item) => item.classList.toggle('hidden', item !== screen));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);
}

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.classList.add('show');
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => element.classList.remove('show'), 2800);
}

function shortenPath(path) {
  const home = /^\/Users\/[^/]+/.test(path) ? path.replace(/^\/Users\/[^/]+/, '~') : path;
  return home.length > 74 ? `…${home.slice(-73)}` : home;
}

async function updateScanStatus() {
  try {
    const status = await state.api.get_scan_status();
    $('#loading-current').textContent = `Scanning ${shortenPath(status.current_path)}`;
    $('#loading-stats').textContent = `${status.folders_scanned.toLocaleString()} folders · ${status.files_scanned.toLocaleString()} files checked`;
  } catch (_) {
    // The scan remains useful even if the optional live status call is unavailable.
  }
}

async function scan(root) {
  if (!state.api) return;
  show($('#loading-screen'));
  $('#loading-copy').textContent = root ? `Scanning ${shortenPath(root)}.` : 'Scanning your user account. System folders are not included.';
  $('#loading-current').textContent = 'Preparing scan…';
  $('#loading-stats').textContent = '0 folders · 0 files checked';
  window.clearInterval(state.progressTimer);
  state.progressTimer = window.setInterval(updateScanStatus, 300);
  updateScanStatus();
  try {
    state.data = root ? await state.api.scan(root) : await state.api.scan();
    renderOverview();
    show($('#dashboard-screen'));
  } catch (error) {
    show($('#welcome-screen'));
    toast(error.message || 'Could not scan this location.');
  } finally {
    window.clearInterval(state.progressTimer);
    state.progressTimer = null;
  }
}

function renderOverview() {
  const { categories, free_space: freeSpace, root } = state.data;
  $('#free-space').textContent = freeSpace;
  $('#scan-root').textContent = `Scanned ${root}`;
  const [largest] = categories;
  $('#start-card').innerHTML = largest ? `
    <div class="eyebrow">START HERE</div>
    <h3>${escapeHtml(largest.name)} is using ${escapeHtml(largest.display_size)}</h3>
    <p>Open the biggest category first. You will see clear file or folder labels before you make a decision.</p>
    <button class="button primary" data-category="${escapeHtml(largest.name)}" type="button">Review ${escapeHtml(largest.name)} →</button>` : `
    <div class="eyebrow">SCAN COMPLETE</div><h3>No readable storage was found.</h3><p>Choose a different location or grant the desktop app access to more storage.</p>`;
  $('#category-grid').innerHTML = categories.map((category) => `
    <article class="category-card">
      <div><h3>${escapeHtml(category.name)}</h3><p>Review the largest items first.</p><button data-category="${escapeHtml(category.name)}" type="button">Review →</button></div>
      <div class="category-size">${escapeHtml(category.display_size)}</div>
    </article>`).join('');
}

function renderCategory(category) {
  state.category = category;
  const chunks = state.data.chunks.filter((chunk) => chunk.category === category.name);
  $('#category-name').textContent = category.name;
  $('#category-total').textContent = `${category.display_size} total. Largest readable chunks are first.`;
  $('#chunk-list').innerHTML = chunks.length ? chunks.map((chunk) => `
    <article class="chunk">
      <div>
        <div class="chunk-kind">${escapeHtml(chunk.kind.toUpperCase())}</div>
        <h3>${escapeHtml(chunk.name)}</h3>
        <p>${escapeHtml(chunk.guidance)}</p>
        <p class="path">${escapeHtml(chunk.parent)}</p>
      </div>
      <div>
        <div class="category-size">${escapeHtml(chunk.display_size)}</div>
        <div class="chunk-actions">
          <button data-action="reveal" data-path="${escapeHtml(chunk.path)}" type="button">Reveal</button>
          <button data-action="ask" data-path="${escapeHtml(chunk.path)}" type="button">Ask any AI</button>
          <button class="danger" data-action="trash" data-path="${escapeHtml(chunk.path)}" type="button">Move to Trash</button>
        </div>
      </div>
    </article>`).join('') : '<p class="empty">This category is spread across smaller items. No individual file or folder exceeded 100 MB.</p>';
  show($('#detail-screen'));
}

async function runChunkAction(action, path) {
  try {
    if (action === 'reveal') {
      await state.api.reveal(path);
      toast('Opened its location.');
    }
    if (action === 'ask') {
      $('#ai-prompt').value = await state.api.ai_prompt(path);
      $('#prompt-dialog').showModal();
    }
    if (action === 'trash') {
      const moved = await state.api.move_to_trash(path);
      if (moved) {
        toast('Moved to Trash. Refreshing storage…');
        scan(state.data.root);
      }
    }
  } catch (error) {
    toast(error.message || 'That action could not be completed.');
  }
}

$('#scan-drive').addEventListener('click', () => scan());
$('#choose-folder').addEventListener('click', async () => {
  try {
    const folder = await state.api.choose_folder();
    if (folder) scan(folder);
  } catch (error) { toast(error.message || 'Could not open the folder picker.'); }
});
$('#rescan').addEventListener('click', () => $('#choose-folder').click());
$('#home-button').addEventListener('click', () => show($('#welcome-screen')));
$('#back-to-overview').addEventListener('click', () => show($('#dashboard-screen')));
$('#close-prompt').addEventListener('click', () => $('#prompt-dialog').close());
$('#copy-prompt').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText($('#ai-prompt').value);
    toast('Prompt copied. No file content was included.');
  } catch (_) {
    $('#ai-prompt').select();
    document.execCommand('copy');
    toast('Prompt copied. No file content was included.');
  }
});
$('#start-card').addEventListener('click', (event) => {
  const button = event.target.closest('[data-category]');
  if (button) renderCategory(state.data.categories.find((category) => category.name === button.dataset.category));
});
$('#category-grid').addEventListener('click', (event) => {
  const button = event.target.closest('[data-category]');
  if (button) renderCategory(state.data.categories.find((category) => category.name === button.dataset.category));
});
$('#chunk-list').addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (button) runChunkAction(button.dataset.action, button.dataset.path);
});

window.addEventListener('pywebviewready', () => {
  state.api = window.pywebview.api;
  $('#scan-drive').disabled = false;
  $('#choose-folder').disabled = false;
});
