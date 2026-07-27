import sys
sys.stdout.reconfigure(encoding='utf-8')

bundle_path = 'app/static/static/js/main.f973130c.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target exact Builder NodeConfigPanel select dropdown match
target_snippet = '(0,ia.jsx)("select",{className:"form-select",value:c.tool||"web_search",onChange:e=>f("tool",e.target.value),children:a.map(e=>(0,ia.jsx)("option",{value:e,children:e},e))})'

replacement_snippet = '(0,ia.jsx)("select",{className:"form-select",value:c.tool||"mcp::yuno-tools::web_search",onChange:e=>f("tool",e.target.value),children:a.map(e=>(0,ia.jsx)("option",{value:e,children:e==="mcp::yuno-tools::web_search"?"Web Search":e==="mcp::yuno-tools::calculator"?"Calculator":e==="mcp::yuno-tools::report_generator"?"Report Generator":e==="mcp::yuno-tools::file_reader"?"File Reader":e==="mcp::yuno-tools::analyze_text"?"Analyze Text":e==="mcp::yuno-tools::calculate_metrics"?"Calculate Metrics":e==="mcp::yuno-tools::format_report"?"Format Report":(e.includes("::")?e.split("::").pop().replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase()):e.replace(/_/g," ").replace(/\\b\\w/g,l=>l.toUpperCase()))},e))})'

if target_snippet in content:
    content = content.replace(target_snippet, replacement_snippet)
    print("SUCCESSFULLY replaced Builder dropdown option renderer in static bundle!")
else:
    print("ERROR: Target snippet not found in static bundle.")

# Also update default fallback value in Builder NodeConfigPanel
content = content.replace('value:c.tool||"web_search"', 'value:c.tool||"mcp::yuno-tools::web_search"')

with open(bundle_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patching complete.")
