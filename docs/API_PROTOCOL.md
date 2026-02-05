# LUMINA Client Integration Protocol
**License Unified Management & Identity Network Authorization**

## Overview

This document defines the client integration protocol for the LUMINA License Authentication Server. Client programs can implement license verification functionality through this protocol.

**Server Address**: To be provided by the user (e.g., `https://license.example.com`)

**API Version**: v1

**Base Path**: `/api/v1`

**Authentication Method**: JWT Bearer Token (admin endpoints only)

---

## Core Concepts

### License Key
- Format: `LS-YYYY-XXXXXXXXXXXXXXX`
- Example: `LS-2026-CHSVYS8PAB9LT53L`
- Length: 16 characters (excluding prefix)
- Uniqueness: Each license key is globally unique

### Machine Code
- **Purpose**: Identifies a unique device to prevent license sharing
- **Generation Method**: Based on hardware information (CPU, MAC address, hostname, etc.)
- **Format**: 32-character uppercase hexadecimal string
- Example: `A1B2C3D4E5F67890123456789012345AB`
- **Importance**: Required if machine binding is enabled

### Activation
- **Definition**: First verification of a license on a specific device
- **Limit**: Each license has a maximum activation count limit
- **Record**: Includes machine code, IP address, activation time, verification count

---

## API Endpoint Details

### 1. License Verification

**Endpoint**: `POST /api/v1/license/verify`

**Purpose**: Client verifies whether a license key is valid

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "license_key": "LS-2026-CHSVYS8PAB9LT53L",
  "machine_code": "A1B2C3D4E5F67890123456789012345AB",
  "ip": "192.168.1.100"
}
```

**Field Descriptions**:

| Field        | Type   | Required | Description                                    |
| ------------ | ------ | -------- | ---------------------------------------------- |
| license_key  | string | ✅        | License key                                    |
| machine_code | string | ⚠️        | Machine code (required if machine binding is enabled for the license) |
| ip           | string | ❌        | Client IP (optional, server will auto-detect)  |

**Success Response** (200 OK):
```json
{
  "valid": true,
  "message": "License verified successfully",
  "license": {
    "key": "LS-2026-CHSVYS8PAB9LT53L",
    "product": "MyApp",
    "version": "1.0.0",
    "customer": "John Smith",
    "email": "john.smith@example.com",
    "max_activations": 2,
    "machine_binding": true,
    "ip_whitelist": [],
    "expiry_date": "2026-12-31T23:59:59Z",
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
    "activations": [...]
  },
  "remaining_activations": 1,
  "expiry_date": "2026-12-31T23:59:59Z"
}
```

**Failure Response** (200 OK, but valid=false):

**Scenario 1: License does not exist**
```json
{
  "valid": false,
  "message": "Invalid license key",
  "license": null,
  "remaining_activations": null,
  "expiry_date": null
}
```

**Scenario 2: License has expired**
```json
{
  "valid": false,
  "message": "License has expired",
  "license": null,
  "remaining_activations": null,
  "expiry_date": null
}
```

**Scenario 3: Maximum activations reached**
```json
{
  "valid": false,
  "message": "Maximum activations reached",
  "license": null,
  "remaining_activations": null,
  "expiry_date": null
}
```

**Scenario 4: IP not in whitelist**
```json
{
  "valid": false,
  "message": "IP address not authorized",
  "license": null,
  "remaining_activations": null,
  "expiry_date": null
}
```

**Scenario 5: License is disabled**
```json
{
  "valid": false,
  "message": "License is disabled",
  "license": null,
  "remaining_activations": null,
  "expiry_date": null
}
```

---

### 2. License Status Query (Lightweight)

**Endpoint**: `GET /api/v1/license/check/{key}`

**Purpose**: Quickly check if a license exists and is activated (does not return detailed information)

**Path Parameters**:
- `key`: License key

**Success Response** (200 OK):
```json
{
  "exists": true,
  "active": true,
  "product": "MyApp",
  "customer": "John Smith"
}
```

**Not Found** (404 Not Found):
```json
{
  "exists": false,
  "message": "License not found"
}
```

---

## Error Code Definitions

| HTTP Status Code | Error Type            | Description                      |
| ---------------- | --------------------- | -------------------------------- |
| 200              | OK                    | Request successful (verification may have failed) |
| 400              | Bad Request           | Invalid request parameters       |
| 401              | Unauthorized          | Unauthorized (admin endpoints)   |
| 404              | Not Found             | Resource not found               |
| 500              | Internal Server Error | Internal server error            |

**Error Response Format**:
```json
{
  "detail": "Detailed error information"
}
```

---

## Client Integration Flow

### Standard Verification Flow

```
┌─────────┐                ┌──────────────┐                ┌─────────────┐
│ Client  │                │ License Server│               │  Data Store │
└────┬────┘                └──────┬───────┘                └──────┬──────┘
     │                            │                              │
     │ 1. Start application       │                              │
     ├──────────────────────────> │                              │
     │    POST /license/verify    │                              │
     │    {                       │                              │
     │      license_key,          │                              │
     │      machine_code          │                              │
     │    }                       │                              │
     │                            │                              │
     │                            │ 2. Query license             │
     │                            ├─────────────────────────────>│
     │                            │                              │
     │                            │ 3. Return license data       │
     │                            │<─────────────────────────────┤
     │                            │                              │
     │ 4. Verification result     │                              │
     │<────────────────────────── │                              │
     │    {                      │                              │
     │      valid: true/false,   │                              │
     │      message,             │                              │
     │      remaining_activations│                              │
     │    }                      │                              │
     │                            │                              │
     │ 5. Decide based on result  │                              │
     │    - valid=true: Start     │                              │
     │    - valid=false: Exit     │                              │
     │                            │                              │
```

### Offline Mode (Optional)

In certain scenarios, clients may need to work offline:

1. **First Activation**: Must verify online, record activation information
2. **Cache Verification Result**: Client caches license information and expiration time
3. **Offline Verification**:
   - Check if locally cached license has expired
   - If within grace period (e.g., 7 days), allow usage
   - After grace period, require online verification

---

## Machine Code Generation Guide

### Recommended Algorithm

```python
import hashlib
import platform
import uuid

def generate_machine_code():
    """Generate unique machine code"""
    # Collect hardware information
    info = {
        "platform": platform.platform(),
        "node": platform.node(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "mac": ":".join(["{:02x}".format((uuid.getnode() >> i) & 0xff)
                         for i in range(0, 48, 8)][::-1])
    }

    # Generate hash
    info_str = "|".join(info.values())
    machine_code = hashlib.sha256(info_str.encode()).hexdigest()[:32].upper()

    return machine_code
```

### Machine Code Requirements

- **Uniqueness**: Should be the same each time on the same device
- **Stability**: Small hardware changes should not change the machine code
- **Length**: 32-character hexadecimal string
- **Case**: Uppercase

---

## Client Integration Best Practices

### 1. Verification Timing

- ✅ **On application startup**: Must verify
- ✅ **Periodic verification**: Verify every 24 hours
- ⚠️ **Before key features**: Decide based on business requirements

### 2. Error Handling

```python
# Pseudo-code example
try:
    result = verify_license(license_key, machine_code)

    if result.valid:
        # Start application
        start_application()
    else:
        # Show friendly error
        show_error(result.message)
        exit_application()

except NetworkError:
    # Network error handling
    if can_use_offline_mode():
        start_application_offline()
    else:
        show_error("Unable to connect to license server")
        exit_application()

except Exception as e:
    # Log error
    log_error(e)
    show_error("License verification failed")
    exit_application()
```

### 3. Security Recommendations

- 🔒 **Protect license key**: Encrypt and store locally
- 🔒 **Prevent tampering**: Obfuscate or sign client code
- 🔒 **Transit encryption**: Always use HTTPS
- ⏱️ **Set timeout**: Verification request timeout (recommend 5-10 seconds)

### 4. User Experience

- 💡 **Friendly prompts**: Clearly inform users of verification failure reasons
- 💡 **Guide actions**: Provide links to purchase or activate licenses
- 💡 **Grace period**: Allow short-term offline usage (e.g., 7 days)

---

## Complete Client Example (Python)

```python
import requests
import hashlib
import platform
import uuid
from datetime import datetime

class LicenseClient:
    """License client"""

    def __init__(self, server_url: str, license_key: str):
        """
        Initialize client

        Args:
            server_url: License server address (e.g., https://license.example.com)
            license_key: License key
        """
        self.server_url = server_url.rstrip('/')
        self.license_key = license_key
        self.machine_code = self._generate_machine_code()

    def _generate_machine_code(self) -> str:
        """Generate machine code"""
        info = {
            "platform": platform.platform(),
            "node": platform.node(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "mac": ":".join(["{:02x}".format((uuid.getnode() >> i) & 0xff)
                             for i in range(0, 48, 8)][::-1])
        }

        info_str = "|".join(info.values())
        return hashlib.sha256(info_str.encode()).hexdigest()[:32].upper()

    def verify(self) -> dict:
        """
        Verify license

        Returns:
            Verification result dictionary
        """
        url = f"{self.server_url}/api/v1/license/verify"

        payload = {
            "license_key": self.license_key,
            "machine_code": self.machine_code
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "message": f"Connection error: {str(e)}"
            }

    def verify_and_start(self) -> bool:
        """Verify license and decide whether to start application"""
        print(f"Verifying license...")
        print(f"Server: {self.server_url}")
        print(f"License: {self.license_key}")
        print(f"Machine Code: {self.machine_code}")

        result = self.verify()

        if result.get("valid"):
            print(f"✓ License verified successfully!")
            print(f"  Product: {result['license']['product']}")
            print(f"  Customer: {result['license']['customer']}")

            if result.get('expiry_date'):
                expiry = result['expiry_date']
                print(f"  Expires: {expiry}")

            remaining = result.get('remaining_activations')
            if remaining is not None:
                print(f"  Remaining activations: {remaining}")

            return True
        else:
            print(f"✗ License verification failed: {result.get('message')}")
            return False


# Usage example
if __name__ == "__main__":
    # Configuration
    SERVER_URL = "https://license.example.com"  # Change to your server address
    LICENSE_KEY = "LS-2026-CHSVYS8PAB9LT53L"    # Change to your license key

    # Create client and verify
    client = LicenseClient(SERVER_URL, LICENSE_KEY)

    if client.verify_and_start():
        print("\nApplication started successfully!")
        # Start your application logic here
    else:
        print("\nApplication cannot start, please contact technical support.")
        exit(1)
```

---

## Testing Checklist

After implementing the client, please test the following scenarios:

- [ ] **Normal verification**: Valid license + correct machine code
- [ ] **Invalid key**: Non-existent license key
- [ ] **Expired license**: Already expired license
- [ ] **Incorrect machine code**: Machine binding enabled, machine code mismatch
- [ ] **Exceeded activations**: Maximum activation limit reached
- [ ] **IP restriction**: IP not in whitelist
- [ ] **Network error**: Server inaccessible
- [ ] **Timeout handling**: Server response timeout
- [ ] **Repeated verification**: Multiple verifications on same device

---

## Configuration Checklist

Before using this protocol, please confirm:

- [ ] Server address is accessible
- [ ] Valid license key is possessed
- [ ] Machine code generation is correctly implemented
- [ ] Network exceptions are handled
- [ ] Friendly user prompts are implemented
- [ ] Various failure scenarios are tested

---

## FAQ

**Q: How often should verification requests be sent?**
A: Verify on application startup. If stricter control is needed, verify every 24 hours.

**Q: What if the user changes hardware?**
A: The machine code will change. An administrator needs to delete the old activation record on the server to allow reactivation.

**Q: Can it be used offline?**
A: First activation must be online. Subsequent offline verification mechanisms can be implemented (see Offline Mode section).

**Q: How to prevent license leakage?**
A:
1. Obfuscate client code
2. Encrypt and store license key
3. Implement code integrity checks

**Q: Is HTTP supported?**
A: Yes, but not recommended. Production environments strongly recommend using HTTPS.

---

## Appendix

### A. Complete License Object Structure

```typescript
interface License {
  key: string;                      // License key
  product: string;                  // Product name
  version: string;                  // Product version
  customer: string;                 // Customer name
  email: string | null;             // Customer email
  max_activations: number;          // Maximum activations
  machine_binding: boolean;         // Whether machine binding is enabled
  ip_whitelist: string[];           // IP whitelist
  expiry_date: string | null;       // Expiration time (ISO 8601)
  status: string;                   // Status: active, disabled, expired
  created_at: string;               // Creation time (ISO 8601)
  updated_at: string;               // Update time (ISO 8601)
  activations: Activation[];        // List of activation records
}

interface Activation {
  machine_code: string | null;      // Machine code
  ip: string | null;                // IP address
  activated_at: string;             // Activation time (ISO 8601)
  last_verified: string | null;     // Last verification time (ISO 8601)
  verification_count: number;       // Verification count
}
```

### B. Supported Language Client Examples

- Python: See above
- JavaScript/Node.js: Refer to Python example
- C#: Use `HttpClient` and `System.Security.Cryptography`
- Java: Use `HttpURLConnection` and `java.security`
- Go: Use `net/http` and `crypto/sha256`

---

## Version History

- **v1.0** (2026-01-01): Initial version

---

## Contact Support

For questions or assistance, please contact:
- Technical Support Email: support@example.com
- Documentation: https://license.example.com/docs
- GitHub Issues: https://github.com/example/license-server/issues
