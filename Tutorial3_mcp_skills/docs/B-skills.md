# Part B · Agent Skills: give your agent a method

**Goal:** see how a skill turns a tool into a reliable procedure. **No AI key needed for the
server;** your AI app does the writing. About 10 minutes.

| | Gives the agent | Here |
|---|---|---|
| **MCP tool** | The ability to do something | `calculate` runs a sum exactly |
| **Skill** | The know-how to do it well | `skills/calculator/SKILL.md`: when to calculate, which formula, how to report it |

## How a skill travels through MCP: progressive disclosure

A skill is a folder with a `SKILL.md` file. It loads in stages, so an unused skill costs almost
nothing:

| Level | Tool | What the model gets |
|---|---|---|
| 1. Discover | `list_skills` | The name and description of every skill |
| 2. Load | `load_skill` | The full procedure, when a task matches |
| 3. Look up | `read_skill_file` | A reference file, only if a step needs it |

The **description** at the top of `SKILL.md` decides whether the skill is ever used.
Serving skills this way works in any MCP app. Apps with native skill support can also install the
folder directly; in Claude Code, for example, copy it to `~/.claude/skills/`.

## B1. The calculator: the tool does the sum, the skill teaches the method

Run the tool on its own:

```bash
python try_server.py calc "412/487*100"
python try_server.py calc "1*F/(3.6*157.76)"
python try_server.py calc "__import__('os')"
```

✅ **Checkpoint:** `84.5996`, then `169.888` (the theoretical capacity of LiFePO4, in mAh/g), then
an `ERROR`. Anything that is not arithmetic is refused, so the tool cannot be used to run code.

Read the skill in `skills/calculator/`:

```text
calculator/
├── SKILL.md               name, description and the procedure
├── references/formulas.md battery and materials formulas, read only when needed
└── scripts/calc.py        the code, which server.py also uses
```

Now ask your app, and watch the tool calls:

```text
A pouch cell keeps 412 mAh of its original 487 mAh after 500 cycles.
What is the capacity retention and the average fade per cycle?
```

✅ **Checkpoint:** you see `load_skill`, then `calculate` at each step: 84.6% and about 0.031% per cycle.

## B2. A skill with a checker: lay abstracts

The lay-abstract skill gives the procedure; two MCP tools do the work:

```text
 document --> prepare_lay_abstract --> AI writes a draft --> review_lay_abstract
                                              ^                      |
                                              +------ REVISE <-------+--> PASS: final text
```

The checker is ordinary code, so it gives the same result every time. It flags more than **200
words**, a **Flesch-Kincaid grade** above 10, **sentences** over 25 words, **possible jargon**, and
**numbers that do not appear in the source**, which catches invented or mistyped figures.

Test the checker on its own:

```bash
python try_server.py lay paper5
```

Then send a document, in one of three ways:

```text
Write a lay abstract of paper5 for first-year students.
```

```text
Write a lay abstract of the document below for a funding panel, using the lay-abstract skill.
Pass its full text to prepare_lay_abstract and to review_lay_abstract. [paste the text]
```

Or copy a new file into your library folder and name it in the first prompt.

✅ **Checkpoint:** you see the review run, and the final text comes with its grade and word count.

**Your job:** the checker measures readability and matches numbers. It cannot tell whether the
summary is *right*. Is this the main finding? Did "suggests" stay "suggests"? Is the biggest
limitation still there?

> **Security note.** Tools read only inside your library folder; a path such as
> `/Users/me/secret.pdf` is refused. Document text is treated as data, never as instructions,
> because a PDF can contain hidden text telling the agent what to do.

## Try this

1. Add your field's formula to `skills/calculator/references/formulas.md`, then ask a question that needs it.
2. Make the calculator's description vague ("Helps with numbers"), restart your app and ask again.
3. Change `MAX_GRADE` in `research_tools/lay_abstract.py` to 7. How many revisions does it take now?

**Next:** [Part C · MCP and Skills together](C-together.md)
