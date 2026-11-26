# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2,<2"]
# ///
"""End-to-end test: start fluidmeet_mcp.py over stdio against tests/fake-fv-serve.

Run with:  uv run tests/test_server.py
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
FAKE = ROOT / "tests" / "fake-fv-serve"


def text(result) -> str:
    return "\n".join(part.text for part in result.content if part.type == "text")


async def session_run(env_extra: dict, check):
    env = {**os.environ, "FV_SERVE_PATH": str(FAKE), **env_extra}
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "fluidmeet_mcp.py")], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await check(session)


async def main():
    log = Path(tempfile.mkstemp()[1])

    async def happy(session: ClientSession):
        tools = sorted(t.name for t in (await session.list_tools()).tools)
        assert tools == ["get_summary", "get_transcript", "list_meetings", "search_meetings", "sharing_status"], tools

        meetings = json.loads(text(await session.call_tool("list_meetings", {"since": "7d", "limit": 5})))
        assert meetings[0]["title"] == "Weekly sync"

        transcript = await session.call_tool("get_transcript", {"meeting": "latest", "from_time": "00:00", "to_time": "01:00"})
        assert not transcript.isError and "budget" in text(transcript)

        missing = await session.call_tool("get_transcript", {"meeting": "nope"})
        assert missing.isError and "No meeting matches" in text(missing)

        summary = await session.call_tool("get_summary", {})
        assert "Budget reviewed" in text(summary)

        hits = await session.call_tool("search_meetings", {"query": "-dash first"})
        assert "-dash first" in text(hits)

        empty = await session.call_tool("search_meetings", {"query": "  "})
        assert empty.isError

        status = json.loads(text(await session.call_tool("sharing_status", {})))
        assert status == {"access": True, "meetings": 1}

    async def sharing_off(session: ClientSession):
        result = await session.call_tool("list_meetings", {})
        assert result.isError and "not sharing meetings" in text(result), text(result)

    await session_run({"FAKE_LOG": str(log)}, happy)
    await session_run({"FAKE_ACCESS": "off"}, sharing_off)

    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert ["meet", "list", "--json", "--since", "7d", "--limit", "5"] in calls, calls
    assert ["meet", "show", "latest", "--from", "00:00", "--to", "01:00"] in calls, calls
    assert ["meet", "search", "--", "-dash first"] in calls, calls
    print("All tests passed.")


asyncio.run(main())
