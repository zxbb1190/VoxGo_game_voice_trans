import json,sys,hashlib
from pathlib import Path
from voxgo.ui.chinese_text import recognition_display_text
from voxgo.ui import _opencc
raw='後衛🙂在後門，還有15秒，不要開槍。'
expected='后卫🙂在后门，还有15秒，不要开枪。'
assert recognition_display_text(raw,'zh')==expected
assert recognition_display_text('後ろへ移動','ja')=='後ろへ移動'
assert recognition_display_text('乾隆與乾淨的頭髮','zh')=='乾隆与干净的头发'
base=Path(_opencc.__file__).parent
manifest=json.loads((base/'UPSTREAM.json').read_text('utf-8'))
checked=[]
for entry in manifest['files']:
    if entry['path'].endswith('.py'):continue  # Python code is in the PYZ archive.
    actual=hashlib.sha256((base/entry['path']).read_bytes()).hexdigest()
    assert actual==entry['sha256']
    checked.append(entry['path'])
print(json.dumps(dict(frozen=bool(getattr(sys,'frozen',False)),simplified_display=recognition_display_text(raw,'zh'),
    japanese_unchanged=True,resources_sha256_valid=True,checked=checked,real_api_requests=0),ensure_ascii=True))
