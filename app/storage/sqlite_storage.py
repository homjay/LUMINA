"""SQLite storage implementation."""
import aiosqlite
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from app.models.schemas import License, LicenseCreate, LicenseUpdate, ActivationRecord
from app.storage.base import BaseStorage
from app.utils.key_generator import generate_license_key
from app.core.config import settings


class SQLiteStorage(BaseStorage):
    """SQLite storage for licenses."""

    def __init__(self, db_path: str = None):
        """Initialize SQLite storage."""
        self.db_path = db_path or settings.storage.sqlite_path
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database tables exist."""
        if self._initialized:
            return

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    key TEXT PRIMARY KEY,
                    product TEXT NOT NULL,
                    version TEXT,
                    customer TEXT NOT NULL,
                    email TEXT,
                    max_activations INTEGER DEFAULT 1,
                    machine_binding INTEGER DEFAULT 1,
                    expiry_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS ip_whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    FOREIGN KEY (license_key) REFERENCES licenses(key) ON DELETE CASCADE
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT NOT NULL,
                    machine_code TEXT,
                    ip TEXT,
                    activated_at TEXT NOT NULL,
                    last_verified TEXT,
                    verification_count INTEGER DEFAULT 0,
                    FOREIGN KEY (license_key) REFERENCES licenses(key) ON DELETE CASCADE
                )
            """)

            await db.commit()

        self._initialized = True

    async def get_license(self, key: str) -> Optional[License]:
        """Get a license by key."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM licenses WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            # Get IP whitelist
            ip_cursor = await db.execute(
                "SELECT ip FROM ip_whitelist WHERE license_key = ?",
                (key,)
            )
            ip_rows = await ip_cursor.fetchall()
            ip_whitelist = [row["ip"] for row in ip_rows]

            # Get activations
            act_cursor = await db.execute(
                "SELECT * FROM activations WHERE license_key = ?",
                (key,)
            )
            act_rows = await act_cursor.fetchall()
            activations = []
            for act in act_rows:
                activations.append(ActivationRecord(
                    machine_code=act["machine_code"],
                    ip=act["ip"],
                    activated_at=datetime.fromisoformat(act["activated_at"]),
                    last_verified=datetime.fromisoformat(act["last_verified"]) if act["last_verified"] else None,
                    verification_count=act["verification_count"]
                ))

            return License(
                key=row["key"],
                product=row["product"],
                version=row["version"],
                customer=row["customer"],
                email=row["email"],
                max_activations=row["max_activations"],
                machine_binding=bool(row["machine_binding"]),
                ip_whitelist=ip_whitelist,
                expiry_date=datetime.fromisoformat(row["expiry_date"]) if row["expiry_date"] else None,
                status=row["status"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                activations=activations
            )

    async def get_all_licenses(self) -> List[License]:
        """Get all licenses."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT key FROM licenses")
            rows = await cursor.fetchall()

            licenses = []
            for row in rows:
                license_data = await self.get_license(row["key"])
                if license_data:
                    licenses.append(license_data)

            return licenses

    async def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license."""
        await self._ensure_initialized()

        key = license_data.key or generate_license_key()
        now = datetime.utcnow().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """
                    INSERT INTO licenses (
                        key, product, version, customer, email, max_activations,
                        machine_binding, expiry_date, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        license_data.product,
                        license_data.version or "1.0.0",
                        license_data.customer,
                        license_data.email,
                        license_data.max_activations,
                        1 if license_data.machine_binding else 0,
                        license_data.expiry_date.isoformat() if license_data.expiry_date else None,
                        license_data.status or "active",
                        now,
                        now
                    )
                )

                # Add IP whitelist entries
                for ip in license_data.ip_whitelist:
                    await db.execute(
                        "INSERT INTO ip_whitelist (license_key, ip) VALUES (?, ?)",
                        (key, ip)
                    )

                await db.commit()
            except aiosqlite.IntegrityError:
                raise ValueError(f"License with key {key} already exists")

        return await self.get_license(key)

    async def update_license(self, key: str, license_data: LicenseUpdate) -> Optional[License]:
        """Update an existing license."""
        await self._ensure_initialized()

        update_dict = license_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.get_license(key)

        # Build update query
        set_clauses = []
        values = []
        for field, value in update_dict.items():
            if field == "ip_whitelist":
                continue  # Handle separately
            if value is not None:
                set_clauses.append(f"{field} = ?")
                if field == "expiry_date" and isinstance(value, datetime):
                    values.append(value.isoformat())
                elif field == "machine_binding":
                    values.append(1 if value else 0)
                else:
                    values.append(value)

        if not set_clauses:
            return await self.get_license(key)

        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(key)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE licenses SET {', '.join(set_clauses)} WHERE key = ?",
                values
            )

            # Update IP whitelist if provided
            if "ip_whitelist" in update_dict and update_dict["ip_whitelist"] is not None:
                await db.execute("DELETE FROM ip_whitelist WHERE license_key = ?", (key,))
                for ip in update_dict["ip_whitelist"]:
                    await db.execute(
                        "INSERT INTO ip_whitelist (license_key, ip) VALUES (?, ?)",
                        (key, ip)
                    )

            await db.commit()

        return await self.get_license(key)

    async def delete_license(self, key: str) -> bool:
        """Delete a license."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM licenses WHERE key = ?", (key,))
            await db.commit()
            return cursor.rowcount > 0

    async def license_exists(self, key: str) -> bool:
        """Check if a license exists."""
        license_data = await self.get_license(key)
        return license_data is not None

    async def add_activation(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Add an activation record to a license."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            # Check if activation already exists
            if machine_code:
                cursor = await db.execute(
                    "SELECT id FROM activations WHERE license_key = ? AND machine_code = ?",
                    (key, machine_code)
                )
            else:
                cursor = await db.execute(
                    "SELECT id FROM activations WHERE license_key = ? AND ip = ?",
                    (key, ip)
                )

            if await cursor.fetchone():
                return False  # Already activated

            await db.execute(
                """
                INSERT INTO activations (license_key, machine_code, ip, activated_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, machine_code, ip, datetime.utcnow().isoformat())
            )
            await db.commit()
            return True

    async def update_verification(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Update verification count and timestamp."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            if machine_code:
                cursor = await db.execute(
                    """
                    UPDATE activations
                    SET verification_count = verification_count + 1,
                        last_verified = ?,
                        ip = ?
                    WHERE license_key = ? AND machine_code = ?
                    """,
                    (datetime.utcnow().isoformat(), ip, key, machine_code)
                )
            else:
                cursor = await db.execute(
                    """
                    UPDATE activations
                    SET verification_count = verification_count + 1,
                        last_verified = ?
                    WHERE license_key = ? AND ip = ?
                    """,
                    (datetime.utcnow().isoformat(), key, ip)
                )

            await db.commit()
            return cursor.rowcount > 0

    async def get_activations_count(self, key: str) -> int:
        """Get the number of activations for a license."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM activations WHERE license_key = ?",
                (key,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
