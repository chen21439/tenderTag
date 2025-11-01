"""
项目启动脚本

使用方式:
- 开发模式: poetry run dev
- 生产模式: poetry run start
"""
import os
import sys

# 修复Windows终端编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def dev():
    """
    开发环境启动脚本
    - 启用自动重载 (--reload)
    - 监听 127.0.0.1:8000
    - 适合本地开发调试
    """
    import uvicorn

    # 获取环境变量配置 (可选)
    host = os.getenv("DEV_HOST", "127.0.0.1")
    port = int(os.getenv("DEV_PORT", "8000"))

    print(f"🚀 启动开发服务器: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔄 已启用自动重载")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


def start():
    """
    生产环境启动脚本
    - 关闭自动重载
    - 监听 0.0.0.0:8000 (允许外部访问)
    - 适合生产环境部署
    """
    import uvicorn

    # 获取环境变量配置 (可选)
    host = os.getenv("PROD_HOST", "0.0.0.0")
    port = int(os.getenv("PROD_PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))

    print(f"🚀 启动生产服务器: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"👷 工作进程数: {workers}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="warning"
    )


if __name__ == "__main__":
    # 支持直接运行脚本 (python scripts.py dev|start)
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "dev":
            dev()
        elif command == "start":
            start()
        else:
            print(f"❌ 未知命令: {command}")
            print("💡 可用命令: dev | start")
    else:
        print("💡 使用方式:")
        print("  poetry run dev       # 开发模式")
        print("  poetry run start     # 生产模式")