# 接口开发规范

## 统一返回格式

所有接口都必须使用以下统一的返回格式作为最外层结构：

```json
{
    "success": true,
    "errCode": null,
    "errMsg": null,
    "data": {
        // 实际业务数据
    }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 请求是否成功 (true/false) |
| errCode | string \| null | 是 | 错误码，成功时为 null |
| errMsg | string \| null | 是 | 错误信息，成功时为 null |
| data | object \| null | 是 | 业务数据，失败时可为 null |

### 成功响应示例

```json
{
    "success": true,
    "errCode": null,
    "errMsg": null,
    "data": {
        "userId": "12345",
        "userName": "张三"
    }
}
```

### 失败响应示例

```json
{
    "success": false,
    "errCode": "AUTH_001",
    "errMsg": "用户未登录",
    "data": null
}
```

## 命名规范

### 字段命名

- **使用驼峰命名法**: `userId`, `createTime`, `projectName`
- **禁止使用下划线**: ~~`user_id`~~, ~~`create_time`~~

### 时间格式

- 统一使用字符串格式: `"YYYY-MM-DD HH:MM:SS"`
- 示例: `"2025-11-01 20:55:01"`

## 分页接口规范

### 请求参数

```json
{
    "pageNum": 1,
    "pageSize": 10
}
```

### 响应格式

```json
{
    "success": true,
    "errCode": null,
    "errMsg": null,
    "data": {
        "total": "100",
        "pageSize": "10",
        "pageTotal": "10",
        "pageNum": "1",
        "dataList": [
            // 数据列表
        ]
    }
}
```

### 分页数据字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total | string | 总记录数 |
| pageSize | string | 每页大小 |
| pageTotal | string | 总页数 |
| pageNum | string | 当前页码 |
| dataList | array | 数据列表 |

## 示例接口

### `/api/pdf/page` - 分页查询任务列表

**请求:**
```json
POST /api/pdf/page
{
    "pageNum": 1,
    "pageSize": 5
}
```

**响应:**
```json
{
    "success": true,
    "errCode": null,
    "errMsg": null,
    "data": {
        "total": "2",
        "pageSize": "5",
        "pageTotal": "1",
        "pageNum": "1",
        "dataList": [
            {
                "taskId": "1984605092971569153",
                "fileId": "1984605089775599618",
                "fileName": "鄂尔多斯市政府网站群集约化平台升级改造项目.pdf",
                "projectName": null,
                "projectCode": null,
                "reviewStatus": 2,
                "reviewResult": 1,
                "createTime": "2025-11-01 20:55:01",
                "createUserName": "陈晓敏（内蒙）",
                "reviewProgress": 100
            }
        ]
    }
}
```

## 注意事项

1. ✅ 所有接口都必须遵循统一返回格式
2. ✅ 字段名必须使用驼峰命名
3. ✅ 时间统一使用 "YYYY-MM-DD HH:MM:SS" 格式
4. ✅ 分页信息字段统一使用字符串类型
5. ✅ 错误时 `success` 为 `false`，并填写 `errCode` 和 `errMsg`
6. ✅ 成功时 `errCode` 和 `errMsg` 为 `null`