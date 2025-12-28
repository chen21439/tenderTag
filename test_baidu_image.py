"""
快速测试百度图像理解 API
使用 WSL 中的实际图片
"""
from app.utils.AIDocument import BaiduImageClientBearer
from app.prompts.AIDocument.image_understanding_prompt import BASIC_IMAGE_PROMPT
import os


def test_wsl_image():
    """测试使用 WSL 路径中的图片"""
    print("\n" + "=" * 80)
    print("测试：百度图像理解（使用 WSL 路径图片）")
    print("=" * 80)

    # WSL 路径（在 Git Bash/MSYS 环境中使用 // 格式）
    wsl_image_dir = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务"
    image_name = "城市大数据中心物业管理服务_0.jpg"
    image_path = os.path.join(wsl_image_dir, image_name)

    print(f"图片路径: {image_path}")

    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return

    print(f"[OK] 文件存在，大小: {os.path.getsize(image_path) / 1024:.2f} KB")

    # 初始化客户端（使用默认配置，已内置 API Key）
    client = BaiduImageClientBearer()

    # 发送请求
    try:
        print("\n开始调用百度 API...")
        response = client.send_request(
            prompt=BASIC_IMAGE_PROMPT,
            image_path=image_path,
            temperature=0.000001,
            top_p=1.0
        )

        print(f"\n{'=' * 80}")
        print("✅ 调用成功！")
        print(f"{'=' * 80}")
        print(f"\nAI 响应:\n{response}")
        print(f"\n{'=' * 80}")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()


def test_with_json_data():
    """测试带 JSON 数据的调用"""
    print("\n" + "=" * 80)
    print("测试：带 JSON 数据的文档图像理解")
    print("=" * 80)

    # WSL 路径
    wsl_image_dir = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务"
    image_name = "城市大数据中心物业管理服务_0.jpg"
    image_path = os.path.join(wsl_image_dir, image_name)

    print(f"图片路径: {image_path}")

    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return

    print(f"✅ 文件存在")

    # 模拟 JSON 数据（lines）
    json_data = {
        "lines": [
            {
                "id": 1,
                "text": "城市大数据中心物业管理服务",
                "bbox": [100, 50, 500, 100],
                "font_size": 18,
                "is_bold": True
            },
            {
                "id": 2,
                "text": "服务内容说明",
                "bbox": [100, 120, 400, 150],
                "font_size": 14,
                "is_bold": False
            }
        ]
    }

    # 自定义提示词（结合图片和 JSON）
    prompt_template = """请分析这张文档图片，并结合以下提取的文本行数据：

```json
{json_data}
```

请回答：
1. 图片中的主要内容是什么？
2. 提供的文本行数据是否准确反映了图片内容？
3. 是否有遗漏或错误的地方？

请用简洁的语言回答。"""

    # 初始化客户端
    client = BaiduImageClientBearer()

    # 发送请求
    try:
        print("\n开始调用百度 API...")
        response = client.send_request_with_json(
            prompt_template=prompt_template,
            image_path=image_path,
            json_data=json_data,
            temperature=0.000001
        )

        print(f"\n{'=' * 80}")
        print("✅ 调用成功！")
        print(f"{'=' * 80}")
        print(f"\nAI 响应:\n{response}")
        print(f"\n{'=' * 80}")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()


def list_available_images():
    """列出可用的图片"""
    print("\n" + "=" * 80)
    print("可用图片列表")
    print("=" * 80)

    wsl_image_dir = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务"

    try:
        files = os.listdir(wsl_image_dir)
        image_files = [f for f in files if f.endswith('.jpg') or f.endswith('.png')]

        print(f"\n目录: {wsl_image_dir}")
        print(f"共找到 {len(image_files)} 张图片:\n")

        for i, img in enumerate(sorted(image_files)[:10], 1):  # 只显示前10张
            full_path = os.path.join(wsl_image_dir, img)
            size_kb = os.path.getsize(full_path) / 1024
            print(f"{i:2d}. {img:50s} ({size_kb:8.2f} KB)")

        if len(image_files) > 10:
            print(f"\n... 还有 {len(image_files) - 10} 张图片")

    except Exception as e:
        print(f"❌ 读取目录失败: {e}")


if __name__ == "__main__":
    print("""
百度图像理解快速测试脚本

WSL 路径说明：
- Windows: \\\\wsl.localhost\\Ubuntu-22.04\\root\\...
- Git Bash/MSYS: //wsl.localhost/Ubuntu-22.04/root/...
- Python os.path: //wsl.localhost/Ubuntu-22.04/root/...

可用测试：
1. list_available_images()  # 列出可用图片
2. test_wsl_image()         # 基础图像理解
3. test_with_json_data()    # 带 JSON 数据

运行测试：
    """)

    # 列出可用图片
    list_available_images()

    # 运行测试（取消注释）
    print("\n" + "=" * 80)
    print("开始测试...")
    print("=" * 80)

    test_wsl_image()
    # test_with_json_data()
