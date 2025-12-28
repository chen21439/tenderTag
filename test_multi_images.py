"""
测试多图文档布局分析
使用百度 qianfan-vl-8b 模型
"""
from app.utils.AIDocument import BaiduImageClientBearer
from app.utils.AIDocument.document_processor import (
    get_images_from_directory,
    process_document_batch
)
from app.prompts.AIDocument.image_understanding_prompt import (
    DOCUMENT_LAYOUT_ANALYSIS_PROMPT
)
import json


def test_multi_images_simple():
    """测试简单的多图调用（手动指定图片）"""
    print("\n" + "=" * 80)
    print("测试：多图文档布局分析（手动指定图片）")
    print("=" * 80)

    # WSL 图片目录
    image_dir = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务"

    # 手动选择前3张图片
    image_paths = [
        f"{image_dir}/城市大数据中心物业管理服务_0.jpg",
        f"{image_dir}/城市大数据中心物业管理服务_1.jpg",
        f"{image_dir}/城市大数据中心物业管理服务_2.jpg",
    ]

    # 构建页面描述
    page_descriptions = """图片 1: 文档《城市大数据中心物业管理服务》的第 0 页
图片 2: 文档《城市大数据中心物业管理服务》的第 1 页
图片 3: 文档《城市大数据中心物业管理服务》的第 2 页"""

    # 替换提示词模板
    prompt = DOCUMENT_LAYOUT_ANALYSIS_PROMPT.replace("{page_descriptions}", page_descriptions)

    # 初始化客户端
    client = BaiduImageClientBearer()

    # 调用多图API
    try:
        response = client.send_request_multi_images(
            prompt=prompt,
            image_paths=image_paths,
            temperature=0.000001
        )

        print("\n" + "=" * 80)
        print("AI 响应:")
        print("=" * 80)
        print(response)

        # 尝试解析JSON
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            result = json.loads(json_str)
            print("\n" + "=" * 80)
            print("解析后的JSON:")
            print("=" * 80)
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"\n[ERROR] 调用失败: {e}")
        import traceback
        traceback.print_exc()


def test_batch_processing():
    """测试批量处理（使用 document_processor）"""
    print("\n" + "=" * 80)
    print("测试：批量文档处理（每批5张图片）")
    print("=" * 80)

    # WSL 图片目录
    image_dir = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务"

    # 初始化客户端
    client = BaiduImageClientBearer()

    # 获取第一批图片（0-4页）
    batches = get_images_from_directory(image_dir, batch_size=5)

    if not batches:
        print("[ERROR] 未找到图片")
        return

    print(f"\n找到 {len(batches)} 个批次")
    print(f"第一批包含 {len(batches[0])} 张图片:")
    for doc_name, page_num, path in batches[0]:
        print(f"  - 第 {page_num} 页: {path}")

    # 处理第一批
    try:
        print("\n开始处理第一批...")
        response = process_document_batch(
            client=client,
            batch=batches[0],
            prompt_template=DOCUMENT_LAYOUT_ANALYSIS_PROMPT,
            temperature=0.000001,
            verbose=True
        )

        print("\n" + "=" * 80)
        print("AI 响应:")
        print("=" * 80)
        print(response)

        # 尝试解析JSON
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            result = json.loads(json_str)
            print("\n" + "=" * 80)
            print("解析后的JSON:")
            print("=" * 80)
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"\n[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()


def test_all_batches():
    """测试处理所有批次"""
    print("\n" + "=" * 80)
    print("测试：处理所有文档（分批处理）")
    print("=" * 80)

    from app.utils.AIDocument.document_processor import process_all_documents

    # WSL 图片目录
    image_dir = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务"

    # 初始化客户端
    client = BaiduImageClientBearer()

    # 处理所有文档（每批5张）
    results = process_all_documents(
        directory=image_dir,
        client=client,
        prompt_template=DOCUMENT_LAYOUT_ANALYSIS_PROMPT,
        batch_size=5,
        temperature=0.000001,
        verbose=True
    )

    # 保存结果
    output_file = "document_analysis_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    print("""
多图文档布局分析测试脚本

可用测试：
1. test_multi_images_simple()  # 简单多图测试（3张图片）
2. test_batch_processing()     # 批量处理测试（第一批5张）
3. test_all_batches()          # 处理所有批次

取消下面的注释运行测试：
    """)

    # 运行测试（取消注释）
    test_multi_images_simple()
    # test_batch_processing()
    # test_all_batches()
