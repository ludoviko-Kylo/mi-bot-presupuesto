// Gestión de estado y persistencia en LocalStorage
const STORAGE_KEY = 'mi_presupuesto_transactions_v1';
const PREFS_KEY = 'mi_presupuesto_prefs_v1';
const API_URL_KEY = 'mi_presupuesto_api_url';

// Obtiene la URL base de la API (Render, Railway, Cloudflare, etc.)
function getApiBaseUrl() {
  // 1. Prioridad: Guardado por el usuario en localStorage
  const saved = localStorage.getItem(API_URL_KEY);
  if (saved && saved.trim()) {
    return saved.trim().replace(/\/+$/, '');
  }

  // 2. Configurado en js/config.js (VITE_API_URL, REACT_APP_API_URL, window.ENV_API_URL)
  if (window.APP_CONFIG && window.APP_CONFIG.API_URL && window.APP_CONFIG.API_URL.trim()) {
    return window.APP_CONFIG.API_URL.trim().replace(/\/+$/, '');
  }

  // 3. Fallback: Cadena vacía (utiliza rutas relativas en el mismo servidor)
  return '';
}

// Helpers para formato local de fecha y hora
function getLocalDateString(d = new Date()) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getLocalTimeString(d = new Date()) {
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

// Generador de datos semilla realistas basados en la fecha actual
function getInitialSeedData() {
  const now = new Date();
  const today = getLocalDateString(now);
  const time = getLocalTimeString(now);
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');

  return [
    {
      id: 'tx_seed_1',
      type: 'income',
      amount: 2850.00,
      category: 'salario',
      concept: 'Nómina Mensual',
      date: `${year}-${month}-01`,
      time: '09:00',
      created_at: `${year}-${month}-01 09:00:00`,
      datetime: `${year}-${month}-01T09:00:00`,
      notes: 'Transferencia bancaria principal'
    },
    {
      id: 'tx_seed_2',
      type: 'income',
      amount: 450.00,
      category: 'freelance',
      concept: 'Diseño Web Cliente',
      date: `${year}-${month}-05`,
      time: '14:30',
      created_at: `${year}-${month}-05 14:30:00`,
      datetime: `${year}-${month}-05T14:30:00`,
      notes: 'Pago por proyecto freelance'
    },
    {
      id: 'tx_seed_3',
      type: 'expense',
      amount: 750.00,
      category: 'vivienda',
      concept: 'Alquiler y Gastos Comunes',
      date: `${year}-${month}-02`,
      time: '10:15',
      created_at: `${year}-${month}-02 10:15:00`,
      datetime: `${year}-${month}-02T10:15:00`,
      notes: 'Pago mensual de departamento'
    },
    {
      id: 'tx_seed_4',
      type: 'expense',
      amount: 320.50,
      category: 'alimentacion',
      concept: 'Supermercado Mensual',
      date: `${year}-${month}-04`,
      time: '18:45',
      created_at: `${year}-${month}-04 18:45:00`,
      datetime: `${year}-${month}-04T18:45:00`,
      notes: 'Compras de despensa para el mes'
    },
    {
      id: 'tx_seed_5',
      type: 'expense',
      amount: 85.00,
      category: 'transporte',
      concept: 'Abono de Transporte y Combustible',
      date: `${year}-${month}-08`,
      time: '08:20',
      created_at: `${year}-${month}-08 08:20:00`,
      datetime: `${year}-${month}-08T08:20:00`,
      notes: 'Recarga tarjeta de metro'
    },
    {
      id: 'tx_seed_6',
      type: 'expense',
      amount: 65.00,
      category: 'ocio',
      concept: 'Cena con amigos y Cine',
      date: today,
      time: time.substring(0, 5),
      created_at: `${today} ${time}`,
      datetime: `${today}T${time}`,
      notes: 'Salida del día de hoy'
    }
  ];
}

class TransactionStore {
  constructor() {
    this.currency = 'S/';
    this.transactions = [];
    this.listeners = [];
    this.lastHash = '';
    
    // Carga inicial inmediata
    this.init();
  }

  init() {
    // 1. Carga inmediata desde objeto local embebido (soporta protocolo file:// y offline)
    if (window.LOCAL_TRANSACTIONS) {
      this.parsePayload(window.LOCAL_TRANSACTIONS);
    }

    // 2. Carga directa desde transacciones.json vía fetch
    this.loadFromJSON();

    // 3. Fallback de localStorage si aún no hay datos
    if (this.transactions.length === 0) {
      const stored = this.loadFromStorage();
      if (stored && stored.length > 0) {
        this.transactions = stored;
      }
    }

    // 4. Iniciar sincronización periódica (cada 3 segundos) para reflejar gastos del bot en vivo
    this.startAutoSync();
  }

  parsePayload(payload) {
    if (!payload) return false;
    let list = [];
    if (Array.isArray(payload)) {
      list = payload;
    } else if (payload.transactions && Array.isArray(payload.transactions)) {
      list = payload.transactions;
      if (payload.currency) {
        this.currency = payload.currency;
      }
    }

    // Normalizar movimientos para que siempre tengan fecha y hora válidos
    list = list.map(tx => {
      const date = tx.date || (tx.created_at ? tx.created_at.substring(0, 10) : getLocalDateString());
      const time = tx.time || (tx.created_at && tx.created_at.length >= 16 ? tx.created_at.substring(11, 16) : '00:00');
      const createdAt = tx.created_at || `${date} ${time}:00`;
      return {
        ...tx,
        date,
        time,
        created_at: createdAt,
        datetime: tx.datetime || `${date}T${time}:00`
      };
    });

    const newHash = JSON.stringify(list);
    if (newHash !== this.lastHash) {
      this.lastHash = newHash;
      this.transactions = list;
      this.saveToStorage(list);
      return true;
    }
    return false;
  }

  async loadFromJSON() {
    try {
      const apiBase = getApiBaseUrl();
      const url = `${apiBase}/transacciones.json?_t=${Date.now()}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const hasChanges = this.parsePayload(data);
        if (hasChanges) {
          this.notifyListeners();
          return true;
        }
      }
    } catch (e) {
      // Ignorar de forma silenciosa en caso de error de red o file://
    }
    return false;
  }

  startAutoSync() {
    // Sondear periódicamente si estamos sobre HTTP o si hay una API configurada
    const shouldSync = window.location.protocol.startsWith('http') || Boolean(getApiBaseUrl());
    if (shouldSync) {
      setInterval(async () => {
        await this.loadFromJSON();
      }, 3000);
    }
  }

  getApiUrl() {
    return getApiBaseUrl();
  }

  setApiUrl(url) {
    const clean = (url || '').trim().replace(/\/+$/, '');
    if (clean) {
      localStorage.setItem(API_URL_KEY, clean);
    } else {
      localStorage.removeItem(API_URL_KEY);
    }
    this.loadFromJSON();
    this.notifyListeners();
  }

  subscribe(listener) {
    if (typeof listener === 'function') {
      this.listeners.push(listener);
    }
  }

  notifyListeners() {
    this.listeners.forEach(fn => {
      try {
        fn();
      } catch (err) {
        console.error('Error en listener de sincronización:', err);
      }
    });
  }

  loadCurrency() {
    return this.currency || 'S/';
  }

  setCurrency(symbol) {
    this.currency = symbol;
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify({ currency: symbol }));
    } catch (e) {
      console.warn('Error al guardar preferencias:', e);
    }
  }

  loadFromStorage() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (data) {
        return JSON.parse(data);
      }
    } catch (e) {
      console.error('Error al leer de localStorage:', e);
    }
    return [];
  }

  saveToStorage(transactions) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(transactions));
    } catch (e) {
      console.error('Error al guardar en localStorage:', e);
    }
  }

  getAll() {
    // Retorna ordenado por fecha y hora descendente
    return [...this.transactions].sort((a, b) => {
      const timeA = a.created_at || (a.date + ' ' + (a.time || '00:00:00'));
      const timeB = b.created_at || (b.date + ' ' + (b.time || '00:00:00'));
      return timeB.localeCompare(timeA);
    });
  }

  getById(id) {
    return this.transactions.find(tx => tx.id === id);
  }

  // Filtrado por período temporal sin alterar la base de datos
  getFilteredByPeriod(period = 'today', customDate = null) {
    const list = this.getAll();
    const now = new Date();
    const todayStr = getLocalDateString(now);

    if (period === 'today') {
      return list.filter(tx => tx.date === todayStr);
    }

    if (period === 'yesterday') {
      const y = new Date(now);
      y.setDate(y.getDate() - 1);
      const yesterdayStr = getLocalDateString(y);
      return list.filter(tx => tx.date === yesterdayStr);
    }

    if (period === 'this_week') {
      const dayOfWeek = now.getDay();
      const diffToMonday = (dayOfWeek + 6) % 7;
      const monday = new Date(now);
      monday.setDate(now.getDate() - diffToMonday);
      const mondayStr = getLocalDateString(monday);

      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      const sundayStr = getLocalDateString(sunday);

      return list.filter(tx => tx.date && tx.date >= mondayStr && tx.date <= sundayStr);
    }

    if (period === 'this_month') {
      const monthPrefix = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
      return list.filter(tx => tx.date && tx.date.startsWith(monthPrefix));
    }

    if (period === 'custom' && customDate) {
      return list.filter(tx => tx.date === customDate);
    }

    // 'all'
    return list;
  }

  async add(transaction) {
    const now = new Date();
    const dateStr = transaction.date || getLocalDateString(now);
    const timeStr = transaction.time ? (transaction.time.length === 5 ? transaction.time + ':00' : transaction.time) : getLocalTimeString(now);
    const fullDateTime = `${dateStr} ${timeStr}`;

    const newTx = {
      id: 'tx_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
      type: transaction.type, // 'income' | 'expense'
      amount: parseFloat(transaction.amount) || 0,
      category: transaction.category,
      concept: transaction.concept.trim(),
      date: dateStr,
      time: timeStr.substring(0, 5),
      created_at: fullDateTime,
      datetime: fullDateTime,
      timestamp: new Date(`${dateStr}T${timeStr}`).getTime() || now.getTime(),
      notes: transaction.notes ? transaction.notes.trim() : ''
    };

    this.transactions.unshift(newTx);
    this.saveToStorage(this.transactions);

    // Persistir en backend (remoto o local)
    const apiBase = getApiBaseUrl();
    const shouldSend = window.location.protocol.startsWith('http') || Boolean(apiBase);
    if (shouldSend) {
      try {
        await fetch(`${apiBase}/api/transactions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: newTx.type,
            amount: newTx.amount,
            category: newTx.category,
            concept: newTx.concept,
            description: newTx.notes,
            created_at: fullDateTime
          })
        });
      } catch (err) {
        console.warn('Error al guardar movimiento en backend:', err);
      }
    }

    this.notifyListeners();
    return newTx;
  }

  update(id, updatedData) {
    const index = this.transactions.findIndex(tx => tx.id === id);
    if (index === -1) return null;

    const existing = this.transactions[index];
    const dateStr = updatedData.date || existing.date;
    const timeStr = updatedData.time || existing.time || '12:00';
    const fullDateTime = `${dateStr} ${timeStr.length === 5 ? timeStr + ':00' : timeStr}`;

    this.transactions[index] = {
      ...existing,
      type: updatedData.type,
      amount: parseFloat(updatedData.amount) || 0,
      category: updatedData.category,
      concept: updatedData.concept.trim(),
      date: dateStr,
      time: timeStr.substring(0, 5),
      created_at: fullDateTime,
      datetime: fullDateTime,
      notes: updatedData.notes ? updatedData.notes.trim() : ''
    };

    this.saveToStorage(this.transactions);
    this.notifyListeners();
    return this.transactions[index];
  }

  async delete(id) {
    const initialLen = this.transactions.length;
    this.transactions = this.transactions.filter(tx => tx.id !== id);
    this.saveToStorage(this.transactions);

    const apiBase = getApiBaseUrl();
    const shouldSend = window.location.protocol.startsWith('http') || Boolean(apiBase);
    if (shouldSend) {
      try {
        await fetch(`${apiBase}/api/transactions/${id}`, {
          method: 'DELETE'
        });
      } catch (err) {
        console.warn('Error al borrar en backend:', err);
      }
    }

    this.notifyListeners();
    return this.transactions.length < initialLen;
  }

  resetSeedData() {
    const seeds = getInitialSeedData();
    this.transactions = seeds;
    this.saveToStorage(this.transactions);
    this.notifyListeners();
    return seeds;
  }

  async clearAll() {
    this.transactions = [];
    this.lastHash = JSON.stringify([]);
    this.saveToStorage(this.transactions);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Error al limpiar localStorage:', e);
    }

    if (window.LOCAL_TRANSACTIONS) {
      window.LOCAL_TRANSACTIONS = {
        currency: this.currency,
        last_updated: new Date().toISOString(),
        total_count: 0,
        transactions: []
      };
    }

    // Enviar DELETE al backend (remoto o local) para borrar físicamente
    const apiBase = getApiBaseUrl();
    const shouldSend = window.location.protocol.startsWith('http') || Boolean(apiBase);
    if (shouldSend) {
      try {
        await fetch(`${apiBase}/api/transactions`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (err) {
        console.warn('Error al enviar DELETE /api/transactions:', err);
      }
    }

    this.notifyListeners();
  }

  // Métricas acumuladas para una lista de transacciones o el total
  getMetrics(txList = null) {
    const list = txList !== null ? txList : this.transactions;
    let totalIncome = 0;
    let totalExpense = 0;

    list.forEach(tx => {
      const amt = parseFloat(tx.amount) || 0;
      if (tx.type === 'income') {
        totalIncome += amt;
      } else if (tx.type === 'expense') {
        totalExpense += amt;
      }
    });

    const balance = totalIncome - totalExpense;
    const savingsRate = totalIncome > 0 ? Math.max(0, ((totalIncome - totalExpense) / totalIncome) * 100) : 0;

    return {
      balance,
      totalIncome,
      totalExpense,
      savingsRate: Math.round(savingsRate * 10) / 10
    };
  }

  // Agrupado de gastos por categoría
  getExpensesByCategory(txList = null) {
    const list = (txList !== null ? txList : this.transactions).filter(tx => tx.type === 'expense');
    const categoryTotals = {};

    list.forEach(tx => {
      const cat = tx.category;
      const amt = parseFloat(tx.amount) || 0;
      categoryTotals[cat] = (categoryTotals[cat] || 0) + amt;
    });

    return categoryTotals;
  }

  // Agrupado mensual de ingresos y gastos (últimos 6 meses)
  getMonthlyHistory(monthsCount = 6) {
    const months = [];
    const now = new Date();

    for (let i = monthsCount - 1; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      const label = d.toLocaleDateString('es-ES', { month: 'short' });
      months.push({ key, label: label.charAt(0).toUpperCase() + label.slice(1) });
    }

    const incomeMap = {};
    const expenseMap = {};
    months.forEach(m => {
      incomeMap[m.key] = 0;
      expenseMap[m.key] = 0;
    });

    this.transactions.forEach(tx => {
      if (!tx.date) return;
      const monthKey = tx.date.substring(0, 7);
      if (incomeMap[monthKey] !== undefined && tx.type === 'income') {
        incomeMap[monthKey] += parseFloat(tx.amount) || 0;
      } else if (expenseMap[monthKey] !== undefined && tx.type === 'expense') {
        expenseMap[monthKey] += parseFloat(tx.amount) || 0;
      }
    });

    return {
      labels: months.map(m => m.label),
      incomes: months.map(m => incomeMap[m.key]),
      expenses: months.map(m => expenseMap[m.key])
    };
  }

  // Exportar a CSV
  exportToCSV() {
    if (this.transactions.length === 0) return null;

    const headers = ['ID', 'Tipo', 'Concepto', 'Monto', 'Categoría', 'Fecha', 'Hora', 'Notas'];
    const rows = this.transactions.map(tx => {
      const cat = getCategoryById(tx.category, tx.type);
      return [
        tx.id,
        tx.type === 'income' ? 'Ingreso' : 'Gasto',
        `"${(tx.concept || '').replace(/"/g, '""')}"`,
        tx.amount,
        `"${cat.name}"`,
        tx.date,
        tx.time || '',
        `"${(tx.notes || '').replace(/"/g, '""')}"`
      ];
    });

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    return csvContent;
  }
}

// Instancia global
const store = new TransactionStore();
