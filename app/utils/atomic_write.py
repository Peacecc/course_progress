"""原子写入工具 — 先写临时文件，成功后替换，防止写入中断导致数据损坏"""

import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(filepath: Path, data, indent: int = 4, ensure_ascii: bool = False):
    """
    原子写入 JSON 文件。

    流程：
    1. 在目标文件同目录创建临时文件
    2. 将 JSON 写入临时文件
    3. 调用 os.replace 原子替换（Windows 上也保证原子性）
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # 在同目录创建临时文件（确保在同一文件系统，os.replace 才能原子操作）
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(filepath.parent),
        prefix=f".{filepath.name}.",
        suffix=".tmp"
    )

    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        os.replace(tmp_path, str(filepath))
    except Exception:
        # 清理临时文件
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


def safe_read_json(filepath: Path, default=None):
    """
    安全读取 JSON 文件。

    - 文件不存在 → 返回 default
    - JSON 损坏 → 备份原文件为 .bak，返回 default
    - 正常 → 返回解析后的数据
    """
    if default is None:
        default = {}

    filepath = Path(filepath)

    if not filepath.exists():
        return default

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        # 备份损坏文件
        backup_path = filepath.with_suffix(filepath.suffix + '.bak')
        try:
            import shutil
            shutil.copy2(str(filepath), str(backup_path))
            print(f"[DataManager] 数据文件已损坏，已备份至: {backup_path}")
            print(f"[DataManager] 错误: {e}")
        except Exception as backup_err:
            print(f"[DataManager] 备份失败: {backup_err}")
        return default
