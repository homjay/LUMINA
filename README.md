# LUMINA

**License Unified Management & Identity Network Authorization**

A Python-based license authentication server system for software authorization management and verification.

## Features

- 📝 **Multiple Storage Methods**: Support for JSON files, SQLite, MySQL databases
- 🔐 **Flexible Authentication**: Support for key verification, machine code binding, IP restrictions
- 📊 **Usage Tracking**: Record authentication count, machine codes, IPs and other detailed information
- 🐳 **Docker Support**: Complete Docker configuration provided
- 🚀 **RESTful API**: High-performance interface based on FastAPI
- ⚙️ **Configuration Management**: JSON file support for quick user management

## Quick Start

### Using JSON Configuration File (Recommended for Quick Deployment)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the application:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml to set your configuration
```

3. Run the server:
```bash
python main.py
```

The server will start on `http://localhost:8000`

### Using Docker

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

2. Access the API:
- API documentation: `http://localhost:18001/docs`
- Health check: `http://localhost:18001/api/v1/health/ping`

## API Usage

### Admin Login

```bash
curl -X POST "http://localhost:8000/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Create License

```bash
curl -X POST "http://localhost:8000/api/v1/admin/license" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "product": "MyApp",
    "customer": "John Doe",
    "email": "john@example.com",
    "max_activations": 1
  }'
```

### Verify License

```bash
curl -X POST "http://localhost:8000/api/v1/license/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "LS-2026-XXXXXXXXXXXXXXX",
    "machine_code": "MACHINE-001"
  }'
```

## Configuration

### Main Configuration File (config/config.yaml)

```yaml
app:
  name: "LUMINA"
  version: "1.0.0"
  debug: true
  host: "0.0.0.0"
  port: 18000

storage:
  type: json  # Options: json, sqlite, mysql
  json:
    path: "data/licenses.json"

security:
  admin_username: "admin"
  admin_password: "admin123"  # Change this in production!
  secret_key: "your-secret-key-change-this-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 60
```

### Environment Variables

You can also configure the application using environment variables:

```bash
export APP__DEBUG=false
export APP__PORT=8000
export STORAGE__TYPE=mysql
export STORAGE__MYSQL__HOST=localhost
export STORAGE__MYSQL__DATABASE=license_server
export STORAGE__MYSQL__USER=root
export STORAGE__MYSQL__PASSWORD=your_password
```

## License Management

### Using Command Line Tool

A command line tool is provided to easily add licenses:

```bash
# Basic usage
python add_license.py MyApp "John Doe"

# With email and activation count
python add_license.py MyApp "John Doe" john@example.com 2

# Full parameters
python add_license.py MyApp "John Doe" john@example.com 2 1.5.0

# View help
python add_license.py --help
```

### Manual JSON File Editing

You can also directly edit the `data/licenses.json` file:

```json
{
  "licenses": [
    {
      "key": "LS-2026-XXXXXXXXXXXXXXX",
      "product": "MyApp",
      "version": "1.0.0",
      "customer": "John Doe",
      "email": "john@example.com",
      "max_activations": 1,
      "machine_binding": true,
      "ip_whitelist": [],
      "expiry_date": null,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "activations": []
    }
  ],
  "metadata": {
    "version": "1.0",
    "total_licenses": 1,
    "last_updated": "2024-01-01T00:00:00Z"
  }
}
```

## Client Integration

See the client integration example in `examples/client_example.py` and the protocol documentation in `docs/API_PROTOCOL.md`.

## Security Considerations

1. **Change Default Password**: Always change the default admin password in production
2. **Use HTTPS**: Configure HTTPS for production environments
3. **Secret Key**: Use a strong, randomly generated secret key
4. **Rate Limiting**: Configure appropriate rate limiting for your use case
5. **IP Whitelisting**: Use IP whitelisting when possible for additional security

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 code style guidelines.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support, please open an issue on the GitHub repository or contact the development team.
