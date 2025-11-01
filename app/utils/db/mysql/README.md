# MySQL 工具类使用文档

基于 SQLAlchemy 2.x 的 MySQL 数据库封装。

## 安装依赖

```bash
# 推荐: PyMySQL (纯 Python, 安装简单)
poetry add sqlalchemy pymysql

# 或者: mysqlclient (C扩展, 性能更好, 需要编译环境)
poetry add sqlalchemy mysqlclient
```

## 快速开始

### 1. 初始化连接

```python
from app.utils.db.mysql import MySQLUtil

mysql = MySQLUtil(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="pdf_db",
    charset="utf8mb4",
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    echo=False           # 是否打印 SQL (调试用)
)
```

### 2. 创建表

```python
# 创建所有表 (基于 models.py 中定义的模型)
mysql.create_tables(drop_existing=False)
```

### 3. 使用 Core SQL 风格

#### 查询

```python
# 原生 SQL 查询
rows = mysql.execute_raw_sql(
    "SELECT * FROM pdf_documents WHERE status = :status LIMIT :limit",
    {"status": "completed", "limit": 10}
)

for row in rows:
    print(row)  # 字典格式
```

#### 插入

```python
count = mysql.execute_insert(
    "INSERT INTO pdf_documents (doc_id, task_id, file_name, status) VALUES (:doc_id, :task_id, :file_name, :status)",
    {
        "doc_id": "test_20250101_120000",
        "task_id": "test",
        "file_name": "test.pdf",
        "status": "pending"
    }
)
print(f"插入了 {count} 条记录")
```

#### 更新

```python
count = mysql.execute_update(
    "UPDATE pdf_documents SET status = :status WHERE doc_id = :doc_id",
    {"status": "completed", "doc_id": "test_20250101_120000"}
)
print(f"更新了 {count} 条记录")
```

#### 删除

```python
count = mysql.execute_delete(
    "DELETE FROM pdf_documents WHERE status = :status",
    {"status": "failed"}
)
print(f"删除了 {count} 条记录")
```

### 4. 使用 ORM 风格 (推荐)

#### 定义模型 (在 models.py 中)

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
```

#### 插入

```python
from app.utils.db.mysql.models import PDFDocument

# 插入单条
doc = PDFDocument(
    doc_id="test_20250101_120000",
    task_id="test",
    file_name="test.pdf",
    status="pending"
)
saved_doc = mysql.insert_one(doc)
print(f"插入成功, ID: {saved_doc.id}")

# 批量插入
docs = [
    PDFDocument(doc_id=f"doc_{i}", task_id=f"task_{i}", file_name=f"file_{i}.pdf", status="pending")
    for i in range(100)
]
count = mysql.insert_many(docs)
print(f"插入了 {count} 条记录")
```

#### 查询

```python
# 根据主键查询
doc = mysql.get_by_id(PDFDocument, 1)
print(doc)

# 查询所有
all_docs = mysql.get_all(PDFDocument, limit=100)

# 条件查询
pending_docs = mysql.filter_by(PDFDocument, status="pending")
for doc in pending_docs:
    print(doc.doc_id, doc.status)
```

#### 更新

```python
from datetime import datetime

# 根据主键更新
success = mysql.update_by_id(
    PDFDocument,
    1,
    status="completed",
    processed_at=datetime.now()
)
print(f"更新成功: {success}")
```

#### 删除

```python
# 根据主键删除
success = mysql.delete_by_id(PDFDocument, 1)
print(f"删除成功: {success}")
```

#### 统计

```python
# 统计所有记录
total = mysql.count(PDFDocument)

# 条件统计
completed = mysql.count(PDFDocument, status="completed")
print(f"总文档数: {total}, 已完成: {completed}")
```

### 5. 使用 Session 手动控制事务 (高级用法)

```python
from app.utils.db.mysql.models import PDFDocument, ProcessingLog

with mysql.get_session() as session:
    # 查询
    doc = session.get(PDFDocument, 1)

    # 修改
    doc.status = "processing"

    # 添加关联记录
    log = ProcessingLog(
        doc_id=doc.doc_id,
        level="info",
        stage="extract",
        message="开始提取表格"
    )
    session.add(log)

    # 复杂查询
    from sqlalchemy import select
    stmt = select(PDFDocument).where(PDFDocument.status == "pending").limit(10)
    pending_docs = session.execute(stmt).scalars().all()

    # 自动提交 (退出 with 块时)
```

### 6. 使用 with 语句自动管理连接

```python
with MySQLUtil(host="localhost", user="root", password="pwd", database="db") as mysql:
    docs = mysql.filter_by(PDFDocument, status="pending")
    # 自动关闭连接
```

## 示例模型

项目已内置两个示例模型:

### PDFDocument (PDF 文档元数据表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键ID |
| doc_id | String(200) | 文档唯一标识 (带时间戳) |
| task_id | String(200) | 任务ID (不带时间戳) |
| file_name | String(500) | 文件名 |
| file_path | Text | 文件路径 |
| status | String(50) | 处理状态: pending/processing/completed/failed |
| total_pages | Integer | 总页数 |
| total_tables | Integer | 表格数量 |
| total_cells | Integer | 单元格数量 |
| milvus_collection | String(100) | Milvus 集合名称 |
| milvus_count | Integer | Milvus 中的记录数 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| processed_at | DateTime | 处理完成时间 |
| error_message | Text | 错误信息 |

### ProcessingLog (处理日志表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键ID |
| doc_id | String(200) | 文档ID |
| level | String(20) | 日志级别: debug/info/warning/error |
| stage | String(50) | 处理阶段: extract/convert/vectorize/save |
| message | Text | 日志消息 |
| details | Text | 详细信息 (JSON) |
| created_at | DateTime | 创建时间 |

## 连接池配置

```python
mysql = MySQLUtil(
    host="localhost",
    pool_size=10,        # 连接池常驻连接数
    max_overflow=20,     # 最大溢出连接数 (总连接数 = pool_size + max_overflow)
    pool_timeout=30,     # 获取连接超时时间 (秒)
    pool_pre_ping=True   # 连接健康检查 (自动重连)
)
```

## 性能优化

### 1. 批量插入

```python
# 批量插入 (比循环 insert_one 快 10-100 倍)
docs = [PDFDocument(...) for _ in range(1000)]
mysql.insert_many(docs)
```

### 2. 批量更新

```python
with mysql.get_session() as session:
    docs = session.execute(select(PDFDocument).where(PDFDocument.status == "pending")).scalars().all()
    for doc in docs:
        doc.status = "processing"
    # 批量提交
```

### 3. 使用索引

```python
# 在常用查询字段上创建索引 (已在模型中定义)
doc_id: Mapped[str] = mapped_column(String(200), index=True)
status: Mapped[str] = mapped_column(String(50), index=True)
```

## 注意事项

1. **字符集**: 推荐使用 `utf8mb4` (支持 emoji 等 4 字节字符)
2. **时区**: SQLAlchemy 默认使用数据库服务器时区
3. **连接池**: 生产环境建议配置合适的 `pool_size` 和 `max_overflow`
4. **事务**: 使用 `with mysql.get_session()` 自动管理事务
5. **驱动选择**:
   - PyMySQL: 纯 Python, 安装简单, 跨平台兼容好
   - mysqlclient: C扩展, 性能更好, 需要编译环境

## 切换到 mysqlclient 驱动

如果需要更好的性能, 可以切换到 mysqlclient:

```python
# 1. 安装 mysqlclient
poetry add mysqlclient

# 2. 修改 mysql_util.py 中的连接 URL
connection_url = f"mysql+mysqldb://{user}:{password}@{host}:{port}/{database}?charset={charset}"
```

## 常见问题

### Q: 如何打印 SQL 语句?
A: 初始化时设置 `echo=True`

### Q: 如何处理大量数据?
A: 使用批量操作 (`insert_many`) 和生成器

### Q: 如何使用事务?
A: 使用 `with mysql.get_session()` 自动管理事务

### Q: 如何自定义模型?
A: 在 `models.py` 中定义新的类, 继承自 `Base`