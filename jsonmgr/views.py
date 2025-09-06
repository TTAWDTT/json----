import json
import time
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
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
    is_backup = False
    if not p.exists():
        # try backups dir
        p_b = BACKUP_DIR / fn
        if p_b.exists():
            p = p_b
            is_backup = True
        else:
            return HttpResponseNotFound('file not found')

    message = ''
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')
        json_value = request.POST.get('json_value') == 'on'
        if is_backup:
            message = '不能修改备份文件，请打开原始文件后再修改。'
        else:
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
    # build files list for sidebar
    files = []
    backups_map = {}
    if JSON_DIR.exists():
        for p2 in JSON_DIR.iterdir():
            if p2.is_file() and p2.suffix == '.json':
                files.append(p2.name)
    # prepare backups mapping: { original_filename: [backup_filenames...] }
    if BACKUP_DIR.exists():
        for p3 in BACKUP_DIR.iterdir():
            if p3.is_file():
                # backups are named like "<orig>.bak-<ts>" or "<orig>.json.bak-..."
                name = p3.name
                # try to find the original file name part
                parts = name.split('.bak-')
                if parts:
                    orig = parts[0]
                else:
                    orig = name
                backups_map.setdefault(orig, []).append(name)

    # load current content but avoid embedding very large files in the HTML
    content = ''
    content_obj = None
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
            # parse full JSON so template can inject structured data safely
            try:
                content_obj = json.loads(raw)
            except Exception:
                content_obj = None
    except Exception:
        content = ''
    return render(request, 'jsonmgr/view.html', {'name': fn, 'content': content, 'content_obj': content_obj, 'message': message, 'truncated': truncated, 'files': files, 'backups': backups_map})


def raw_file(request):
    name = request.GET.get('name')
    if not name:
        return HttpResponseNotFound('missing name')
    fn = Path(name).name
    p = JSON_DIR / fn
    if not p.exists():
        p_b = BACKUP_DIR / fn
        if p_b.exists():
            p = p_b
        else:
            return HttpResponseNotFound('file not found')
    # serve as file response (streamed)
    return FileResponse(open(p, 'rb'), content_type='application/json')


def api_files(request):
    files = []
    backups_map = {}
    if JSON_DIR.exists():
        for p in JSON_DIR.iterdir():
            if p.is_file() and p.suffix == '.json':
                files.append(p.name)
    if BACKUP_DIR.exists():
        for p in BACKUP_DIR.iterdir():
            if p.is_file():
                name = p.name
                parts = name.split('.bak-')
                orig = parts[0] if parts else name
                backups_map.setdefault(orig, []).append(name)
    return JsonResponse({'files': files, 'backups': backups_map}, safe=False)
