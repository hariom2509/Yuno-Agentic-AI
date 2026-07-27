import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Target legacy hardcoded array pattern
legacy_pattern = '["web_search","calculator","report_generator","file_reader","mcp::github-mcp::create_issue","mcp::github-mcp::create_pull_request","mcp::github-mcp::delete_repository","mcp::postgres-mcp::query","mcp::postgres-mcp::truncate_table","mcp::postgres-mcp::drop_table"]'

canonical_yuno_tools = '["mcp::yuno-tools::web_search","mcp::yuno-tools::calculator","mcp::yuno-tools::report_generator","mcp::yuno-tools::file_reader","mcp::yuno-tools::analyze_text","mcp::yuno-tools::calculate_metrics","mcp::yuno-tools::format_report"]'

count_replaced = content.count(legacy_pattern)
content = content.replace(legacy_pattern, canonical_yuno_tools)
print(f"Replaced {count_replaced} legacy tool array occurrences with canonical Yuno Tools array.")

# 2. Target option label renderer in the select dropdown to format friendly names
# Original: children:e},e))
# Replacement: children:e.startsWith("mcp::yuno-tools::")?e.split("::")[2].replace(/_/g," ").replace(/\b\w/g,l=>l.toUpperCase()):e},e))

old_option_render = 'children:e},e))'
new_option_render = 'children:e.startsWith("mcp::yuno-tools::")?e.split("::")[2].replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase()):e},e))'

if old_option_render in content:
    content = content.replace(old_option_render, new_option_render, 1)
    print("Updated select option label renderer to display friendly names (e.g. Web Search).")

# 3. Patch API call in Builder useEffect to fetch /api/capabilities/builder-tools
old_fetch_pattern = 'aa.get("/skills/").catch(('
new_fetch_pattern = 'aa.get("/api/capabilities/builder-tools").then(e=>{const t=(e.data?.groups||[]).flatMap(g=>(g.tools||[]).map(x=>x.canonical_name||x.id));if(t.length)C(t);}).catch(()=>{}); aa.get("/skills/").catch(('

if old_fetch_pattern in content:
    content = content.replace(old_fetch_pattern, new_fetch_pattern, 1)
    print("Patched Builder useEffect to trigger GET /api/capabilities/builder-tools on mount.")

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Static production JS bundle patch complete.")
