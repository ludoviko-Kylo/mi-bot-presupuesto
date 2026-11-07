import logging
import sys

# Asegurar codificación UTF-8 en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import TELEGRAM_BOT_TOKEN, PORT, HOST, DATABASE_URL, APP_URL
from database import init_db, get_db_cursor, is_postgres
from handlers.basic import start_handler, help_handler
from handlers.transactions import (
    expense_handler,
    income_handler,
    delete_handler,
    undo_handler,
    quick_text_handler
)
from handlers.reports import (
    balance_handler,
    today_summary_handler,
    month_summary_handler,
    week_summary_handler,
    history_handler
)
from services.transaction_service import (
    export_transactions_to_json,
    add_transaction,
    delete_transaction,
    clear_all_transactions
)
import http.server
import socketserver
import threading
import json
from urllib.parse import urlparse
from functools import partial

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("PresupuestoBot")

def run_local_server(port: int = None, host: str = None) -> None:
    """Ejecuta un servidor HTTP en segundo plano con soporte para API REST, CORS y archivos estáticos."""
    server_port = int(port if port is not None else PORT)
    server_host = str(host if host is not None else HOST)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(BASE_DIR), **kwargs)

        def log_message(self, format, *args):
            # No saturar la consola con logs de peticiones HTTP estáticas
            pass

        def _send_cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS, PUT")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

        def end_headers(self):
            self._send_cors_headers()
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.end_headers()

        def do_GET(self):
            parsed = urlparse(self.path)
            clean_path = parsed.path.rstrip("/")

            if clean_path in ("/api/health", "/health"):
                resp = json.dumps({"status": "ok", "app": "mi-bot-presupuesto"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                return

            if clean_path in ("/api/transactions", "/api/transactions/all"):
                try:
                    target_file = BASE_DIR / "transacciones.json"
                    if target_file.exists():
                        with open(target_file, "r", encoding="utf-8") as f:
                            data = f.read().encode("utf-8")
                    else:
                        data = json.dumps({"total_count": 0, "transactions": []}).encode("utf-8")

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception as e:
                    err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(err)))
                    self.end_headers()
                    self.wfile.write(err)
                    return

            # Para archivos estáticos, delegar en SimpleHTTPRequestHandler
            super().do_GET()

        def do_DELETE(self):
            parsed = urlparse(self.path)
            clean_path = parsed.path.rstrip("/")

            if clean_path in ("/api/transactions", "/api/clear", "/api/reset"):
                try:
                    deleted_count = clear_all_transactions()
                    resp = {
                        "status": "ok",
                        "message": "Todas las transacciones han sido eliminadas físicamente de la base de datos.",
                        "deleted_count": deleted_count
                    }
                    payload = json.dumps(resp).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors_headers()
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors_headers()
                    self.send_header("Content-Length", str(len(err)))
                    self.end_headers()
                    self.wfile.write(err)
            elif clean_path.startswith("/api/transactions/"):
                try:
                    raw_id = clean_path.split("/")[-1].replace("tx_", "")
                    tx_id = int(raw_id)
                    with get_db_cursor() as cursor:
                        cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
                        deleted = cursor.rowcount > 0
                    export_transactions_to_json()
                    resp = {"status": "ok", "deleted": deleted, "id": tx_id}
                    payload = json.dumps(resp).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors_headers()
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors_headers()
                    self.send_header("Content-Length", str(len(err)))
                    self.end_headers()
                    self.wfile.write(err)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            parsed = urlparse(self.path)
            clean_path = parsed.path.rstrip("/")

            if clean_path in ("/api/clear", "/api/reset"):
                return self.do_DELETE()

            if clean_path == "/api/transactions":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    data = json.loads(body.decode("utf-8"))

                    tx_type = "gasto" if data.get("type") == "expense" else (data.get("type") or "gasto")
                    amount = float(data.get("amount", 0))
                    category = data.get("category", "Otros")
                    concept = data.get("concept") or data.get("description") or ""
                    created_at = data.get("created_at") or data.get("datetime")
                    user_id = int(data.get("user_id", 1))

                    tx = add_transaction(
                        user_id=user_id,
                        type_=tx_type,
                        amount=amount,
                        category=category,
                        description=concept,
                        created_at=created_at
                    )

                    resp = {"status": "ok", "transaction": tx}
                    payload = json.dumps(resp).encode("utf-8")
                    self.send_response(201)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors_headers()
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors_headers()
                    self.send_header("Content-Length", str(len(err)))
                    self.end_headers()
                    self.wfile.write(err)
            else:
                self.send_response(404)
                self.end_headers()

    socketserver.TCPServer.allow_reuse_address = True
    ports_to_try = [server_port] if server_port != 8000 else [server_port, 8080, 5500, 8001]
    for p in ports_to_try:
        try:
            with socketserver.TCPServer((server_host, p), QuietHandler) as httpd:
                print(f"🌐 Panel Web disponible en: http://{server_host}:{p} (API activa)")
                httpd.serve_forever()
                break
        except OSError as e:
            if p == ports_to_try[-1]:
                print(f"⚠️ No se pudo iniciar el servidor web en el puerto {p}: {e}")
            continue

async def button_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Distribuye las pulsaciones del teclado inferior a sus respectivos manejadores."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text in ("☀️ Hoy", "📅 Hoy", "Hoy"):
        await today_summary_handler(update, context)
    elif text == "📊 Balance":
        await balance_handler(update, context)
    elif text == "📅 Resumen Mes":
        await month_summary_handler(update, context)
    elif text == "🗓️ Esta Semana":
        await week_summary_handler(update, context)
    elif text == "🧾 Historial":
        await history_handler(update, context)
    elif text == "❓ Ayuda":
        await help_handler(update, context)
    else:
        # Si no es un botón fijo, evaluar si es un atajo rápido (+500, -150 comida, etc.)
        await quick_text_handler(update, context)

def main() -> None:
    """Punto de entrada principal para ejecutar el bot y sincronizar la app web."""
    print("=" * 60)
    print(" 🤖 INICIANDO BOT DE PRESUPUESTO PERSONAL EN TELEGRAM")
    print("=" * 60)

    # 1. Verificar Token
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "tu_token_aqui":
        print("\n❌ ERROR: No se ha configurado el TELEGRAM_BOT_TOKEN en el archivo .env")
        print("\nPasos para configurarlo:")
        print("1. Abre Telegram y busca @BotFather")
        print("2. Envía /newbot y sigue los pasos para obtener tu Token")
        print("3. Crea o edita el archivo .env en esta carpeta:")
        print("   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz")
        print("4. Vuelve a ejecutar: python main.py\n")
        sys.exit(1)

    # 2. Inicializar Base de Datos (PostgreSQL o SQLite)
    if is_postgres():
        print("🐘 Conectando a PostgreSQL / Supabase en la nube...")
    else:
        print("📦 Inicializando base de datos SQLite local...")
    init_db()
    print("✅ Base de datos lista.")

    # 3. Sincronizar transacciones.json inicial
    print("📄 Sincronizando transacciones.json...")
    export_transactions_to_json()
    print("✅ Archivo transacciones.json actualizado.")

    # 4. Iniciar servidor web en segundo plano
    web_thread = threading.Thread(target=run_local_server, args=(PORT, HOST), daemon=True)
    web_thread.start()

    # 5. Construir la aplicación del bot
    print("🔌 Conectando con la API de Telegram...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Comandos básicos
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler(["ayuda", "help"], help_handler))

    # Comandos de transacciones
    app.add_handler(CommandHandler("gasto", expense_handler))
    app.add_handler(CommandHandler("ingreso", income_handler))
    app.add_handler(CommandHandler("borrar", delete_handler))
    app.add_handler(CommandHandler("deshacer", undo_handler))

    # Comandos de reportes
    app.add_handler(CommandHandler(["hoy", "today"], today_summary_handler))
    app.add_handler(CommandHandler("balance", balance_handler))
    app.add_handler(CommandHandler("resumen", month_summary_handler))
    app.add_handler(CommandHandler(["semana", "week"], week_summary_handler))
    app.add_handler(CommandHandler(["historial", "history"], history_handler))

    # Manejo de botones de teclado inferior y texto rápido
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_dispatcher))

    print("🚀 Bot en funcionamiento (Polling activo). Presiona Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()

