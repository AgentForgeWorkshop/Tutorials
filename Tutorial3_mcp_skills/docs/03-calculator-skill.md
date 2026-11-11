# Step 3: Calculator skill

**Goal:** the model stops doing arithmetic in its head. **No API key needed.**

This step shows the difference between the two main ideas of the workshop:

| | Gives the agent | Here |
|---|---|---|
| **MCP tool** | The ability to do something | `calculate` runs the sum exactly |
| **Skill** | The know-how to do it well | `skills/calculator/SKILL.md`: when to calculate, which formula, how to report it |

## 3.1 Run the tool

```bash
python try_server.py calc "412/487*100"
python try_server.py calc "1*F/(3.6*157.76)"
python try_server.py calc "__import__('os')"
```

✅ **Checkpoint:** `84.5996`, then `169.888` (the theoretical capacity of LiFePO4, in mAh/g), then
an `ERROR`. Anything that is not arithmetic is refused, so the tool cannot be used to run code.

## 3.2 Read the skill

Open `skills/calculator/`:

```text
calculator/
├── SKILL.md               name, description and the procedure
├── references/formulas.md battery and materials formulas, read only when needed
└── scripts/calc.py        the code, which server.py also uses
```

The **description** at the top of `SKILL.md` is the most important line, because it decides
whether the skill gets used at all.

## 3.3 How a skill travels through MCP

Skills load in stages, so an unused skill costs almost nothing:

| Stage | Tool | What the model gets |
|---|---|---|
| Discover | `list_skills` | One line per skill |
| Load | `load_skill` | The full procedure |
| Look up | `read_skill_file` | A reference file, only if a step needs it |

Serving skills this way works in any MCP app. Apps with native skill support can also install the
folder directly. In Claude Code, for example, copy it to `~/.claude/skills/`.

## 3.4 Use it

```text
A pouch cell keeps 412 mAh of its original 487 mAh after 500 cycles.
What is the capacity retention and the average fade per cycle?
```

✅ **Checkpoint:** the tool calls show `calculate` running for each step, giving 84.6% and about 0.031% per cycle.

Now combine it with your library:

```text
In paper5, how many times longer did cells last with pressure alone than with an interlayer at 1 MPa?
```

Expect 2.4 / 1.1 ≈ 2.2 times, with the numbers cited from the paper.

## Try this

1. Add your field's formula to `references/formulas.md`, then ask a question that needs it.
2. Make the description vague ("Helps with numbers"), restart your app and ask again. Does the
   model still use the tool?

**Next:** [Step 4: Lay abstract](04-lay-abstract.md)
