# replace_json_field — JSON 字段批量替换工具

一个小型、跨平台的 Python 工具，用于在单个 JSON 文件或目录（递归）内查找指定字段名并将其值替换为用户提供的统一内容。

## 主要功能
- 支持对单个文件或目录递归处理（按扩展名过滤，默认 `.json`）。
- 支持将替换值按字符串处理或解析为 JSON 字面量（数字、布尔、数组、对象、null）。
- 为每个被修改的文件生成备份，备份文件名包含时间戳，便于恢复。

## 脚本位置
# replace_json_field — JSON 字段批量替换工具

一个小型、跨平台的 Python 工具，用于在单个 JSON 文件或目录（递归）内查找指定字段名并将其值替换为用户提供的统一内容。

## 主要功能
- 支持对单个文件或目录递归处理（按扩展名过滤，默认 `.json`）。
- 支持将替换值按字符串处理或解析为 JSON 字面量（数字、布尔、数组、对象、null）。
- 为每个被修改的文件生成备份，备份文件名包含时间戳，便于恢复。

## 脚本位置
主脚本：`replace_json_field.py`

## 参数说明
- `--path <path>` (必需)：要处理的文件或目录路径。如果是目录，会按 `--ext` 递归查找。
- `--field <name>` (必需)：要替换的字段名（精确键名匹配，区分大小写）。
- `--value <value>` (必需)：替换值，默认按字符串处理。
- `--json-value` (可选)：如果指定，脚本会将 `--value` 当作 JSON 字面量解析（例如 `123`、`true`、`[1,2]` 或 `{"a":1}`）。
- `--ext <ext>` (可选)：当 `--path` 指向目录时，按该扩展名过滤文件（默认 `.json`）。可以传 `json` 或 `.json`。

## 基本用法 示例
在 PowerShell 中将 `test.json` 中所有键 `name` 的值替换为字符串 `REPLACED`：

```powershell
python .\replace_json_field.py --path .\test.json --field name --value REPLACED
```

在 PowerShell 中，将 `data` 目录内所有 `.json` 文件里键 `meta` 的值替换为对象（注意引号转义，外层使用单引号）：

```powershell
python .\replace_json_field.py --path .\data --field meta --value '{"a":1, "b":[2,3]}' --json-value
```

在 bash（Linux/macOS）下传入 JSON 字面量示例：

```bash
python ./replace_json_field.py --path ./test.json --field foo --value '{"k": "v"}' --json-value
```

## Web UI（Django）
本仓库包含一个最小的 Django 前后端（应用名 `jsonmgr`），用于通过浏览器查看、下载和在页面上替换 JSON 文件字段。

重要说明：默认页面读取位置为仓库根的 `json_files/` 目录（即 `d:\桌面\json字段处理\json_files`），备份会写入 `json_files/backups/`。请确保该目录存在且可读写。

快速启动（PowerShell）

```powershell
# 建议先在虚拟环境中运行
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
# 在本机浏览器访问 http://localhost:8000/ 或 http://<本机IP>:8000/
```

页面功能简要：
- 首页 `/`：列出 `json_files/` 下所有 `.json` 文件并支持即时搜索。
- 文件页 `/file/?name=<file>`：展示（截断）文件内容、支持替换字段并保存，提供 `/raw/?name=<file>` 下载完整文件或在页面异步加载完整内容。

安全提示：生产环境不要使用 Django 开发服务器做对外服务；在内网或本地开发测试用途下可以使用上面的 runserver 命令。

## 备份与恢复
- 脚本和 Web UI 都会在写回前生成备份，文件在 `json_files/backups/`，文件名包含 `.bak-<timestamp>`。
- 恢复示例（PowerShell）：

```powershell
Copy-Item -Path .\json_files\backups\test.json.bak-1612345678 -Destination .\json_files\test.json -Force
```

## 实现细节与注意事项
- 字段名匹配为精确键名（区分大小写）。脚本会在任意嵌套层级（对象、数组中的对象）查找并替换匹配项。
- 对于同名键，脚本会替换所有出现的位置。如果你只想替换顶层字段或按路径筛选，需要对脚本进行扩展。
- 使用 `--json-value` 时，`--value` 必须是合法 JSON 字面量。PowerShell 中通常外层使用单引号包裹整个 JSON 字符串以保留内部双引号。
- 当遇到无法解析为 JSON 的文件时，脚本会跳过该文件并打印警告信息，原始文件不会被覆盖。

## 依赖与 requirements
- Python 版本：推荐 Python 3.8+（本次开发使用 3.11）
- 依赖见 `requirements.txt`（示例包含 Django）

## 排错建议
- 如果看到“无法解析为 JSON”的错误，请用 `python -c "import json,sys; json.load(open('file'))"` 或在线 JSON 校验工具确认该文件是合法 JSON。
- 在 PowerShell 里传递 JSON 字面量时，请使用单引号包裹外层字符串，内部用双引号；或者对双引号进行转义。

## 可选扩展（建议）
- 增加 `--dry-run` 模式，仅打印将被替换的键与位置，不写回文件。
- 支持按 JSONPath 精确定位要替换的条目。
- 支持并行处理大目录以及备份保留策略（保留最近 N 个备份）。

