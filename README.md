# 💰 Bot de Presupuesto Personal para Telegram & Web Pro 🤖🌐

Un ecosistema integral de finanzas personales compuesto por un **Bot de Telegram** y un **Panel Web Moderno**, compatible con arquitectura local (SQLite) y arquitectura en la nube 24/7 (**PostgreSQL / Supabase + Render / Railway**).

---

## ✨ Características Principales

- ⚡ **Registro ultrarrápido:** Registra gastos e ingresos con comandos estructurados (`/gasto`, `/ingreso`) o atajos de texto libre (`-150 comida`, `+2000 sueldo`).
- ☀️ **Filtros e Historiales Diarios:** Métricas de la jornada ("Hoy") para comenzar el día limpio, con navegación temporal ("Ayer", "Esta semana", "Este mes", o fecha específica del calendario).
- 🏷️ **Categorización inteligente:** Emojis y colores dinámicos por categoría (🍔 Alimentación, 🚗 Transporte, 🏠 Vivienda, 💼 Salario, etc.).
- 🌐 **Panel Web Dashboard Interactivo:**
  - KPI Cards en vivo (Balance Neto, Ingresos, Gastos, Tasa de Ahorro).
  - Gráficos interactivos con Chart.js (Dona de distribución y barras comparativas mensuales).
  - Tabla de transacciones con búsqueda, filtros y soporte de fecha/hora exacta.
  - Restablecimiento total de fábrica con confirmación y borrado físico.
  - Compatible con acceso multidispositivo (móvil, tablet, PC).
- ☁️ **Arquitectura Híbrida Nube / Local:**
  - **Local:** SQLite sin dependencias externas.
  - **Nube:** PostgreSQL en Supabase, Neon o Render Postgres para sincronización 24/7.
- 🔒 **Seguridad y Privacidad:** Variables de entorno protegidas con `.env` y soporte multiusuario.

---

## 🛠️ Variables de Entorno (.env)

Crea un archivo `.env` en la raíz (puedes guiarte de [`.env.example`](file:///d:/Google%20Antigravity/mi-bot-presupuesto/.env.example)):

```env
# 1. Token de Telegram (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz

# 2. Base de datos (Dejar vacío para SQLite local o asignar PostgreSQL/Supabase)
DATABASE_URL=postgresql://postgres.xxx:TuPassword@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require

# 3. Moneda
DEFAULT_CURRENCY=S/

# 4. Servidor Web (Render y Railway definen PORT automáticamente)
PORT=8000
HOST=0.0.0.0
```

---

## 🚀 Despliegue en la Nube (24/7 y Multidispositivo)

### 1. Base de Datos en Supabase (Gratis)
1. Crea un proyecto en [Supabase.com](https://supabase.com).
2. Ve a **Project Settings > Database > Connection String > URI**.
3. Copia la URL de conexión (asegúrate de incluir tu contraseña) y configúrala como `DATABASE_URL`.
4. Las tablas e índices se crearán automáticamente al iniciar la aplicación.

---

### 2. Despliegue en Render (Recomendado)
El proyecto incluye [`render.yaml`](file:///d:/Google%20Antigravity/mi-bot-presupuesto/render.yaml) y [`Procfile`](file:///d:/Google%20Antigravity/mi-bot-presupuesto/Procfile):
1. Sube tu código a un repositorio en **GitHub**.
2. En [Render.com](https://render.com), haz clic en **New + > Blueprint** (o **Web Service**) y selecciona tu repositorio.
3. En la sección **Environment Variables**, añade:
   - `TELEGRAM_BOT_TOKEN`: Tu token de BotFather.
   - `DATABASE_URL`: Tu conexión de Supabase / PostgreSQL.
   - `DEFAULT_CURRENCY`: Tu moneda (ejemplo: `S/` o `$`).
4. Haz clic en **Deploy**. El bot de Telegram y la API web estarán en línea 24/7.

---

### 3. Despliegue en Railway
El proyecto incluye [`railway.json`](file:///d:/Google%20Antigravity/mi-bot-presupuesto/railway.json):
1. En [Railway.app](https://railway.app), crea un nuevo proyecto desde tu repositorio de **GitHub**.
2. En la pestaña **Variables**, añade `TELEGRAM_BOT_TOKEN`, `DATABASE_URL` y `DEFAULT_CURRENCY`.
3. Railway compilará e iniciará automáticamente el servicio con el puerto adecuado.

---

### 4. Uso del Panel Web desde Cualquier Dispositivo
- **Opción A (Monolítico):** Accede a la URL asignada por Render/Railway (ejemplo: `https://mi-bot-presupuesto.onrender.com`). El panel web cargará directamente conectado a la API.
- **Opción B (GitHub Pages / Vercel / Móvil):** Si hospedas el frontend por separado o lo abres desde otro dispositivo, abre el botón **☁️ Servidor Nube** en la barra superior del panel e introduce la URL de tu backend en Render. Se guardará de forma persistente y sincronizará en tiempo real.

---

## 💻 Ejecución Local

Si deseas probarlo localmente en tu ordenador:

1. Haz doble clic en [`iniciar_bot.bat`](file:///d:/Google%20Antigravity/mi-bot-presupuesto/iniciar_bot.bat) (o ejecuta `python main.py`).
2. El bot responderá en Telegram y el panel web estará disponible en:
   `http://localhost:8000`

---

## 📱 Comandos del Bot de Telegram

- `/hoy` o botón **☀️ Hoy**: Balance y métricas exclusivas del día actual.
- `/gasto 150 comida almuerzo`: Registra un gasto.
- `/ingreso 2000 sueldo quincena`: Registra un ingreso.
- `-50 taxi` o `+200 venta`: Atajos rápidos de texto libre.
- `/balance` o botón **📊 Balance**: Balance global acumulado.
- `/resumen` o botón **📅 Resumen Mes**: Desglose mensual detallado.
- `/semana` o botón **🗓️ Esta Semana**: Resumen de los últimos 7 días.
- `/historial` o botón **🧾 Historial**: Últimos movimientos registrados.
- `/deshacer`: Elimina el último movimiento registrado.
- `/borrar ID`: Elimina una transacción específica por ID.

---

## 🧪 Pruebas Unitarias

Ejecuta la suite de pruebas automatizadas:
```powershell
python test_bot.py
```

---

## 📁 Estructura del Proyecto

```text
mi-bot-presupuesto/
├── .env.example          # Plantilla para variables de entorno (Nube y Local)
├── .gitignore            # Exclusión de archivos sensibles y base de datos local
├── .dockerignore         # Optimización para construcción de contenedores
├── Dockerfile            # Imagen de contenedor lista para Render / Railway
├── Procfile              # Comando de inicio estándar para servicios web
├── render.yaml           # Infraestructura como código (Blueprint de Render)
├── railway.json          # Configuración para despliegue en Railway
├── requirements.txt      # Dependencias: python-telegram-bot, psycopg2-binary, dotenv
├── config.py             # Configuración centralizada y lectura de variables de entorno
├── database.py           # Capa de datos híbrida (PostgreSQL / Supabase y SQLite)
├── main.py               # Servidor web REST + Polling 24/7 del Bot de Telegram
├── test_bot.py           # Suite de pruebas unitarias
├── index.html            # Interfaz gráfica moderna del panel de finanzas
├── transacciones.json    # Almacén de sincronización
├── transacciones_data.js # Soporte offline / fallback
├── css/
│   └── styles.css        # Estilos personalizados y animaciones
├── js/
│   ├── config.js         # Configuración de URL API remota (Vite/React/Cloud)
│   ├── store.js          # Gestor de estado, sincronización y persistencia
│   ├── app.js            # Controlador de la UI, modales y filtros
│   ├── categories.js     # Catálogo de categorías, iconos y colores
│   └── charts.js         # Configuración de gráficos interactivos Chart.js
├── services/
│   └── transaction_service.py # Lógica de negocio y métricas
├── handlers/
│   ├── basic.py          # /start, /ayuda y teclado interactivo
│   ├── transactions.py   # Registro y eliminación de transacciones
│   └── reports.py        # Generación de reportes (/hoy, /balance, /resumen)
└── utils/
    └── formatters.py     # Formateo de monedas y barras de progreso
```
