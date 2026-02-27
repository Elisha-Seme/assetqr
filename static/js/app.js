/* ── Toast ────────────────────────────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast toast--${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

/* ── Modal system ─────────────────────────────────────────────────────────── */
function openModal(id) {
  document.getElementById('modal-overlay').classList.add('open');
  document.getElementById(id).classList.add('open');
}

function closeAllModals() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
}

/* ── Category datalist ────────────────────────────────────────────────────── */
function populateCatList(cats) {
  const dl = document.getElementById('cat-list');
  if (!dl) return;
  dl.innerHTML = '';
  cats.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    dl.appendChild(opt);
  });
}

/* ── Asset Modal: Add ─────────────────────────────────────────────────────── */
function openAddModal() {
  document.getElementById('asset-modal-title').textContent = 'Add Asset';
  document.getElementById('edit-asset-db-id').value = '';
  clearAssetForm();
  openModal('asset-modal');
  setTimeout(() => document.getElementById('f-name').focus(), 80);
}

/* ── Asset Modal: Edit ────────────────────────────────────────────────────── */
async function openEditModal(id) {
  try {
    const res = await fetch(`/api/assets/${id}`);
    if (!res.ok) { toast('Failed to load asset', 'error'); return; }
    const a = await res.json();

    document.getElementById('asset-modal-title').textContent = 'Edit Asset';
    document.getElementById('edit-asset-db-id').value = id;
    document.getElementById('f-name').value          = a.name || '';
    document.getElementById('f-asset-id').value      = a.asset_id || '';
    document.getElementById('f-asset-id').readOnly   = true;
    document.getElementById('f-category').value      = a.category || '';
    document.getElementById('f-location').value      = a.location || '';
    document.getElementById('f-status').value        = a.status || 'active';
    document.getElementById('f-serial').value        = a.serial_number || '';
    document.getElementById('f-purchase-date').value = a.purchase_date || '';
    document.getElementById('f-description').value   = a.description || '';
    document.getElementById('f-notes').value         = a.notes || '';
    openModal('asset-modal');
  } catch(e) {
    toast('Error: ' + e.message, 'error');
  }
}

function clearAssetForm() {
  ['f-name','f-asset-id','f-category','f-location','f-serial',
   'f-purchase-date','f-description','f-notes'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.value = ''; el.readOnly = false; }
  });
  const st = document.getElementById('f-status');
  if (st) st.value = 'active';
}

/* ── Asset Modal: Save ────────────────────────────────────────────────────── */
async function saveAsset() {
  const id   = document.getElementById('edit-asset-db-id').value;
  const name = document.getElementById('f-name').value.trim();
  if (!name) { toast('Name is required', 'error'); document.getElementById('f-name').focus(); return; }

  const payload = {
    name:          name,
    asset_id:      document.getElementById('f-asset-id').value.trim(),
    category:      document.getElementById('f-category').value.trim(),
    location:      document.getElementById('f-location').value.trim(),
    status:        document.getElementById('f-status').value,
    serial_number: document.getElementById('f-serial').value.trim(),
    purchase_date: document.getElementById('f-purchase-date').value,
    description:   document.getElementById('f-description').value.trim(),
    notes:         document.getElementById('f-notes').value.trim(),
  };

  const saveBtn = document.querySelector('#asset-modal .btn-primary');
  saveBtn.disabled = true; saveBtn.textContent = 'Saving…';

  try {
    let res;
    if (id) {
      res = await fetch(`/api/assets/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/assets', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    }
    const data = await res.json();
    if (!res.ok) { toast(data.error || 'Save failed', 'error'); return; }
    toast(id ? 'Asset updated!' : 'Asset added!');
    closeAllModals();
    location.reload();
  } catch(e) {
    toast('Error: ' + e.message, 'error');
  } finally {
    saveBtn.disabled = false; saveBtn.textContent = 'Save Asset';
  }
}

/* ── Delete ───────────────────────────────────────────────────────────────── */
let _deleteId = null;
function openDeleteModal(id, name) {
  _deleteId = id;
  document.getElementById('delete-asset-name').textContent = name;
  openModal('delete-modal');
}

async function confirmDelete() {
  if (!_deleteId) return;
  const btn = document.querySelector('#delete-modal .btn-danger');
  btn.disabled = true; btn.textContent = 'Deleting…';
  try {
    const res  = await fetch(`/api/assets/${_deleteId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      toast('Asset deleted');
      closeAllModals();
      // Remove row from table without full reload
      const row = document.querySelector(`tr[data-id="${_deleteId}"]`);
      if (row) row.remove();
      updateCountLabel();
    } else {
      toast(data.error || 'Delete failed', 'error');
    }
  } catch(e) {
    toast('Error: ' + e.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Delete';
    _deleteId = null;
  }
}

function updateCountLabel() {
  const lbl  = document.getElementById('asset-count');
  const rows = document.querySelectorAll('#asset-table tbody tr').length;
  if (lbl) lbl.textContent = `${rows} asset${rows !== 1 ? 's' : ''}`;
}

/* ── QR Preview ───────────────────────────────────────────────────────────── */
let _qrAssetId = null;
function showQR(assetId, qrPath, name) {
  _qrAssetId = assetId;
  document.getElementById('qr-modal-title').textContent   = name;
  document.getElementById('qr-preview-img').src           = qrPath;
  document.getElementById('qr-preview-url').textContent   = window.location.origin + '/asset/' + assetId;
  const dl = document.getElementById('qr-download-btn');
  dl.href           = qrPath;
  dl.download       = `qr_${assetId}.png`;
  openModal('qr-modal');
}

function exportSingleLabel() {
  // Find the DB id from the table row with this asset_id
  const row = document.querySelector(`tr[data-asset-id="${_qrAssetId}"]`);
  if (row) {
    window.open(`/export/labels?ids=${row.dataset.id}`, '_blank');
  }
  closeAllModals();
}

/* ── Table selection ──────────────────────────────────────────────────────── */
function toggleAll(master) {
  document.querySelectorAll('.row-check').forEach(cb => cb.checked = master.checked);
  updateBulkBar();
}

function updateBulkBar() {
  const checked = document.querySelectorAll('.row-check:checked').length;
  const bar     = document.getElementById('bulk-bar');
  const cnt     = document.getElementById('bulk-count');
  if (!bar) return;
  if (checked > 0) {
    bar.style.display = '';
    cnt.textContent   = `${checked} selected`;
  } else {
    bar.style.display = 'none';
  }
  // Sync master checkbox
  const all = document.querySelectorAll('.row-check').length;
  const master = document.getElementById('select-all');
  if (master) {
    master.checked       = checked > 0 && checked === all;
    master.indeterminate = checked > 0 && checked < all;
  }
}

function getSelectedIds() {
  return Array.from(document.querySelectorAll('.row-check:checked'))
    .map(cb => cb.closest('tr').dataset.id)
    .filter(Boolean);
}

/* ── Export ───────────────────────────────────────────────────────────────── */
function exportAction(type, selectedOnly) {
  const ids  = selectedOnly ? getSelectedIds() : [];
  const url  = new URL(`/export/${type === 'pdf' ? 'pdf' : type}`, window.location.origin);
  // Pass current filters from URL
  const sp   = new URLSearchParams(window.location.search);
  ['q','cat','status'].forEach(k => { if (sp.get(k)) url.searchParams.set(k, sp.get(k)); });
  if (ids.length) url.searchParams.set('ids', ids.join(','));
  window.open(url.toString(), '_blank');
  // Close dropdown if open
  const m = document.getElementById('export-menu');
  if (m) m.classList.remove('open');
}

/* ── Bulk delete ──────────────────────────────────────────────────────────── */
async function bulkDelete() {
  const ids = getSelectedIds();
  if (!ids.length) return;
  if (!confirm(`Delete ${ids.length} selected asset(s)? This cannot be undone.`)) return;
  let ok = 0;
  for (const id of ids) {
    const res = await fetch(`/api/assets/${id}`, { method: 'DELETE' });
    const d   = await res.json();
    if (d.success) {
      const row = document.querySelector(`tr[data-id="${id}"]`);
      if (row) row.remove();
      ok++;
    }
  }
  toast(`${ok} asset${ok!==1?'s':''} deleted`);
  updateBulkBar();
  updateCountLabel();
}

/* ── Keyboard shortcuts ───────────────────────────────────────────────────── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAllModals();
  // Ctrl/Cmd+Enter in modal → save
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    if (document.getElementById('asset-modal').classList.contains('open')) saveAsset();
  }
});
