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
python3 ./replace_json_field.py --path ./test.json --field foo --value '{"k": "v"}' --json-value
```

## 备份与恢复
- 脚本会在修改文件前为该文件创建备份，备份文件名为原文件名后追加 `.bak-<timestamp>`，例如 `test.json.bak-1612345678`。
- 恢复示例（PowerShell）：

```powershell
Copy-Item -Path .\test.json.bak-1612345678 -Destination .\test.json -Force
```

## 实现细节与注意事项
- 字段名匹配为精确键名（区分大小写）。脚本会在任意嵌套层级（对象、数组中的对象）查找并替换匹配项。
- 对于同名键，脚本会替换所有出现的位置。如果你只想替换顶层字段或按路径筛选，需要对脚本进行扩展。
- 使用 `--json-value` 时，`--value` 必须是合法 JSON 字面量。PowerShell 中通常外层使用单引号包裹整个 JSON 字符串以保留内部双引号。
- 当遇到无法解析为 JSON 的文件时，脚本会跳过该文件并打印警告信息，原始文件不会被覆盖。

## 常见问题（FAQ）
Q：如何只替换顶层字段？
A：当前实现递归替换；如需仅顶层替换，可在 `replace_in_obj` 中增加层级参数并仅在顶层字典中匹配。

Q：替换后的文件格式会保持可读吗？
A：脚本使用 `json.dump(..., ensure_ascii=False, indent=2)`，会以可读的缩进格式写回文件，并保留 UTF-8 编码。

Q：脚本是否支持按 JSONPath 或更复杂规则匹配？
A：当前不支持。可扩展为使用 `jsonpath-ng` 等库实现更细粒度匹配，但那会增加依赖。

## 排错建议
- 如果看到“无法解析为 JSON”的错误，请用 `python -c "import json,sys; json.load(open('file'))"` 或在线 JSON 校验工具确认该文件是合法 JSON。
- 在 PowerShell 里传递 JSON 字面量时，请使用单引号包裹外层字符串，内部用双引号；或者对双引号进行转义。

## 可选扩展（建议）
- 增加 `--dry-run` 模式，仅打印将被替换的键与位置，不写回文件。
- 支持按 JSONPath 精确定位要替换的条目。
- 支持并行处理大目录以及备份保留策略（保留最近 N 个备份）。

