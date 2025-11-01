"""
测试合规审查服务 - 插入一条数据

使用前请修改数据库连接信息
"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.utils.db.mysql import MySQLUtil, ComplianceService


def test_insert():
    """
    测试插入一条数据
    """
    print("="*80)
    print("测试合规审查服务 - 插入数据")
    print("="*80)

    # ========== 1. 配置数据库连接 ==========
    DB_CONFIG = {
        "host": "172.16.0.116",    # 数据库主机
        "port": 3306,              # 数据库端口
        "user": "root",            # 数据库用户名
        "password": "123456",      # 数据库密码
        "database": "tender_compliance",  # 数据库名称
        "charset": "utf8mb4",
        "echo": True  # 打印 SQL 语句 (调试用)
    }

    print("\n[步骤 1] 连接数据库...")
    print(f"  主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  数据库: {DB_CONFIG['database']}")

    try:
        mysql = MySQLUtil(**DB_CONFIG)
        print("  [OK] 连接成功")
    except Exception as e:
        print(f"  [FAIL] 连接失败: {e}")
        print("\n请检查数据库连接信息是否正确!")
        return

    # ========== 2. 初始化服务 ==========
    print("\n[步骤 2] 初始化合规审查服务...")
    service = ComplianceService(mysql)

    # ========== 3. 准备测试数据 ==========
    print("\n[步骤 3] 准备测试数据...")

    # 使用一个测试 PDF 路径 (可以不存在,仅用于测试文件名)
    # 如果要真实插入,请替换为实际的 PDF 路径
    test_pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\test\测试招标文件.pdf"

    # 创建测试 PDF 文件 (如果不存在)
    test_pdf = Path(test_pdf_path)
    if not test_pdf.exists():
        print(f"  [WARN] PDF 文件不存在,创建临时测试文件...")
        test_pdf.parent.mkdir(parents=True, exist_ok=True)
        test_pdf.write_text("测试PDF内容", encoding="utf-8")
        print(f"  [OK] 已创建测试文件: {test_pdf_path}")

    # ========== 4. 插入数据 ==========
    print("\n[步骤 4] 插入测试数据...")

    try:
        task = service.create_task_from_pdf(
            pdf_path=test_pdf_path,
            file_id=None,  # 自动生成
            project_name="鄂尔多斯市政府网站群集约化平台升级改造项目",
            project_code="ORDOS-2025-001",
            procurement_method="公开招标",
            project_type="信息化建设",
            overview="对鄂尔多斯市政府网站进行集约化平台升级改造，提升用户体验和服务能力，实现统一管理和资源共享。",
            app_id="tenant_ordos",
            create_user="admin001",
            create_user_name="系统管理员"
        )

        print("\n" + "="*80)
        print("[OK] 数据插入成功!")
        print("="*80)
        print(f"\n任务详情:")
        print(f"  任务ID: {task.id}")
        print(f"  文件ID: {task.file_id}")
        print(f"  文件名: {task.file_name}")
        print(f"  项目名称: {task.project_name}")
        print(f"  项目编号: {task.project_code}")
        print(f"  采购方式: {task.procurement_method}")
        print(f"  项目类型: {task.project_type}")
        print(f"  项目概述: {task.overview[:50]}...")
        print(f"  评审状态: {task.review_status} (3=解析中)")
        print(f"  租户ID: {task.app_id}")
        print(f"  创建用户: {task.create_user_name} ({task.create_user})")
        print(f"  创建时间: {task.create_time}")

        # ========== 5. 验证插入 ==========
        print("\n[步骤 5] 验证插入的数据...")
        found_task = service.get_task(task.id)

        if found_task:
            print("  [OK] 数据验证成功,已从数据库读取到刚插入的记录")
            print(f"  ID: {found_task.id}")
            print(f"  文件名: {found_task.file_name}")
            print(f"  项目名称: {found_task.project_name}")
        else:
            print("  [FAIL] 验证失败,无法从数据库读取到插入的记录")

        # ========== 6. 统计信息 ==========
        print("\n[步骤 6] 统计信息...")
        from app.utils.db.mysql.models import ComplianceFileTask

        total = mysql.count(ComplianceFileTask)
        parsing = service.count_tasks_by_status(review_status=3)

        print(f"  总任务数: {total}")
        print(f"  解析中的任务: {parsing}")

    except FileNotFoundError as e:
        print(f"\n[FAIL] 错误: {e}")
        print("请修改 test_pdf_path 为实际的 PDF 文件路径")

    except Exception as e:
        print(f"\n[FAIL] 插入失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # ========== 7. 关闭连接 ==========
        print("\n[步骤 7] 关闭数据库连接...")
        mysql.close()
        print("  [OK] 连接已关闭")

    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)


if __name__ == "__main__":
    test_insert()