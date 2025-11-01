"""
PDF 处理路由

提供 PDF 文件上传、解析、向量化和数据库存储功能
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import uuid
from datetime import datetime
import shutil

# 创建路由
router = APIRouter(tags=["PDF处理"])


# ==================== 响应模型 ====================

class PDFProcessResponse(BaseModel):
    """PDF 处理响应"""
    success: bool
    message: str
    task_id: str
    doc_id: str
    data: Optional[Dict[str, Any]] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    review_status: Optional[int] = None
    review_result: Optional[int] = None
    file_name: Optional[str] = None
    project_name: Optional[str] = None
    created_at: Optional[str] = None


# ==================== 辅助函数 ====================

def generate_task_id() -> str:
    """
    生成任务ID (20位字符串)

    Returns:
        任务ID (格式: 时间戳12位 + 随机数8位)
    """
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")  # 12位
    random_part = str(uuid.uuid4().int)[:8]  # 8位随机数
    return timestamp + random_part


def create_task_directory(task_id: str, base_dir: str = "file") -> Path:
    """
    创建任务目录

    Args:
        task_id: 任务ID
        base_dir: 基础目录 (默认 "file")

    Returns:
        任务目录路径
    """
    task_dir = Path(base_dir) / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


# ==================== 路由接口 ====================

@router.post("/upload_pdf", response_model=PDFProcessResponse, summary="上传并处理PDF文件")
async def upload_and_process_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    project_name: Optional[str] = Form(None, description="项目名称"),
    project_code: Optional[str] = Form(None, description="项目编号"),
    procurement_method: Optional[str] = Form(None, description="采购方式"),
    project_type: Optional[str] = Form(None, description="项目类型"),
    overview: Optional[str] = Form(None, description="项目概述"),
    app_id: Optional[str] = Form(None, description="租户ID"),
    create_user: Optional[str] = Form(None, description="创建用户ID"),
    create_user_name: Optional[str] = Form(None, description="创建用户名称"),
    save_to_db: bool = Form(True, description="是否保存到数据库"),
    save_to_milvus: bool = Form(True, description="是否保存到Milvus向量库")
):
    """
    上传并处理 PDF 文件

    功能:
    1. 接收 PDF 文件上传
    2. 生成唯一任务ID
    3. 创建任务目录 (file/{task_id}/)
    4. 保存 PDF 文件
    5. 调用 PDFContentExtractor 提取表格和单元格
    6. 生成 JSON 文件 (table.json, cells.json)
    7. 保存到 MySQL 数据库 (可选)
    8. 保存到 Milvus 向量库 (可选)

    返回:
        任务ID、文档ID和处理结果
    """
    try:
        # 1. 验证文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持 PDF 文件")

        # 2. 生成任务ID
        task_id = generate_task_id()

        # 3. 创建任务目录
        task_dir = create_task_directory(task_id)

        # 4. 保存 PDF 文件
        pdf_filename = file.filename
        pdf_path = task_dir / pdf_filename

        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"[PDF处理] 任务ID: {task_id}")
        print(f"[PDF处理] PDF已保存: {pdf_path}")

        # 5. 调用 PDFContentExtractor 处理
        from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor

        extractor = PDFContentExtractor(
            pdf_path=str(pdf_path),
            enable_cross_page_merge=True,
            enable_cell_merge=False,
            enable_ai_row_classification=False,
            verbose=False
        )

        # 6. 提取并保存 JSON (保存到任务目录)
        result_paths = extractor.save_to_json(
            output_dir=str(task_dir),
            include_paragraphs=False,  # 只保存表格
            task_id=task_id,
            save_cells=True  # 保存单元格数据并写入 Milvus
        )

        print(f"[PDF处理] JSON已生成:")
        for key, path in result_paths.items():
            print(f"  - {key}: {path}")

        # 7. 生成 doc_id (从 cells JSON 中读取)
        doc_id = task_id
        if "cells" in result_paths:
            import json
            with open(result_paths["cells"], "r", encoding="utf-8") as f:
                cells_data = json.load(f)
                doc_id = cells_data.get("doc_id", task_id)

        # 8. 保存到数据库 (如果启用)
        db_task_id = None
        if save_to_db:
            try:
                from app.utils.db.mysql import MySQLUtil, ComplianceService

                # 初始化数据库连接
                mysql = MySQLUtil(
                    host="172.16.0.116",
                    port=3306,
                    user="root",
                    password="123456",
                    database="tender_compliance",
                    charset="utf8mb4",
                    echo=False
                )

                # 创建合规审查任务
                service = ComplianceService(mysql)
                db_task = service.create_task_from_pdf(
                    pdf_path=str(pdf_path),
                    file_id=None,  # 自动生成
                    project_name=project_name,
                    project_code=project_code,
                    procurement_method=procurement_method,
                    project_type=project_type,
                    overview=overview,
                    app_id=app_id,
                    create_user=create_user,
                    create_user_name=create_user_name
                )

                db_task_id = db_task.id
                print(f"[PDF处理] 数据库任务ID: {db_task_id}")

                mysql.close()

            except Exception as e:
                print(f"[PDF处理] 数据库保存失败: {e}")
                # 不中断流程,继续返回结果

        # 9. 构建响应
        response_data = {
            "task_id": task_id,
            "doc_id": doc_id,
            "db_task_id": db_task_id,
            "pdf_path": str(pdf_path),
            "files": result_paths,
            "project_name": project_name,
            "saved_to_db": save_to_db and db_task_id is not None,
            "saved_to_milvus": save_to_milvus and "cells" in result_paths
        }

        return PDFProcessResponse(
            success=True,
            message=f"PDF 处理成功",
            task_id=task_id,
            doc_id=doc_id,
            data=response_data
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/task/{task_id}", response_model=TaskStatusResponse, summary="查询任务状态")
async def get_task_status(task_id: str):
    """
    查询任务状态

    Args:
        task_id: 任务ID (数据库中的主键)

    Returns:
        任务状态信息
    """
    try:
        from app.utils.db.mysql import MySQLUtil, ComplianceService

        # 初始化数据库连接
        mysql = MySQLUtil(
            host="172.16.0.116",
            port=3306,
            user="root",
            password="123456",
            database="tender_compliance",
            charset="utf8mb4",
            echo=False
        )

        # 查询任务
        service = ComplianceService(mysql)
        task = service.get_task(task_id)

        mysql.close()

        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

        return TaskStatusResponse(
            task_id=task.id,
            status="completed" if task.review_status == 2 else "processing",
            review_status=task.review_status,
            review_result=task.review_result,
            file_name=task.file_name,
            project_name=task.project_name,
            created_at=task.create_time.isoformat() if task.create_time else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.put("/task/{task_id}/status", summary="更新任务状态")
async def update_task_status(
    task_id: str,
    review_status: Optional[int] = Form(None, description="评审状态 (1:审查中 2:审查结束 -1:失败 3:解析中)"),
    review_result: Optional[int] = Form(None, description="评审结果 (0:无风险 1:有风险)"),
    update_user: Optional[str] = Form(None, description="更新用户ID")
):
    """
    更新任务状态

    Args:
        task_id: 任务ID
        review_status: 评审状态
        review_result: 评审结果
        update_user: 更新用户ID

    Returns:
        更新结果
    """
    try:
        from app.utils.db.mysql import MySQLUtil, ComplianceService

        # 初始化数据库连接
        mysql = MySQLUtil(
            host="172.16.0.116",
            port=3306,
            user="root",
            password="123456",
            database="tender_compliance",
            charset="utf8mb4",
            echo=False
        )

        # 更新任务状态
        service = ComplianceService(mysql)
        success = service.update_task_status(
            task_id=task_id,
            review_status=review_status,
            review_result=review_result,
            update_user=update_user
        )

        mysql.close()

        if not success:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在或更新失败")

        return {"success": True, "message": "状态更新成功", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/tasks", summary="查询任务列表")
async def list_tasks(
    app_id: Optional[str] = None,
    review_status: Optional[int] = None,
    limit: int = 100
):
    """
    查询任务列表

    Args:
        app_id: 租户ID (可选)
        review_status: 评审状态 (可选)
        limit: 返回数量限制

    Returns:
        任务列表
    """
    try:
        from app.utils.db.mysql import MySQLUtil, ComplianceService

        # 初始化数据库连接
        mysql = MySQLUtil(
            host="172.16.0.116",
            port=3306,
            user="root",
            password="123456",
            database="tender_compliance",
            charset="utf8mb4",
            echo=False
        )

        service = ComplianceService(mysql)

        # 根据条件查询
        if app_id:
            tasks = service.get_tasks_by_app_id(app_id, limit=limit)
        elif review_status is not None:
            tasks = service.get_tasks_by_status(review_status, limit=limit)
        else:
            from app.utils.db.mysql.models import ComplianceFileTask
            tasks = mysql.get_all(ComplianceFileTask, limit=limit)

        mysql.close()

        # 转换为响应格式
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.id,
                "file_name": task.file_name,
                "project_name": task.project_name,
                "review_status": task.review_status,
                "review_result": task.review_result,
                "app_id": task.app_id,
                "created_at": task.create_time.isoformat() if task.create_time else None
            })

        return {
            "success": True,
            "total": len(task_list),
            "tasks": task_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")