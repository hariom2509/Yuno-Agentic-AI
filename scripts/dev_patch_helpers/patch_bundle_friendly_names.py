import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Canvas Node Card label rendering
old_role_snippet = 'n?"tool: ".concat(t.tool||"web_search"):t.model||"llama-3.3-70b-versatile"'
new_role_snippet = 'n?"tool: ".concat(t.tool?(t.tool.includes("::")?t.tool.split("::").pop().replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase()):t.tool):"Web Search"):t.model||"llama-3.3-70b-versatile"'

if old_role_snippet in content:
    content = content.replace(old_role_snippet, new_role_snippet)
    print("Updated canvas node card tool label renderer.")
else:
    print("Canvas node role snippet not found or already updated.")

# 2. Map exact friendly names for select options
# E.g. mcp::yuno-tools::web_search -> Web Search
# mcp::yuno-tools::calculator -> Calculator
# mcp::yuno-tools::report_generator -> Report Generator
# mcp::yuno-tools::file_reader -> File Reader
# mcp::yuno-tools::analyze_text -> Analyze Text
# mcp::yuno-tools::calculate_metrics -> Calculate Metrics
# mcp::yuno-tools::format_report -> Format Report

mapping_code = 'let label_map = {"mcp::yuno-tools::web_search":"Web Search","mcp::yuno-tools::calculator":"Calculator","mcp::yuno-tools::report_generator":"Report Generator","mcp::yuno-tools::file_reader":"File Reader","mcp::yuno-tools::analyze_text":"Analyze Text","mcp::yuno-tools::calculate_metrics":"Calculate Metrics","mcp::yuno-tools::format_report":"Format Report"};'

# Replace option render string if needed
old_option_code = 'children:e.startsWith("mcp::yuno-tools::")?e.split("::")[2].replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase()):e}'
new_option_code = 'children:e.startsWith("mcp::yuno-tools::")?(e.split("::")[2]==="web_search"?"Web Search":e.split("::")[2]==="calculator"?"Calculator":e.split("::")[2]==="report_generator"?"Report Generator":e.split("::")[2]==="file_reader"?"File Reader":e.split("::")[2]==="analyze_text"?"Analyze Text":e.split("::")[2]==="calculate_metrics"?"Calculate Metrics":e.split("::")[2]==="format_report"?"Format Report":e.split("::")[2].replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase())):e}'

if old_option_code in content:
    content = content.replace(old_option_code, new_option_code)
    print("Updated option label string map in select dropdown.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Friendly display names patch complete.")
