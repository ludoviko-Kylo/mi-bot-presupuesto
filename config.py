import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 1. Credenciales y Tokens
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# 2. Base de Datos: PostgreSQL/Supabase en la nube o SQLite local como respaldo
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "presupuesto.db")).strip()

# 3. Moneda por defecto ($, S/., €, MXN, etc.)
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "$").strip()

# 4. Configuración de Red y Despliegue en la Nube (Render, Railway o Local)
# Render y Railway inyectan la variable PORT automáticamente (ej: 10000 o 8080)
PORT = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
HOST = os.getenv("HOST", "0.0.0.0")
APP_URL = os.getenv("APP_URL", os.getenv("RENDER_EXTERNAL_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN", ""))).strip()

# Categorías estándar de gastos e ingresos
EXPENSE_CATEGORIES = [
    "Comida",
    "Transporte",
    "Vivienda",
    "Servicios",
    "Ocio",
    "Salud",
    "Educación",
    "Compras",
    "Otros",
]

INCOME_CATEGORIES = [
    "Sueldo",
    "Venta",
    "Inversión",
    "Regalo",
    "Otros",
]

# Emojis asociados a categorías para mejorar la visualización
CATEGORY_EMOJIS = {
    "comida": "🍔",
    "alimentación": "🍔",
    "restaurante": "🍽️",
    "supermercado": "🛒",
    "transporte": "🚗",
    "gasolina": "⛽",
    "taxi": "🚕",
    "vivienda": "🏠",
    "alquiler": "🏠",
    "servicios": "💡",
    "luz": "💡",
    "agua": "💧",
    "internet": "🌐",
    "ocio": "🎮",
    "entretenimiento": "🎉",
    "salud": "💊",
    "medicina": "🏥",
    "educación": "📚",
    "compras": "🛍️",
    "sueldo": "💼",
    "salario": "💼",
    "nómina": "💼",
    "venta": "🏷️",
    "inversión": "📈",
    "regalo": "🎁",
    "otros": "📦",
    "otro": "📦",
}

def get_category_emoji(category: str) -> str:
    """Devuelve un emoji representativo para la categoría."""
    normalized = category.strip().lower()
    return CATEGORY_EMOJIS.get(normalized, "🏷️")
