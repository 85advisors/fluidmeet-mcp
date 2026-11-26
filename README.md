# fluidmeet-mcp

An MCP server that lets Claude Desktop (or any MCP client) read the meetings
[FluidVoice](https://github.com/altic-dev/FluidVoice)'s FluidMeet records on your Mac.

It is **read-only** and **local**. It never touches FluidVoice's files directly: every
tool calls `fv-serve`, the command-line reader that ships inside FluidVoice.app. That
means FluidVoice's own sharing switch stays in control. Turn sharing off in FluidVoice
and this server stops returning meetings.

> Not affiliated with FluidVoice or Altic. This is an unofficial wrapper around their
> official `fv-serve` tool.

## Tools

| Tool | What it does |
|---|---|
| `list_meetings` | Recent meetings, newest first (id, title, date, length, speakers, saved summaries). Filters: `since` (`24h`, `7d`, `2026-11-01`), `limit`. |
| `get_transcript` | A transcript with speaker names and timestamps. `from_time` / `to_time` (`MM:SS`) read one part. |
| `get_summary` | Summaries already written in FluidVoice, optionally one `style`. |
| `search_meetings` | Transcript lines that mention some text, grouped by meeting. |
| `sharing_status` | Whether FluidVoice is sharing meetings, and how many. |

Meetings can be referred to by full id, the first 8 characters of the id, or `latest`.

## Requirements

- macOS with **FluidVoice 1.6.12 or later** (`brew install --cask fluidvoice`)
- [uv](https://docs.astral.sh/uv/) (`brew install uv`). It installs the one Python
  dependency (the `mcp` package) automatically on first run.

## Setup

There's nothing to clone. `uvx` installs the server straight from GitHub and runs it
whenever Claude Desktop starts.

1. **Turn on meeting sharing in FluidVoice.** Open FluidVoice > FluidMeet settings >
   **Integrations**. Under **Other agents**, press **Copy instructions**. Pressing it is
   what turns sharing on; you don't need to paste the copied text anywhere.

2. **Make sure git can reach the repo.** It's private, so you need access to it on GitHub
   and git signed in on your Mac. Check with:

   ```sh
   git ls-remote https://github.com/85advisors/fluidmeet-mcp
   ```

   If that asks for a password or fails, run `brew install gh`, then `gh auth login`, then
   `gh auth setup-git`, and try again.

3. **Find uvx's full path.** Claude Desktop doesn't use your shell's PATH, so it needs the
   full path:

   ```sh
   which uvx    # usually /opt/homebrew/bin/uvx
   ```

4. **Add the server to Claude Desktop.** Open Claude Desktop > Settings > Developer >
   Edit Config. That opens `~/Library/Application Support/Claude/claude_desktop_config.json`.
   Add this entry, and keep any servers already in `mcpServers`:

   ```json
   {
     "mcpServers": {
       "fluidmeet": {
         "command": "/opt/homebrew/bin/uvx",
         "args": [
           "--refresh",
           "--from", "git+https://github.com/85advisors/fluidmeet-mcp",
           "fluidmeet-mcp"
         ]
       }
     }
   }
   ```

   `--refresh` picks up the latest commit each time Claude Desktop starts. To stay on a
   fixed version instead, drop `--refresh` and add `@` plus a commit hash (or a tag) to
   the end of the git URL, for example `git+https://github.com/85advisors/fluidmeet-mcp@fbe08d2`.

5. **Quit and reopen Claude Desktop**, then try something like *"What did we decide in my
   last meeting?"* or *"Search my meetings from this week for 'budget'."*

### Other clients

- **Claude Code:**
  `claude mcp add fluidmeet -- uvx --refresh --from git+https://github.com/85advisors/fluidmeet-mcp fluidmeet-mcp`
- **Cursor and others:** use the same `command` and `args` as the Claude Desktop entry above.

### Running from a local copy instead

If you'd rather not depend on GitHub at start-up, clone the repo to a normal local
folder (not iCloud Drive or Dropbox) and point Claude Desktop at the file:

```json
"fluidmeet": {
  "command": "/opt/homebrew/bin/uv",
  "args": ["run", "--script", "/Users/YOUR_NAME/mcp-servers/fluidmeet-mcp/fluidmeet_mcp.py"]
}
```

### FluidVoice installed somewhere unusual?

The server looks in `/Applications`, `~/Applications`, on your PATH, and then asks
Spotlight. If it still can't find FluidVoice, add an `env` block to the config entry:

```json
"env": { "FV_SERVE_PATH": "/path/to/FluidVoice.app/Contents/Helpers/fv-serve" }
```

## Troubleshooting

- **"FluidVoice is not sharing meetings with any agent yet"**: do step 1 again. Pressing
  "Stop sharing" in FluidVoice, or removing every Claude Code/Codex skill, turns sharing off.
- **"Could not verify FluidVoice meeting-sharing permission"**: open FluidVoice once, then
  check Integrations.
- **The server doesn't show up in Claude Desktop**: check that the `command` path is the
  full path from step 3 and that step 2's `git ls-remote` works, then see Claude Desktop's
  MCP logs in `~/Library/Logs/Claude/` (look for `mcp-server-fluidmeet.log`).
- **First start is slow**: uvx is fetching the repo and the `mcp` package. Later starts
  only check GitHub for new commits.

You can also check everything from Terminal:

```sh
/Applications/FluidVoice.app/Contents/Helpers/fv-serve status
```

## Privacy

Meetings stay on your Mac until an assistant reads them. Whatever the assistant reads
(transcripts, summaries, search results) is then sent to that assistant's AI provider as
part of the conversation, like anything else you share in a chat. Only connect assistants
you trust with your meetings.

## Development

The tests run the real server over MCP against a fake `fv-serve`, so they work without
FluidVoice (on any OS):

```sh
uv run tests/test_server.py
```

The server is pinned to the v1 `mcp` Python SDK (`mcp>=1.2,<2`). Version 2 renamed
`FastMCP`, so moving to it needs a small code change.

## License

MIT. See [LICENSE](LICENSE).
