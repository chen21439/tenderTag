# PDF 接口迁移计划

从 `tender-tagger` 迁移到 `tender_ontology` 项目

---

## 📋 项目分析

### **源项目** (tender-tagger)
- **位置**: `E:\programFile\AIProgram\tender-tagger`
- **主要功能**: PDF 上传、解析、表格提取、向量化存储
- **核心接口**: `/api/pdf/upload_pdf`
- **技术栈**: FastAPI + PDFPlumber + PyMuPDF + Milvus + MySQL

### **目标项目** (tender_ontology)
- **位置**: `E:\programFile\AIProgram\tender_ontology`
- **当前功能**: 本体管理（知识图谱）
- **技术栈**: FastAPI + Docling (文档处理)
- **项目结构**: 标准 Poetry 项目，使用 `src/tender_ontology` 布局

### **迁移范围说明**
- ✅ **需要迁移**: PDF 上传接口、文件存储、数据库记录管理
- ❌ **不需要迁移**: 表格提取功能、向量化存储功能（后续由 Docling 完成）
- 📁 **文件存储位置**: `static/` 目录（而非源项目的 `file/` 目录）

---

## 🎯 迁移计划

### **阶段一：依赖和工具类迁移**

#### 1.1 添加必要的依赖到目标项目
需要在 `tender_ontology/pyproject.toml` 添加：

```toml
dependencies = [
    # ... 现有依赖 ...
    "sqlalchemy (>=2.0.44,<3.0.0)",
    "pymysql (>=1.1.2,<2.0.0)",
]
```

**说明**：
- ❌ **不需要添加** `pdfplumber`, `pymupdf`, `pymilvus`, `flagembedding`, `qdrant-client`
- ✅ **只需添加** 数据库相关依赖（MySQL）
- 📌 PDF 处理将由 Docling 完成，无需额外的 PDF 处理库

#### 1.2 迁移核心工具类
需要迁移的模块：

**数据库工具** (仅需迁移数据库相关):
- `app/utils/db/mysql/` → `src/tender_ontology/utils/db/mysql/`
  - `mysql_util.py` (MySQL 连接工具)
  - `compliance_service.py` (业务服务)
  - `models.py` (数据模型)

**❌ 不需要迁移**:
- ~~PDF 处理工具~~ (由 Docling 替代)
- ~~向量库工具~~ (后续由 Docling 处理)

---

### **阶段二：API 路由迁移**

#### 2.1 创建 PDF 处理路由
创建文件：`src/tender_ontology/routers/pdf_process.py`

**需要迁移的接口**:

| 方法 | 路径 | 功能 | 优先级 |
|------|------|------|--------|
| POST | `/api/pdf/upload_pdf` | PDF 上传和处理 | ⭐⭐⭐ |
| GET | `/api/pdf/task/{task_id}` | 查询任务状态 | ⭐⭐⭐ |
| PUT | `/api/pdf/task/{task_id}/status` | 更新任务状态 | ⭐⭐ |
| GET | `/api/pdf/tasks` | 查询任务列表 | ⭐⭐ |
| POST | `/api/pdf/page` | 分页查询任务 | ⭐⭐⭐ |
| GET | `/api/pdf/task/{task_id}/pdf` | 下载 PDF | ⭐⭐ |

#### 2.2 修改响应模型以符合目标项目规范

**源项目响应格式** (pdf_process.py):
```python
class PDFProcessResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    doc_id: str
    data: Optional[Dict[str, Any]] = None
```

**目标项目统一响应格式** (基于 CLAUDE.md 规范):
```python
{
    "success": bool,
    "errCode": str | null,
    "errMsg": str | null,
    "data": dict | null
}
```

**需要调整**:
- ✅ 字段命名改为驼峰式（camelCase）：`task_id` → `taskId`
- ✅ 时间格式统一为 `"YYYY-MM-DD HH:MM:SS"`
- ✅ 分页字段统一为字符串类型：`total: int` → `total: str`
- ✅ 添加 `errCode` 和 `errMsg` 字段
- ✅ 将业务数据统一放入 `data` 对象

**调整示例**:
```python
# 原响应
{
    "success": true,
    "message": "PDF 处理成功",
    "task_id": "25110214431528850637",
    "doc_id": "25110214431528850637",
    "data": {...}
}

# 新响应
{
    "success": true,
    "errCode": null,
    "errMsg": null,
    "data": {
        "taskId": "25110214431528850637",
        "docId": "25110214431528850637",
        "message": "PDF 处理成功",
        ...
    }
}
```

---

### **阶段三：配置和集成**

#### 3.1 更新 main.py
在 `src/tender_ontology/main.py` 中注册新路由：

```python
from tender_ontology.routers import health, ontology, pdf_process

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(ontology.router, tags=["ontology"])
app.include_router(pdf_process.router, prefix="/api/pdf", tags=["PDF处理"])
```

#### 3.2 更新路由导出
在 `src/tender_ontology/routers/__init__.py` 添加：

```python
from . import health, ontology, pdf_process

__all__ = ["health", "ontology", "pdf_process"]
```

#### 3.3 创建配置文件
在 `src/tender_ontology/config/settings.py` 添加数据库配置：

```python
import os
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # MySQL 配置
    MYSQL_HOST: str = "172.16.0.116"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "tender_compliance"
    MYSQL_CHARSET: str = "utf8mb4"

    # 文件存储配置（使用 static 目录）
    FILE_STORAGE_BASE: str = "static"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

**说明**：
- ✅ 文件存储改为 `static/` 目录
- ❌ 移除 Milvus 配置（不需要向量化）

#### 3.4 创建数据模型
在 `src/tender_ontology/models/` 添加：

**pdf_task.py** - PDF 任务相关模型:
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class PDFProcessResponse(BaseModel):
    """PDF 处理统一响应"""
    success: bool
    errCode: Optional[str] = None
    errMsg: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    success: bool
    errCode: Optional[str] = None
    errMsg: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class PageRequest(BaseModel):
    """分页请求"""
    pageNum: int = 1
    pageSize: int = 10

class PageDataResponse(BaseModel):
    """分页数据响应"""
    total: str
    pageSize: str
    pageTotal: str
    pageNum: str
    dataList: list

class PageResponse(BaseModel):
    """分页响应"""
    success: bool
    errCode: Optional[str] = None
    errMsg: Optional[str] = None
    data: PageDataResponse
```

**compliance.py** - 合规审查模型（如果需要数据库）

---

### **阶段四：目录结构调整**

#### 4.1 文件存储目录说明

使用现有的 `static/` 目录存储 PDF 文件：

```
tender_ontology/
└── static/         # 静态文件目录（已存在）
    └── uploads/    # PDF 上传目录（新建子目录）
        └── {task_id}.pdf  # 直接以任务ID命名PDF文件
```

**说明**：
- ✅ 使用 `static/uploads/` 目录存储上传的 PDF
- ✅ PDF 文件直接以 `{task_id}.pdf` 命名，无需创建子目录
- ❌ 不需要生成 `table.json` 和 `cells.json`（由 Docling 处理）

#### 4.2 迁移后的完整目录结构
```
tender_ontology/
├── src/
│   └── tender_ontology/
│       ├── __init__.py
│       ├── main.py
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   ├── ontology.py
│       │   └── pdf_process.py        # 新增 ⭐
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── db/                    # 新增 ⭐
│       │   │   ├── __init__.py
│       │   │   └── mysql/
│       │   │       ├── __init__.py
│       │   │       ├── mysql_util.py
│       │   │       ├── compliance_service.py
│       │   │       └── models.py
│       │   ├── document_struct/       # 已存在
│       │   └── request/               # 已存在
│       ├── models/
│       │   ├── __init__.py
│       │   ├── ontology.py
│       │   ├── pdf_task.py            # 新增 ⭐
│       │   └── compliance.py          # 新增 ⭐（如需要）
│       ├── services/
│       │   └── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py            # 更新配置 ⭐
│       ├── prompts/
│       └── scripts/
├── tests/
├── static/
│   └── uploads/                       # 新增 ⭐ (PDF上传目录)
├── pyproject.toml                      # 更新依赖 ⭐
├── .env.example                        # 更新配置 ⭐
└── README.md                           # 更新文档 ⭐
```

**说明**：
- ❌ **不需要** `utils/pdf/` 目录（PDF处理由Docling完成）
- ❌ **不需要** `utils/db/milvus/` 目录（不需要向量化）
- ❌ **不需要** `file/` 目录（使用 `static/uploads/`）

---

### **阶段五：测试和验证**

#### 5.1 功能测试清单
- [ ] PDF 上传功能
  - [ ] 验证文件类型检查（只允许 PDF）
  - [ ] 验证文件保存到 `static/uploads/{task_id}.pdf`
  - 
  - [ ] 验证任务 ID 生成
- [ ] 数据库存储功能
  - [ ] 验证任务记录创建
  - [ ] 验证状态更新
  - [ ] 验证查询功能
- [ ] 任务状态查询
  - [ ] 验证单个任务查询
  - [ ] 验证任务列表查询
- [ ] 分页查询
  - [ ] 验证分页逻辑
  - [ ] 验证响应格式（驼峰命名）
- [ ] PDF 下载
  - [ ] 验证文件下载
  - [ ] 验证文件名正确性

**❌ 不需要测试**：
- ~~表格提取功能~~ (由 Docling 处理)
- ~~向量化功能~~ (由 Docling 处理)

#### 5.2 接口测试
使用 Swagger UI 测试：`http://localhost:8000/docs`

**测试用例**:

1. **上传 PDF**:
```bash
curl -X POST "http://localhost:8000/api/pdf/upload_pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf" \
  -F "project_name=测试项目" \
  -F "save_to_db=true" \
  -F "save_to_milvus=true"
```

2. **查询任务状态**:
```bash
curl -X GET "http://localhost:8000/api/pdf/task/{task_id}"
```

3. **分页查询**:
```bash
curl -X POST "http://localhost:8000/api/pdf/page" \
  -H "Content-Type: application/json" \
  -d '{"pageNum": 1, "pageSize": 10}'
```

#### 5.3 数据一致性测试
验证：
- [ ] 数据库记录的字段完整性
- [ ] JSON 文件格式正确性
- [ ] 向量库数据一致性
- [ ] 文件路径正确性

---

## 📝 关键注意事项

### 1. **路径和导入调整**
所有导入需要从 `app.` 改为 `tender_ontology.`：

```python
# ❌ 原导入（源项目）
from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor
from app.utils.db.mysql import MySQLUtil, ComplianceService

# ✅ 新导入（目标项目）
from tender_ontology.utils.pdf.pdf_content_extractor import PDFContentExtractor
from tender_ontology.utils.db.mysql import MySQLUtil, ComplianceService
```

### 2. **数据库连接配置**
- ✅ 使用 `pydantic-settings` 管理配置
- ✅ 使用 `.env` 文件存储敏感信息
- ❌ 避免硬编码数据库密码

**示例配置** (.env):
```env
MYSQL_HOST=172.16.0.116
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=tender_compliance
```

### 3. **文件存储路径**
- ✅ 统一使用项目根目录的 `file/` 目录
- ✅ 确保路径兼容性（使用 `Path` 对象）
- ✅ 使用相对路径，避免硬编码

**示例**:
```python
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
FILE_STORAGE = PROJECT_ROOT / "file"

# 创建任务目录
task_dir = FILE_STORAGE / task_id
task_dir.mkdir(parents=True, exist_ok=True)
```

### 4. **响应格式统一**
严格遵循 `CLAUDE.md` 中的接口规范：

**统一响应结构**:
```python
{
    "success": bool,      # 必填
    "errCode": str | null, # 必填，成功时为 null
    "errMsg": str | null,  # 必填，成功时为 null
    "data": dict | null    # 必填，失败时可为 null
}
```

**命名规范**:
- ✅ 驼峰命名：`taskId`, `createTime`, `projectName`
- ❌ 下划线命名：~~`task_id`~~, ~~`create_time`~~

**时间格式**:
- ✅ `"2025-11-01 20:55:01"`
- ❌ ~~`"2025-11-01T20:55:01"`~~

**分页字段类型**:
```python
{
    "total": "100",      # 字符串
    "pageSize": "10",    # 字符串
    "pageTotal": "10",   # 字符串
    "pageNum": "1"       # 字符串
}
```

### 5. **依赖版本兼容性**

**Python 版本**:
- 源项目: `>=3.11,<3.12`
- 目标项目: `>=3.11.2,<3.12`
- ✅ 兼容

**关键依赖对比**:

| 依赖 | tender-tagger | tender_ontology | 兼容性 |
|------|--------------|----------------|--------|
| fastapi | >=0.119.1 | >=0.121.3 | ⚠️ 需要更新 |
| pydantic | >=2.12.3 | ==2.12.4 | ✅ 兼容 |
| uvicorn | >=0.38.0 | >=0.38.0 | ✅ 兼容 |
| sqlalchemy | >=2.0.44 | - | ➕ 需要添加 |
| pdfplumber | >=0.11.7 | - | ➕ 需要添加 |
| pymupdf | >=1.26.5 | - | ➕ 需要添加 |

### 6. **错误处理**
统一错误响应格式：

```python
# 成功响应
{
    "success": true,
    "errCode": null,
    "errMsg": null,
    "data": {...}
}

# 失败响应
{
    "success": false,
    "errCode": "PDF_001",
    "errMsg": "只支持 PDF 文件",
    "data": null
}
```

**错误码定义建议**:
- `PDF_001`: 文件类型错误
- `PDF_002`: 文件处理失败
- `PDF_003`: 数据库保存失败
- `PDF_004`: 向量化失败
- `TASK_001`: 任务不存在
- `TASK_002`: 任务状态更新失败

---

## 🚀 迁移步骤执行顺序

### **步骤 1: 准备阶段**
```bash
# 1.1 备份目标项目
cd E:\programFile\AIProgram
cp -r tender_ontology tender_ontology_backup_$(date +%Y%m%d)

# 1.2 创建新分支
cd tender_ontology
git checkout -b feature/pdf-upload-migration
```

### **步骤 2: 依赖安装**
```bash
# 2.1 更新 pyproject.toml（手动添加依赖）
# 参考 "阶段一：1.1 添加必要的依赖"

# 2.2 安装依赖
poetry install

# 2.3 验证安装
poetry show | grep -E "pdfplumber|pymupdf|pymilvus|sqlalchemy"
```

### **步骤 3: 工具类迁移**
```bash
# 3.1 创建目标目录（只需MySQL）
mkdir -p src/tender_ontology/utils/db/mysql

# 3.2 复制 MySQL 工具类文件
cp -r ../tender-tagger/app/utils/db/mysql/* src/tender_ontology/utils/db/mysql/

# 3.3 调整导入路径
find src/tender_ontology/utils/db/mysql -name "*.py" -exec sed -i 's/from app\./from tender_ontology./g' {} \;
find src/tender_ontology/utils/db/mysql -name "*.py" -exec sed -i 's/import app\./import tender_ontology./g' {} \;
```

**说明**：
- ❌ **不需要复制** PDF 处理工具 (`unTaggedPDF/`)
- ❌ **不需要复制** Milvus 工具
- ✅ **只需复制** MySQL 数据库工具

### **步骤 4: 模型迁移**
```bash
# 4.1 创建模型文件
touch src/tender_ontology/models/pdf_task.py
touch src/tender_ontology/models/compliance.py

# 4.2 编写模型代码
# 参考 "阶段三：3.4 创建数据模型"
```

### **步骤 5: 路由迁移**
```bash
# 5.1 创建路由文件
cp ../tender-tagger/app/routers/pdf_process.py src/tender_ontology/routers/

# 5.2 调整导入路径
sed -i 's/from app\./from tender_ontology./g' src/tender_ontology/routers/pdf_process.py

# 5.3 调整响应格式
# 手动修改响应模型，参考 "阶段二：2.2"
```

### **步骤 6: 配置更新**
```bash
# 6.1 更新配置文件
# 编辑 src/tender_ontology/config/settings.py
# 参考 "阶段三：3.3"

# 6.2 更新环境变量示例
# 编辑 .env.example
```

### **步骤 7: 主应用更新**
```bash
# 7.1 更新 main.py
# 添加路由注册，参考 "阶段三：3.1"

# 7.2 更新路由导出
# 编辑 routers/__init__.py，参考 "阶段三：3.2"
```

### **步骤 8: 测试验证**
```bash
# 8.1 启动服务
poetry run dev

# 8.2 访问 Swagger UI
# http://localhost:8000/docs

# 8.3 测试接口
# 参考 "阶段五：5.2 接口测试"
```

### **步骤 9: 文档更新**
```bash
# 9.1 更新 README.md
# 添加 PDF 接口说明

# 9.2 创建 API 文档
# 如果需要，创建详细的 API 文档
```

### **步骤 10: 提交代码**
```bash
# 10.1 检查修改
git status
git diff

# 10.2 提交代码
git add .
git commit -m "feat: 迁移 PDF 上传和处理接口

- 添加 PDF 处理相关依赖
- 迁移 PDF 工具类和数据库工具
- 添加 6 个 PDF 处理接口
- 统一响应格式符合项目规范
- 添加配置管理
"

# 10.3 推送到远程
git push origin feature/pdf-upload-migration
```

---

## ❓ 需要确认的问题

### 1. **数据库表结构是否需要同步？**
- ❓ 目标项目是否已有 `tender_compliance` 数据库？
- ❓ 是否需要迁移表结构（CREATE TABLE 语句）？
- ❓ 是否需要迁移历史数据？

**建议**:
- 如果目标项目需要独立数据库，创建新的数据库实例
- 如果共享数据库，确保表结构一致

### 2. **向量库选择**
- ❓ 使用 Milvus 还是 Qdrant？
- ❓ 向量库连接信息是否一致？
- ❓ 是否需要创建新的集合（Collection）？

**当前情况**:
- 源项目使用 Milvus
- 目标项目已有 Qdrant 依赖

**建议**:
- 保持使用 Milvus（迁移更简单）
- 或者重构向量化逻辑以支持 Qdrant

### 3. **文件存储策略**
- ❓ 是否使用相同的文件存储位置？
- ❓ 是否需要迁移已有的 PDF 文件？
- ❓ 文件存储是否需要云存储支持（如 OSS）？

**建议**:
- 在目标项目根目录创建独立的 `file/` 目录
- 不迁移历史文件，只处理新上传的文件

### 4. **环境配置**
- ❓ 两个项目是否共享配置？
- ❓ 是否需要独立的 `.env` 文件？
- ❓ 生产环境配置如何管理？

**建议**:
- 使用独立的 `.env` 文件
- 创建 `.env.example` 模板
- 使用 `pydantic-settings` 管理配置

### 5. **API 版本控制**
- ❓ 是否需要 API 版本控制（如 `/api/v1/pdf`）？
- ❓ 是否需要向后兼容旧接口？

**建议**:
- 暂不添加版本控制，使用 `/api/pdf`
- 未来如需版本控制，可统一添加

### 6. **日志和监控**
- ❓ 是否需要添加日志记录？
- ❓ 是否需要性能监控？
- ❓ 是否需要错误追踪（如 Sentry）？

**建议**:
- 添加结构化日志（使用 `logging` 或 `loguru`）
- 添加关键操作的日志记录

---

## 📚 参考文档

### 源项目文档
- `app/routers/pdf_process.py` - PDF 处理接口
- `app/routers/CLAUDE.md` - 接口开发规范
- `app/utils/unTaggedPDF/pdf_content_extractor.py` - PDF 提取器
- `app/utils/db/mysql/README.md` - 数据库工具文档

### 目标项目文档
- `README.md` - 项目说明
- `pyproject.toml` - 依赖配置
- `src/tender_ontology/main.py` - 应用入口

### 外部文档
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [Poetry 官方文档](https://python-poetry.org/docs/)

---

## 🎯 迁移完成标准

### 功能完整性
- [x] 所有 6 个接口迁移完成
- [x] PDF 处理功能正常工作
- [x] 数据库操作正常
- [x] 向量化功能正常（如果启用）

### 代码质量
- [x] 所有导入路径正确
- [x] 响应格式符合规范
- [x] 错误处理完善
- [x] 代码格式化（black）
- [x] 代码检查通过（ruff）

### 测试覆盖
- [x] 所有接口测试通过
- [x] 功能测试通过
- [x] 集成测试通过

### 文档完善
- [x] API 文档更新
- [x] README 更新
- [x] 配置说明完善

---

## 📞 联系方式

如有问题，请联系：
- 项目负责人：[填写联系方式]
- 技术支持：[填写联系方式]

---

**迁移计划创建时间**: 2025-11-24
**预计完成时间**: [根据实际情况填写]
**当前状态**: 📝 计划阶段