import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any unescaped emojis or corrupt characters
content = content.replace("🛠️ ", "")
content = content.replace("✓ ", "")
content = content.replace("✓", "")
content = content.replace("⏰ ", "")
content = content.replace("🛡️ ", "")

# Fix any property name issues like justifyBetween -> justifyContent
content = content.replace('justifyBetween:"space-between",', '')

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Encoding and syntax fix complete.")
