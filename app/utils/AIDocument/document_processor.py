"""
文档批量处理工具
支持多页文档的批量图像分析
"""
import os
import re
from typing import List, Tuple
from pathlib import Path


def parse_image_filename(filename: str) -> Tuple[str, int]:
    """
    解析图片文件名，提取文档名和页码

    Args:
        filename: 文件名，格式为 fileName_pageNumber.jpg

    Returns:
        (文档名, 页码) 元组
    """
    # 去掉扩展名
    name_without_ext = os.path.splitext(filename)[0]

    # 使用正则分割最后一个下划线
    match = re.match(r'(.+)_(\d+)$', name_without_ext)
    if match:
        doc_name = match.group(1)
        page_number = int(match.group(2))
        return doc_name, page_number
    else:
        # 如果格式不匹配，返回文件名和0
        return name_without_ext, 0


def get_images_from_directory(
    directory: str,
    batch_size: int = 5,
    file_pattern: str = "*.jpg"
) -> List[List[Tuple[str, int, str]]]:
    """
    从目录中获取图片并分批

    Args:
        directory: 图片目录路径
        batch_size: 每批图片数量，默认5张
        file_pattern: 文件匹配模式，默认 "*.jpg"

    Returns:
        批次列表，每个批次包含 [(文档名, 页码, 完整路径), ...]
    """
    # 获取所有匹配的图片文件
    image_files = sorted(Path(directory).glob(file_pattern))

    # 解析文件名并添加完整路径
    images_with_info = []
    for img_path in image_files:
        doc_name, page_num = parse_image_filename(img_path.name)
        images_with_info.append((doc_name, page_num, str(img_path)))

    # 按页码排序
    images_with_info.sort(key=lambda x: x[1])

    # 分批
    batches = []
    for i in range(0, len(images_with_info), batch_size):
        batch = images_with_info[i:i + batch_size]
        batches.append(batch)

    return batches


def build_page_descriptions(batch: List[Tuple[str, int, str]]) -> str:
    """
    构建页面描述文本

    Args:
        batch: 批次信息列表 [(文档名, 页码, 路径), ...]

    Returns:
        页面描述文本
    """
    descriptions = []
    for i, (doc_name, page_num, _) in enumerate(batch, 1):
        descriptions.append(f"图片 {i}: 文档《{doc_name}》的第 {page_num} 页")

    return "\n".join(descriptions)


def process_document_batch(
    client,
    batch: List[Tuple[str, int, str]],
    prompt_template: str,
    temperature: float = 0.000001,
    verbose: bool = True
) -> str:
    """
    处理一批文档图片

    Args:
        client: BaiduImageClientBearer 实例
        batch: 批次信息 [(文档名, 页码, 路径), ...]
        prompt_template: 提示词模板（包含 {page_descriptions} 占位符）
        temperature: 温度参数
        verbose: 是否打印详细信息

    Returns:
        AI 响应
    """
    # 提取图片路径
    image_paths = [path for _, _, path in batch]

    # 构建页面描述
    page_descriptions = build_page_descriptions(batch)

    # 替换提示词中的占位符
    prompt = prompt_template.replace("{page_descriptions}", page_descriptions)

    # 调用多图API
    response = client.send_request_multi_images(
        prompt=prompt,
        image_paths=image_paths,
        temperature=temperature,
        verbose=verbose
    )

    return response


def process_all_documents(
    directory: str,
    client,
    prompt_template: str,
    batch_size: int = 5,
    temperature: float = 0.000001,
    verbose: bool = True
) -> List[dict]:
    """
    处理目录中所有文档图片

    Args:
        directory: 图片目录
        client: BaiduImageClientBearer 实例
        prompt_template: 提示词模板
        batch_size: 每批图片数量
        temperature: 温度参数
        verbose: 是否打印详细信息

    Returns:
        所有批次的结果列表
    """
    # 获取分批信息
    batches = get_images_from_directory(directory, batch_size)

    if verbose:
        print(f"[DocumentProcessor] 共找到 {sum(len(b) for b in batches)} 张图片")
        print(f"[DocumentProcessor] 分为 {len(batches)} 个批次处理（每批 {batch_size} 张）")

    results = []

    # 逐批处理
    for batch_idx, batch in enumerate(batches, 1):
        if verbose:
            print(f"\n{'=' * 80}")
            print(f"[Batch {batch_idx}/{len(batches)}] 处理第 {batch[0][1]} - {batch[-1][1]} 页")
            print(f"{'=' * 80}")

        try:
            response = process_document_batch(
                client=client,
                batch=batch,
                prompt_template=prompt_template,
                temperature=temperature,
                verbose=verbose
            )

            results.append({
                "batch_index": batch_idx,
                "pages": [page_num for _, page_num, _ in batch],
                "response": response,
                "success": True
            })

        except Exception as e:
            if verbose:
                print(f"[ERROR] 批次 {batch_idx} 处理失败: {e}")

            results.append({
                "batch_index": batch_idx,
                "pages": [page_num for _, page_num, _ in batch],
                "error": str(e),
                "success": False
            })

    # 统计
    if verbose:
        success_count = sum(1 for r in results if r["success"])
        print(f"\n{'=' * 80}")
        print(f"[DocumentProcessor] 处理完成")
        print(f"  - 成功: {success_count}/{len(batches)}")
        print(f"  - 失败: {len(batches) - success_count}/{len(batches)}")
        print(f"{'=' * 80}")

    return results


if __name__ == "__main__":
    # 测试文件名解析
    test_filenames = [
        "城市大数据中心物业管理服务_0.jpg",
        "城市大数据中心物业管理服务_1.jpg",
        "城市大数据中心物业管理服务_10.jpg",
    ]

    print("测试文件名解析:")
    for filename in test_filenames:
        doc_name, page_num = parse_image_filename(filename)
        print(f"  {filename} -> 文档: {doc_name}, 页码: {page_num}")
