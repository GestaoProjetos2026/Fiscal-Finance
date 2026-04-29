// ============================================================
// ui.js — Utilitários de interface: toasts, modais, loading
// ============================================================

// ─── Toast ────────────────────────────────────────────────────
function toast(msg, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-msg">${msg}</span>
  `;
  container.appendChild(el);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => el.classList.add('show'));
  });

  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 300);
  }, duration);
}

// ─── Modal ────────────────────────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// Fecha modal ao clicar fora
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// ─── Loading em botão ─────────────────────────────────────────
function setLoading(btn, loading) {
  if (loading) {
    btn._originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Aguarde...';
    btn.classList.add('btn-loading');
  } else {
    btn.disabled = false;
    btn.innerHTML = btn._originalText || btn.innerHTML;
    btn.classList.remove('btn-loading');
  }
}

// ─── Loading Global ───────────────────────────────────────────
function setGlobalLoading(active) {
  let overlay = document.querySelector('.loading-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner-lg"></div>';
    document.body.appendChild(overlay);
  }

  if (active) {
    overlay.classList.add('active');
  } else {
    overlay.classList.remove('active');
  }
}

// ─── Formata moeda ────────────────────────────────────────────
function formatBRL(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency', currency: 'BRL'
  }).format(value || 0);
}

// ─── Formata data ISO para pt-BR ──────────────────────────────
function formatDate(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  if (isNaN(d)) return isoStr;
  return d.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

// ─── Guard de autenticação ────────────────────────────────────
function requireAuth() {
  if (!getToken()) {
    window.location.href = 'index.html';
    return false;
  }
  return true;
}

// ─── Preenche dados do usuário na sidebar ─────────────────────
function fillUserSidebar() {
  const user = getUser();
  if (!user) return;

  const nameEl = document.getElementById('sidebar-user-name');
  const roleEl = document.getElementById('sidebar-user-role');
  const avatarEl = document.getElementById('sidebar-avatar');

  if (nameEl) nameEl.textContent = user.nome || 'Usuário';
  if (roleEl) roleEl.textContent = user.papel || 'usuario';
  if (avatarEl) avatarEl.textContent = (user.nome || 'U')[0].toUpperCase();
}

// ─── Logout ───────────────────────────────────────────────────
async function handleLogout() {
  try { await API.Auth.logout(); } catch {}
  clearToken();
  window.location.href = 'index.html';
}

// ─── Nav ativo ───────────────────────────────────────────────
function setActiveNav(page) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
}

// ─── Estado vazio de tabela ───────────────────────────────────
function emptyRow(cols, msg = 'Nenhum registro encontrado.') {
  return `<tr><td colspan="${cols}" style="text-align:center;padding:36px;color:var(--text-secondary);">${msg}</td></tr>`;
}

// Exporta globalmente
window.toast = toast;
window.openModal = openModal;
window.closeModal = closeModal;
window.setLoading = setLoading;
window.setGlobalLoading = setGlobalLoading;
window.formatBRL = formatBRL;
window.formatDate = formatDate;
window.requireAuth = requireAuth;
window.fillUserSidebar = fillUserSidebar;
window.handleLogout = handleLogout;
window.setActiveNav = setActiveNav;
window.emptyRow = emptyRow;
