#!/bin/bash

# 测试节点移动 API

# 配置
TIMESTAMP="20251218_141436_checkpoint-3000_096b7b"
FILENAME="少年宫.json"
API_URL="http://localhost:3000/api/runs/${TIMESTAMP}/move-node"

# 测试数据
LINE_ID="L00006"       # 要移动的节点
NEW_PARENT_ID="L00001" # 新的父节点（section）

echo "========================================="
echo "测试节点移动 API"
echo "========================================="
echo "API URL: $API_URL"
echo "文件名: $FILENAME"
echo "节点ID: $LINE_ID"
echo "新父节点ID: $NEW_PARENT_ID"
echo "========================================="
echo ""

# 发送请求
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"fileName\": \"$FILENAME\",
    \"lineId\": \"$LINE_ID\",
    \"newParentId\": \"$NEW_PARENT_ID\"
  }" \
  | python -m json.tool

echo ""
echo "========================================="
echo "测试完成"
echo "========================================="
