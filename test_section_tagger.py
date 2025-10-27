"""
测试 SectionTagger - 简化版测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.section_tagger import SectionTagger
from app.utils.file_reader import FileReader, DEFAULT_FILE_DIR


def test_file_reader():
    """测试 FileReader 获取最新JSON"""
    print("=" * 60)
    print("测试 FileReader")
    print("=" * 60)

    reader = FileReader(DEFAULT_FILE_DIR)
    latest_json = reader.get_latest_analysis_json()

    if latest_json:
        print(f"找到文件: {latest_json.name}")
        print(f"完整路径: {latest_json}")

        # 读取并解析JSON
        import json
        content = reader.read_file(str(latest_json))
        data = json.loads(content)

        print(f"\nJSON结构:")
        print(f"- doc_meta: {list(data.get('doc_meta', {}).keys())}")
        print(f"- layout_stats: {list(data.get('layout_stats', {}).keys())}")
        print(f"- tree 节点数: {len(data.get('tree', []))}")

        # 统计section数量
        sections = [node for node in data.get('tree', []) if node.get('type') == 'section']
        print(f"- section 数量: {len(sections)}")

        # 显示前3个section
        print(f"\n前3个section:")
        for i, section in enumerate(sections[:3]):
            print(f"  {i+1}. {section.get('text')} (level={section.get('level')})")
            blocks = section.get('blocks', [])
            print(f"     - blocks数量: {len(blocks)}")

        return latest_json
    else:
        print("未找到JSON文件")
        return None


def test_section_tagger_init():
    """测试 SectionTagger 初始化"""
    print("\n" + "=" * 60)
    print("测试 SectionTagger 初始化")
    print("=" * 60)

    try:
        tagger = SectionTagger(model_name="qwen3:4b")
        print("✓ SectionTagger 初始化成功")
        print(f"  - 模型: {tagger.model_name}")
        print(f"  - 文件目录: {tagger.file_directory}")
        return tagger
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return None


def test_extract_fields(tagger, json_path):
    """测试字段提取"""
    print("\n" + "=" * 60)
    print("测试字段提取")
    print("=" * 60)

    # 读取JSON
    import json
    content = tagger.file_reader.read_file(str(json_path))
    data = json.loads(content)

    # 获取第一个section
    tree = data.get('tree', [])
    first_section = None
    for node in tree:
        if node.get('type') == 'section':
            first_section = node
            break

    if not first_section:
        print("未找到section节点")
        return

    # 提取字段
    extracted = tagger.extract_section_fields(first_section)

    print(f"提取的字段:")
    print(f"  - id: {extracted.get('id')}")
    print(f"  - text: {extracted.get('text')}")
    print(f"  - level: {extracted.get('level')}")
    print(f"  - normalized: {extracted.get('normalized')}")
    print(f"  - heading_source: {extracted.get('heading_source')}")
    print(f"  - blocks数量: {len(extracted.get('blocks', []))}")

    # 显示blocks
    blocks = extracted.get('blocks', [])
    if blocks:
        print(f"\n  前3个blocks:")
        for i, block in enumerate(blocks[:3]):
            print(f"    {i+1}. type={block.get('type')}, id={block.get('id')}")


if __name__ == '__main__':
    # 测试1: FileReader
    json_path = test_file_reader()

    if not json_path:
        print("\n测试终止: 未找到JSON文件")
        sys.exit(1)

    # 测试2: SectionTagger初始化
    tagger = test_section_tagger_init()

    if not tagger:
        print("\n测试终止: SectionTagger初始化失败")
        sys.exit(1)

    # 测试3: 字段提取
    test_extract_fields(tagger, json_path)

    print("\n" + "=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)
