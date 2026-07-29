import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app/static/static/js/main.f973130c.js', 'r', encoding='utf-8') as f:
    text = f.read()

target = '["web_search"'
idx = text.find(target)
print("Found target index:", idx)
if idx != -1:
    print(text[idx:idx+350])
