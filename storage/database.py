"""
Camada de Persistência SQLite para o Produto SaaS (AlphaMacro B3).
Gerencia:
1. Carteiras salvas pelos usuários (saved_portfolios)
2. Leads e assinantes capturados (leads_subscribers)
3. Telemetria de eventos de uso e conversão (usage_events)
4. Configurações comerciais do fundador (saas_settings)
"""
import json
import os
import sqlite3
import datetime
from typing import Dict, Any, List, Optional


class SaaSDatabase:
    """Gerenciador SQLite thread-safe para persistência de carteiras, leads e métricas SaaS."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "saas_platform.db")
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saved_portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT UNIQUE NOT NULL,
                    portfolio_name TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    holdings_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leads_subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    whatsapp TEXT,
                    broker TEXT,
                    experience_level TEXT,
                    tier TEXT DEFAULT 'free',
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_tier TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saas_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Semear dados iniciais de demonstração caso a tabela de leads esteja vazia
            cur.execute("SELECT COUNT(*) as cnt FROM leads_subscribers")
            if cur.fetchone()["cnt"] == 0:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                seed_leads = [
                    ("Wallace Abreu (Fundador)", "founder@alphamacro.com.br", "(11) 99999-0000", "Itaú / Íon Itaú", "Avançado", "founder", now_str),
                    ("Carlos Eduardo Silva", "carlos.silva@email.com", "(11) 98811-2233", "XP Investimentos", "Intermediário", "pro", now_str),
                    ("Mariana Costa", "mariana.costa@email.com", "(21) 97722-3344", "Itaú / Íon Itaú", "Iniciante", "pro", now_str),
                    ("Roberto Almeida", "roberto.almeida@email.com", "(31) 99123-4567", "BTG Pactual", "Intermediário", "free", now_str),
                    ("Fernanda Oliveira", "fernanda.oli@email.com", "(41) 98456-7890", "Nubank / NuInvest", "Nunca investi", "free", now_str),
                    ("Lucas Mendes", "lucas.mendes@email.com", "(51) 99345-6789", "Banco Inter", "Iniciante", "pro", now_str),
                ]
                cur.executemany("""
                    INSERT OR IGNORE INTO leads_subscribers
                    (name, email, whatsapp, broker, experience_level, tier, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, seed_leads)

            # Semear carteira padrão do fundador caso não exista
            cur.execute("SELECT COUNT(*) as cnt FROM saved_portfolios")
            if cur.fetchone()["cnt"] == 0:
                default_holdings = [
                    {"Ticker (B3)": "TAEE11", "Quantidade": 100, "Preço Médio (R$)": 38.00},
                    {"Ticker (B3)": "CXSE3", "Quantidade": 220, "Preço Médio (R$)": 16.50},
                    {"Ticker (B3)": "BBSE3", "Quantidade": 115, "Preço Médio (R$)": 33.20},
                    {"Ticker (B3)": "ISAE4", "Quantidade": 150, "Preço Médio (R$)": 25.80},
                    {"Ticker (B3)": "BBAS3", "Quantidade": 170, "Preço Médio (R$)": 23.00},
                ]
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                cur.execute("""
                    INSERT OR IGNORE INTO saved_portfolios
                    (user_key, portfolio_name, broker, holdings_json, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, ("minha_carteira_itau", "Carteira Principal Itaú", "Itaú / Íon Itaú", json.dumps(default_holdings), now_str))

            conn.commit()
        finally:
            conn.close()

    def save_portfolio(
        self,
        user_key: str,
        portfolio_name: str,
        broker: str,
        holdings: List[Dict[str, Any]]
    ) -> bool:
        """Salva ou atualiza uma carteira de usuário no banco SQLite."""
        clean_key = user_key.strip().lower()
        if not clean_key:
            return False
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO saved_portfolios (user_key, portfolio_name, broker, holdings_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_key) DO UPDATE SET
                    portfolio_name = excluded.portfolio_name,
                    broker = excluded.broker,
                    holdings_json = excluded.holdings_json,
                    updated_at = excluded.updated_at
            """, (clean_key, portfolio_name.strip() or "Minha Carteira", broker, json.dumps(holdings), now_str))
            conn.commit()
            return True
        finally:
            conn.close()

    def load_portfolio(self, user_key: str) -> Optional[Dict[str, Any]]:
        """Carrega uma carteira salva pelo identificador do usuário."""
        clean_key = user_key.strip().lower()
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "SELECT user_key, portfolio_name, broker, holdings_json, updated_at FROM saved_portfolios WHERE user_key = ?",
                (clean_key,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_key": row["user_key"],
                "portfolio_name": row["portfolio_name"],
                "broker": row["broker"],
                "holdings": json.loads(row["holdings_json"]),
                "updated_at": row["updated_at"],
            }
        finally:
            conn.close()

    def list_saved_portfolios(self) -> List[Dict[str, Any]]:
        """Lista todas as carteiras salvas."""
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT user_key, portfolio_name, broker, updated_at FROM saved_portfolios ORDER BY updated_at DESC")
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def register_lead(
        self,
        name: str,
        email: str,
        whatsapp: str = "",
        broker: str = "Itaú / Íon Itaú",
        experience_level: str = "Iniciante",
        tier: str = "free"
    ) -> bool:
        """Cadastra ou atualiza um lead/assinante na base de marketing e vendas."""
        clean_email = email.strip().lower()
        if not clean_email or "@" not in clean_email:
            return False
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO leads_subscribers (name, email, whatsapp, broker, experience_level, tier, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    whatsapp = excluded.whatsapp,
                    broker = excluded.broker,
                    experience_level = excluded.experience_level
            """, (name.strip() or "Investidor", clean_email, whatsapp.strip(), broker, experience_level, tier, now_str))
            conn.commit()
            return True
        finally:
            conn.close()

    def list_leads(self) -> List[Dict[str, Any]]:
        """Retorna todos os leads e assinantes cadastrados."""
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT id, name, email, whatsapp, broker, experience_level, tier, created_at FROM leads_subscribers ORDER BY id DESC")
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def log_event(self, event_type: str, user_tier: str, details: str = "") -> None:
        """Registra evento de telemetria e conversão."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO usage_events (event_type, user_tier, details, created_at) VALUES (?, ?, ?, ?)",
                (event_type, user_tier, details, now_str)
            )
            conn.commit()
        finally:
            conn.close()

    def set_setting(self, key: str, value: str) -> None:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO saas_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (key, value, now_str))
            conn.commit()
        finally:
            conn.close()

    def get_setting(self, key: str, default: str = "") -> str:
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT value FROM saas_settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else default
        finally:
            conn.close()

