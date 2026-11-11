---
name: calculator
description: Does exact arithmetic for science questions with the calculate tool instead of mental maths - ratios, percentage changes, capacity retention, fade per cycle, specific and theoretical capacity, C-rates. Use whenever an answer needs a number computed from other numbers.
license: MIT
metadata:
  author: AgentForge Tutorial 3
  version: "2.0"
---

# Calculator

Language models make arithmetic slips. Never compute a number in your head: use the tool.

## Steps

1. Write the calculation as one expression, for example `412/487*100`.
   For battery and materials formulas (retention, fade per cycle, specific and theoretical
   capacity, C-rate, energy), read `references/formulas.md` first with
   `read_skill_file(name="calculator", path="references/formulas.md")`.
2. Call `calculate` with the expression. If the `calculate` tool is not available, run
   `python scripts/calc.py "412/487*100"` from this skill's folder instead.
3. Report the expression, the result with sensible significant figures, and the units.
   If an input number came from a paper, cite where it came from as (file, p. N).

## Rules

- One calculation per call. For multi-step problems, call the tool once per step and show each step.
- If the result starts with ERROR, fix the expression and try again. Never guess the result.
