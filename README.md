# LUMINA License Server

License authentication server for software authorization management and verification.

## Quick Start

```bash
docker-compose up -d
```

Server: `http://localhost:18000`
API Docs: `http://localhost:18000/docs`

## Basic Usage

### Admin Login

```bash
curl -X POST "http://localhost:18000/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Create License

```bash
curl -X POST "http://localhost:18000/api/v1/admin/license" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product": "MyApp", "customer": "John Doe", "max_activations": 1}'
```

### Verify License (Client)

```bash
curl -X POST "http://localhost:18000/api/v1/license/verify" \
  -H "Content-Type: application/json" \
  -d '{"license_key": "LS-2026-XXXXXXXXXXXXXXX", "machine_code": "MACHINE-001"}'
```

## Configuration

Edit `data/config.yaml`:

```yaml
security:
  admin_password: "your-secure-password"  # Change this!
  secret_key: "your-secret-key"            # Change this!
```

```bash
docker-compose restart
```

## Client Integration

For implementation details, see [docs/API_PROTOCOL.md](docs/API_PROTOCOL.md)

## Features

- Multiple storage backends (JSON, SQLite, MySQL)
- Machine code binding
- IP restrictions
- Usage tracking
- Docker support
