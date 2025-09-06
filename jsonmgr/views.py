import json
import time
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse

BASE = Path(__file__).resolve().parent.parent
JSON_DIR = BASE / 'json_files'
BACKUP_DIR = JSON_DIR / 'backups'


def replace_in_obj(obj, field, new_value):
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if k == field:
                obj[k] = new_value
            else:
                replace_in_obj(obj[k], field, new_value)
    elif isinstance(obj, list):
        for item in obj:
            replace_in_obj(item, field, new_value)


def index(request):
    files = []
    if JSON_DIR.exists():
        for p in JSON_DIR.iterdir():
            if p.is_file() and p.suffix == '.json':
                files.append(p.name)
    return render(request, 'jsonmgr/index.html', {'files': files})


@csrf_exempt
def view_file(request):
    name = request.GET.get('name')
    if not name:
        return HttpResponseNotFound('missing name')
    # sanitize
    fn = Path(name).name
    p = JSON_DIR / fn
    if not p.exists():
        return HttpResponseNotFound('file not found')

    message = ''
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')
        json_value = request.POST.get('json_value') == 'on'
        if field is not None:
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
            except Exception as e:
                message = f'无法解析 JSON: {e}'
            else:
                if json_value:
                    try:
                        new_value = json.loads(value)
                    except Exception as e:
                        message = f'解析替换值为 JSON 失败: {e}'
                        new_value = value
                else:
                    new_value = value
                # backup
                BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                ts = int(time.time())
                bak = BACKUP_DIR / f"{fn}.bak-{ts}"
                p.replace(bak)  # move as a backup
                # reload original from backup then modify
                data = json.loads(bak.read_text(encoding='utf-8'))
                replace_in_obj(data, field, new_value)
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
                message = f'已替换字段并备份到 {bak.name}'
    # load current content but avoid embedding very large files in the HTML
    content = ''
    truncated = False
    try:
        raw = p.read_text(encoding='utf-8')
        max_len = 200 * 1024  # 200KB
        if len(raw.encode('utf-8')) > max_len:
            # show only the first chunk to avoid proxy/buffer issues
            content = raw[:max_len]
            truncated = True
        else:
            content = raw
    except Exception:
        content = ''
    return render(request, 'jsonmgr/view.html', {'name': fn, 'content': content, 'message': message, 'truncated': truncated})


def raw_file(request):
    name = request.GET.get('name')
    if not name:
        return HttpResponseNotFound('missing name')
    fn = Path(name).name
    p = JSON_DIR / fn
    if not p.exists():
        return HttpResponseNotFound('file not found')
    # serve as file response (streamed)
    return FileResponse(open(p, 'rb'), content_type='application/json')
