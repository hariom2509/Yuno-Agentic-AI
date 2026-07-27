import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all unsafe b.tools.includes calls with (b.tools||[]).includes
old_sel_check = 'let sel=b.tools.includes(t.id)||b.tools.includes(t.id.split("::").pop());'
new_sel_check = 'let sel=(b.tools||[]).includes(t.id)||(b.tools||[]).includes(t.id.split("::").pop());'

count = content.count(old_sel_check)
print(f"Found {count} unsafe sel checks.")

if count > 0:
    content = content.replace(old_sel_check, new_sel_check)
    print("Replaced all unsafe b.tools checks with (b.tools||[]).includes null-safe checks!")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Null safety patch complete.")
