import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from database import get_db_cursor, get_or_create_user
from config import BASE_DIR, DEFAULT_CURRENCY

def map_category_to_web_id(category: str, tx_type: str, description: str = "") -> str:
    """Mapea una categoría y descripción al ID correspondiente en la interfaz web de escritorio."""
    combined = f"{category} {description}".strip().lower()
    if tx_type == "expense":
        if any(w in combined for w in [
            "comida", "almuerzo", "cena", "super", "mercado", "alimento", "desayuno",
            "restaurante", "cafe", "café", "papa", "papas", "pan", "pizza", "hamburguesa",
            "fruta", "carne", "pollo", "verdura", "postre"
        ]):
            return "alimentacion"
        if any(w in combined for w in [
            "transporte", "gasolina", "taxi", "uber", "pasaje", "bus", "metro",
            "colectivo", "peaje", "combustible", "indrive", "didi", "tren"
        ]):
            return "transporte"
        if any(w in combined for w in [
            "vivienda", "alquiler", "renta", "casa", "depa", "departamento",
            "luz", "agua", "gas", "internet", "servicio", "servicios", "mantenimiento"
        ]):
            return "vivienda"
        if any(w in combined for w in [
            "ocio", "cine", "juego", "fiesta", "salida", "cerveza", "diversion",
            "bar", "paseo", "concierto", "suscripcion", "netflix", "spotify"
        ]):
            return "ocio"
        if any(w in combined for w in [
            "compra", "compras", "ropa", "zapato", "zapatillas", "tienda", "mall", "shopping"
        ]):
            return "compras"
        if any(w in combined for w in [
            "salud", "farmacia", "medicina", "doctor", "clinica", "hospital", "dentista", "pastillas"
        ]):
            return "salud"
        if any(w in combined for w in [
            "educacion", "curso", "libro", "colegio", "universidad", "taller", "estudio", "matricula"
        ]):
            return "educacion"
        return "otros_gastos"
    else:
        if any(w in combined for w in ["sueldo", "salario", "nomina", "quincena", "pago", "honorarios"]):
            return "salario"
        if any(w in combined for w in ["freelance", "proyecto", "cliente", "asesoria", "consultoria"]):
            return "freelance"
        if any(w in combined for w in ["inversion", "dividendo", "interes", "cripto", "accion", "deposito"]):
            return "inversiones"
        if any(w in combined for w in ["regalo", "premio", "bono", "sorteo"]):
            return "premios_regalos"
        return "otros_ingresos"

def export_transactions_to_json(filepath: Optional[str] = None) -> None:
    """
    Exporta todas las transacciones de SQLite al archivo transacciones.json
    y genera transacciones_data.js para garantizar carga sin problemas de CORS.
    """
    target_json = Path(filepath) if filepath else (BASE_DIR / "transacciones.json")
    target_js = BASE_DIR / "transacciones_data.js"

    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM transactions ORDER BY created_at DESC, id DESC")
        rows = cursor.fetchall()

    web_transactions = []
    for r in rows:
        tx_type = "expense" if r["type"] == "gasto" else "income"
        raw_cat = r["category"] or ""
        raw_desc = r["description"] or ""

        # Si el usuario escribió 'en taxi', la verdadera categoría o concepto es 'taxi'
        if raw_cat.strip().lower() in ("en", "de", "por", "para") and raw_desc.strip():
            display_concept = raw_desc.strip().capitalize()
            category_id = map_category_to_web_id(raw_desc, tx_type, raw_desc)
        else:
            display_concept = raw_desc.strip().capitalize() if raw_desc.strip() else raw_cat.strip().capitalize()
            category_id = map_category_to_web_id(raw_cat, tx_type, raw_desc)

        created_at_val = r["created_at"]
        if hasattr(created_at_val, "strftime"):
            created_at_raw = created_at_val.strftime("%Y-%m-%d %H:%M:%S")
        elif created_at_val:
            created_at_raw = str(created_at_val)
        else:
            created_at_raw = ""

        if created_at_raw:
            date_str = created_at_raw[:10]
            time_str = created_at_raw[11:19] if len(created_at_raw) >= 19 else created_at_raw[11:]
            try:
                dt_obj = datetime.strptime(created_at_raw[:19], "%Y-%m-%d %H:%M:%S")
                iso_str = dt_obj.isoformat()
                timestamp_ms = int(dt_obj.timestamp() * 1000)
            except Exception:
                iso_str = f"{date_str}T{time_str or '00:00:00'}"
                timestamp_ms = None
        else:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            created_at_raw = f"{date_str} {time_str}"
            iso_str = now.isoformat()
            timestamp_ms = int(now.timestamp() * 1000)

        web_transactions.append({
            "id": f"tx_{r['id']}",
            "raw_id": r["id"],
            "type": tx_type,
            "amount": float(r["amount"]),
            "category": category_id,
            "concept": display_concept,
            "date": date_str,
            "time": time_str,
            "created_at": created_at_raw,
            "datetime": iso_str,
            "timestamp": timestamp_ms,
            "notes": raw_desc or f"Registrado vía Telegram ({raw_cat})"
        })


    payload = {
        "currency": DEFAULT_CURRENCY,
        "last_updated": datetime.now().isoformat(),
        "total_count": len(web_transactions),
        "transactions": web_transactions
    }

    # Guardar transacciones.json
    try:
        temp_json = target_json.with_suffix(".tmp")
        with open(temp_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        temp_json.replace(target_json)
    except Exception as e:
        print(f"Error al escribir transacciones.json: {e}")

    # Guardar transacciones_data.js (para soporte offline directo sin servidor web)
    try:
        temp_js = target_js.with_suffix(".tmp")
        with open(temp_js, "w", encoding="utf-8") as f:
            f.write(
                f"// Archivo generado automáticamente por el Bot de Presupuesto\n"
                f"window.LOCAL_TRANSACTIONS = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
            )
        temp_js.replace(target_js)
    except Exception as e:
        print(f"Error al escribir transacciones_data.js: {e}")

def add_transaction(
    user_id: int,
    type_: str,
    amount: float,
    category: str,
    description: str = "",
    created_at: Optional[str] = None
) -> Dict[str, Any]:
    """Registra un nuevo gasto o ingreso para el usuario especificado y sincroniza JSON."""
    if amount <= 0:
        raise ValueError("El monto debe ser un número positivo mayor a 0.")
    
    clean_type = type_.strip().lower()
    if clean_type not in ("gasto", "ingreso"):
        raise ValueError("El tipo debe ser 'gasto' o 'ingreso'.")

    clean_category = category.strip().capitalize() or "Otros"
    clean_description = (description or "").strip()

    # Asegurar que el usuario exista en la tabla users
    get_or_create_user(user_id, username="", first_name="Usuario")

    final_created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO transactions (user_id, type, amount, category, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, clean_type, round(amount, 2), clean_category, clean_description, final_created_at)
        )
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (new_id,))
        record = dict(cursor.fetchone())

    # Sincronizar automáticamente con transacciones.json
    export_transactions_to_json()
    return record

def delete_transaction(user_id: int, transaction_id: int) -> bool:
    """Elimina una transacción por su ID y actualiza el archivo JSON."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, user_id)
        )
        deleted = cursor.rowcount > 0

    if deleted:
        export_transactions_to_json()
    return deleted

def clear_all_transactions(user_id: Optional[int] = None) -> int:
    """
    Elimina físicamente todas las transacciones de SQLite y actualiza transacciones.json
    y transacciones_data.js dejándolos limpios.
    """
    with get_db_cursor() as cursor:
        if user_id is not None:
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("DELETE FROM transactions")
            # SQLite
            try:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'transactions'")
            except Exception:
                pass
            # PostgreSQL
            try:
                cursor.execute("ALTER SEQUENCE transactions_id_seq RESTART WITH 1")
            except Exception:
                pass
        deleted_count = cursor.rowcount

    export_transactions_to_json()
    return deleted_count

def get_last_transaction(user_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene la última transacción registrada por el usuario."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_balance(user_id: int) -> Dict[str, Any]:
    """Calcula el balance global histórico del usuario."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'ingreso' THEN amount ELSE 0 END), 0.0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'gasto' THEN amount ELSE 0 END), 0.0) as total_expense,
                COUNT(*) as total_count
            FROM transactions
            WHERE user_id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        income = float(row["total_income"])
        expense = float(row["total_expense"])
        return {
            "total_income": income,
            "total_expense": expense,
            "net_balance": income - expense,
            "total_count": int(row["total_count"])
        }

def get_summary_by_date_range(
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Genera un resumen detallado con desglose por categorías en un rango de fechas."""
    start_str = start_date.strftime("%Y-%m-%d 00:00:00")
    end_str = end_date.strftime("%Y-%m-%d 23:59:59")

    with get_db_cursor() as cursor:
        # Totales generales del periodo
        cursor.execute(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'ingreso' THEN amount ELSE 0 END), 0.0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'gasto' THEN amount ELSE 0 END), 0.0) as total_expense,
                COUNT(*) as total_count
            FROM transactions
            WHERE user_id = ? AND created_at BETWEEN ? AND ?
            """,
            (user_id, start_str, end_str)
        )
        totals = cursor.fetchone()
        total_income = float(totals["total_income"])
        total_expense = float(totals["total_expense"])

        # Desglose de gastos por categoría
        cursor.execute(
            """
            SELECT 
                category,
                SUM(amount) as category_total,
                COUNT(*) as count
            FROM transactions
            WHERE user_id = ? AND type = 'gasto' AND created_at BETWEEN ? AND ?
            GROUP BY category
            ORDER BY category_total DESC
            """,
            (user_id, start_str, end_str)
        )
        expense_rows = cursor.fetchall()
        expense_by_category = []
        for r in expense_rows:
            cat_total = float(r["category_total"])
            pct = (cat_total / total_expense * 100) if total_expense > 0 else 0.0
            expense_by_category.append({
                "category": r["category"],
                "total": cat_total,
                "count": int(r["count"]),
                "percentage": round(pct, 1)
            })

        # Desglose de ingresos por categoría
        cursor.execute(
            """
            SELECT 
                category,
                SUM(amount) as category_total,
                COUNT(*) as count
            FROM transactions
            WHERE user_id = ? AND type = 'ingreso' AND created_at BETWEEN ? AND ?
            GROUP BY category
            ORDER BY category_total DESC
            """,
            (user_id, start_str, end_str)
        )
        income_rows = cursor.fetchall()
        income_by_category = [
            {
                "category": r["category"],
                "total": float(r["category_total"]),
                "count": int(r["count"])
            }
            for r in income_rows
        ]

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense,
            "total_count": int(totals["total_count"]),
            "expense_by_category": expense_by_category,
            "income_by_category": income_by_category,
            "start_date": start_date,
            "end_date": end_date
        }

def get_today_summary(user_id: int) -> Dict[str, Any]:
    """Genera el resumen de las transacciones del día de hoy."""
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0)
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
    return get_summary_by_date_range(user_id, start_of_day, end_of_day)

def get_yesterday_summary(user_id: int) -> Dict[str, Any]:
    """Genera el resumen de las transacciones del día de ayer."""
    yesterday = datetime.now() - timedelta(days=1)
    start_of_day = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
    end_of_day = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    return get_summary_by_date_range(user_id, start_of_day, end_of_day)

def get_current_month_summary(user_id: int) -> Dict[str, Any]:
    """Genera el resumen desde el día 1 del mes actual hasta hoy."""
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    return get_summary_by_date_range(user_id, start_of_month, now)

def get_last_7_days_summary(user_id: int) -> Dict[str, Any]:
    """Genera el resumen de los últimos 7 días."""
    now = datetime.now()
    start_7_days = now - timedelta(days=6)
    return get_summary_by_date_range(user_id, start_7_days, now)

def get_recent_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Devuelve las transacciones más recientes ordenadas por fecha descendente."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
