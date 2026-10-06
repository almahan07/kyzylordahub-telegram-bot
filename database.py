import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
import aiosqlite
from config import DB_PATH, COURSES, get_course_code, get_course_limit

logger = logging.getLogger(__name__)

# Race condition болдырмау үшін асинхронды құлып (Lock)
_db_lock = asyncio.Lock()


async def init_db() -> None:
    """Деректер базасы мен кестелерді инициализациялау."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")

        # Пайдаланушылардың әр курс бойынша алған промокодтары кестесі
        # Әр пайдаланушы бірнеше курсқа промокод ала алады, бірақ бір курсқа тек 1 рет!
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_promos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                course TEXT NOT NULL,
                promocode TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, course)
            );
            """
        )

        # Ескі users кестесінен деректерді көшіру (егер бар болса)
        try:
            await db.execute(
                """
                INSERT OR IGNORE INTO user_promos (user_id, username, course, promocode, created_at)
                SELECT user_id, username, course, promocode, created_at FROM users;
                """
            )
        except Exception:
            pass

        # Жеке жүктелетін промокодтар кестесі
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS promocodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                is_used INTEGER DEFAULT 0,
                user_id INTEGER DEFAULT NULL
            );
            """
        )

        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_promos_uid_course 
            ON user_promos(user_id, course);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_promocodes_course_used 
            ON promocodes(course, is_used);
            """
        )
        await db.commit()
    logger.info("Деректер базасы сәтті инициализацияланды.")


async def get_user_course_promo(user_id: int, course_key: str) -> Optional[Dict[str, Any]]:
    """Пайдаланушының нақты осы курсқа промокод алғанын тексеру."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, username, course, promocode, created_at FROM user_promos WHERE user_id = ? AND course = ?",
            (user_id, course_key),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None


async def get_user_claimed_courses(user_id: int) -> List[Dict[str, Any]]:
    """Пайдаланушының бұрын алған барлық курстары мен промокодтарының тізімін алу."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT course, promocode, created_at FROM user_promos WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def claim_promocode(
    user_id: int, username: Optional[str], course_key: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Пайдаланушыға таңдалған курстың промокодын беру.
    Логика:
    1) Бір пайдаланушы бірнеше түрлі курсқа промокод ала алады!
    2) Бірақ бір курсқа қайта ала алмайды (әр курсқа 1 реттен).
    3) Егер бұрын осы курсқа алған болса -> 'already_claimed' қайтарады.
    4) Егер алмаған болса -> промокодты береді.
    """
    async with _db_lock:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE;")

            try:
                # 1. Осы курсқа бұрын алған ба тексереміз
                async with db.execute(
                    "SELECT promocode FROM user_promos WHERE user_id = ? AND course = ?",
                    (user_id, course_key),
                ) as cur:
                    existing = await cur.fetchone()
                    if existing:
                        await db.commit()
                        return False, existing["promocode"], "already_claimed"

                promo_code = None

                # 2. Жеке жүктелген промокод бар ма тексереміз
                async with db.execute(
                    """
                    SELECT id, code FROM promocodes
                    WHERE course = ? AND is_used = 0
                    ORDER BY id ASC
                    LIMIT 1
                    """,
                    (course_key,),
                ) as cur:
                    individual_promo = await cur.fetchone()

                if individual_promo:
                    promo_id = individual_promo["id"]
                    promo_code = individual_promo["code"]
                    await db.execute(
                        "UPDATE promocodes SET is_used = 1, user_id = ? WHERE id = ?",
                        (user_id, promo_id),
                    )
                else:
                    # 3. Ресми хаб промокодын лимит бойынша береміз
                    default_code = get_course_code(course_key)
                    limit = get_course_limit(course_key)

                    # Осы курсқа қанша промокод берілгенін санаймыз
                    async with db.execute(
                        "SELECT COUNT(*) FROM user_promos WHERE course = ?",
                        (course_key,),
                    ) as cur:
                        row = await cur.fetchone()
                        used_count = row[0] if row else 0

                    if used_count >= limit or not default_code:
                        await db.rollback()
                        return False, None, "out_of_stock"

                    promo_code = default_code

                # 4. user_promos кестесіне жазу
                await db.execute(
                    """
                    INSERT INTO user_promos (user_id, username, course, promocode, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, username or "", course_key, promo_code),
                )

                await db.commit()
                logger.info(
                    f"User {user_id} (@{username}) claimed promo '{promo_code}' for course '{course_key}'"
                )
                return True, promo_code, None

            except Exception as e:
                await db.rollback()
                logger.error(f"Промокод беру кезінде қате: {e}", exc_info=True)
                raise e


async def add_promocodes(items: List[Tuple[str, str]]) -> Tuple[int, int]:
    """Жеке промокодтарды базаға қосу (дубликаттар өткізіледі)."""
    if not items:
        return 0, 0

    async with _db_lock:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("BEGIN TRANSACTION;")
            try:
                existing_codes = set()
                async with db.execute("SELECT code FROM promocodes") as cur:
                    async for row in cur:
                        existing_codes.add(row[0])

                added = 0
                duplicates = 0
                for course, code in items:
                    code_cleaned = code.strip()
                    if code_cleaned in existing_codes:
                        duplicates += 1
                        continue

                    await db.execute(
                        "INSERT INTO promocodes (course, code, is_used) VALUES (?, ?, 0)",
                        (course, code_cleaned),
                    )
                    existing_codes.add(code_cleaned)
                    added += 1

                await db.commit()
                return added, duplicates
            except Exception as e:
                await db.rollback()
                logger.error(f"Промокодтарды сақтауда қате: {e}", exc_info=True)
                raise e


async def get_stats() -> Dict[str, Any]:
    """Курстар мен промокодтардың нақты статистикасын есептеу."""
    stats: Dict[str, Any] = {
        "courses": {},
        "total_users": 0,
        "grand_total": 0,
        "grand_used": 0,
        "grand_available": 0,
    }

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Бірегей пайдаланушылар саны
        async with db.execute("SELECT COUNT(DISTINCT user_id) as cnt FROM user_promos") as cur:
            row = await cur.fetchone()
            stats["total_users"] = row["cnt"] if row else 0

        for course_key in COURSES.keys():
            limit = get_course_limit(course_key)

            # Осы курсты алғандар саны
            async with db.execute(
                "SELECT COUNT(*) FROM user_promos WHERE course = ?",
                (course_key,),
            ) as cur:
                user_row = await cur.fetchone()
                users_on_course = user_row[0] if user_row else 0

            # promocodes кестесінде жеке кодтар бар ма
            async with db.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_used = 1 THEN 1 ELSE 0 END) as used,
                    SUM(CASE WHEN is_used = 0 THEN 1 ELSE 0 END) as available
                FROM promocodes
                WHERE course = ?
                """,
                (course_key,),
            ) as cur:
                row = await cur.fetchone()
                db_total = row["total"] if row and row["total"] is not None else 0
                db_used = row["used"] if row and row["used"] is not None else 0
                db_available = row["available"] if row and row["available"] is not None else 0

            if db_total > 0:
                total = db_total
                used = db_used
                available = db_available
            else:
                total = limit
                used = users_on_course
                available = max(0, limit - users_on_course)

            stats["courses"][course_key] = {
                "total": total,
                "used": used,
                "available": available,
            }
            stats["grand_total"] += total
            stats["grand_used"] += used
            stats["grand_available"] += available

    return stats


async def get_all_user_ids() -> List[int]:
    """Хабарлама тарату үшін барлық бірегей пайдаланушылардың ID тізімін алу."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT DISTINCT user_id FROM user_promos") as cur:
            rows = await cur.fetchall()
            return [row[0] for row in rows]
