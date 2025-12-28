"""
生成百度图像理解 API 的 curl 命令
"""
import base64
import json

# API 配置
api_key = "bce-v3/ALTAK-JkjnSArfweuMYH0Rr0RIN/45271747bda2067bcc0c855c7a6b6f61edd5b51f"
api_name = "qianfan-vl-8b"
url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chatv/{api_name}"

# 读取图片
image_path = "//wsl.localhost/Ubuntu-22.04/root/code/layoutlmft/data/output/images/城市大数据中心物业管理服务/城市大数据中心物业管理服务_0.jpg"

with open(image_path, 'rb') as f:
    image_data = f.read()
    b64_str = base64.b64encode(image_data).decode('utf-8')
    image_base64 = f"data:image/jpeg;base64,{b64_str}"

# 构建 messages
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "请描述这张图片的内容"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_base64
                }
            }
        ]
    }
]

# 构建完整 payload
payload = {
    "messages": messages,
    "temperature": 0.000001,
    "top_p": 1.0,
    "stream": False
}

# 保存 payload 到文件
with open("payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("=" * 80)
print("完整 curl 命令:")
print("=" * 80)
print()
print(f"curl -X POST \\")
print(f'  "{url}" \\')
print(f'  -H "Content-Type: application/json" \\')
print(f'  -H "Authorization: Bearer {api_key}" \\')
print(f'  -d @payload.json')
print()
print("=" * 80)
print("说明:")
print("=" * 80)
print(f"- API URL: {url}")
print(f"- API Key: {api_key[:20]}...{api_key[-10:]}")
print(f"- 图片路径: {image_path}")
print(f"- 图片 base64 长度: {len(image_base64)} 字符")
print(f"- Payload 已保存到: payload.json")
print()
print("你可以直接运行上面的 curl 命令测试")
