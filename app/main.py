# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# 可选：有 classify 路由就挂载，没有也不报错
def _maybe_include_classify(app: FastAPI):
    try:
        from app.routers.classify import router as classify_router
        app.include_router(classify_router, prefix="/api")
    except Exception:
        # 没有该路由文件或导入失败时，仍可启动
        pass

def _maybe_include_pdf_process(app: FastAPI):
    """注册 PDF 处理路由"""
    try:
        from app.routers.pdf_process import router as pdf_router
        app.include_router(pdf_router, prefix="/api/pdf", tags=["PDF处理"])
        print("[启动] PDF处理路由已加载")
    except Exception as e:
        print(f"[警告] PDF处理路由加载失败: {e}")
        pass

def create_app() -> FastAPI:
    app = FastAPI(
        title="Tender Tagger",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS（按需调整或删除）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @_health(app)
    def _():  # 占位让修饰器运行
        ...

    _maybe_include_classify(app)
    _maybe_include_pdf_process(app)  # 注册 PDF 处理路由
    return app

def _health(app: FastAPI):
    """装饰器：注册健康检查与根路由"""
    def dec(func):
        @app.get("/health")
        def health():
            return {"ok": True}

        @app.get("/")
        def root():
            return {"service": "tender-tagger", "docs": "/docs", "health": "/health"}

        return func
    return dec

app = create_app()