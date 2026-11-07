import re
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes
from database import get_or_create_user
from services.transaction_service import (
    add_transaction,
    delete_transaction,
    get_last_transaction
)
from utils.formatters import format_currency
from config import get_category_emoji

def parse_transaction_arguments(args: list) -> Tuple[float, str, str]:
    """
    Parsea los argumentos de /gasto o /ingreso.
    Formato esperado: <monto> <categoria> [descripcion...]
    """
    if len(args) < 2:
        raise ValueError(
            "Debes indicar al menos el monto y la categoría.\n"
            "Ejemplo: <code>/gasto 250 comida almuerzo</code>"
        )

    # Limpiar monto permitiendo coma o punto
    amount_str = args[0].replace(",", ".").replace("$", "").strip()
    try:
        amount = float(amount_str)
    except ValueError:
        raise ValueError(f"'{args[0]}' no es un monto numérico válido.")

    if amount <= 0:
        raise ValueError("El monto debe ser un valor mayor a cero.")

    remaining = args[1:]
    # Descartar preposiciones iniciales como 'en', 'de', 'para', 'por'
    if remaining and remaining[0].lower() in ("en", "de", "por", "para"):
        remaining = remaining[1:]

    if not remaining:
        raise ValueError(
            "Debes indicar la categoría o concepto.\n"
            "Ejemplo: <code>/gasto 8 taxi</code> o <code>/gasto 8 en taxi</code>"
        )

    category = remaining[0].strip()
    description = " ".join(remaining[1:]).strip() if len(remaining) > 1 else ""

    return amount, category, description

async def expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /gasto <monto> <categoría> [descripción]."""
    user = update.effective_user
    if not user or not update.message:
        return

    get_or_create_user(user.id, user.username or "", user.first_name or "")

    try:
        amount, category, description = parse_transaction_arguments(context.args or [])
        tx = add_transaction(
            user_id=user.id,
            type_="gasto",
            amount=amount,
            category=category,
            description=description
        )

        emoji = get_category_emoji(tx["category"])
        desc_line = f"📝 <i>Detalle:</i> {tx['description']}\n" if tx['description'] else ""
        msg = (
            f"✅ <b>Gasto registrado correctamente</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💸 <b>Monto:</b> -{format_currency(tx['amount'])}\n"
            f"{emoji} <b>Categoría:</b> {tx['category']}\n"
            f"{desc_line}"
            f"🆔 <i>ID de registro: #{tx['id']} (usa /deshacer si te equivocaste)</i>"
        )
        await update.message.reply_html(msg)
    except ValueError as e:
        await update.message.reply_html(f"⚠️ {str(e)}")

async def income_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /ingreso <monto> <categoría> [descripción]."""
    user = update.effective_user
    if not user or not update.message:
        return

    get_or_create_user(user.id, user.username or "", user.first_name or "")

    try:
        amount, category, description = parse_transaction_arguments(context.args or [])
        tx = add_transaction(
            user_id=user.id,
            type_="ingreso",
            amount=amount,
            category=category,
            description=description
        )

        emoji = get_category_emoji(tx["category"])
        desc_line = f"📝 <i>Detalle:</i> {tx['description']}\n" if tx['description'] else ""
        msg = (
            f"🎉 <b>Ingreso registrado correctamente</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Monto:</b> +{format_currency(tx['amount'])}\n"
            f"{emoji} <b>Categoría:</b> {tx['category']}\n"
            f"{desc_line}"
            f"🆔 <i>ID de registro: #{tx['id']} (usa /deshacer si te equivocaste)</i>"
        )
        await update.message.reply_html(msg)
    except ValueError as e:
        await update.message.reply_html(f"⚠️ {str(e)}")

async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /borrar <id>."""
    user = update.effective_user
    if not user or not update.message:
        return

    if not context.args or len(context.args) == 0:
        await update.message.reply_html(
            "⚠️ Indica el ID de la transacción que deseas eliminar.\n"
            "Ejemplo: <code>/borrar 14</code>\n"
            "<i>(Puedes ver tus transacciones y sus IDs con /historial)</i>"
        )
        return

    try:
        tx_id = int(context.args[0].replace("#", ""))
    except ValueError:
        await update.message.reply_html("⚠️ El ID de la transacción debe ser un número entero.")
        return

    success = delete_transaction(user_id=user.id, transaction_id=tx_id)
    if success:
        await update.message.reply_html(f"🗑️ Transacción <b>#{tx_id}</b> eliminada con éxito.")
    else:
        await update.message.reply_html(
            f"⚠️ No se encontró la transacción #{tx_id} o no pertenece a tu cuenta."
        )

async def undo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador de /deshacer: elimina la última transacción creada por el usuario."""
    user = update.effective_user
    if not user or not update.message:
        return

    last_tx = get_last_transaction(user_id=user.id)
    if not last_tx:
        await update.message.reply_html("ℹ️ No tienes transacciones recientes para deshacer.")
        return

    tx_id = last_tx["id"]
    delete_transaction(user_id=user.id, transaction_id=tx_id)
    emoji = get_category_emoji(last_tx["category"])
    sign = "+" if last_tx["type"] == "ingreso" else "-"
    await update.message.reply_html(
        f"↩️ Se eliminó la última transacción:\n"
        f"<b>#{tx_id}</b> | {emoji} {last_tx['category']}: {sign}{format_currency(last_tx['amount'])}"
    )

def parse_quick_text(text: str) -> Optional[Tuple[str, float, str, str]]:
    """
    Intenta interpretar textos rápidos como:
    - "-150 comida café" -> ('gasto', 150.0, 'comida', 'café')
    - "+5000 sueldo" -> ('ingreso', 5000.0, 'sueldo', '')
    - "gasto 120 transporte taxi"
    - "ingreso 300 venta reloj"
    """
    raw = text.strip()

    # Patrón con signo - o + al inicio
    # Patrón con signo - o + al inicio (ej: -8 en taxi, +500 sueldo)
    match_sign = re.match(
        r"^([+-])\s*(\d+(?:[.,]\d+)?)\s+(?:(?:en|de|por|para)\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)(?:\s+(.*))?$",
        raw,
        re.IGNORECASE
    )
    if match_sign:
        sign, amount_str, cat, desc = match_sign.groups()
        tx_type = "ingreso" if sign == "+" else "gasto"
        amount = float(amount_str.replace(",", "."))
        return tx_type, amount, cat, desc or ""

    # Patrón con palabra clave gasto / ingreso (ej: gasto 8 en taxi)
    match_word = re.match(
        r"^(gasto|ingreso)\s+(\d+(?:[.,]\d+)?)\s+(?:(?:en|de|por|para)\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)(?:\s+(.*))?$",
        raw,
        re.IGNORECASE
    )
    if match_word:
        tx_type, amount_str, cat, desc = match_word.groups()
        amount = float(amount_str.replace(",", "."))
        return tx_type.lower(), amount, cat, desc or ""

    return None

async def quick_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja mensajes de texto libre que coinciden con formatos rápidos."""
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    parsed = parse_quick_text(text)
    if not parsed:
        return

    tx_type, amount, category, description = parsed
    get_or_create_user(user.id, user.username or "", user.first_name or "")

    tx = add_transaction(
        user_id=user.id,
        type_=tx_type,
        amount=amount,
        category=category,
        description=description
    )

    emoji = get_category_emoji(tx["category"])
    desc_line = f"📝 <i>Detalle:</i> {tx['description']}\n" if tx['description'] else ""
    title = "✅ Gasto registrado" if tx_type == "gasto" else "🎉 Ingreso registrado"
    sign = "-" if tx_type == "gasto" else "+"

    msg = (
        f"<b>{title}</b> (vía atajo)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Monto:</b> {sign}{format_currency(tx['amount'])}\n"
        f"{emoji} <b>Categoría:</b> {tx['category']}\n"
        f"{desc_line}"
        f"🆔 <i>#{tx['id']} (usa /deshacer si te equivocaste)</i>"
    )
    await update.message.reply_html(msg)
