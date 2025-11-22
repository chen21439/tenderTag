"""
快速测试百度图像理解（Bearer 鉴权）
已内置 API Key，可以直接运行测试
"""
from app.utils.AIDocument import BaiduImageClientBearer
from app.prompts.AIDocument.image_understanding_prompt import (
    BASIC_IMAGE_PROMPT,
    DOCUMENT_IMAGE_WITH_JSON_PROMPT
)


def test_basic():
    """测试基础图像理解"""
    print("\n" + "=" * 80)
    print("测试：基础图像理解（Bearer 鉴权）")
    print("=" * 80)

    # 使用默认配置（已内置 API Key）
    client = BaiduImageClientBearer()

    # 测试图片路径（请替换为实际路径）
    image_path = "path/to/your/test/image.jpg"

    try:
        response = client.send_request(
            prompt=BASIC_IMAGE_PROMPT,
            image_path=image_path
        )

        print(f"\n✅ 调用成功！")
        print(f"\n响应内容:\n{response}")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")


def test_with_json():
    """测试带 JSON 数据的调用"""
    print("\n" + "=" * 80)
    print("测试：带 JSON 数据的文档图像理解")
    print("=" * 80)

    client = BaiduImageClientBearer()

    # 模拟 JSON 数据
    json_data = {
        "lines": [
            {
                "id": 1,
                "text": "第一章 总则",
                "bbox": [100, 50, 300, 80],
                "font_size": 16
            },
            {
                "id": 2,
                "text": "第一条 本规定适用于...",
                "bbox": [100, 100, 500, 120],
                "font_size": 12
            }
        ]
    }

    # 测试图片路径
    image_path = "path/to/your/document/page.jpg"

    try:
        response = client.send_request_with_json(
            prompt_template=DOCUMENT_IMAGE_WITH_JSON_PROMPT,
            image_path=image_path,
            json_data=json_data
        )

        print(f"\n✅ 调用成功！")
        print(f"\n响应内容:\n{response}")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")


def test_custom_prompt():
    """测试自定义提示词"""
    print("\n" + "=" * 80)
    print("测试：自定义提示词")
    print("=" * 80)

    client = BaiduImageClientBearer()

    # 自定义提示词
    custom_prompt = """请识别这张图片中的所有文字，并按照从上到下的顺序列出。

对于每一行文字，请输出：
1. 文字内容
2. 大致位置（上/中/下）
3. 是否为标题（字体较大、加粗等）

请以 JSON 格式输出。"""

    image_path = "path/to/your/image.jpg"

    try:
        response = client.send_request(
            prompt=custom_prompt,
            image_path=image_path,
            temperature=0.000001  # 更确定的输出
        )

        print(f"\n✅ 调用成功！")
        print(f"\n响应内容:\n{response}")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")


if __name__ == "__main__":
    print("""
百度图像理解快速测试（Bearer 鉴权）

✅ 优势：
- 已内置 API Key，无需额外配置
- 使用新一代 Bearer 鉴权机制
- 直接调用，不需要换 access_token

📝 使用前：
1. 将下面的图片路径替换为实际路径
2. 运行对应的测试函数

可用测试：
- test_basic()          # 基础图像理解
- test_with_json()      # 带 JSON 数据
- test_custom_prompt()  # 自定义提示词

取消下面的注释运行测试：
    """)

    # 运行测试（取消注释，并替换图片路径）
    # test_basic()
    # test_with_json()
    # test_custom_prompt()

    # 或者使用全局单例
    from app.utils.AIDocument import get_baidu_client_bearer

    print("\n使用全局单例示例:")
    print("=" * 80)
    client = get_baidu_client_bearer()
    print("✅ 全局客户端已初始化，可以直接使用！")
    print("\n调用示例:")
    print("""
    response = client.send_request(
        prompt="请描述这张图片",
        image_path="your/image.jpg"
    )
    """)
