#!/usr/bin/env python3
"""
replace_json_field.py
将 JSON 文件或目录中指定字段名的所有值替换为统一内容。
用法示例：
  python replace_json_field.py --path data.json --field name --value REPLACED
支持将单个文件或目录（递归）处理。会为每个被修改的文件生成一个备份（.bak）。
"""

import argparse
import json
from pathlib import Path
from typing import Any
import shutil
import time
import os


def parse_args():
    p = argparse.ArgumentParser(description="Replace JSON field values by field name")
    p.add_argument("--path", required=True, help="File or directory path to process")
    p.add_argument("--field", required=True, help="Field name to replace (exact key match)")
    p.add_argument("--value", required=True, help="Replacement value (string). Use --json-value to supply JSON literal")
    p.add_argument("--json-value", action="store_true", help="Interpret --value as JSON literal (numbers, objects, arrays, true/false/null)")
    p.add_argument("--ext", default=".json", help="File extension to process when path is a directory (default .json)")
    return p.parse_args()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj: Any, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def replace_in_obj(obj: Any, field: str, new_value: Any):
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if k == field:
                obj[k] = new_value
            else:
                replace_in_obj(obj[k], field, new_value)
    elif isinstance(obj, list):
        for item in obj:
            replace_in_obj(item, field, new_value)
    # primitives: nothing to do


def process_file(path: Path, field: str, new_value: Any):
    try:
        data = load_json(path)
    except Exception as e:
        print(f"跳过 {path}（无法解析为 JSON）：{e}")
        return False
    # backup -> place backups under workspace/json_files/backups/ if possible
    ts = int(time.time())
    # try to find workspace root (assume two levels up from script) or use file parent
    try:
        workspace_root = Path(__file__).resolve().parent
    except Exception:
        workspace_root = path.parent
    backups_dir = workspace_root / "json_files" / "backups"
    os.makedirs(backups_dir, exist_ok=True)
    bak = backups_dir / f"{path.name}.bak-{ts}"
    shutil.copy2(path, bak)
    replace_in_obj(data, field, new_value)
    dump_json(data, path)
    print(f"已处理并备份 {path} -> {bak}")
    return True


def main():
    args = parse_args()
    p = Path(args.path)
    # If user passed the repository root ('.' or script parent), prefer json_files/
    if p.exists() and p.is_dir():
        # Heuristic: if the directory contains replace_json_field.py, treat it as workspace root
        if (p / Path(__file__).name).exists():
            jf = p / "json_files"
            if jf.exists():
                p = jf
    # parse replacement value
    if args.json_value:
        try:
            new_value = json.loads(args.value)
        except Exception as e:
            print(f"解析 --value 为 JSON 时出错：{e}")
            return
    else:
        new_value = args.value

    if p.is_file():
        process_file(p, args.field, new_value)
    elif p.is_dir():
        ext = args.ext.startswith(".") and args.ext or "." + args.ext
        for f in p.rglob(f"*{ext}"):
            process_file(f, args.field, new_value)
    else:
        print("路径不存在：", p)


if __name__ == '__main__':
    main()
