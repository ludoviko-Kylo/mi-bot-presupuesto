// Controlador principal de la aplicación de presupuesto
class AppController {
  constructor() {
    // Período activo superior: 'today' por defecto
    this.currentPeriod = 'today';
    this.customDate = null;

    this.currentFilters = {
      search: '',
      type: 'all',
      category: 'all',
      month: 'all'
    };

    this.editingId = null;
    this.pendingDeleteId = null;

    this.init();
  }

  init() {
    this.bindEvents();
    this.populateMonthFilter();
    this.populateCategorySelect('expense'); // Default modal category type
    this.populateCategoryFilter();
    this.updatePeriodUI();
    this.updateCloudStatusBadge();

    // Actualización automática al recibir nuevos gastos o ingresos del bot de Telegram
    store.subscribe(() => {
      this.populateMonthFilter();
      this.populateCategoryFilter();
      this.render();
      console.log('🔄 Interfaz actualizada automáticamente desde transacciones.json');
    });

    this.render();
  }

  // Enlace de eventos del DOM
  bindEvents() {
    // Botón de nueva transacción
    const btnNewTx = document.getElementById('btnNewTransaction');
    if (btnNewTx) {
      btnNewTx.addEventListener('click', () => this.openTransactionModal());
    }

    // Botón cancelar / cerrar modal
    const btnCancelModal = document.getElementById('btnCancelModal');
    const btnCloseModalX = document.getElementById('btnCloseModalX');
    const modalBackdrop = document.getElementById('transactionModal');

    if (btnCancelModal) btnCancelModal.addEventListener('click', () => this.closeTransactionModal());
    if (btnCloseModalX) btnCloseModalX.addEventListener('click', () => this.closeTransactionModal());
    if (modalBackdrop) {
      modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) this.closeTransactionModal();
      });
    }

    // Toggle tipo en modal (Gasto vs Ingreso)
    const btnTypeExpense = document.getElementById('btnTypeExpense');
    const btnTypeIncome = document.getElementById('btnTypeIncome');

    if (btnTypeExpense && btnTypeIncome) {
      btnTypeExpense.addEventListener('click', () => this.setModalType('expense'));
      btnTypeIncome.addEventListener('click', () => this.setModalType('income'));
    }

    // Formulario de transacción
    const formTx = document.getElementById('transactionForm');
    if (formTx) {
      formTx.addEventListener('submit', (e) => this.handleSaveTransaction(e));
    }

    // Modal de confirmación de eliminación individual
    const btnConfirmDelete = document.getElementById('btnConfirmDelete');
    const btnCancelDelete = document.getElementById('btnCancelDelete');
    const deleteModal = document.getElementById('deleteConfirmModal');

    if (btnConfirmDelete) {
      btnConfirmDelete.addEventListener('click', () => this.handleConfirmDelete());
    }
    if (btnCancelDelete) {
      btnCancelDelete.addEventListener('click', () => this.closeDeleteModal());
    }
    if (deleteModal) {
      deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) this.closeDeleteModal();
      });
    }

    // Modal de Restablecimiento de Fábrica (Borrar todos los datos)
    const btnTopResetFactory = document.getElementById('btnTopResetFactory');
    const btnClearAll = document.getElementById('btnClearAll');
    const btnCancelFactoryReset = document.getElementById('btnCancelFactoryReset');
    const btnConfirmFactoryReset = document.getElementById('btnConfirmFactoryReset');
    const factoryResetModal = document.getElementById('factoryResetModal');

    if (btnTopResetFactory) {
      btnTopResetFactory.addEventListener('click', () => this.openFactoryResetModal());
    }
    if (btnClearAll) {
      btnClearAll.addEventListener('click', () => this.openFactoryResetModal());
    }
    if (btnCancelFactoryReset) {
      btnCancelFactoryReset.addEventListener('click', () => this.closeFactoryResetModal());
    }
    if (btnConfirmFactoryReset) {
      btnConfirmFactoryReset.addEventListener('click', () => this.handleConfirmFactoryReset());
    }
    if (factoryResetModal) {
      factoryResetModal.addEventListener('click', (e) => {
        if (e.target === factoryResetModal) this.closeFactoryResetModal();
      });
    }

    // Modal de Conexión en la Nube (API Remota)
    const btnCloudConfig = document.getElementById('btnCloudConfig');
    const btnCloseCloudModal = document.getElementById('btnCloseCloudModal');
    const btnTestCloudConnection = document.getElementById('btnTestCloudConnection');
    const btnSaveCloudConfig = document.getElementById('btnSaveCloudConfig');
    const cloudConfigModal = document.getElementById('cloudConfigModal');

    if (btnCloudConfig) {
      btnCloudConfig.addEventListener('click', () => this.openCloudModal());
    }
    if (btnCloseCloudModal) {
      btnCloseCloudModal.addEventListener('click', () => this.closeCloudModal());
    }
    if (btnTestCloudConnection) {
      btnTestCloudConnection.addEventListener('click', () => this.testCloudConnection());
    }
    if (btnSaveCloudConfig) {
      btnSaveCloudConfig.addEventListener('click', () => this.saveCloudConfig());
    }
    if (cloudConfigModal) {
      cloudConfigModal.addEventListener('click', (e) => {
        if (e.target === cloudConfigModal) this.closeCloudModal();
      });
    }

    // Selector de Períodos en Panel Superior (Hoy, Ayer, Esta semana, Este mes, Todo)
    const periodPills = document.querySelectorAll('.period-pill');
    periodPills.forEach(pill => {
      pill.addEventListener('click', () => {
        const period = pill.dataset.period;
        this.setPeriod(period);
      });
    });

    // Selector de Fecha Personalizada en Panel Superior
    const periodCustomDate = document.getElementById('periodCustomDate');
    if (periodCustomDate) {
      periodCustomDate.addEventListener('change', (e) => {
        if (e.target.value) {
          this.setPeriod('custom', e.target.value);
        }
      });
    }

    // Filtros de búsqueda en tabla
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.currentFilters.search = e.target.value.toLowerCase().trim();
        this.renderTableOnly();
      });
    }

    // Filtros de pestañas de tipo (Todos, Ingresos, Gastos)
    const typeFilterTabs = document.querySelectorAll('.type-filter-tab');
    typeFilterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        typeFilterTabs.forEach(t => {
          t.classList.remove('bg-white', 'text-slate-900', 'shadow-sm');
          t.classList.add('text-slate-500', 'hover:text-slate-800');
        });
        tab.classList.add('bg-white', 'text-slate-900', 'shadow-sm');
        tab.classList.remove('text-slate-500', 'hover:text-slate-800');

        this.currentFilters.type = tab.dataset.type;
        this.renderTableOnly();
      });
    });

    // Filtro por categoría en tabla
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
      categoryFilter.addEventListener('change', (e) => {
        this.currentFilters.category = e.target.value;
        this.renderTableOnly();
      });
    }

    // Filtro por mes en tabla
    const monthFilter = document.getElementById('monthFilter');
    if (monthFilter) {
      monthFilter.addEventListener('change', (e) => {
        this.currentFilters.month = e.target.value;
        this.render();
      });
    }

    // Botón restablecer filtros de la tabla
    const btnResetFilters = document.getElementById('btnResetFilters');
    if (btnResetFilters) {
      btnResetFilters.addEventListener('click', () => this.resetFilters());
    }

    // Selector de moneda
    const currencySelector = document.getElementById('currencySelector');
    if (currencySelector) {
      currencySelector.value = store.currency;
      currencySelector.addEventListener('change', (e) => {
        store.setCurrency(e.target.value);
        this.render();
        this.showToast(`Moneda cambiada a ${e.target.value}`, 'success');
      });
    }

    // Menú de opciones secundarias (Exportar, Semilla)
    const btnExportCSV = document.getElementById('btnExportCSV');
    if (btnExportCSV) {
      btnExportCSV.addEventListener('click', () => this.exportCSV());
    }

    const btnResetSeed = document.getElementById('btnResetSeed');
    if (btnResetSeed) {
      btnResetSeed.addEventListener('click', () => {
        if (confirm('¿Cargar datos demo de ejemplo? Se añadirán transacciones para pruebas.')) {
          store.resetSeedData();
          this.setPeriod('all');
          this.showToast('Datos de ejemplo cargados', 'success');
        }
      });
    }
  }

  // Cambio de período activo en el panel superior
  setPeriod(period, customDate = null) {
    this.currentPeriod = period;
    this.customDate = customDate;

    const periodCustomDate = document.getElementById('periodCustomDate');
    if (periodCustomDate && period !== 'custom') {
      periodCustomDate.value = '';
    }

    this.updatePeriodUI();
    this.render();
  }

  // Actualiza los estilos visuales del panel superior de período
  updatePeriodUI() {
    const periodPills = document.querySelectorAll('.period-pill');
    periodPills.forEach(pill => {
      const isCurrent = pill.dataset.period === this.currentPeriod;
      if (isCurrent) {
        pill.className = 'period-pill px-3 py-1.5 rounded-lg bg-white text-indigo-700 shadow-sm transition-all flex items-center gap-1.5 font-bold';
      } else {
        pill.className = 'period-pill px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5 font-medium';
      }
    });

    const activeLabel = document.getElementById('activePeriodLabel');
    const activeDesc = document.getElementById('activePeriodDescription');
    const balanceScope = document.getElementById('metricBalanceScope');
    const incomeScope = document.getElementById('metricIncomeScope');
    const expenseScope = document.getElementById('metricExpenseScope');

    const now = new Date();
    const optionsDate = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };

    let labelText = 'Hoy';
    let descText = 'Mostrando finanzas y balances de la jornada actual';
    let scopeText = '(de hoy)';

    if (this.currentPeriod === 'today') {
      labelText = 'Hoy';
      const formattedToday = now.toLocaleDateString('es-ES', optionsDate);
      descText = `Jornada del ${formattedToday}`;
      scopeText = '(de hoy)';
    } else if (this.currentPeriod === 'yesterday') {
      labelText = 'Ayer';
      const y = new Date(now);
      y.setDate(y.getDate() - 1);
      const formattedYesterday = y.toLocaleDateString('es-ES', optionsDate);
      descText = `Jornada del ${formattedYesterday}`;
      scopeText = '(de ayer)';
    } else if (this.currentPeriod === 'this_week') {
      labelText = 'Esta Semana';
      descText = 'Lunes a domingo de la semana en curso';
      scopeText = '(esta semana)';
    } else if (this.currentPeriod === 'this_month') {
      const monthName = now.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
      labelText = 'Este Mes';
      descText = `Movimientos de ${monthName}`;
      scopeText = '(este mes)';
    } else if (this.currentPeriod === 'custom' && this.customDate) {
      const [year, month, day] = this.customDate.split('-');
      const d = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      labelText = `${day}/${month}/${year}`;
      descText = `Día específico: ${d.toLocaleDateString('es-ES', optionsDate)}`;
      scopeText = `(${day}/${month})`;
    } else {
      labelText = 'Historial Completo';
      descText = 'Total histórico acumulado de todos los períodos';
      scopeText = '(acumulado)';
    }

    if (activeLabel) activeLabel.textContent = labelText;
    if (activeDesc) activeDesc.textContent = descText;
    if (balanceScope) balanceScope.textContent = scopeText;
    if (incomeScope) incomeScope.textContent = scopeText;
    if (expenseScope) expenseScope.textContent = scopeText;
  }

  // Formato monetario
  formatMoney(amount) {
    return `${store.currency} ${Number(amount).toLocaleString('es-ES', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  }

  // Llena el selector de meses con los meses presentes en el historial
  populateMonthFilter() {
    const monthFilter = document.getElementById('monthFilter');
    if (!monthFilter) return;

    const currentVal = monthFilter.value;
    const transactions = store.getAll();
    const monthsSet = new Set();

    transactions.forEach(tx => {
      if (tx.date) {
        monthsSet.add(tx.date.substring(0, 7)); // YYYY-MM
      }
    });

    const sortedMonths = Array.from(monthsSet).sort().reverse();
    monthFilter.innerHTML = '<option value="all">Todos los meses</option>';

    sortedMonths.forEach(m => {
      const [year, month] = m.split('-');
      const dateObj = new Date(parseInt(year), parseInt(month) - 1, 1);
      const label = dateObj.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
      const capitalized = label.charAt(0).toUpperCase() + label.slice(1);
      
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = capitalized;
      monthFilter.appendChild(opt);
    });

    if (sortedMonths.includes(currentVal)) {
      monthFilter.value = currentVal;
    }
  }

  // Llena el filtro de categorías en la barra de búsqueda
  populateCategoryFilter() {
    const categoryFilter = document.getElementById('categoryFilter');
    if (!categoryFilter) return;

    categoryFilter.innerHTML = '<option value="all">Todas las categorías</option>';

    const allCategories = [...CATEGORIES.expense, ...CATEGORIES.income];
    allCategories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat.id;
      opt.textContent = `${cat.type === 'income' ? '🟢' : '🔴'} ${cat.name}`;
      categoryFilter.appendChild(opt);
    });
  }

  // Llena el desplegable de categoría dentro del modal de crear/editar
  populateCategorySelect(type, selectedCategory = null) {
    const select = document.getElementById('txCategory');
    if (!select) return;

    const cats = getCategoriesByType(type);
    select.innerHTML = '';

    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      if (selectedCategory && selectedCategory === c.id) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });
  }

  // Cambiar entre pestaña Gasto / Ingreso en el modal
  setModalType(type) {
    const btnExpense = document.getElementById('btnTypeExpense');
    const btnIncome = document.getElementById('btnTypeIncome');
    const hiddenType = document.getElementById('txType');

    if (hiddenType) hiddenType.value = type;

    if (type === 'expense') {
      btnExpense.className = 'flex-1 py-2.5 text-xs font-semibold rounded-lg bg-rose-50 text-rose-700 border border-rose-200 transition-all flex items-center justify-center gap-1.5 shadow-sm';
      btnIncome.className = 'flex-1 py-2.5 text-xs font-semibold rounded-lg text-slate-500 hover:bg-slate-100 transition-all flex items-center justify-center gap-1.5';
    } else {
      btnIncome.className = 'flex-1 py-2.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 transition-all flex items-center justify-center gap-1.5 shadow-sm';
      btnExpense.className = 'flex-1 py-2.5 text-xs font-semibold rounded-lg text-slate-500 hover:bg-slate-100 transition-all flex items-center justify-center gap-1.5';
    }

    this.populateCategorySelect(type);
  }

  // Abrir modal de nueva transacción o edición
  openTransactionModal(txId = null) {
    const modal = document.getElementById('transactionModal');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('transactionForm');
    if (!modal || !form) return;

    form.reset();
    this.editingId = txId;

    const now = new Date();
    const todayStr = getLocalDateString(now);
    const timeStr = getLocalTimeString(now).substring(0, 5);

    if (txId) {
      const tx = store.getById(txId);
      if (!tx) return;

      modalTitle.textContent = 'Editar Movimiento';
      document.getElementById('txConcept').value = tx.concept;
      document.getElementById('txAmount').value = tx.amount;
      document.getElementById('txDate').value = tx.date;
      const txTimeInput = document.getElementById('txTime');
      if (txTimeInput) txTimeInput.value = tx.time || timeStr;
      document.getElementById('txNotes').value = tx.notes || '';

      this.setModalType(tx.type);
      this.populateCategorySelect(tx.type, tx.category);
    } else {
      modalTitle.textContent = 'Nuevo Movimiento';
      // Si hay una fecha específica seleccionada en el filtro, sugerirla
      const defaultDate = (this.currentPeriod === 'custom' && this.customDate) ? this.customDate : todayStr;
      document.getElementById('txDate').value = defaultDate;
      const txTimeInput = document.getElementById('txTime');
      if (txTimeInput) txTimeInput.value = timeStr;
      this.setModalType('expense');
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => {
      document.getElementById('txConcept').focus();
    }, 50);
  }

  closeTransactionModal() {
    const modal = document.getElementById('transactionModal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
    this.editingId = null;
  }

  // Guardar transacción
  async handleSaveTransaction(e) {
    e.preventDefault();

    const type = document.getElementById('txType').value;
    const concept = document.getElementById('txConcept').value;
    const amount = parseFloat(document.getElementById('txAmount').value);
    const category = document.getElementById('txCategory').value;
    const date = document.getElementById('txDate').value;
    const timeInput = document.getElementById('txTime');
    const time = timeInput ? timeInput.value : '';
    const notes = document.getElementById('txNotes').value;

    if (!concept || isNaN(amount) || amount <= 0 || !date || !category) {
      this.showToast('Por favor completa todos los campos requeridos con valores válidos', 'error');
      return;
    }

    const txData = { type, concept, amount, category, date, time, notes };

    if (this.editingId) {
      store.update(this.editingId, txData);
      this.showToast('Movimiento actualizado con éxito', 'success');
    } else {
      await store.add(txData);
      this.showToast('Movimiento registrado con éxito', 'success');
    }

    this.closeTransactionModal();
    this.populateMonthFilter();
    this.render();
  }

  // Diálogo de eliminación individual
  confirmDelete(id) {
    this.pendingDeleteId = id;
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }
  }

  closeDeleteModal() {
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
    this.pendingDeleteId = null;
  }

  async handleConfirmDelete() {
    if (this.pendingDeleteId) {
      await store.delete(this.pendingDeleteId);
      this.closeDeleteModal();
      this.populateMonthFilter();
      this.render();
      this.showToast('Movimiento eliminado', 'info');
    }
  }

  // Modal de Restablecimiento de Fábrica (Borrar todos los datos)
  openFactoryResetModal() {
    const modal = document.getElementById('factoryResetModal');
    if (modal) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }
  }

  closeFactoryResetModal() {
    const modal = document.getElementById('factoryResetModal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }

  async handleConfirmFactoryReset() {
    const btnConfirm = document.getElementById('btnConfirmFactoryReset');
    const originalText = btnConfirm ? btnConfirm.innerHTML : '';
    if (btnConfirm) {
      btnConfirm.disabled = true;
      btnConfirm.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Borrando...';
      if (window.lucide) window.lucide.createIcons();
    }

    try {
      await store.clearAll();
      this.closeFactoryResetModal();
      this.setPeriod('today');
      this.showToast('Restablecimiento completado: base de datos y memoria local en cero.', 'success');
    } catch (err) {
      this.showToast('Error al restablecer datos: ' + err.message, 'error');
    } finally {
      if (btnConfirm) {
        btnConfirm.disabled = false;
        btnConfirm.innerHTML = originalText;
        if (window.lucide) window.lucide.createIcons();
      }
    }
  }

  // Modal de Configuración de API / Servidor Nube
  openCloudModal() {
    const modal = document.getElementById('cloudConfigModal');
    const input = document.getElementById('cloudApiUrlInput');
    const statusMsg = document.getElementById('cloudStatusMsg');
    const statusIndicator = document.getElementById('cloudStatusIndicator');

    if (!modal) return;
    if (input) input.value = store.getApiUrl() || '';

    if (statusMsg && statusIndicator) {
      const currentUrl = store.getApiUrl();
      if (currentUrl) {
        statusMsg.textContent = `Configurado: ${currentUrl}`;
        statusIndicator.className = 'w-2.5 h-2.5 rounded-full bg-indigo-500';
      } else {
        statusMsg.textContent = 'Usando misma URL del navegador (relativa)';
        statusIndicator.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500';
      }
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => {
      if (input) input.focus();
    }, 50);
  }

  closeCloudModal() {
    const modal = document.getElementById('cloudConfigModal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }

  async testCloudConnection() {
    const input = document.getElementById('cloudApiUrlInput');
    const statusMsg = document.getElementById('cloudStatusMsg');
    const statusIndicator = document.getElementById('cloudStatusIndicator');
    const btnTest = document.getElementById('btnTestCloudConnection');

    const targetUrl = (input ? input.value : '').trim().replace(/\/+$/, '');
    const pingUrl = targetUrl ? `${targetUrl}/api/health` : '/api/health';

    if (btnTest) {
      btnTest.disabled = true;
      btnTest.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> Probando...';
      if (window.lucide) window.lucide.createIcons();
    }

    try {
      const res = await fetch(pingUrl, { method: 'GET' });
      if (res.ok) {
        if (statusMsg) statusMsg.textContent = '¡Conexión exitosa con el backend!';
        if (statusIndicator) statusIndicator.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500';
        this.showToast('Conexión con el backend verificada con éxito', 'success');
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err) {
      if (statusMsg) statusMsg.textContent = `Error al conectar: ${err.message}`;
      if (statusIndicator) statusIndicator.className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
      this.showToast('No se pudo contactar al backend en esa URL', 'error');
    } finally {
      if (btnTest) {
        btnTest.disabled = false;
        btnTest.innerHTML = '<i data-lucide="activity" class="w-3.5 h-3.5"></i> Probar Conexión';
        if (window.lucide) window.lucide.createIcons();
      }
    }
  }

  saveCloudConfig() {
    const input = document.getElementById('cloudApiUrlInput');
    const newUrl = input ? input.value : '';
    store.setApiUrl(newUrl);
    this.closeCloudModal();
    this.updateCloudStatusBadge();
    this.showToast(
      newUrl ? `Backend configurado: ${newUrl}` : 'Configuración restablecida a URL relativa',
      'success'
    );
    this.render();
  }

  updateCloudStatusBadge() {
    const label = document.getElementById('cloudStatusLabel');
    if (!label) return;
    const url = store.getApiUrl();
    if (url) {
      try {
        const parsed = new URL(url);
        label.textContent = parsed.hostname;
      } catch {
        label.textContent = 'Nube Activa';
      }
    } else {
      label.textContent = 'Servidor Nube';
    }
  }

  // Restablecer filtros de la tabla
  resetFilters() {
    this.currentFilters = {
      search: '',
      type: 'all',
      category: 'all',
      month: 'all'
    };

    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';

    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) categoryFilter.value = 'all';

    const monthFilter = document.getElementById('monthFilter');
    if (monthFilter) monthFilter.value = 'all';

    const typeTabs = document.querySelectorAll('.type-filter-tab');
    typeTabs.forEach((tab, idx) => {
      if (idx === 0) {
        tab.classList.add('bg-white', 'text-slate-900', 'shadow-sm');
        tab.classList.remove('text-slate-500', 'hover:text-slate-800');
      } else {
        tab.classList.remove('bg-white', 'text-slate-900', 'shadow-sm');
        tab.classList.add('text-slate-500', 'hover:text-slate-800');
      }
    });

    this.render();
  }

  // Obtiene los movimientos según el período seleccionado en el panel superior
  getPeriodTransactions() {
    return store.getFilteredByPeriod(this.currentPeriod, this.customDate);
  }

  // Obtener lista filtrada para la tabla aplicando búsqueda, tipo, categoría y mes adicional
  getFilteredTransactions() {
    let list = this.getPeriodTransactions();

    // Filtro adicional por mes si el usuario seleccionó uno específico en la tabla
    if (this.currentFilters.month !== 'all') {
      list = list.filter(tx => tx.date && tx.date.startsWith(this.currentFilters.month));
    }

    // Filtro por tipo
    if (this.currentFilters.type !== 'all') {
      list = list.filter(tx => tx.type === this.currentFilters.type);
    }

    // Filtro por categoría
    if (this.currentFilters.category !== 'all') {
      list = list.filter(tx => tx.category === this.currentFilters.category);
    }

    // Filtro por búsqueda
    if (this.currentFilters.search) {
      list = list.filter(tx => {
        const cat = getCategoryById(tx.category, tx.type);
        const matchConcept = tx.concept.toLowerCase().includes(this.currentFilters.search);
        const matchNotes = (tx.notes || '').toLowerCase().includes(this.currentFilters.search);
        const matchCat = cat.name.toLowerCase().includes(this.currentFilters.search);
        return matchConcept || matchNotes || matchCat;
      });
    }

    return list;
  }

  // Renderizado completo (Métricas, Gráficos y Tabla)
  render() {
    this.renderMetrics();
    this.renderCharts();
    this.renderTableOnly();
  }

  // Renderizado de tarjetas KPI: estrictamente calculado sobre el período activo
  renderMetrics() {
    const txScope = this.getPeriodTransactions();
    const metrics = store.getMetrics(txScope);

    const balanceEl = document.getElementById('metricBalance');
    const incomeEl = document.getElementById('metricIncome');
    const expenseEl = document.getElementById('metricExpense');
    const savingsEl = document.getElementById('metricSavingsRate');
    const savingsBar = document.getElementById('savingsProgressBar');
    const balanceBadge = document.getElementById('balanceBadge');

    if (balanceEl) balanceEl.textContent = this.formatMoney(metrics.balance);
    if (incomeEl) incomeEl.textContent = this.formatMoney(metrics.totalIncome);
    if (expenseEl) expenseEl.textContent = this.formatMoney(metrics.totalExpense);
    if (savingsEl) savingsEl.textContent = `${metrics.savingsRate}%`;

    if (savingsBar) {
      savingsBar.style.width = `${Math.min(100, metrics.savingsRate)}%`;
      if (metrics.savingsRate >= 20) {
        savingsBar.className = 'h-full bg-emerald-500 rounded-full transition-all duration-500';
      } else if (metrics.savingsRate > 0) {
        savingsBar.className = 'h-full bg-amber-500 rounded-full transition-all duration-500';
      } else {
        savingsBar.className = 'h-full bg-rose-500 rounded-full transition-all duration-500';
      }
    }

    if (balanceBadge) {
      if (metrics.balance > 0) {
        balanceBadge.textContent = 'Superávit saludable';
        balanceBadge.className = 'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200';
      } else if (metrics.balance === 0) {
        balanceBadge.textContent = 'En balance neutro';
        balanceBadge.className = 'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200';
      } else {
        balanceBadge.textContent = 'Déficit presupuestario';
        balanceBadge.className = 'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200';
      }
    }
  }

  // Renderizado de gráficos
  renderCharts() {
    const txScope = this.getPeriodTransactions();
    const expensesByCategory = store.getExpensesByCategory(txScope);
    budgetCharts.updateDonutChart(expensesByCategory, store.currency);

    const monthlyHistory = store.getMonthlyHistory(6);
    budgetCharts.updateBarChart(monthlyHistory, store.currency);
  }

  // Renderizado de la tabla de transacciones
  renderTableOnly() {
    const list = this.getFilteredTransactions();
    const tbody = document.getElementById('transactionsTableBody');
    const emptyState = document.getElementById('tableEmptyState');
    const countBadge = document.getElementById('transactionCountBadge');

    if (countBadge) {
      countBadge.textContent = `${list.length} ${list.length === 1 ? 'movimiento' : 'movimientos'}`;
    }

    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = '';
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    }

    if (emptyState) emptyState.classList.add('hidden');

    tbody.innerHTML = list.map(tx => {
      const isIncome = tx.type === 'income';
      const cat = getCategoryById(tx.category, tx.type);
      const sign = isIncome ? '+' : '-';
      const amountClass = isIncome ? 'text-emerald-600 font-semibold' : 'text-slate-900 font-semibold';

      const [year, month, day] = (tx.date || '').split('-');
      const formattedDate = (year && month && day) ? `${day}/${month}/${year}` : (tx.date || '');
      const timeDisplay = tx.time ? `<span class="text-[10px] text-slate-400 block">${tx.time}</span>` : '';

      return `
        <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-100 last:border-b-0 group">
          <td class="py-3.5 px-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${cat.bgClass || 'bg-slate-50 border-slate-200 text-slate-600'}">
                <i data-lucide="${cat.icon || 'circle-dot'}" class="w-5 h-5"></i>
              </div>
              <div class="min-w-0">
                <p class="font-medium text-slate-900 text-sm truncate">${this.escapeHTML(tx.concept)}</p>
                ${tx.notes ? `<p class="text-xs text-slate-400 truncate mt-0.5">${this.escapeHTML(tx.notes)}</p>` : ''}
              </div>
            </div>
          </td>
          <td class="py-3.5 px-4">
            <span class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${cat.bgClass || 'bg-slate-50 border-slate-200 text-slate-600'}">
              ${cat.name}
            </span>
          </td>
          <td class="py-3.5 px-4 text-xs text-slate-600 whitespace-nowrap">
            <span>${formattedDate}</span>
            ${timeDisplay}
          </td>
          <td class="py-3.5 px-4 text-right whitespace-nowrap">
            <span class="text-sm ${amountClass}">
              ${sign} ${this.formatMoney(tx.amount)}
            </span>
          </td>
          <td class="py-3.5 px-4 text-right whitespace-nowrap">
            <div class="flex items-center justify-end gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
              <button 
                onclick="app.openTransactionModal('${tx.id}')"
                title="Editar movimiento"
                class="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors">
                <i data-lucide="pencil" class="w-4 h-4"></i>
              </button>
              <button 
                onclick="app.confirmDelete('${tx.id}')"
                title="Eliminar movimiento"
                class="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Re-crear íconos Lucide para los elementos generados
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  // Exportar a CSV
  exportCSV() {
    const csv = store.exportToCSV();
    if (!csv) {
      this.showToast('No hay transacciones para exportar', 'info');
      return;
    }

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const dateStr = getLocalDateString(new Date());

    link.setAttribute('href', url);
    link.setAttribute('download', `presupuesto_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    this.showToast('Reporte CSV descargado con éxito', 'success');
  }

  // Notificaciones Toast elegantes
  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    const colors = {
      success: 'bg-emerald-600 text-white shadow-emerald-600/20',
      error: 'bg-rose-600 text-white shadow-rose-600/20',
      info: 'bg-slate-900 text-white shadow-slate-900/20'
    };

    const icons = {
      success: 'check-circle-2',
      error: 'alert-triangle',
      info: 'info'
    };

    toast.className = `flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-xs font-medium animate-toast pointer-events-auto ${colors[type] || colors.info}`;
    toast.innerHTML = `
      <i data-lucide="${icons[type] || 'info'}" class="w-4 h-4 shrink-0"></i>
      <span>${this.escapeHTML(message)}</span>
    `;

    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    setTimeout(() => {
      toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[tag] || tag)
    );
  }
}

// Inicialización global
let app = null;
document.addEventListener('DOMContentLoaded', () => {
  app = new AppController();
  if (window.lucide) {
    window.lucide.createIcons();
  }
});
