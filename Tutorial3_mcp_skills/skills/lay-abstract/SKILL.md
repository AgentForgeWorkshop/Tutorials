---
name: lay-abstract
description: Writes and checks a lay abstract, a plain-language summary of one document for non-specialists such as students, journalists, funders or family. Use when the user asks to explain a paper simply, for a general audience, without jargon, or asks for a lay summary or lay abstract.
license: MIT
metadata:
  author: AgentForge Tutorial 3
  version: "2.0"
---

# Lay abstract

## Steps

1. Call `prepare_lay_abstract` with the document and the audience. The document can be a file
   in the library or the full text of a document the user pasted or attached.
2. Write a draft that follows the brief the tool returns.
3. Call `review_lay_abstract` with the draft and the same document.
4. If the verdict is REVISE, fix what it lists and call it again, at most three times.
5. Show the final lay abstract, then one line with its grade level and word count, then
   Source: (file, p. N).

## Rules

- Every number must come from the document. Round it only if the meaning stays the same.
- Keep the author's certainty: "suggests" stays "suggests".
- If the checker flags a term as jargon but no plainer word exists, explain it in brackets and
  say so in your final line.
- Never claim the draft passed unless the last review returned PASS.
