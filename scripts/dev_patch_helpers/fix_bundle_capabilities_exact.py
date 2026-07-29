import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

legacy_array = '["web_search","calculator","report_generator","file_reader","mcp::github-mcp::create_issue","mcp::github-mcp::create_pull_request","mcp::github-mcp::delete_repository","mcp::postgres-mcp::query","mcp::postgres-mcp::truncate_table","mcp::postgres-mcp::drop_table","mcp::yuno-native-mcp::analyze_text","mcp::yuno-native-mcp::calculate_metrics","mcp::yuno-native-mcp::format_report"]'

canonical_yuno_tools = '["mcp::yuno-tools::web_search","mcp::yuno-tools::calculator","mcp::yuno-tools::report_generator","mcp::yuno-tools::file_reader","mcp::yuno-tools::analyze_text","mcp::yuno-tools::calculate_metrics","mcp::yuno-tools::format_report"]'

count = content.count(legacy_array)
print(f"Found {count} occurrences of legacy array.")

content = content.replace(legacy_array, canonical_yuno_tools)

# Patch option renderer to display friendly names in the Builder dropdown
# Old renderer snippet: children:e},e))
# New renderer snippet: children:e.startsWith("mcp::yuno-tools::")?e.split("::")[2].replace(/_/g," ").replace(/\b\w/g,l=>l.toUpperCase()):e},e))

old_render = 'children:e},e))'
new_render = 'children:e.startsWith("mcp::yuno-tools::")?e.split("::")[2].replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase()):e},e))'

if old_render in content:
    content = content.replace(old_render, new_render, 1)
    print("Updated select option renderer for friendly display labels.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully replaced {count} legacy tool array occurrences in production JS bundle!")
