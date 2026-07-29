import json
import logging
from sqlalchemy import text
from app.db.database import engine
from app.services.capability_registry import CapabilityRegistry

logger = logging.getLogger(__name__)

def migrate_saved_workflows():
    """
    Migrates saved Workflow graph JSON objects in database from legacy tool names
    (e.g., mcp::yuno-native-mcp::analyze_text or raw web_search)
    to canonical Yuno Tools identifiers (e.g., mcp::yuno-tools::analyze_text).
    """
    try:
        with engine.begin() as conn:
            rows = conn.execute(text("SELECT id, graph FROM workflows")).fetchall()
            updated_count = 0
            for row in rows:
                wf_id, graph_data = row[0], row[1]
                if not graph_data:
                    continue

                if isinstance(graph_data, str):
                    try:
                        graph_json = json.loads(graph_data)
                    except Exception:
                        continue
                else:
                    graph_json = graph_data

                nodes = graph_json.get("nodes", [])
                changed = False
                for node in nodes:
                    if node.get("type") == "toolNode" or (node.get("data") or {}).get("type") == "tool":
                        data = node.get("data") or {}
                        old_tool = data.get("tool")
                        if old_tool:
                            canonical = CapabilityRegistry.resolve_canonical_name(old_tool)
                            if canonical != old_tool:
                                data["tool"] = canonical
                                node["data"] = data
                                changed = True

                if changed:
                    new_graph_str = json.dumps(graph_json)
                    conn.execute(
                        text("UPDATE workflows SET graph = :graph WHERE id = :id"),
                        {"graph": new_graph_str, "id": wf_id}
                    )
                    updated_count += 1

            logger.info(f"Successfully migrated {updated_count} legacy saved workflow graphs to canonical MCP names.")
            print(f"Successfully migrated {updated_count} legacy saved workflow graphs to canonical MCP names.")
    except Exception as e:
        logger.error(f"Error migrating legacy saved workflows: {e}")

if __name__ == "__main__":
    migrate_saved_workflows()
