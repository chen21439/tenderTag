"""
命令行入口

提供开发和生产环境的启动命令
"""

import sys
import os


def dev():
    """开发模式启动 (带热重载)"""
    import uvicorn

    print("="*80)
    print("启动开发服务器 (热重载已启用)")
    print("="*80)
    print("API 文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    print("="*80)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开启热重载
        reload_dirs=["app"],  # 监听 app 目录
        log_level="info"
    )


def start():
    """生产模式启动 (无热重载)"""
    import uvicorn

    print("="*80)
    print("启动生产服务器")
    print("="*80)
    print("API 文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    print("="*80)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 关闭热重载
        workers=4,  # 多进程
        log_level="info"
    )


def main():
    """主入口 (根据参数选择模式)"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "dev":
            dev()
        elif command == "start":
            start()
        else:
            print(f"未知命令: {command}")
            print("可用命令:")
            print("  dev   - 开发模式 (热重载)")
            print("  start - 生产模式 (多进程)")
            sys.exit(1)
    else:
        # 默认开发模式
        dev()


if __name__ == "__main__":
    main()