# LUMINA Configuration Guide

## 配置文件结构

```
lumina/
├── config/
│   └── config.yaml.example    # 配置模板（Git 跟踪）
├── data/
│   ├── config.yaml            # 实际配置文件（Git 忽略）
│   ├── licenses.json          # 许可证数据（Git 忽略）
│   └── licenses.db            # SQLite 数据（Git 忽略）
└── logs/
    └── license_server.log     # 日志文件（Git 忽略）
```

## 首次部署步骤

### 1. 创建配置文件

从模板复制配置文件：

```bash
cp config/config.yaml.example data/config.yaml
```

### 2. 修改配置

编辑 `data/config.yaml`，修改关键配置：

```yaml
# ⚠️ 生产环境必须修改
security:
  admin_password: "your-secure-password"  # 修改管理员密码
  secret_key: "your-random-secret-key-32-chars"  # 修改密钥

app:
  debug: false  # 生产环境设为 false
  port: 18000  # 根据需要修改端口
```

### 3. 启动服务

```bash
docker-compose up -d
```

## 配置优先级

1. **data/config.yaml** - 用户配置（优先级最高）
2. **config/config.yaml** - 兼容旧配置（fallback）
3. **环境变量** - 可以覆盖配置文件
4. **代码默认值** - 最后的兜底值

## Git 管理

- ✅ **跟踪**: `config/config.yaml.example`
- ❌ **忽略**: `data/config.yaml`（在 .gitignore 中）

这样你的本地配置不会被 git pull 覆盖！

## 环境变量覆盖

可以通过环境变量覆盖任何配置：

```bash
export APP__PORT=8080
export SECURITY__ADMIN_PASSWORD=secure_pass
export STORAGE__TYPE=mysql
```

格式：`<section>__<key>=value`（双下划线）

## 多环境配置

### 开发环境

```yaml
# data/config.yaml
app:
  debug: true
  port: 18000

logging:
  level: "DEBUG"
```

### 生产环境

```yaml
# data/config.yaml
app:
  debug: false
  port: 8000

security:
  admin_password: "<强密码>"
  secret_key: "<随机密钥>"

storage:
  type: mysql  # 使用生产数据库
  mysql:
    host: "mysql-server"
    database: "lumina_prod"
```

## 故障排查

### 配置文件未生效？

1. 检查文件位置：`data/config.yaml`
2. 检查文件权限：`ls -la data/config.yaml`
3. 查看日志：`docker-compose logs`

### 默认配置加载？

如果 `data/config.yaml` 不存在，系统会使用代码默认值。

建议首次部署时先复制示例配置！
