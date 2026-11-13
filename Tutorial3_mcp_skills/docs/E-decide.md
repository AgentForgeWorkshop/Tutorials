# Part E · Decide: MCP, a skill, or both?

**Goal:** apply the rule from the talk to your own research. **No setup, no key.** About 3 minutes,
or take it home.

| If your agent needs… | Use |
|---|---|
| Live information from a database, a website or an instrument, or to act in another application | **MCP** |
| To follow a consistent procedure, apply your group's standards, or produce a fixed format | **A skill** |
| Both external access and a repeatable workflow | **Both** |

## Your turn

Pick two or three tasks from your own work and fill in the table:

| Your research task | Needs access to… | Needs a procedure for… | MCP, skill or both? |
|---|---|---|---|
| *Example:* a weekly digest of new papers on my topic | arXiv / OpenAlex (live data) | what counts as relevant; the digest format | Both |
| | | | |
| | | | |
| | | | |

## Sample answers

| Task | Answer | Why |
|---|---|---|
| Search my group's sample database for every film annealed above 400 °C | **MCP** | Live data in a database |
| Write every methods section in our journal's required format | **Skill** | A procedure and a format, no live data |
| Check each new XRD pattern against reference phases and report | **Both** | Reads files (MCP) and follows a fixed method (skill) |
| Summarise this week's arXiv papers on perovskite stability for the group | **Both** | Live papers (MCP) and your relevance rules (skill) |

**The pattern:** live data needs MCP; rules or a format need a skill; most real research tasks need both.

## Build one

- **A tool:** write a Python function in `server.py` with `@mcp.tool()` and a clear docstring.
  Restart your app and it appears.
- **A skill:** copy `skills/_template/` to `skills/<your-skill-name>/`, set the `name` to the folder
  name, and replace every EDIT ME. Say in the description *when* to use it.

Keep the checkable parts (tolerances, units, references) in code, not in instructions to the model.

**Done!** See the [README](../README.md#keep-going) for ideas to take into your hackathon.
