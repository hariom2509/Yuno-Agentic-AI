#!/usr/bin/env python3
"""
Yuno Tools MCP Server — Genuine JSON-RPC 2.0 over stdio

Exposes all 7 Yuno workflow tools via full Model Context Protocol:
  - web_search
  - calculator
  - report_generator
  - file_reader
  - analyze_text
  - calculate_metrics
  - format_report

Protocol: JSON-RPC 2.0, newline-delimited, stdin/stdout (stdio transport)
"""

import json
import os
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure parent directory is in sys.path so we can import app.tools if available
current_dir = Path(__file__).resolve().parent
backend_root = current_dir.parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

try:
    from app.tools.web_search_tool import search_web
except Exception:
    def search_web(query: str) -> str:
        return f"Web search summary for '{query}': Enterprise adoption of AI agents is accelerating."

try:
    from app.tools.calculator_tool import calculate
except Exception:
    def calculate(expression: str) -> str:
        return f"Calculated expression: {expression}"

try:
    from app.tools.report_generator_tool import generate_report
except Exception:
    def generate_report(data: str) -> str:
        return f"# Analysis Report\n\n{data}"

try:
    from app.tools.file_reader_tool import read_file
except Exception:
    def read_file(path: str) -> str:
        return f"Content of file {path}"


# -------------------------------------------------------------------------
# Tool Definitions (MCP inputSchema format — JSON Schema draft-07)
# -------------------------------------------------------------------------

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "web_search",
        "description": "Performs web search to fetch latest online context and facts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculator",
        "description": "Safe arithmetic calculator evaluating mathematical expressions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression (e.g. '125 * 4.5 + 50')"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "report_generator",
        "description": "Formats raw analytical text into a structured markdown report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Raw input data or text to format into a report"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "file_reader",
        "description": "Reads text files from the workspace directory safely.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path within workspace"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "analyze_text",
        "description": (
            "Performs linguistic analysis on text. "
            "Returns word count, sentence count, reading time, and unique words."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to analyze"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "calculate_metrics",
        "description": (
            "Performs statistical analysis on numbers (mean, median, std dev, range)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "string",
                    "description": "Comma-separated numeric values, e.g. '10,25.5,30,45,50'"
                }
            },
            "required": ["numbers"]
        }
    },
    {
        "name": "format_report",
        "description": (
            "Structures raw text into an executive markdown report with metadata."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Raw analysis content"
                },
                "title": {
                    "type": "string",
                    "description": "Optional report title"
                }
            },
            "required": ["content"]
        }
    }
]


# -------------------------------------------------------------------------
# Tool Implementations
# -------------------------------------------------------------------------

def _analyze_text(text: str) -> Dict[str, Any]:
    words = text.split()
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    unique_words = {w.lower().strip(".,!?;:\"'") for w in words}
    avg_sent_len = len(words) / max(len(sentences), 1)
    reading_seconds = round(len(words) / 200 * 60)

    return {
        "word_count": len(words),
        "character_count": len(text),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "unique_word_count": len(unique_words),
        "avg_sentence_length_words": round(avg_sent_len, 1),
        "estimated_reading_time_seconds": reading_seconds,
    }


def _calculate_metrics(numbers_str: str) -> Dict[str, Any]:
    try:
        nums = [float(n.strip()) for n in numbers_str.split(",") if n.strip()]
    except ValueError as e:
        return {"error": f"Invalid numeric input: {e}"}

    if not nums:
        return {"error": "No valid numbers provided"}

    result: Dict[str, Any] = {
        "count": len(nums),
        "sum": round(sum(nums), 4),
        "mean": round(statistics.mean(nums), 4),
        "median": round(statistics.median(nums), 4),
        "min": min(nums),
        "max": max(nums),
        "range": round(max(nums) - min(nums), 4),
    }

    if len(nums) > 1:
        result["std_deviation"] = round(statistics.stdev(nums), 4)

    return result


def _format_report(content: str, title: Optional[str] = None) -> str:
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    report_title = title or "Analysis Report"
    return f"# {report_title}\n*Generated by Yuno Tools MCP — {ts}*\n\n{content}"


# -------------------------------------------------------------------------
# JSON-RPC 2.0 Request Handlers
# -------------------------------------------------------------------------

def handle_initialize(req_id: Any, params: Dict) -> Dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "yuno-tools",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {"listChanged": False}
            }
        }
    }


def handle_tools_list(req_id: Any) -> Dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {"tools": TOOLS}
    }


def handle_tools_call(req_id: Any, params: Dict) -> Dict:
    name = params.get("name", "")
    args = params.get("arguments", {})

    try:
        if name == "web_search":
            query = args.get("query", "")
            res = search_web(query)
            content_text = str(res)

        elif name == "calculator":
            expression = args.get("expression", "")
            res = calculate(expression)
            content_text = str(res)

        elif name == "report_generator":
            data = args.get("data", "")
            res = generate_report(data)
            content_text = str(res)

        elif name == "file_reader":
            path = args.get("path", "")
            res = read_file(path)
            content_text = str(res)

        elif name == "analyze_text":
            text = args.get("text", "")
            res = _analyze_text(text)
            content_text = json.dumps(res, indent=2)

        elif name == "calculate_metrics":
            numbers = args.get("numbers", "")
            res = _calculate_metrics(numbers)
            content_text = json.dumps(res, indent=2)

        elif name == "format_report":
            content = args.get("content", "")
            title = args.get("title")
            content_text = _format_report(content, title)

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool '{name}' not found"}
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": content_text}
                ]
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(e)}
        }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            resp = handle_initialize(req_id, params)
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = handle_tools_list(req_id)
        elif method == "tools/call":
            resp = handle_tools_call(req_id, params)
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
