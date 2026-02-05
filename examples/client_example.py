"""
LUMINA 客户端集成示例
License Unified Management & Identity Network Authorization

展示如何在应用程序中集成许可证验证功能。
"""

import requests
import hashlib
import platform
import uuid


class LicenseClient:
    """许可证客户端"""

    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        初始化客户端

        Args:
            server_url: 许可证服务器地址
        """
        self.server_url = server_url.rstrip("/")
        self.api_base = f"{self.server_url}/api/v1"

    def get_machine_code(self) -> str:
        """
        生成机器码

        基于系统信息生成唯一的机器标识符。
        """
        # 获取系统信息
        system_info = {
            "platform": platform.platform(),
            "node": platform.node(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "mac": ":".join(
                [
                    "{:02x}".format((uuid.getnode() >> i) & 0xFF)
                    for i in range(0, 48, 8)
                ][::-1]
            ),
        }

        # 生成哈希
        info_str = "|".join(system_info.values())
        machine_code = hashlib.sha256(info_str.encode()).hexdigest()[:32].upper()

        return machine_code

    def verify_license(self, license_key: str) -> dict:
        """
        验证许可证

        Args:
            license_key: 许可证密钥

        Returns:
            验证结果字典
        """
        machine_code = self.get_machine_code()

        payload = {"license_key": license_key, "machine_code": machine_code}

        try:
            response = requests.post(
                f"{self.api_base}/license/verify", json=payload, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"valid": False, "message": f"Connection error: {str(e)}"}

    def check_license(self, license_key: str) -> bool:
        """
        简单检查许可证是否有效

        Args:
            license_key: 许可证密钥

        Returns:
            是否有效
        """
        result = self.verify_license(license_key)
        return result.get("valid", False)


class AppWithLicense:
    """应用程序集成示例"""

    def __init__(self, license_key: str, license_server: str = "http://localhost:8000"):
        """
        初始化应用

        Args:
            license_key: 许可证密钥
            license_server: 许可证服务器地址
        """
        self.license_key = license_key
        self.client = LicenseClient(license_server)
        self.verified = False

    def verify_and_start(self) -> bool:
        """验证许可证并启动应用"""
        print("正在验证许可证...")

        result = self.client.verify_license(self.license_key)

        if result.get("valid"):
            self.verified = True
            print("✓ 许可证验证成功！")
            print(f"  产品: {result['license']['product']}")
            print(f"  客户: {result['license']['customer']}")
            print(f"  剩余激活数: {result.get('remaining_activations', 'N/A')}")
            expiry = result.get("expiry_date")
            if expiry:
                print(f"  到期日期: {expiry}")
            return True
        else:
            print(f"✗ 许可证验证失败: {result.get('message')}")
            return False

    def run(self):
        """运行应用"""
        if not self.verified:
            print("错误: 未验证许可证！")
            return

        print("\n应用程序运行中...")
        print("机器码:", self.client.get_machine_code())

        # 在这里添加你的应用逻辑
        # ...


# 使用示例
if __name__ == "__main__":
    # 示例 1: 基本使用
    print("=" * 50)
    print("示例 1: 基本许可证验证")
    print("=" * 50)

    client = LicenseClient()

    # 使用你的许可证密钥
    license_key = "LS-2026-CHSVYS8PAB9LT53L"  # 替换为你的许可证

    result = client.verify_license(license_key)
    print(f"验证结果: {result}")

    # 示例 2: 应用集成
    print("\n" + "=" * 50)
    print("示例 2: 应用集成")
    print("=" * 50)

    app = AppWithLicense(license_key)
    if app.verify_and_start():
        app.run()
    else:
        print("应用程序无法启动，许可证无效！")

    # 示例 3: 获取机器码
    print("\n" + "=" * 50)
    print("示例 3: 获取机器码")
    print("=" * 50)
    print(f"当前机器码: {client.get_machine_code()}")
