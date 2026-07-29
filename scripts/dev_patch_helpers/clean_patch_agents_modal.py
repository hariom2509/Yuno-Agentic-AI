import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's inspect around index 243000 to see current content in main.f973130c.js
idx = content.find('Max Tokens')
print('Max Tokens index:', idx)
if idx != -1:
    print(content[idx-50:idx+600])
