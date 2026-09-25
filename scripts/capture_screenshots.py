import os
import time
from playwright.sync_api import sync_playwright

output_dir = os.path.abspath("docs/screenshots")
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 880},
        device_scale_factor=2,  # Crisp retina quality
    )
    page = context.new_page()

    # 1. Dashboard
    print("Capturing 01_dashboard.png...")
    page.goto("http://localhost:3000/", wait_until="networkidle")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(output_dir, "01_dashboard.png"))

    # 2. Visual Builder with Workflow 1 loaded
    print("Capturing 02_visual_builder.png...")
    page.goto("http://localhost:3000/builder/1", wait_until="networkidle")
    time.sleep(2.0)
    page.screenshot(path=os.path.join(output_dir, "02_visual_builder.png"))

    # 3. Observability & HITL Monitoring (expanding pending execution)
    print("Capturing 03_monitoring_hitl.png...")
    page.goto("http://localhost:3000/monitoring", wait_until="networkidle")
    time.sleep(1.5)
    try:
        # Find the row with #26 or text 'waiting_for_approval' and click it to expand
        hitl_row = page.locator("tr:has-text('waiting_for_approval')").first
        if hitl_row.is_visible():
            hitl_row.click()
            time.sleep(1.5)
    except Exception as e:
        print("Note expanding HITL row:", e)
    page.screenshot(path=os.path.join(output_dir, "03_monitoring_hitl.png"))

    # 4. Admin - MCP Tools Security
    print("Capturing 04_admin_tools_security.png...")
    page.goto("http://localhost:3000/admin", wait_until="networkidle")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(output_dir, "04_admin_tools_security.png"))

    # 5. Admin - Agent ACL Permissions
    print("Capturing 05_admin_agent_acls.png...")
    try:
        page.locator("button:has-text('Agent Tool Permissions')").click()
        time.sleep(1.0)
        # Select second agent if available
        select_box = page.locator("select").first
        if select_box.is_visible():
            options = select_box.locator("option").all()
            if len(options) > 1:
                select_box.select_option(index=1)
                time.sleep(1.0)
        page.screenshot(path=os.path.join(output_dir, "05_admin_agent_acls.png"))
    except Exception as e:
        print("Error on tab 2:", e)

    # 6. Admin - MCP Servers & Transports
    print("Capturing 06_admin_mcp_servers.png...")
    try:
        page.locator("button:has-text('MCP Servers & Transports')").click()
        time.sleep(1.0)
        page.screenshot(path=os.path.join(output_dir, "06_admin_mcp_servers.png"))
    except Exception as e:
        print("Error on tab 3:", e)

    # 7. Agents Management Page
    print("Capturing 07_agents_management.png...")
    page.goto("http://localhost:3000/agents", wait_until="networkidle")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(output_dir, "07_agents_management.png"))

    # 8. Templates Page
    print("Capturing 08_workflow_templates.png...")
    page.goto("http://localhost:3000/templates", wait_until="networkidle")
    time.sleep(1.5)
    page.screenshot(path=os.path.join(output_dir, "08_workflow_templates.png"))

    browser.close()
    print("All screenshots successfully captured in:", output_dir)
