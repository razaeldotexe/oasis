import aiosqlite
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tickets.db")


async def init_db():
    """Inisialisasi database tiket — buat tabel jika belum ada."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id     TEXT    NOT NULL,
                channel_id   TEXT    UNIQUE,
                user_id      TEXT    NOT NULL,
                judul        TEXT    NOT NULL,
                deskripsi    TEXT,
                kategori     TEXT,
                prioritas    TEXT    DEFAULT 'Low',
                status       TEXT    DEFAULT 'OPEN',
                claimed_by   TEXT,
                claimed_at   DATETIME,
                rating       INTEGER,
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_by    TEXT,
                closed_at    DATETIME
            )
        """)
        await db.commit()


async def create_ticket(
    guild_id: str,
    channel_id: str,
    user_id: str,
    judul: str,
    deskripsi: str,
    kategori: str,
    prioritas: str,
) -> int:
    """Simpan tiket baru ke database. Mengembalikan ticket_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO tickets (guild_id, channel_id, user_id, judul, deskripsi, kategori, prioritas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, channel_id, user_id, judul, deskripsi, kategori, prioritas),
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_ticket(user_id: str, guild_id: str) -> dict | None:
    """Cek apakah pengguna sudah punya tiket aktif (OPEN / IN_PROGRESS)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM tickets
            WHERE user_id = ? AND guild_id = ? AND status IN ('OPEN', 'IN_PROGRESS')
            LIMIT 1
            """,
            (user_id, guild_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_ticket_by_channel(channel_id: str) -> dict | None:
    """Cari tiket berdasarkan channel_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE channel_id = ?",
            (channel_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_ticket(ticket_id: int, **kwargs) -> None:
    """Perbarui kolom tertentu pada tiket."""
    if not kwargs:
        return
    columns = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values())
    values.append(ticket_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE tickets SET {columns} WHERE ticket_id = ?",
            values,
        )
        await db.commit()


async def claim_ticket(ticket_id: int, staff_id: str) -> None:
    """Staff mengklaim tiket — ubah status ke IN_PROGRESS."""
    await update_ticket(
        ticket_id,
        status="IN_PROGRESS",
        claimed_by=staff_id,
        claimed_at=datetime.now().isoformat(),
    )


async def close_ticket(ticket_id: int, closed_by: str) -> None:
    """Tutup tiket — ubah status ke CLOSED."""
    await update_ticket(
        ticket_id,
        status="CLOSED",
        closed_by=closed_by,
        closed_at=datetime.now().isoformat(),
    )


async def set_ticket_rating(ticket_id: int, rating: int) -> None:
    """Simpan rating dari pengguna."""
    await update_ticket(ticket_id, rating=rating)
