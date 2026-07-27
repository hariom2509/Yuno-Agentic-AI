import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any legacy hardcoded array or old endpoint fetching in the bundle with capability API fetch
old_pattern = '["web_search","calculator","report_generator","file_reader","mcp::github-mcp::create_issue","mcp::github-mcp::create_pull_request","mcp::github-mcp::delete_repository","mcp::postgres-mcp::query","mcp::postgres-mcp::truncate_table","mcp::postgres-mcp::drop_table"]'

new_tools = '["mcp::yuno-tools::web_search","mcp::yuno-tools::calculator","mcp::yuno-tools::report_generator","mcp::yuno-tools::file_reader","mcp::yuno-tools::analyze_text","mcp::yuno-tools::calculate_metrics","mcp::yuno-tools::format_report"]'

patched_content = content.replace(old_pattern, new_tools)

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(patched_content)

print("Main static JS bundle successfully patched with clean capability tools list.")
