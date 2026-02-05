# LUMINA

**License Unified Management & Identity Network Authorization**
（许可证统一管理与身份网络授权系统）

一个基于 Python 的许可证认证服务器系统，用于软件授权管理和验证。

## 功能特性

- 📝 **多种存储方式**：支持 JSON 文件、SQLite、MySQL 数据库
- 🔐 **灵活的认证机制**：支持密钥验证、机器码绑定、IP 限制
- 📊 **使用记录追踪**：记录认证次数、机器码、IP 等详细信息
- 🐳 **Docker 支持**：提供完整的 Docker 配置
- 🚀 **RESTful API**：基于 FastAPI 的高性能接口
- ⚙️ **配置文件管理**：支持 JSON 文件快速管理用户

## 快速开始

### 使用 JSON 配置文件（推荐用于快速部署）

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置应用：
```bash
cp config/config.yaml.example config/config.yaml
# 编辑 config/config.yaml 设置你的配置
```

3. 运行服务器：
```bash
python main.py
```

服务器将在 `http://localhost:8000` 启动

### 使用 Docker

1. 使用 Docker Compose 构建和运行：
```bash
docker-compose up -d
```

2. 访问 API：
- API 文档：`http://localhost:18001/docs`
- 健康检查：`http://localhost:18001/api/v1/health/ping`

## API 使用

### 管理员登录

```bash
curl -X POST "http://localhost:8000/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 创建许可证

```bash
curl -X POST "http://localhost:8000/api/v1/admin/license" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "product": "MyApp",
    "customer": "张三",
    "email": "zhangsan@example.com",
    "max_activations": 1
  }'
```

### 验证许可证

```bash
curl -X POST "http://localhost:8000/api/v1/license/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "LS-2026-XXXXXXXXXXXXXXX",
    "machine_code": "MACHINE-001"
  }'
```

## 配置

### 主配置文件 (config/config.yaml)

```yaml
app:
  name: "LUMINA"
  version: "1.0.0"
  debug: true
  host: "0.0.0.0"
  port: 18000

storage:
  type: json  # 选项：json, sqlite, mysql
  json:
    path: "data/licenses.json"

security:
  admin_username: "admin"
  admin_password: "admin123"  # 生产环境中请更改！
  secret_key: "your-secret-key-change-this-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 60
```

### 环境变量

你也可以使用环境变量来配置应用：

```bash
export APP__DEBUG=false
export APP__PORT=8000
export STORAGE__TYPE=mysql
export STORAGE__MYSQL__HOST=localhost
export STORAGE__MYSQL__DATABASE=license_server
export STORAGE__MYSQL__USER=root
export STORAGE__MYSQL__PASSWORD=your_password
```

## 许可证管理

### 使用命令行工具

提供了一个命令行工具来轻松添加许可证：

```bash
# 基本用法
python add_license.py MyApp "张三"

# 带邮箱和激活数
python add_license.py MyApp "张三" zhangsan@example.com 2

# 完整参数
python add_license.py MyApp "张三" zhangsan@example.com 2 1.5.0

# 查看帮助
python add_license.py --help
```

### 手动编辑 JSON 文件

你也可以直接编辑 `data/licenses.json` 文件：

```json
{
  "licenses": [
    {
      "key": "LS-2026-XXXXXXXXXXXXXXX",
      "product": "MyApp",
      "version": "1.0.0",
      "customer": "张三",
      "email": "zhangsan@example.com",
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

## 客户端集成

请参阅 `examples/client_example.py` 中的客户端集成示例和 `docs/API_PROTOCOL.md` 中的协议文档。

## 安全考虑

1. **更改默认密码**：在生产环境中始终更改默认管理员密码
2. **使用 HTTPS**：为生产环境配置 HTTPS
3. **密钥**：使用强随机生成的密钥
4. **速率限制**：根据你的用例配置适当的速率限制
5. **IP 白名单**：尽可能使用 IP 白名单以增加安全性

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码风格

本项目遵循 PEP 8 代码风格指南。

### 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行你的更改
4. 为新功能添加测试
5. 确保所有测试通过
6. 提交拉取请求

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 支持

如需支持，请在 GitHub 仓库上打开问题或联系开发团队。