import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

mcp_tools_json = '["web_search","calculator","report_generator","file_reader","mcp::github-mcp::create_issue","mcp::github-mcp::create_pull_request","mcp::github-mcp::delete_repository","mcp::postgres-mcp::query","mcp::postgres-mcp::truncate_table","mcp::postgres-mcp::drop_table","mcp::yuno-native-mcp::analyze_text","mcp::yuno-native-mcp::calculate_metrics","mcp::yuno-native-mcp::format_report"]'

# 1. Patch initial useState
old_state = 'E=d((0,o.useState)(["web_search","calculator","report_generator","file_reader"]),2)'
new_state = f'E=d((0,o.useState)({mcp_tools_json}),2)'

# 2. Patch useEffect C([...t])
old_effect = 'C(["web_search","calculator","report_generator","file_reader",...t])'
new_effect = f'C([...{mcp_tools_json},...t])'

if old_state in content:
    content = content.replace(old_state, new_state)
    print("Patched initial useState!")
else:
    print("old_state not found!")

if old_effect in content:
    content = content.replace(old_effect, new_effect)
    print("Patched useEffect!")
else:
    print("old_effect not found!")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("COMPLETE BUILDER PATCH APPLIED SUCCESSFULLY!")
