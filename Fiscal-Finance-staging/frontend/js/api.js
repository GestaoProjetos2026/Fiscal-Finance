// ============================================================
// api.js — Camada de comunicação com a API Flask
// Todas as chamadas HTTP do sistema passam por aqui
// FISC-MOD2-05: adiciona Usuarios + tratamento de 401/403
// ============================================================

const API_BASE = 'http://localhost:5000/v1/fisc';

// --- Token JWT (localStorage) --------------------------------
function getToken() {
  return localStorage.getItem('fisc_token');
}

function setToken(token) {
  localStorage.setItem('fisc_token', token);
}

function clearToken() {
  localStorage.removeItem('fisc_token');
  localStorage.removeItem('fisc_user');
}

function getUser() {
  try { return JSON.parse(localStorage.getItem('fisc_user')); }
  catch { return null; }
}

function setUser(user) {
  localStorage.setItem('fisc_user', JSON.stringify(user));
}

// --- Fetch base com headers automaticos ----------------------
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': token } : {}),
    ...(options.headers || {})
  };

  let res, json;
  try {
    res  = await fetch(`${API_BASE}${path}`, { ...options, headers });
    json = await res.json();
  } catch (err) {
    return {
      ok: false,
      status: 0,
      body: { status: 'error', data: null, message: 'Sem conexao com o servidor. Verifique se a API esta rodando.' }
    };
  }

  // 401: token invalido ou expirado — limpa sessao e redireciona para login
  if (res.status === 401) {
    clearToken();
    const isLoginPage = window.location.pathname.endsWith('index.html')
      || window.location.pathname === '/'
      || window.location.pathname === '';
    if (!isLoginPage) {
      window.location.href = 'index.html';
    }
    return { ok: false, status: 401, body: json };
  }

  // 403: sem permissão (RBAC)
  if (res.status === 403) {
    if (window.toast) window.toast(json.message || 'Acesso negado.', 'error');
    return { ok: false, status: 403, body: json };
  }

  return { ok: res.ok, status: res.status, body: json };
}

// --- AUTH ----------------------------------------------------
const Auth = {
  async login(email, senha) {
    return apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, senha })
    });
  },
  async logout() {
    const r = await apiFetch('/auth/logout', { method: 'POST' });
    clearToken();
    return r;
  },
  async me() {
    return apiFetch('/auth/me');
  }
};

// --- PRODUTOS ------------------------------------------------
const Produtos = {
  async listar(nome = '') {
    const q = nome ? `?nome=${encodeURIComponent(nome)}` : '';
    return apiFetch(`/products${q}`);
  },
  async buscar(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`);
  },
  async criar(dados) {
    return apiFetch('/products', {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },
  async editar(sku, dados) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`, {
      method: 'PUT',
      body: JSON.stringify(dados)
    });
  },
  async remover(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`, {
      method: 'DELETE'
    });
  }
};

// --- ESTOQUE -------------------------------------------------
// Saldo de estoque vem junto com os produtos (campo saldo_estoque)
const Estoque = {
  async listar() {
    return apiFetch('/products');
  },
  async buscar(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`);
  },
  async registrarEntrada(sku, quantidade, motivo) {
    return apiFetch('/stock/entry', {
      method: 'POST',
      body: JSON.stringify({ sku, quantidade, motivo })
    });
  }
};

// --- NOTA FISCAL ---------------------------------------------
const Notas = {
  async calcularIntencao(itens) {
    return apiFetch('/invoice/intent', {
      method: 'POST',
      body: JSON.stringify({ itens })
    });
  },
  async confirmar(numero, descricao, itens) {
    return apiFetch('/invoice/confirm', {
      method: 'POST',
      body: JSON.stringify({ numero, descricao, itens })
    });
  },
  async buscar(numero) {
    return apiFetch(`/invoice/${encodeURIComponent(numero)}`);
  }
};

// --- CAIXA ---------------------------------------------------
const Caixa = {
  async saldo() {
    return apiFetch('/cashflow/balance');
  },
  async extrato(from, to) {
    return apiFetch(`/cashflow/statement?from=${from}&to=${to}`);
  },
  async registrarDespesa(descricao, valor, data = null) {
    const body = { descricao, valor };
    if (data) body.data = data;
    return apiFetch('/cashflow/expense', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }
};

// --- USUARIOS (FISC-MOD2-05 — admin only) --------------------
const Usuarios = {
  async listar() {
    return apiFetch('/auth/users');
  },
  async criar(dados) {
    return apiFetch('/auth/users', {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },
  async editar(id, dados) {
    return apiFetch(`/auth/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados)
    });
  },
  async desativar(id) {
    return apiFetch(`/auth/users/${id}`, { method: 'DELETE' });
  },
  async permissoes() {
    return apiFetch('/auth/permissions');
  }
};

// --- Exporta globalmente -------------------------------------
window.API = { Auth, Produtos, Estoque, Notas, Caixa, Usuarios };
window.getToken    = getToken;
window.setToken    = setToken;
window.clearToken  = clearToken;
window.getUser     = getUser;
window.setUser     = setUser;
