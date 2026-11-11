# Step 4: Lay abstract review

**Goal:** send a document to your MCP server and get a plain-language summary that has been
*checked*, not just written. **The server needs no API key.** Your AI app does the writing.

## 4.1 How it works

```text
 document --> prepare_lay_abstract --> AI writes a draft --> review_lay_abstract
                                              ^                      |
                                              +------ REVISE <-------+--> PASS: final text
```

| Tool | What it does |
|---|---|
| `prepare_lay_abstract` | Returns the document and a writing brief |
| `review_lay_abstract` | Measures the draft and returns PASS or REVISE |

The checker is ordinary code, so it gives the same result every time. It looks for:

- More than **200 words**
- A **Flesch-Kincaid grade** above 10
- **Sentences** over 25 words
- **Possible jargon** that has not been explained
- **Numbers that do not appear in the source**, which catches invented or mistyped figures

## 4.2 Test the checker

```bash
python try_server.py lay paper5
```

✅ **Checkpoint:** a verdict, a word count and a reading grade.

## 4.3 Send a document

There are three ways to send one:

**A file in your library** (part of the name is enough):

```text
Write a lay abstract of paper5 for first-year students.
```

**A document you paste or attach in the chat:**

```text
Write a lay abstract of the document below for a funding panel, using the lay-abstract skill.
Pass its full text to prepare_lay_abstract and to review_lay_abstract. [paste the text]
```

**A new file:** copy it into your library folder, then use the first prompt.

✅ **Checkpoint:** you see the review run, and the final text comes with its grade and word count.

## 4.4 Check it yourself

The checker measures readability and matches numbers. It cannot tell whether the summary is
*right*. Read the result against the paper and ask yourself:

- Is this the main finding, or just the most interesting one?
- Did "suggests" turn into "proves"?
- Is the biggest limitation still there?

## Security note

Tools read only inside your library folder. Passing a path such as `/Users/me/secret.pdf` is
refused. This is **least privilege**: a misled agent should not be able to reach beyond the folder
you chose. It is also why document text is labelled as data, not instructions, because a PDF can
contain hidden text telling the agent what to do.

## Try this

1. Ask for the same paper for a child, then for a journalist. What changes?
2. Change `MAX_GRADE` in `research_tools/lay_abstract.py` to 7. How many revisions does it take now?
3. Put a wrong number in a draft and pass it to `review_lay_abstract`. Is it caught?

**Next:** [Step 5: Valency in ChatGPT](05-valency-chatgpt.md)
