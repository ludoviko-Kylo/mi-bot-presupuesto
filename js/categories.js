// Catálogo de categorías para ingresos y gastos
const CATEGORIES = {
  expense: [
    { id: 'vivienda', name: 'Vivienda y Servicios', icon: 'home', color: '#6366f1', bgClass: 'bg-indigo-50 text-indigo-600 border-indigo-100' },
    { id: 'alimentacion', name: 'Alimentación y Supermercado', icon: 'utensils', color: '#f59e0b', bgClass: 'bg-amber-50 text-amber-600 border-amber-100' },
    { id: 'transporte', name: 'Transporte y Movilidad', icon: 'car', color: '#0ea5e9', bgClass: 'bg-sky-50 text-sky-600 border-sky-100' },
    { id: 'ocio', name: 'Entretenimiento y Ocio', icon: 'tv', color: '#ec4899', bgClass: 'bg-pink-50 text-pink-600 border-pink-100' },
    { id: 'compras', name: 'Compras y Ropa', icon: 'shopping-bag', color: '#8b5cf6', bgClass: 'bg-purple-50 text-purple-600 border-purple-100' },
    { id: 'salud', name: 'Salud y Bienestar', icon: 'heart-pulse', color: '#10b981', bgClass: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
    { id: 'educacion', name: 'Educación y Cursos', icon: 'graduation-cap', color: '#3b82f6', bgClass: 'bg-blue-50 text-blue-600 border-blue-100' },
    { id: 'otros_gastos', name: 'Otros Gastos', icon: 'tag', color: '#64748b', bgClass: 'bg-slate-50 text-slate-600 border-slate-100' }
  ],
  income: [
    { id: 'salario', name: 'Salario y Nómina', icon: 'briefcase', color: '#10b981', bgClass: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
    { id: 'freelance', name: 'Freelance / Proyectos', icon: 'laptop', color: '#06b6d4', bgClass: 'bg-cyan-50 text-cyan-600 border-cyan-100' },
    { id: 'inversiones', name: 'Inversiones y Rendimientos', icon: 'trending-up', color: '#6366f1', bgClass: 'bg-indigo-50 text-indigo-600 border-indigo-100' },
    { id: 'premios_regalos', name: 'Regalos y Premios', icon: 'gift', color: '#f43f5e', bgClass: 'bg-rose-50 text-rose-600 border-rose-100' },
    { id: 'otros_ingresos', name: 'Otros Ingresos', icon: 'plus-circle', color: '#14b8a6', bgClass: 'bg-teal-50 text-teal-600 border-teal-100' }
  ]
};

function getCategoryById(id, type = null) {
  if (type && CATEGORIES[type]) {
    const found = CATEGORIES[type].find(c => c.id === id);
    if (found) return found;
  }
  const all = [...CATEGORIES.expense, ...CATEGORIES.income];
  return all.find(c => c.id === id) || {
    id: 'general',
    name: 'General',
    icon: 'circle-dot',
    color: '#94a3b8',
    bgClass: 'bg-slate-50 text-slate-600 border-slate-100'
  };
}

function getCategoriesByType(type) {
  return CATEGORIES[type] || [];
}
