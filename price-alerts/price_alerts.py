#!/usr/bin/env python3
"""
WorthItGoods Price Alert System
================================
Tracks product prices and notifies subscribers when prices drop.

Database: SQLite (price_alerts.db)
Email: AgentMail
Price source: Amazon Creators API (reuses chipradar's implementation)

Tables:
- subscribers (email, asin, subscribed_at, last_notified_price, last_notified_at)
- price_history (asin, price, currency, checked_at)
"""

import sqlite3
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

BASE = Path(__file__).parent
DB_PATH = BASE / "price_alerts.db"
PRODUCTS_FILE = BASE.parent / "worthitgoods_products.json"


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            asin TEXT NOT NULL,
            product_title TEXT,
            subscribed_at TEXT DEFAULT (datetime('now')),
            last_notified_price REAL,
            last_notified_at TEXT,
            is_active INTEGER DEFAULT 1,
            UNIQUE(email, asin)
        );
        
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            checked_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions(email);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_asin ON subscriptions(asin);
        CREATE INDEX IF NOT EXISTS idx_price_history_asin ON price_history(asin);
        CREATE INDEX IF NOT EXISTS idx_price_history_time ON price_history(checked_at);
    """)
    
    conn.commit()
    conn.close()
    print("✅ Price alert database initialized")


def subscribe(email: str, asin: str, product_title: str = "") -> dict:
    """Subscribe an email to price alerts for a specific ASIN."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR IGNORE INTO subscriptions (email, asin, product_title)
               VALUES (?, ?, ?)""",
            (email.strip().lower(), asin.strip(), product_title)
        )
        conn.commit()
        if cursor.rowcount > 0:
            return {"success": True, "message": "Subscribed successfully"}
        else:
            return {"success": False, "message": "Already subscribed to this product"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def unsubscribe(email: str, asin: str = None) -> dict:
    """Unsubscribe email from all or specific ASIN alerts."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        email = email.strip().lower()
        if asin:
            cursor.execute(
                "DELETE FROM subscriptions WHERE email = ? AND asin = ?",
                (email, asin.strip())
            )
            msg = "Unsubscribed from this product"
        else:
            cursor.execute("DELETE FROM subscriptions WHERE email = ?", (email,))
            msg = "Unsubscribed from all alerts"
        conn.commit()
        return {"success": True, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def get_subscribers_for_asin(asin: str) -> list:
    """Get all active subscribers for a specific ASIN."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT email, product_title, last_notified_price FROM subscriptions WHERE asin = ? AND is_active = 1",
        (asin,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_all_active_subscriptions() -> list:
    """Get all active subscriptions grouped by ASIN."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT asin, product_title, COUNT(*) as subscriber_count, 
                  GROUP_CONCAT(email) as emails
           FROM subscriptions WHERE is_active = 1
           GROUP BY asin"""
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_last_price(asin: str) -> Optional[float]:
    """Get the most recent price for an ASIN."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price FROM price_history WHERE asin = ? ORDER BY checked_at DESC LIMIT 1",
        (asin,)
    )
    row = cursor.fetchone()
    conn.close()
    return row["price"] if row else None


def record_price(asin: str, price: float):
    """Record a price check in history."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO price_history (asin, price, currency) VALUES (?, ?, 'USD')",
        (asin, price)
    )
    conn.commit()
    conn.close()


def mark_notified(email: str, asin: str, price: float):
    """Mark that a subscriber was notified at this price."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE subscriptions 
           SET last_notified_price = ?, last_notified_at = datetime('now')
           WHERE email = ? AND asin = ?""",
        (price, email, asin)
    )
    conn.commit()
    conn.close()


def get_subscription_count() -> int:
    """Get total active subscriptions."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM subscriptions WHERE is_active = 1")
    count = cursor.fetchone()["count"]
    conn.close()
    return count


def get_unique_subscriber_count() -> int:
    """Get number of unique active subscribers."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT email) as count FROM subscriptions WHERE is_active = 1")
    count = cursor.fetchone()["count"]
    conn.close()
    return count


if __name__ == "__main__":
    init_db()
    print(f"  Subscriptions: {get_subscription_count()}")
    print(f"  Unique subscribers: {get_unique_subscriber_count()}")
    print(f"  Price records: ", end="")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM price_history")
    print(cursor.fetchone()["count"])
    conn.close()