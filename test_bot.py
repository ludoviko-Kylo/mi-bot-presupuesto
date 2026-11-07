import os
import unittest
from datetime import datetime
from database import init_db, get_or_create_user, get_db_cursor
from services.transaction_service import (
    add_transaction,
    delete_transaction,
    get_last_transaction,
    get_balance,
    get_today_summary,
    get_current_month_summary,
    get_last_7_days_summary,
    get_recent_transactions
)
from handlers.transactions import parse_quick_text, parse_transaction_arguments
from utils.formatters import format_currency, render_progress_bar

class TestBudgetBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Asegurar inicialización de base de datos
        init_db()

    def setUp(self):
        # Usuario de prueba fijo
        self.test_user_id = 99999999
        get_or_create_user(self.test_user_id, "test_user", "Tester")
        
        # Limpiar transacciones del usuario de prueba antes de cada test
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (self.test_user_id,))

    def tearDown(self):
        # Limpiar transacciones del usuario de prueba después de cada test
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (self.test_user_id,))
        from services.transaction_service import export_transactions_to_json
        export_transactions_to_json()

    def test_add_and_get_balance(self):
        # Registrar un ingreso y dos gastos
        add_transaction(self.test_user_id, "ingreso", 1000.0, "Sueldo", "Pago mensual")
        add_transaction(self.test_user_id, "gasto", 250.0, "Comida", "Restaurante")
        add_transaction(self.test_user_id, "gasto", 150.0, "Transporte", "Combustible")

        balance = get_balance(self.test_user_id)
        self.assertEqual(balance["total_income"], 1000.0)
        self.assertEqual(balance["total_expense"], 400.0)
        self.assertEqual(balance["net_balance"], 600.0)
        self.assertEqual(balance["total_count"], 3)

    def test_delete_and_undo(self):
        tx1 = add_transaction(self.test_user_id, "gasto", 50.0, "Ocio", "Cine")
        tx2 = add_transaction(self.test_user_id, "gasto", 80.0, "Comida", "Pizza")

        # Verificar última transacción
        last_tx = get_last_transaction(self.test_user_id)
        self.assertIsNotNone(last_tx)
        self.assertEqual(last_tx["id"], tx2["id"])

        # Borrar tx2
        deleted = delete_transaction(self.test_user_id, tx2["id"])
        self.assertTrue(deleted)

        # Ahora la última debe ser tx1
        last_tx_after = get_last_transaction(self.test_user_id)
        self.assertEqual(last_tx_after["id"], tx1["id"])

    def test_month_and_week_summary(self):
        add_transaction(self.test_user_id, "ingreso", 2000.0, "Sueldo")
        add_transaction(self.test_user_id, "gasto", 300.0, "Comida")
        add_transaction(self.test_user_id, "gasto", 100.0, "Transporte")

        month_sum = get_current_month_summary(self.test_user_id)
        self.assertEqual(month_sum["total_income"], 2000.0)
        self.assertEqual(month_sum["total_expense"], 400.0)
        self.assertEqual(len(month_sum["expense_by_category"]), 2)

        # Verificar cálculo de porcentajes
        comida = next(c for c in month_sum["expense_by_category"] if c["category"] == "Comida")
        self.assertEqual(comida["percentage"], 75.0)

        week_sum = get_last_7_days_summary(self.test_user_id)
        self.assertEqual(week_sum["total_expense"], 400.0)

        today_sum = get_today_summary(self.test_user_id)
        self.assertEqual(today_sum["total_income"], 2000.0)
        self.assertEqual(today_sum["total_expense"], 400.0)
        self.assertEqual(today_sum["net_balance"], 1600.0)

    def test_parse_quick_text(self):
        # Test -150 comida café
        res1 = parse_quick_text("-150 comida café")
        self.assertIsNotNone(res1)
        self.assertEqual(res1, ("gasto", 150.0, "comida", "café"))

        # Test +2500 sueldo quincena
        res2 = parse_quick_text("+2500 sueldo quincena")
        self.assertIsNotNone(res2)
        self.assertEqual(res2, ("ingreso", 2500.0, "sueldo", "quincena"))

        # Test gasto 350.50 transporte
        res3 = parse_quick_text("gasto 350.50 transporte")
        self.assertIsNotNone(res3)
        self.assertEqual(res3, ("gasto", 350.5, "transporte", ""))

    def test_parse_arguments(self):
        amount, cat, desc = parse_transaction_arguments(["150,50", "comida", "almuerzo", "de", "negocios"])
        self.assertEqual(amount, 150.50)
        self.assertEqual(cat, "comida")
        self.assertEqual(desc, "almuerzo de negocios")

    def test_formatters(self):
        formatted = format_currency(1250.5, "$")
        self.assertIn("1.250,50", formatted)

        bar = render_progress_bar(50.0, length=10)
        self.assertEqual(len(bar), 10) # 10 emojis

    def test_postgres_detection_and_normalization(self):
        from database import is_postgres, get_normalized_pg_url
        import config

        orig_db_url = config.DATABASE_URL
        try:
            # Test empty url -> SQLite
            config.DATABASE_URL = ""
            self.assertFalse(is_postgres())

            # Test postgres:// -> normalized to postgresql://
            config.DATABASE_URL = "postgres://user:pass@host:5432/db"
            self.assertTrue(is_postgres())
            self.assertEqual(get_normalized_pg_url(), "postgresql://user:pass@host:5432/db")

            # Test postgresql://
            config.DATABASE_URL = "postgresql://user:pass@host:5432/db"
            self.assertTrue(is_postgres())
            self.assertEqual(get_normalized_pg_url(), "postgresql://user:pass@host:5432/db")
        finally:
            config.DATABASE_URL = orig_db_url

if __name__ == "__main__":
    unittest.main()
