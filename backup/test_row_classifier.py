"""
测试跨页行级别分类器

测试 classify_row_pairs_batch 方法
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.unTaggedPDF.crossPageTable import CrossPageCellClassifier


def main():
    print("=" * 80)
    print("跨页行级别智能分类器 - 测试")
    print("=" * 80)

    # 初始化分类器
    try:
        classifier = CrossPageCellClassifier(truncate_length=50)
        print(f"✅ 分类器初始化成功，截取长度: {classifier.truncate_length} 字符")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 准备测试数据
    row_pairs = [
        {
            "prev_row": {
                "第0列": "根据投标人提供的项目技术方案，包括总体架构设计、业务架构设计、数据架构设计、技术架构设",
                "第1列": "5分",
                "第2列": "优秀"
            },
            "next_row": {
                "第0列": "计、网络架构设计、与现有国土空间规划"一张图"实施监测系统及相关系统对接方案等方面进行综合评审。",
                "第1列": "",
                "第2列": ""
            },
            "context": {
                "prev_table_id": "t1_p1",
                "next_table_id": "t1_p2",
                "prev_page": 1,
                "next_page": 2,
                "hint_score": 0.95
            }
        },
        {
            "prev_row": {
                "第0列": "技术方案设计科学、合理、实际可实施、操作性强",
                "第1列": "4分",
                "第2列": "良好"
            },
            "next_row": {
                "第0列": "整体技术方案设计合理可行但内容通用",
                "第1列": "3分",
                "第2列": "一般"
            },
            "context": {
                "prev_table_id": "t2_p2",
                "next_table_id": "t2_p3",
                "prev_page": 2,
                "next_page": 3,
                "hint_score": 0.88
            }
        },
        {
            "prev_row": {
                "第0列": "针对本期项目综合服务要求响应完善，与现有国土空间规划"一张图"实施监测系统及相关系统进行充分对接，",
                "第1列": "5分",
                "第2列": ""
            },
            "next_row": {
                "第0列": "对项目整体技术需求范围覆盖程度高，完全满足招标相关需求",
                "第1列": "",
                "第2列": "优秀"
            },
            "context": {
                "prev_table_id": "t3_p3",
                "next_table_id": "t3_p4",
                "prev_page": 3,
                "next_page": 4,
                "hint_score": 0.92
            }
        }
    ]

    # 期望结果
    expected = [True, False, True]  # 第1、3个应该合并，第2个不应合并

    print(f"\n📊 测试数据: {len(row_pairs)} 个行对")
    print("=" * 80)

    # 调用批量判断
    print(f"\n🤖 开始批量 AI 判断...")
    results = classifier.classify_row_pairs_batch(row_pairs)

    # 打印结果
    print(f"\n✅ 判断完成，收到 {len(results)} 个结果\n")
    print("=" * 80)

    correct_count = 0
    for i, result in enumerate(results):
        print(f"\n【行对 {i+1}】")
        print(f"  上页: {list(row_pairs[i]['prev_row'].values())[0][:40]}...")
        print(f"  下页: {list(row_pairs[i]['next_row'].values())[0][:40]}...")
        print(f"  页码: {row_pairs[i]['context']['prev_page']} → {row_pairs[i]['context']['next_page']}")
        print(f"\n  判断结果:")
        print(f"    should_merge: {result.get('should_merge')}")
        print(f"    confidence: {result.get('confidence', 0):.2f}")
        print(f"    reason: {result.get('reason', 'N/A')}")

        # 检查是否符合预期
        is_correct = result.get('should_merge') == expected[i]
        correct_count += is_correct
        print(f"\n  预期: {'应该合并' if expected[i] else '不应合并'}")
        print(f"  结果: {'✅ 正确' if is_correct else '❌ 错误'}")

        if result.get('error'):
            print(f"  ⚠️  错误: {result.get('error')}")

        print("-" * 80)

    # 统计
    print(f"\n📈 测试统计:")
    print(f"  总数: {len(results)}")
    print(f"  正确: {correct_count}")
    print(f"  准确率: {correct_count / len(results) * 100:.1f}%")
    print("=" * 80)


if __name__ == '__main__':
    main()