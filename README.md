# LUMINA License Server

License authentication server for software authorization management and verification.

## Features

- Multiple storage backends (JSON, SQLite, MySQL)
- Machine code binding
- IP restrictions
- Usage tracking
- Docker support (runs as non-root user)
- Secure admin API with JWT authentication

## Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Set required environment variables
echo "ADMIN_PASSWORD=your_secure_password" >> .env
echo "SECRET_KEY=$(openssl rand -base64 32)" >> .env

# 3. Start server
docker-compose up -d
```

Server: `http://localhost:18001`
API Docs: `http://localhost:18001/docs`

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
# Set environment variable
export ADMIN_PASSWORD=your_password

# Add license
python cli.py add MyApp "Customer Name" --email customer@example.com

# List licenses
python cli.py list

# View license details
python cli.py get LS-2026-XXXXXXXXXXXXXXX

# Delete license
python cli.py delete LS-2026-XXXXXXXXXXXXXXX

# View activations
python cli.py activations LS-2026-XXXXXXXXXXXXXXX

# Delete activation (allow reactivation)
python cli.py rm-activation LS-2026-XXXXXXXXXXXXXXX MACHINE-CODE
```

## API Usage

### Admin Login

```bash
curl -X POST "http://localhost:18001/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Verify License (Client)

```bash
curl -X POST "http://localhost:18001/api/v1/license/verify" \
  -H "Content-Type: application/json" \
  -d '{"license_key": "LS-2026-XXXXXXXXXXXXXXX", "machine_code": "MACHINE-001"}'
```

## Configuration

Configuration file: `data/config.yaml`

Sensitive settings (password, secret key) should be set via environment variables, not in the config file.

## Security

- Container runs as non-root user (uid 1000)
- JWT token authentication for admin API
- Environment variables for sensitive data
- `.env` file is gitignored

## Client Integration

For implementation details, see [docs/API_PROTOCOL.md](docs/API_PROTOCOL.md)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py

# Run tests
pytest tests/
```

## License

MIT License
