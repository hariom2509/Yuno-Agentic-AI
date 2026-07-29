import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '})]},t.id);})})]})]})(0,ia.jsx)("div",{className:"form-group",children:(0,ia.jsxs)("label",{className:"toggle"'

replacement = '})]},t.id);})})]})]}),(0,ia.jsx)("div",{className:"form-group",children:(0,ia.jsxs)("label",{className:"toggle"'

if target in content:
    content = content.replace(target, replacement)
    print("SUCCESSFULLY FIXED MISSING COMMA IN BUNDLE!")
else:
    print("WARNING: target missing comma string not found.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Comma fix script complete.")
