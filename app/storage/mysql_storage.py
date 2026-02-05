"""MySQL storage implementation."""
import aiomysql
from datetime import datetime
from typing import List, Optional

from app.models.schemas import License, LicenseCreate, LicenseUpdate, ActivationRecord
from app.storage.base import BaseStorage
from app.utils.key_generator import generate_license_key
from app.core.config import settings


class MySQLStorage(BaseStorage):
    """MySQL storage for licenses."""

    def __init__(self):
        """Initialize MySQL storage."""
        self.config = settings.storage.mysql
        self._pool = None
        self._initialized = False

    async def _get_pool(self):
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                db=self.config.database,
                minsize=1,
                maxsize=self.config.pool_size,
                autocommit=True
            )
        return self._pool

    async def _ensure_initialized(self):
        """Ensure database tables exist."""
        if self._initialized:
            return

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS licenses (
                        key VARCHAR(255) PRIMARY KEY,
                        product VARCHAR(255) NOT NULL,
                        version VARCHAR(50),
                        customer VARCHAR(255) NOT NULL,
                        email VARCHAR(255),
                        max_activations INT DEFAULT 1,
                        machine_binding TINYINT(1) DEFAULT 1,
                        expiry_date DATETIME,
                        status VARCHAR(50) DEFAULT 'active',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_status (status),
                        INDEX idx_customer (customer)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ip_whitelist (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        license_key VARCHAR(255) NOT NULL,
                        ip VARCHAR(45) NOT NULL,
                        FOREIGN KEY (license_key) REFERENCES licenses(key) ON DELETE CASCADE,
                        INDEX idx_license_key (license_key)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activations (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        license_key VARCHAR(255) NOT NULL,
                        machine_code VARCHAR(255),
                        ip VARCHAR(45),
                        activated_at DATETIME NOT NULL,
                        last_verified DATETIME,
                        verification_count INT DEFAULT 0,
                        FOREIGN KEY (license_key) REFERENCES licenses(key) ON DELETE CASCADE,
                        INDEX idx_license_key (license_key),
                        INDEX idx_machine_code (machine_code)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

        self._initialized = True

    async def get_license(self, key: str) -> Optional[License]:
        """Get a license by key."""
        await self._ensure_initialized()

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM licenses WHERE key = %s",
                    (key,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                # Get IP whitelist
                await cursor.execute(
                    "SELECT ip FROM ip_whitelist WHERE license_key = %s",
                    (key,)
                )
                ip_rows = await cursor.fetchall()
                ip_whitelist = [r["ip"] for r in ip_rows]

                # Get activations
                await cursor.execute(
                    "SELECT * FROM activations WHERE license_key = %s",
                    (key,)
                )
                act_rows = await cursor.fetchall()
                activations = []
                for act in act_rows:
                    activations.append(ActivationRecord(
                        machine_code=act["machine_code"],
                        ip=act["ip"],
                        activated_at=act["activated_at"],
                        last_verified=act["last_verified"],
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
                    expiry_date=row["expiry_date"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    activations=activations
                )

    async def get_all_licenses(self) -> List[License]:
        """Get all licenses."""
        await self._ensure_initialized()

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT key FROM licenses")
                rows = await cursor.fetchall()

                licenses = []
                for row in rows:
                    license_data = await self.get_license(row[0])
                    if license_data:
                        licenses.append(license_data)

                return licenses

    async def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license."""
        await self._ensure_initialized()

        key = license_data.key or generate_license_key()
        now = datetime.utcnow()

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        INSERT INTO licenses (
                            key, product, version, customer, email, max_activations,
                            machine_binding, expiry_date, status, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            key,
                            license_data.product,
                            license_data.version or "1.0.0",
                            license_data.customer,
                            license_data.email,
                            license_data.max_activations,
                            1 if license_data.machine_binding else 0,
                            license_data.expiry_date,
                            license_data.status or "active",
                            now,
                            now
                        )
                    )

                    # Add IP whitelist entries
                    for ip in license_data.ip_whitelist:
                        await cursor.execute(
                            "INSERT INTO ip_whitelist (license_key, ip) VALUES (%s, %s)",
                            (key, ip)
                        )

                    await conn.commit()
                except aiomysql.IntegrityError:
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
                set_clauses.append(f"{field} = %s")
                values.append(value)

        if not set_clauses:
            return await self.get_license(key)

        set_clauses.append("updated_at = %s")
        values.append(datetime.utcnow())
        values.append(key)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE licenses SET {', '.join(set_clauses)} WHERE key = %s",
                    values
                )

                # Update IP whitelist if provided
                if "ip_whitelist" in update_dict and update_dict["ip_whitelist"] is not None:
                    await cursor.execute("DELETE FROM ip_whitelist WHERE license_key = %s", (key,))
                    for ip in update_dict["ip_whitelist"]:
                        await cursor.execute(
                            "INSERT INTO ip_whitelist (license_key, ip) VALUES (%s, %s)",
                            (key, ip)
                        )

                await conn.commit()

        return await self.get_license(key)

    async def delete_license(self, key: str) -> bool:
        """Delete a license."""
        await self._ensure_initialized()

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM licenses WHERE key = %s", (key,))
                await conn.commit()
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

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if activation already exists
                if machine_code:
                    await cursor.execute(
                        "SELECT id FROM activations WHERE license_key = %s AND machine_code = %s",
                        (key, machine_code)
                    )
                else:
                    await cursor.execute(
                        "SELECT id FROM activations WHERE license_key = %s AND ip = %s",
                        (key, ip)
                    )

                if await cursor.fetchone():
                    return False  # Already activated

                await cursor.execute(
                    """
                    INSERT INTO activations (license_key, machine_code, ip, activated_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (key, machine_code, ip, datetime.utcnow())
                )
                await conn.commit()
                return True

    async def update_verification(
        self,
        key: str,
        machine_code: Optional[str],
        ip: Optional[str]
    ) -> bool:
        """Update verification count and timestamp."""
        await self._ensure_initialized()

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if machine_code:
                    await cursor.execute(
                        """
                        UPDATE activations
                        SET verification_count = verification_count + 1,
                            last_verified = %s,
                            ip = %s
                        WHERE license_key = %s AND machine_code = %s
                        """,
                        (datetime.utcnow(), ip, key, machine_code)
                    )
                else:
                    await cursor.execute(
                        """
                        UPDATE activations
                        SET verification_count = verification_count + 1,
                            last_verified = %s
                        WHERE license_key = %s AND ip = %s
                        """,
                        (datetime.utcnow(), key, ip)
                    )

                await conn.commit()
                return cursor.rowcount > 0

    async def get_activations_count(self, key: str) -> int:
        """Get the number of activations for a license."""
        await self._ensure_initialized()

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT COUNT(*) as count FROM activations WHERE license_key = %s",
                    (key,)
                )
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
