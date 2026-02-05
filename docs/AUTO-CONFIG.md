# 配置文件自动创建逻辑

## 🎯 设计目标

确保首次部署时有配置文件，但**绝不覆盖**用户已有的配置。

## 📋 逻辑流程

```
启动应用
    ↓
检查 data/config.yaml 是否存在？
    ↓
    ├─ 存在 → ✅ 使用现有配置，不做任何修改
    │          （保证用户配置永不丢失）
    │
    └─ 不存在 → 尝试从 config/config.yaml.example 复制
                ↓
                ├─ 示例文件存在 → ✅ 复制到 data/config.yaml
                │                  （首次部署自动创建）
                │
                └─ 示例文件不存在 → 创建最小默认配置
                                    （兜底方案）
```

## 🔐 安全保证

| 场景 | 行为 | 说明 |
|------|------|------|
| **首次部署** | ✅ 自动创建配置 | 从 example 复制，用户无需手动操作 |
| **已有配置** | 🔒 绝不覆盖 | 即使 git pull 也不会影响本地配置 |
| **配置损坏** | ⚠️ 保留原文件 | 不会尝试"修复"已有配置 |
| **无示例文件** | ✅ 创建默认配置 | 确保系统可启动 |

## 📝 代码实现

位置：[app/core/config.py](../app/core/config.py)

```python
def ensure_config_exists() -> None:
    """确保配置文件存在，但永不覆盖已有配置。"""

    user_config = Path("data/config.yaml")
    example_config = Path("config/config.yaml.example")

    # 情况1: 用户配置已存在 → 绝不触碰
    if user_config.exists():
        logger.info(f"✓ Using existing config: {user_config}")
        return

    # 情况2: 配置缺失 → 从示例复制
    if example_config.exists():
        shutil.copy2(example_config, user_config)
        logger.info(f"✓ Created config from example")
        logger.warning("⚠️  Please review data/config.yaml!")
        return

    # 情况3: 示例也缺失 → 创建默认配置
    create_default_config(user_config)
```

## 🧪 测试验证

### 测试1: 首次部署
```bash
# 删除现有配置
rm data/config.yaml

# 重启容器
docker-compose restart

# 结果：✅ 自动创建配置文件
ls data/config.yaml  # 文件已创建
```

### 测试2: 已有配置不被覆盖
```bash
# 添加自定义配置
echo "# My Custom Config" >> data/config.yaml
ORIGINAL_MD5=$(md5sum data/config.yaml)

# 重启容器
docker-compose restart

# 结果：✅ 配置未被修改
NEW_MD5=$(md5sum data/config.yaml)
[ "$ORIGINAL_MD5" = "$NEW_MD5" ] && echo "✓ Config preserved!"
```

### 测试3: Git pull 不影响配置
```bash
# 编辑本地配置
vim data/config.yaml  # 修改为你的配置

# 拉取远程代码
git pull origin main

# 重启服务
docker-compose restart

# 结果：✅ 你的配置保持不变
cat data/config.yaml  # 仍然是你的配置
```

## 🎨 日志输出

### 首次部署（配置缺失）
```
lumina  | WARNING  Config file not found: data/config.yaml
lumina  | INFO     ✓ Created config from example: data/config.yaml
lumina  | WARNING  ⚠️  Please review and update data/config.yaml for production!
```

### 正常启动（配置已存在）
```
lumina  | INFO     Using existing config: data/config.yaml
```

## 📂 文件权限

自动创建的配置文件：
- 位置：`data/config.yaml`
- 所有者：运行容器的用户
- 权限：`-rw-r--r--` (644)
- 来源：`config/config.yaml.example`

## ⚙️ 自定义配置流程

### 推荐做法

1. **首次部署**：
   ```bash
   cp config/config.yaml.example data/config.yaml
   vim data/config.yaml  # 根据需要修改
   docker-compose up -d
   ```

2. **修改配置**：
   ```bash
   vim data/config.yaml
   docker-compose restart  # 重启生效
   ```

3. **环境变量覆盖**（可选）：
   ```bash
   export APP__PORT=8080
   export SECURITY__ADMIN_PASSWORD=secure_pass
   docker-compose up -d
   ```

## 🔍 故障排查

### 问题：配置没有生效
```bash
# 检查文件位置
ls -la data/config.yaml

# 检查容器内
docker exec lumina cat /app/data/config.yaml

# 查看日志
docker-compose logs | grep -i config
```

### 问题：想要使用示例配置
```bash
# 备份现有配置
mv data/config.yaml data/config.yaml.old

# 重启（自动创建新配置）
docker-compose restart

# 对比差异
diff data/config.yaml.old data/config.yaml
```

## 🎯 最佳实践

1. ✅ **首次部署后立即修改敏感配置**
   - `security.admin_password`
   - `security.secret_key`

2. ✅ **将 data/ 目录加入版本控制**
   - 配置文件已通过 `.gitignore` 排除
   - 不同环境可以有不同配置

3. ✅ **使用环境变量覆盖敏感信息**
   ```yaml
   security:
     admin_password: ${ADMIN_PASSWORD}  # 从环境变量读取
   ```

4. ✅ **定期备份配置**
   ```bash
   cp data/config.yaml data/config.yaml.backup.$(date +%Y%m%d)
   ```

## 📊 对比传统方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| **自动创建** | ✅ 零配置启动<br>✅ 不会覆盖现有配置<br>✅ Git 友好 | 需要示例文件 |
| 手动复制 | 简单直接 | ❌ 容易遗忘<br>❌ 新手不友好 |
| 环境变量 | 灵活 | ❌ 复杂配置难以管理 |
| ConfigMap | K8s 友好 | ❌ 不够通用 |

---

**结论**：自动创建逻辑平衡了易用性和安全性，是推荐方案！
