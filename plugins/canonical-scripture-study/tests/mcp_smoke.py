"""Exercise the installed optional adapter through the actual stdio protocol."""
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    root = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(command=sys.executable, args=["-m", "bible_study.server"], cwd=str(root))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            tools = (await session.list_tools()).tools
            assert len(tools) == 10
            assert all(t.annotations.read_only_hint and not t.annotations.destructive_hint for t in tools)
            assert all(t.output_schema for t in tools)
            async def call(name, arguments):
                result = await session.call_tool(name, arguments)
                assert not result.is_error
                assert isinstance(result.structured_content, dict), name
                return result.structured_content
            source = await call("fetch_passage", {"reference": "Genesis 1:1-2", "sources": ["WLC"]})
            assert len(source["source_packets"][0]["records"]) == 2
            first = await call("study_plan", {"query": "Translate Genesis 1-2, in Dutch, with original language interlinear"})
            nxt = await call("study_plan", {"query": "Next", "study_state": first["continuation_state"]})
            assert nxt["reference"] == "Genesis 2" and nxt["language"] == "nl" and nxt["translation_format"] == "original_interlinear"
            dss = await call("fetch_dss", {"reference": "Genesis 1:27"})
            assert dss["records"][0]["metadata"]["letter_reconstruction"] == "ALL_LETTER_SLOTS_RECONSTRUCTED"
            word = await call("lookup_word", {"query": "testing"})
            assert word["entries"][0]["entry"]["id"] == "WT008"
            error = await call("fetch_passage", {"reference": "Genesis 1:99"})
            assert "error" in error
            print(json.dumps({"status": "passed", "server": initialized.server_info.name, "tools": len(tools), "read_only_annotations": True, "structured_output": True, "checks": ["initialize", "tool_schemas", "passage", "continuation", "DSS_status", "word_lookup", "structured_error"]}))


if __name__ == "__main__":
    asyncio.run(main())
