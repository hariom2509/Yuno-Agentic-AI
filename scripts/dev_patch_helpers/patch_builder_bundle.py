import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'setAvailableTools(["web_search","calculator","report_generator","file_reader",'
if target not in content:
    target = '["web_search","calculator","report_generator","file_reader"'

replacement = '["web_search","calculator","report_generator","file_reader","mcp::github-mcp::create_issue","mcp::github-mcp::create_pull_request","mcp::github-mcp::delete_repository","mcp::postgres-mcp::query","mcp::postgres-mcp::truncate_table","mcp::postgres-mcp::drop_table","mcp::yuno-native-mcp::analyze_text","mcp::yuno-native-mcp::calculate_metrics","mcp::yuno-native-mcp::format_report"'

if target in content:
    new_content = content.replace(target, replacement, 1)
    with open(bundle_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESSFULLY PATCHED BUILDER TOOLS DROPDOWN IN BUNDLE!")
else:
    print("Target not found in bundle.")
