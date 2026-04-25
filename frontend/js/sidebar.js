// ============================================================
// sidebar.js — Injeta a sidebar e topbar em todas as páginas
// ============================================================

function injectLayout(pageId, pageTitle) {
  const sidebarHTML = `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <div class="logo-icon">💼</div>
          <div>
            <div class="logo-text">Fiscal Finance</div>
            <div class="logo-sub">Squad FISC</div>
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section-label">Principal</div>

        <a class="nav-item" data-page="dashboard" href="dashboard.html">
          <span class="nav-icon">📊</span> Dashboard
        </a>

        <div class="nav-section-label">Módulos</div>

        <a class="nav-item" data-page="produtos" href="produtos.html">
          <span class="nav-icon">📦</span> Produtos
        </a>

        <a class="nav-item" data-page="estoque" href="estoque.html">
          <span class="nav-icon">🏭</span> Estoque
        </a>

        <a class="nav-item" data-page="fiscal" href="fiscal.html">
          <span class="nav-icon">🧾</span> Fiscal
        </a>

        <a class="nav-item" data-page="caixa" href="caixa.html">
          <span class="nav-icon">💰</span> Fluxo de Caixa
        </a>

        <a class="nav-item" data-page="notas" href="notas.html">
          <span class="nav-icon">📄</span> Notas Fiscais
        </a>

        <div class="nav-section-label">Ferramentas</div>

        <a class="nav-item" data-page="api-tester" href="api-tester.html">
          <span class="nav-icon">🧪</span> API Tester
        </a>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar" id="sidebar-avatar">A</div>
          <div class="user-details">
            <div class="user-name" id="sidebar-user-name">Carregando...</div>
            <div class="user-role" id="sidebar-user-role">—</div>
          </div>
          <button class="btn-logout" title="Sair" onclick="handleLogout()">⏻</button>
        </div>
      </div>
    </aside>

    <div class="main-content">
      <header class="topbar">
        <span class="topbar-title" id="topbar-title">${pageTitle}</span>
        <div class="topbar-right">
          <span style="font-size:12px;color:var(--text-secondary);" id="topbar-clock"></span>
        </div>
      </header>
      <div class="page-content" id="page-content">
  `;

  // Injeta antes do conteúdo existente do body
  const body = document.body;
  const existingContent = body.innerHTML;
  body.innerHTML = `
    <div class="app-layout">
      ${sidebarHTML}
        ${existingContent}
      </div>
    </div>
  `;

  // Adiciona toast container
  const toastDiv = document.createElement('div');
  toastDiv.id = 'toast-container';
  document.body.appendChild(toastDiv);

  // Marca nav ativo
  setActiveNav(pageId);

  // Preenche dados do user
  fillUserSidebar();

  // Relógio no topbar
  function updateClock() {
    const el = document.getElementById('topbar-clock');
    if (el) el.textContent = new Date().toLocaleTimeString('pt-BR');
  }
  updateClock();
  setInterval(updateClock, 1000);
}

window.injectLayout = injectLayout;
