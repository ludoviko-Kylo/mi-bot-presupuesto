from telegram import Update
from telegram.ext import ContextTypes
from database import get_or_create_user
from services.transaction_service import (
    get_balance,
    get_today_summary,
    get_current_month_summary,
    get_last_7_days_summary,
    get_recent_transactions
)
from utils.formatters import (
    format_balance_message,
    format_summary_message,
    format_history_message
)

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /balance: balance histórico global."""
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = get_or_create_user(user.id, user.username or "", user.first_name or "")
    currency = db_user.get("currency", "$")

    balance_data = get_balance(user.id)
    msg = format_balance_message(balance_data, currency)
    await update.message.reply_html(msg)

async def today_summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /hoy: reporte del día actual."""
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = get_or_create_user(user.id, user.username or "", user.first_name or "")
    currency = db_user.get("currency", "$")

    summary = get_today_summary(user.id)
    today_str = summary["start_date"].strftime("%d/%m/%Y")
    msg = format_summary_message(f"Resumen de Hoy ({today_str})", summary, currency)
    await update.message.reply_html(msg)

async def month_summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /resumen: reporte del mes en curso."""
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = get_or_create_user(user.id, user.username or "", user.first_name or "")
    currency = db_user.get("currency", "$")

    summary = get_current_month_summary(user.id)
    month_name = summary["start_date"].strftime("%B %Y").capitalize()
    msg = format_summary_message(f"Resumen Mensual ({month_name})", summary, currency)
    await update.message.reply_html(msg)

async def week_summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /semana: reporte de los últimos 7 días."""
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = get_or_create_user(user.id, user.username or "", user.first_name or "")
    currency = db_user.get("currency", "$")

    summary = get_last_7_days_summary(user.id)
    msg = format_summary_message("Resumen de los Últimos 7 Días", summary, currency)
    await update.message.reply_html(msg)

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /historial: lista últimos movimientos."""
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = get_or_create_user(user.id, user.username or "", user.first_name or "")
    currency = db_user.get("currency", "$")

    limit = 10
    if context.args and len(context.args) > 0:
        try:
            limit = min(30, max(1, int(context.args[0])))
        except ValueError:
            pass

    transactions = get_recent_transactions(user.id, limit=limit)
    msg = format_history_message(transactions, currency)
    await update.message.reply_html(msg)
