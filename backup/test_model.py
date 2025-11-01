"""
简单测试 Ollama 模型对话功能
"""
import requests


def test_ollama_chat():
    """测试 Ollama 对话"""

    # Ollama API 配置
    base_url = "http://localhost:11434"
    chat_api_url = f"{base_url}/api/chat"
    model_name = "qwen3:4b"

    # 简单的测试问题
    test_question = "你好，请用一句话介绍一下你自己。"

    print(f"测试模型: {model_name}")
    print(f"问题: {test_question}")
    print("=" * 60)

    # 构建请求
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": test_question}
        ],
        "stream": False
    }

    try:
        # 发送请求
        print("正在请求模型...")
        response = requests.post(chat_api_url, json=payload, timeout=60)
        response.raise_for_status()

        # 解析响应
        result = response.json()
        answer = result.get("message", {}).get("content", "")

        print("\n模型回答:")
        print("-" * 60)
        print(answer)
        print("-" * 60)

        # 显示一些统计信息
        if "eval_count" in result:
            print(f"\n生成 tokens: {result.get('eval_count', 0)}")
        if "total_duration" in result:
            duration = result.get('total_duration', 0) / 1e9  # 纳秒转秒
            print(f"总耗时: {duration:.2f} 秒")

        return True

    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到 Ollama ({base_url})")
        print("请确保 Ollama 正在运行")
        return False

    except requests.exceptions.Timeout:
        print("错误: 请求超时")
        return False

    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == '__main__':
    test_ollama_chat()
