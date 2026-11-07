from typing import List, Dict, Any
from config import get_category_emoji, DEFAULT_CURRENCY

def format_currency(amount: float, currency: str = DEFAULT_CURRENCY) -> str:
    """Formatea un número con separadores de miles y dos decimales."""
    return f"{currency} {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_progress_bar(percentage: float, length: int = 10) -> str:
    """Genera una barra de progreso visual con bloques de emojis."""
    clamped_pct = max(0.0, min(100.0, percentage))
    filled_length = int(round((clamped_pct / 100.0) * length))
    empty_length = length - filled_length
    
    # Elegir color de bloques según magnitud
    if clamped_pct > 50:
        fill_block = "🟥"
    elif clamped_pct > 25:
        fill_block = "🟧"
    else:
        fill_block = "🟩"

    return f"{fill_block * filled_length}{'⬜' * empty_length}"

def format_balance_message(balance_data: Dict[str, Any], currency: str = DEFAULT_CURRENCY) -> str:
    """Crea un mensaje en HTML formateado con el balance global."""
    income = balance_data["total_income"]
    expense = balance_data["total_expense"]
    net = balance_data["net_balance"]
    count = balance_data["total_count"]

    net_sign = "+" if net >= 0 else "-"
    net_emoji = "🟢" if net >= 0 else "🔴"

    return (
        "📊 <b>Estado de Cuenta General</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Total Ingresos:</b> +{format_currency(income, currency)}\n"
        f"🔴 <b>Total Gastos:</b> -{format_currency(expense, currency)}\n"
        "─────────────────────\n"
        f"{net_emoji} <b>Saldo Neto:</b> <b>{net_sign}{format_currency(abs(net), currency)}</b>\n"
        f"📝 <i>Total de registros: {count}</i>\n\n"
        "💡 <i>Usa /resumen para ver el mes en curso o /semana para los últimos 7 días.</i>"
    )

def format_summary_message(
    title: str,
    summary: Dict[str, Any],
    currency: str = DEFAULT_CURRENCY
) -> str:
    """Genera un reporte detallado con desglose porcentual por categorías."""
    income = summary["total_income"]
    expense = summary["total_expense"]
    net = summary["net_balance"]
    categories = summary.get("expense_by_category", [])

    net_sign = "+" if net >= 0 else "-"
    net_emoji = "🟢" if net >= 0 else "🔴"

    lines = [
        f"📅 <b>{title}</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"💰 <b>Ingresos:</b> +{format_currency(income, currency)}",
        f"💸 <b>Gastos:</b> -{format_currency(expense, currency)}",
        f"{net_emoji} <b>Balance:</b> <b>{net_sign}{format_currency(abs(net), currency)}</b>",
        "─────────────────────"
    ]

    if not categories:
        lines.append("\n<i>No se han registrado gastos en este periodo.</i> 🏖️")
    else:
        lines.append("\n🏷️ <b>Desglose de Gastos:</b>\n")
        for cat in categories:
            name = cat["category"]
            cat_total = cat["total"]
            pct = cat["percentage"]
            emoji = get_category_emoji(name)
            bar = render_progress_bar(pct, length=8)
            lines.append(
                f"{emoji} <b>{name}</b>: {format_currency(cat_total, currency)} ({pct}%)\n"
                f"   {bar}"
            )

    return "\n".join(lines)

def format_history_message(
    transactions: List[Dict[str, Any]],
    currency: str = DEFAULT_CURRENCY
) -> str:
    """Muestra la lista de transacciones recientes."""
    if not transactions:
        return "ℹ️ <i>Aún no tienes movimientos registrados. Registra tu primer gasto con /gasto</i>"

    lines = [
        "🧾 <b>Últimos Movimientos Registrados</b>",
        "━━━━━━━━━━━━━━━━━━━━━\n"
    ]

    for tx in transactions:
        tx_id = tx["id"]
        tx_type = tx["type"]
        amount = tx["amount"]
        category = tx["category"]
        desc = tx.get("description", "")
        created_at = tx.get("created_at", "")[:16] # YYYY-MM-DD HH:MM
        emoji = get_category_emoji(category)

        if tx_type == "ingreso":
            sign = "+"
            color_emoji = "🟢"
        else:
            sign = "-"
            color_emoji = "🔴"

        desc_text = f" — <i>{desc}</i>" if desc else ""
        lines.append(
            f"{color_emoji} <b>#{tx_id}</b> | {emoji} {category}: <b>{sign}{format_currency(amount, currency)}</b>{desc_text}\n"
            f"   🕒 <code>{created_at}</code>"
        )

    lines.append("\n💡 <i>Para borrar una transacción equivocada, escribe:</i>\n<code>/borrar ID</code> (ej. <code>/borrar 1</code>)")
    return "\n".join(lines)
