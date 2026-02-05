# LUMINA 许可证服务器

许可证认证服务器，用于软件授权管理和验证。

## 特性

- 多种存储后端（JSON、SQLite、MySQL）
- 机器码绑定
- IP 限制
- 使用量跟踪
- Docker 支持（以非 root 用户运行）
- 安全的管理员 API（JWT 认证）

## 快速开始

```bash
# 1. 创建环境变量文件
cp .env.example .env

# 2. 设置必需的环境变量
echo "ADMIN_PASSWORD=your_secure_password" >> .env
echo "SECRET_KEY=$(openssl rand -base64 32)" >> .env

# 3. 启动服务器
docker-compose up -d
```

服务器地址：`http://localhost:18001`
API 文档：`http://localhost:18001/docs`

## 环境变量

创建 `.env` 文件：

```bash
# 必需
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_min_32_chars

# 可选
ADMIN_USERNAME=admin
LOG_LEVEL=INFO
```

## 命令行工具

```bash
# 设置环境变量
export ADMIN_PASSWORD=your_password

# 添加许可证
python cli.py add MyApp "客户名" --email customer@example.com

# 列出所有许可证
python cli.py list

# 查看许可证详情
python cli.py get LS-2026-XXXXXXXXXXXXXXX

# 删除许可证
python cli.py delete LS-2026-XXXXXXXXXXXXXXX

# 查看激活记录
python cli.py activations LS-2026-XXXXXXXXXXXXXXX

# 删除激活记录（允许重新激活）
python cli.py rm-activation LS-2026-XXXXXXXXXXXXXXX MACHINE-CODE
```

## API 使用

### 管理员登录

```bash
curl -X POST "http://localhost:18001/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 验证许可证（客户端）

```bash
curl -X POST "http://localhost:18001/api/v1/license/verify" \
  -H "Content-Type: application/json" \
  -d '{"license_key": "LS-2026-XXXXXXXXXXXXXXX", "machine_code": "MACHINE-001"}'
```

## 配置

配置文件：`data/config.yaml`

敏感配置（密码、密钥）应该通过环境变量设置，不要写在配置文件中。

## 安全性

- 容器以非 root 用户运行（uid 1000）
- 管理员 API 使用 JWT 令牌认证
- 敏感数据使用环境变量
- `.env` 文件已加入 .gitignore

## 客户端集成

详细的集成说明请参考 [docs/API_PROTOCOL.md](docs/API_PROTOCOL.md)

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务器
python main.py

# 运行测试
pytest tests/
```

## 许可证

MIT License
