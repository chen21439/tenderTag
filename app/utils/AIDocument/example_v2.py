"""
百度图像理解调用示例 V2
基于 OpenAI SDK（推荐使用）
"""
from app.utils.AIDocument import BaiduImageClientV2
from app.prompts.AIDocument.image_understanding_prompt import (
    BASIC_IMAGE_PROMPT,
    DOCUMENT_IMAGE_WITH_JSON_PROMPT,
    TABLE_RECOGNITION_PROMPT
)
import json


def example_v2_basic():
    """示例1: 基础图像理解（V2）"""
    print("\n" + "=" * 80)
    print("示例1: 基础图像理解（V2 - OpenAI SDK）")
    print("=" * 80)

    # 初始化客户端（使用 API Key）
    API_KEY = "your_api_key_here"
    client = BaiduImageClientV2(
        api_key=API_KEY,
        model="qianfan-vl-8b"  # 支持视觉理解的模型
    )

    # 调用
    response = client.send_request(
        prompt=BASIC_IMAGE_PROMPT,
        image_path="path/to/your/image.jpg",
        temperature=0.000001,  # 越小越确定
        top_p=1.0
    )

    print(f"\n响应结果:\n{response}")


def example_v2_with_json():
    """示例2: 带JSON数据的文档图像理解（V2）"""
    print("\n" + "=" * 80)
    print("示例2: 带JSON数据的文档图像理解（V2）")
    print("=" * 80)

    # 初始化客户端
    API_KEY = "your_api_key_here"
    client = BaiduImageClientV2(api_key=API_KEY)

    # 准备JSON数据（模拟从PDF提取的lines）
    lines_data = {
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

    # 调用（带JSON数据）
    response = client.send_request_with_json(
        prompt_template=DOCUMENT_IMAGE_WITH_JSON_PROMPT,
        image_path="path/to/document/page.jpg",
        json_data=lines_data,
        temperature=0.000001
    )

    print(f"\n响应结果:\n{response}")


def example_v2_table():
    """示例3: 表格识别（V2）"""
    print("\n" + "=" * 80)
    print("示例3: 表格识别（V2）")
    print("=" * 80)

    # 初始化客户端
    API_KEY = "your_api_key_here"
    client = BaiduImageClientV2(api_key=API_KEY)

    # 调用
    response = client.send_request(
        prompt=TABLE_RECOGNITION_PROMPT,
        image_path="path/to/table/image.jpg",
        temperature=0.000001
    )

    print(f"\n响应结果:\n{response}")

    # 尝试解析JSON响应
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            result = json.loads(json_str)
            print(f"\n解析后的表格数据:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"JSON解析失败: {e}")


def example_v2_batch():
    """示例4: 批量处理多张图片（V2）"""
    print("\n" + "=" * 80)
    print("示例4: 批量处理多张图片（V2）")
    print("=" * 80)

    # 初始化客户端
    API_KEY = "your_api_key_here"
    client = BaiduImageClientV2(api_key=API_KEY)

    # 图片列表
    image_files = [
        "path/to/page1.jpg",
        "path/to/page2.jpg",
        "path/to/page3.jpg"
    ]

    results = []

    for i, image_path in enumerate(image_files, 1):
        print(f"\n处理第 {i}/{len(image_files)} 张图片: {image_path}")

        try:
            response = client.send_request(
                prompt=BASIC_IMAGE_PROMPT,
                image_path=image_path,
                verbose=False  # 批量处理时关闭详细输出
            )

            results.append({
                "image": image_path,
                "result": response
            })

            print(f"✓ 完成")

        except Exception as e:
            print(f"✗ 失败: {e}")
            results.append({
                "image": image_path,
                "error": str(e)
            })

    # 汇总结果
    print(f"\n总结:")
    print(f"成功: {sum(1 for r in results if 'result' in r)} / {len(image_files)}")
    print(f"失败: {sum(1 for r in results if 'error' in r)} / {len(image_files)}")


if __name__ == "__main__":
    print("""
百度图像理解调用示例 V2（基于 OpenAI SDK）

优势：
1. 使用熟悉的 OpenAI SDK
2. 代码更简洁
3. 百度官方支持的新接口

使用前请先：
1. 安装 OpenAI SDK: pip install openai
2. 获取 API Key: https://console.bce.baidu.com/iam/#/iam/apikey/list
3. 将示例中的 'your_api_key_here' 替换为实际的 API Key
4. 将 'path/to/your/image.jpg' 替换为实际的图片路径

可用示例：
- example_v2_basic()         # 基础图像理解
- example_v2_with_json()     # 带JSON数据的文档分析
- example_v2_table()         # 表格识别
- example_v2_batch()         # 批量处理

支持的模型（带视觉理解）：
- qianfan-vl-8b              # 推荐
- 其他模型参考：https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Fm2vrveyu

取消下面的注释运行示例：
    """)

    # 运行示例（取消注释）
    # example_v2_basic()
    # example_v2_with_json()
    # example_v2_table()
    # example_v2_batch()
