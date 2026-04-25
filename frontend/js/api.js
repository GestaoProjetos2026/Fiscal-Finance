// ============================================================
// api.js — Camada de comunicação com a API Flask
// Todas as chamadas HTTP do sistema passam por aqui
// ============================================================

const API_BASE = 'http://localhost:5000/v1/fisc';

// ─── Token JWT (localStorage) ────────────────────────────────
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

// ─── Fetch base com headers automáticos ──────────────────────
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': token } : {}),
    ...(options.headers || {})
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  const json = await res.json();
  return { ok: res.ok, status: res.status, body: json };
}

// ─── AUTH ─────────────────────────────────────────────────────
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

// ─── PRODUTOS ─────────────────────────────────────────────────
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

// ─── ESTOQUE ──────────────────────────────────────────────────
// O estoque usa os mesmos endpoints de produtos (saldo_estoque vem junto)
// Movimentações via invoice/confirm (saída) e endpoint futuro de entrada
const Estoque = {
  async listar() {
    return apiFetch('/products');
  },
  async buscar(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`);
  }
};

// ─── NOTA FISCAL ──────────────────────────────────────────────
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

// ─── CAIXA ────────────────────────────────────────────────────
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

// ─── Exporta globalmente ──────────────────────────────────────
window.API = { Auth, Produtos, Estoque, Notas, Caixa };
window.getToken = getToken;
window.setToken = setToken;
window.clearToken = clearToken;
window.getUser = getUser;
window.setUser = setUser;
