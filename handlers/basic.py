from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database import get_or_create_user

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Retorna el teclado principal inferior con accesos rápidos."""
    keyboard = [
        [KeyboardButton("☀️ Hoy"), KeyboardButton("📊 Balance")],
        [KeyboardButton("📅 Resumen Mes"), KeyboardButton("🗓️ Esta Semana")],
        [KeyboardButton("🧾 Historial"), KeyboardButton("❓ Ayuda")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /start: da la bienvenida y registra al usuario."""
    user = update.effective_user
    if not user:
        return

    db_user = get_or_create_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or ""
    )

    name = user.first_name or "amig@"
    welcome_text = (
        f"👋 ¡Hola, <b>{name}</b>! Bienvenido a tu <b>Bot de Presupuesto Personal</b> 💰🤖\n\n"
        "Te ayudaré a registrar tus gastos e ingresos al instante y mantener tus finanzas bajo control.\n\n"
        "🚀 <b>¿Cómo registrar movimientos?</b>\n"
        "• Para un gasto: <code>/gasto &lt;monto&gt; &lt;categoría&gt; [detalle]</code>\n"
        "  <i>Ej: /gasto 450 comida almuerzo</i>\n\n"
        "• Para un ingreso: <code>/ingreso &lt;monto&gt; &lt;categoría&gt; [detalle]</code>\n"
        "  <i>Ej: /ingreso 35000 sueldo quincena</i>\n\n"
        "⚡ <b>¡O también con mensajes rápidos!</b>\n"
        "• <code>-120 transporte taxi</code>\n"
        "• <code>+5000 sueldo</code>\n"
        "• <code>gasto 50 café</code>\n\n"
        "Usa los botones de abajo o escribe /ayuda para ver todos los comandos."
    )

    await update.message.reply_html(welcome_text, reply_markup=get_main_keyboard())

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /ayuda."""
    help_text = (
        "📖 <b>Guía de Comandos y Atajos</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💸 <b>Registrar Gastos:</b>\n"
        "• <code>/gasto 150 comida</code> (sin descripción)\n"
        "• <code>/gasto 850 transporte gasolina</code> (con descripción)\n"
        "• <code>-200 compras supermercado</code> (atajo rápido con signo menos)\n\n"
        "💰 <b>Registrar Ingresos:</b>\n"
        "• <code>/ingreso 12000 sueldo</code>\n"
        "• <code>+1500 venta bicicleta</code> (atajo rápido con signo más)\n\n"
        "📊 <b>Consultas y Reportes:</b>\n"
        "• /hoy — Resumen financiero del día actual (ingresos, gastos y balance de hoy).\n"
        "• /balance — Muestra tu balance histórico total acumulado.\n"
        "• /resumen — Resumen detallado del mes actual con porcentajes.\n"
        "• /semana — Reporte de los últimos 7 días.\n"
        "• /historial — Muestra tus últimos movimientos registrados.\n\n"
        "🗑️ <b>Correcciones:</b>\n"
        "• <code>/borrar ID</code> — Elimina una transacción específica (ej. <code>/borrar 5</code>).\n"
        "• <code>/deshacer</code> — Elimina la última transacción registrada inmediatamente.\n"
    )
    await update.message.reply_html(help_text, reply_markup=get_main_keyboard())
