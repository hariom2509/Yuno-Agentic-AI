import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('colSpan:7')
if idx == -1:
    idx = content.find('colSpan')
snippet = content[idx-100:idx+600]
print("COLSPAN BLOCK:")
print(snippet)
