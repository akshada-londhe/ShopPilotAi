# Sub-Agent Prompt Templates

Exact prompts passed to `invoke_sub_agent` during og-debugger operation. Each template has placeholders in `{braces}` that get filled with live context.

## OG-Gang: Validate Hypothesis

**Agent name:** `og-gang`

**Prompt:**

```
Bug under investigation: {bug_statement}

Current phase: {phase_name}
Evidence collected: {evidence_summary}

I need your verdict on the following:

{items_to_validate}

For each item, give me: solid / weak / rejected, with one-line reasoning. If rejected, state what's wrong. If weak, state what's missing.

Previously rejected approaches (do not re-suggest):
{rejected_approaches}
```

## OG-Gang: Validate Fix Proposal

**Agent name:** `og-gang`

**Prompt:**

```
Bug: {bug_statement}
Root cause: {root_cause_statement}
Blast radius: {impact_summary}

Proposed fix approaches:

{fix_approaches_numbered}

Evaluate each approach for:
- Production safety (will it break something else?)
- Completeness (does it address the full root cause or only a symptom?)
- Complexity vs. problem size (is it proportional?)
- Reversibility (how hard to roll back if wrong?)

Give one consensus decision: which approach to take, or reject all with reasoning.
```

## OG-Deep-Grill: Generate Investigation Questions

**Agent name:** `general-task-execution`
**Skill to follow:** og-deep-grill

**Prompt:**

```
I'm debugging a production issue and need penetrating questions to deepen my investigation.

Bug: {bug_statement}
Current phase: {phase_name}
What's established so far: {established_facts}
What's still unknown: {open_areas}

Generate 5-10 sharp questions that would:
- Expose hidden assumptions in my current understanding
- Challenge whether the root cause I'm considering is the real one
- Surface edge cases or failure modes I haven't considered
- Test whether my evidence is complete or has gaps

Questions already answered (skip these):
{answered_questions}

Focus on: {specific_area_to_investigate}
```

## OG-Deep-Grill: Grill a Proposed Answer

**Agent name:** `general-task-execution`
**Skill to follow:** og-deep-grill

**Prompt:**

```
I proposed an answer to a debugging question and need it stress-tested.

Question: {question}
My proposed answer: {proposed_answer}
Evidence I'm basing it on: {evidence}

Grill this answer:
- Is the evidence sufficient to support this conclusion?
- What alternative explanations fit the same evidence?
- What would disprove this answer?
- What am I assuming that might be wrong?
```

## Brainstorming: Answer an Open Question

**Agent name:** `general-task-execution`

**Prompt:**

```
You are brainstorming answers to a debugging question. Think creatively but stay grounded in evidence.

Bug context: {bug_statement}
Investigation so far: {evidence_summary}

Question to answer: {question}

Constraints:
- Answer must be supportable by code evidence or logical deduction from known facts
- If the answer requires information you don't have, say what's missing
- Produce 2-3 candidate answers, each with: the answer itself, what evidence supports it, what would confirm or disprove it

Previously tried answers that were rejected:
{rejected_answers}

Codebase context (relevant files/lines):
{code_context}
```

## Brainstorming: Find Fix Directions

**Agent name:** `general-task-execution`

**Prompt:**

```
You are brainstorming fix approaches for a confirmed bug.

Bug: {bug_statement}
Root cause: {root_cause_statement}
Affected code: {affected_files_and_lines}
Blast radius: {impact_summary}

Generate 2-3 fix approaches. For each:
- What changes (files, functions, conditions)
- What risk it carries (regressions, edge cases)
- What it doesn't fix (known limitations)
- Estimated complexity (one-liner, small patch, multi-file change)

Constraints:
- Production-grade only. No hacks, no temporary workarounds unless labeled as such.
- Proportional to the problem. A one-line root cause should not need a 200-line fix.
- Must address root cause, not symptom.

Rejected approaches (do not re-suggest):
{rejected_approaches}
```

## Context-Gatherer: Understand Unfamiliar Code

**Agent name:** `context-gatherer`

**Prompt:**

```
I'm debugging a bug and need to understand how a specific code area works.

Bug: {bug_statement}
What I need to understand: {investigation_question}

Specifically:
- How does {component_or_function} work?
- What calls it and what does it call?
- What state does it depend on?
- What are its failure modes?

Start from: {entry_point_file_and_line}
```

## Placeholder Reference

| Placeholder | Source |
|-------------|--------|
| `{bug_statement}` | One-sentence bug description confirmed in Phase 0 |
| `{phase_name}` | Current phase (Intake/Verify/Root Cause/Impact/Mitigation) |
| `{evidence_summary}` | Bulleted list of confirmed facts from investigation |
| `{items_to_validate}` | Numbered list of hypotheses/answers to validate |
| `{rejected_approaches}` | Previously rejected ideas (prevents loops) |
| `{root_cause_statement}` | Confirmed root cause from Phase 2 |
| `{impact_summary}` | Blast radius findings from Phase 3 |
| `{fix_approaches_numbered}` | Numbered fix proposals with descriptions |
| `{established_facts}` | What's confirmed true about the bug |
| `{open_areas}` | What's still unknown or unverified |
| `{answered_questions}` | Questions already resolved (prevents re-asking) |
| `{specific_area_to_investigate}` | The narrow focus for this grill round |
| `{question}` | The specific question being answered |
| `{proposed_answer}` | A candidate answer being validated |
| `{evidence}` | Code/logs/traces supporting an answer |
| `{rejected_answers}` | Answers already tried and rejected |
| `{code_context}` | Relevant file excerpts (summarized, not raw dumps) |
| `{affected_files_and_lines}` | Files/lines touched by the bug |
| `{component_or_function}` | What needs understanding |
| `{entry_point_file_and_line}` | Where to start reading |
