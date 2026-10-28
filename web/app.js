const $ = (selector) => document.querySelector(selector);
const screens = [$('#welcome-screen'), $('#loading-screen'), $('#browser-screen')];
const state = { api: null, data: null, history: [], progressTimer: null, scannedRoots: new Map() };

const icons = {
  reveal: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3h7v7M21 3l-9 9M19 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6"/></svg>',
  trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15M10 10v7M14 10v7"/></svg>',
  sparkle: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3ZM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/></svg>',
};

function show(screen) {
  screens.forEach((item) => item.classList.toggle('hidden', item !== screen));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);
}

function formatBytes(size) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = Number(size || 0);
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return index ? `${value.toFixed(1)} ${units[index]}` : `${Math.floor(value)} B`;
}

function shortPath(path) {
  const home = /^\/Users\/[^/]+/.test(path) ? path.replace(/^\/Users\/[^/]+/, '~') : path;
  return home.length > 78 ? `…${home.slice(-77)}` : home;
}

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.classList.add('show');
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => element.classList.remove('show'), 2800);
}

function renderScanningPieces() {
  $('#scan-pieces').innerHTML = [...state.scannedRoots.values()].slice(-18).map((name, index) => `<span class="scan-piece piece-tone-${index % 5}">${escapeHtml(name)}</span>`).join('');
}

async function updateScanStatus() {
  try {
    const status = await state.api.get_scan_status();
    $('#loading-current').textContent = `Scanning ${shortPath(status.current_path)}`;
    $('#loading-stats').textContent = `${formatBytes(status.bytes_scanned)} scanned · ${Number(status.files_scanned).toLocaleString()} files checked`;
    if (status.top_level) {
      const name = status.top_level.split('/').filter(Boolean).pop() || 'Home';
      state.scannedRoots.set(status.top_level, name);
      renderScanningPieces();
    }
  } catch (_) {
    // The scan can complete even if a live status update is unavailable.
  }
}

async function scan(root) {
  if (!state.api) return;
  state.history = [];
  state.scannedRoots = new Map();
  renderScanningPieces();
  show($('#loading-screen'));
  $('#loading-current').textContent = 'Preparing scan…';
  $('#loading-stats').textContent = '0 GB scanned';
  window.clearInterval(state.progressTimer);
  state.progressTimer = window.setInterval(updateScanStatus, 300);
  updateScanStatus();
  try {
    state.data = root ? await state.api.scan(root) : await state.api.scan();
    renderBrowser();
    show($('#browser-screen'));
  } catch (error) {
    show($('#welcome-screen'));
    toast(error.message || 'Could not scan this location.');
  } finally {
    window.clearInterval(state.progressTimer);
    state.progressTimer = null;
  }
}

function pieceClass(folder, index) {
  const maximum = Math.max(...state.data.folders.map((item) => item.size), 1);
  const ratio = folder.size / maximum;
  if (ratio > 0.65) return 'piece-xl';
  if (ratio > 0.28) return 'piece-lg';
  if (ratio > 0.09) return 'piece-md';
  return index % 3 === 0 ? 'piece-tall' : 'piece-sm';
}

function renderBrowser() {
  const { folder, folders, files, free_space: freeSpace, root } = state.data;
  const isRoot = folder.path === root;
  $('#folder-eyebrow').textContent = isRoot ? 'YOUR ACCOUNT' : shortPath(folder.path);
  $('#folder-name').textContent = isRoot ? 'Home' : folder.name;
  $('#folder-meta').textContent = `${folder.display_size} in this folder · ${freeSpace} free`;
  $('#back-button').classList.toggle('hidden', state.history.length === 0);
  $('#puzzle-grid').innerHTML = folders.length ? folders.map((folderEntry, index) => `
    <button class="puzzle-piece ${pieceClass(folderEntry, index)} tone-${index % 5}" data-folder="${escapeHtml(folderEntry.path)}" type="button">
      <span class="piece-label">${escapeHtml(folderEntry.name)}</span>
      <span class="size-badge">${escapeHtml(folderEntry.display_size)}</span>
    </button>`).join('') : '<p class="empty">No folders inside this level. The files below are the endpoint.</p>';
  $('#file-count').textContent = files.length ? `${files.length}${state.data.has_more_files ? '+' : ''} largest direct files` : '';
  $('#entry-list').innerHTML = files.length ? files.map((entry) => `
    <article class="entry-row">
      <div class="entry-main">
        <div class="entry-topline"><span class="entry-kind">${escapeHtml(entry.kind.toUpperCase())}</span><span class="size-badge">${escapeHtml(entry.display_size)}</span></div>
        <h3>${escapeHtml(entry.name)}</h3>
        <p>${escapeHtml(entry.guidance)}</p>
      </div>
      <div class="entry-actions">
        <button class="icon-button" data-action="reveal" data-path="${escapeHtml(entry.path)}" type="button" title="Reveal in Finder" aria-label="Reveal in Finder">${icons.reveal}</button>
        <button class="ask-button" data-action="ask" data-path="${escapeHtml(entry.path)}" type="button">${icons.sparkle}<span>Ask any AI</span></button>
        <button class="icon-button danger" data-action="trash" data-path="${escapeHtml(entry.path)}" type="button" title="Move to Trash" aria-label="Move to Trash">${icons.trash}</button>
      </div>
    </article>`).join('') : '<p class="empty">No direct files at this level.</p>';
}

async function openFolder(path) {
  try {
    state.history.push(state.data);
    state.data = await state.api.browse(path);
    renderBrowser();
  } catch (error) {
    state.history.pop();
    toast(error.message || 'Could not open this folder.');
  }
}

async function runEntryAction(action, path) {
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
        toast('Moved to Trash. Refreshing view…');
        state.data = await state.api.browse(state.data.folder.path);
        renderBrowser();
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
$('#back-button').addEventListener('click', () => {
  state.data = state.history.pop();
  renderBrowser();
});
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
$('#puzzle-grid').addEventListener('click', (event) => {
  const piece = event.target.closest('[data-folder]');
  if (piece) openFolder(piece.dataset.folder);
});
$('#entry-list').addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (button) runEntryAction(button.dataset.action, button.dataset.path);
});

window.addEventListener('pywebviewready', () => {
  state.api = window.pywebview.api;
  $('#scan-drive').disabled = false;
  $('#choose-folder').disabled = false;
});
