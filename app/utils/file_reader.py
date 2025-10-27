"""
简单的文件读取工具
"""
from pathlib import Path
from typing import Dict, Optional
import re


# 默认文件目录（项目外部路径）
DEFAULT_FILE_DIR = "E:/programFile/AIProgram/docxServer/pdf/task/1978018096320905217"


class FileReader:
    """文件读取器"""

    def __init__(self, directory: str):
        """初始化文件读取器"""
        self.directory = Path(directory)
        if not self.directory.exists():
            raise ValueError(f"目录不存在: {directory}")

    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """读取单个文件"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # UTF-8失败则尝试GBK
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()

    def read_all_files(self) -> Dict[str, str]:
        """读取目录中所有文件，返回字典(文件名: 内容)"""
        results = {}

        for file_path in self.directory.iterdir():
            if file_path.is_file():
                try:
                    content = self.read_file(str(file_path))
                    results[file_path.name] = content
                    print(f"已读取: {file_path.name}")
                except Exception as e:
                    print(f"读取失败 {file_path.name}: {e}")

        return results

    def get_latest_analysis_json(self, task_id: str = "1978018096320905217") -> Optional[Path]:
        """
        获取目录中时间戳最大的分析JSON文件

        文件名格式: {task_id}_analysis_{timestamp}.json
        例如: 1978018096320905217_analysis_20251023_190940.json

        Args:
            task_id: 任务ID，默认为 "1978018096320905217"

        Returns:
            时间戳最大的JSON文件路径，如果没有找到则返回None
        """
        pattern = re.compile(rf'^{re.escape(task_id)}_analysis_(\d{{8}}_\d{{6}})\.json$')

        max_timestamp = None
        max_file = None

        for file_path in self.directory.glob(f"{task_id}_analysis_*.json"):
            if file_path.is_file():
                match = pattern.match(file_path.name)
                if match:
                    timestamp = match.group(1)
                    if max_timestamp is None or timestamp > max_timestamp:
                        max_timestamp = timestamp
                        max_file = file_path

        return max_file


def main():
    """命令行入口"""
    import sys
    import io

    # 设置控制台输出编码为UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 使用默认目录或命令行参数
    if len(sys.argv) < 2:
        directory = DEFAULT_FILE_DIR
        print(f"使用默认目录: {directory}")
    else:
        directory = sys.argv[1]

    try:
        reader = FileReader(directory)

        # 获取时间戳最大的分析JSON文件
        latest_json = reader.get_latest_analysis_json()
        if latest_json:
            content = reader.read_file(str(latest_json))
            print(f"{'='*60}")
            print(f"文件: {latest_json.name}")
            print(f"{'='*60}")
            print(content)
            print()
        else:
            print(f"未找到匹配的分析JSON文件于目录: {directory}")

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
