#!/usr/bin/env python3
"""命令行工具：添加新许可证

使用方法:
    python add_license.py <产品名称> <客户名称> [邮箱] [最大激活数] [版本]

参数说明:
    产品名称:      软件产品名称 (必填)
    客户名称:      客户名称 (必填)
    邮箱:          客户邮箱地址 (可选)
    最大激活数:    许可证最大激活次数 (可选，默认为1)
    版本:          产品版本号 (可选，默认为1.0.0)

使用示例:
    # 基本用法
    python add_license.py MyApp "张三"

    # 带邮箱和激活数
    python add_license.py MyApp "张三" zhangsan@example.com 2

    # 完整参数
    python add_license.py MyApp "张三" zhangsan@example.com 2 1.5.0

输出:
    成功添加许可证后，会显示许可证密钥和相关信息。
    许可证密钥可以用于客户端验证。

注意事项:
    - 许可证密钥会自动生成，格式为: LS-YYYY-XXXXXXXX
    - 许可证信息会保存到 data/licenses.json 文件中
    - 确保在运行此脚本前，data/licenses.json 文件已存在
    - 如果文件不存在，脚本会报错
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.key_generator import generate_license_key


def add_license(product, customer, email=None, max_activations=1, version="1.0.0"):
    """添加新许可证到 JSON 文件"""

    # 生成许可证密钥
    license_key = generate_license_key()

    # 创建许可证数据
    new_license = {
        "key": license_key,
        "product": product,
        "version": version,
        "customer": customer,
        "email": email,
        "max_activations": max_activations,
        "machine_binding": True,
        "ip_whitelist": [],
        "expiry_date": None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat() + "Z",
        "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "activations": [],
    }

    # 读取现有的许可证文件
    licenses_file = Path("data/licenses.json")

    if not licenses_file.exists():
        print("Error: licenses.json file not found")
        return False

    with open(licenses_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 添加新许可证
    data["licenses"].append(new_license)
    data["metadata"]["total_licenses"] = len(data["licenses"])
    data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    # 保存回文件
    with open(licenses_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("License added successfully!")
    print(f"License key: {license_key}")
    print(f"Product: {product}")
    print(f"Customer: {customer}")
    print(f"Max activations: {max_activations}")

    return True


if __name__ == "__main__":
    # 显示帮助信息
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print(__doc__)
        sys.exit(0)

    # Check parameter count
    if len(sys.argv) < 3:
        print("Error: Insufficient parameters")
        print(
            "Usage: python add_license.py <product_name> <customer_name> [email] [max_activations] [version]"
        )
        print(
            "Example: python add_license.py MyApp 'John Doe' john@example.com 2 1.0.0"
        )
        print("Use -h or --help for detailed help")
        sys.exit(1)

    try:
        product = sys.argv[1]
        customer = sys.argv[2]
        email = sys.argv[3] if len(sys.argv) > 3 else None
        max_activations = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        version = sys.argv[5] if len(sys.argv) > 5 else "1.0.0"

        # Validate parameters
        if not product or not customer:
            print("Error: Product name and customer name cannot be empty")
            sys.exit(1)

        if max_activations < 1:
            print("Error: Max activations must be greater than 0")
            sys.exit(1)

        # Add license
        add_license(product, customer, email, max_activations, version)

    except ValueError as e:
        print(f"Error: Invalid parameter format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to add license - {e}")
        sys.exit(1)
