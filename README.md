# LUMINA License Server

License authentication server for software authorization management and verification.

## Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Set admin password (required)
echo "ADMIN_PASSWORD=your_secure_password" >> .env
echo "SECRET_KEY=$(openssl rand -base64 32)" >> .env

# 3. Start server
docker-compose up -d
```

Server: `http://localhost:18000`
API Docs: `http://localhost:18000/docs`

## Basic Usage

### Admin Login

```bash
export ADMIN_PASSWORD=your_secure_password
curl -X POST "http://localhost:18000/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_secure_password"}'
```

### Create License

```bash
python cli.py add MyApp "Customer Name" --email customer@example.com
```

### Verify License (Client)

```bash
curl -X POST "http://localhost:18000/api/v1/license/verify" \
  -H "Content-Type: application/json" \
  -d '{"license_key": "LS-2026-XXXXXXXXXXXXXXX", "machine_code": "MACHINE-001"}'
```

## Environment Variables

Create `.env` file:

```bash
# Required
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_min_32_chars

# Optional
ADMIN_USERNAME=admin
LOG_LEVEL=INFO
```

## CLI Tool

```bash
# Using environment variable
export ADMIN_PASSWORD=your_password
python cli.py add MyApp "Customer"

# Or interactive (prompts for password)
python cli.py add MyApp "Customer"

# List licenses
python cli.py list

# View license details
python cli.py get LS-2026-XXXXXXXXXXXXXXX
```

## Configuration

Configuration file: `data/config.yaml`

Sensitive settings (password, secret key) should be set via environment variables.

## Client Integration

For implementation details, see [docs/API_PROTOCOL.md](docs/API_PROTOCOL.md)

## Features

- Multiple storage backends (JSON, SQLite, MySQL)
- Machine code binding
- IP restrictions
- Usage tracking
- Docker support
