# Autonomous Loop Protocol

Disclosed reference for og-debugger's autonomous investigation mode. Loaded when user triggers "grill more on your own" or "open question" commands.

## The Loop

A single iteration:

```
GRILL → ANSWER → VALIDATE → (pass: collect) | (fail: refine → re-validate)
```

Max 3 iterations per loop invocation. If 3 loops produce no validated answer, stop and present what you have with explicit uncertainty markers.

## "Grill More On Your Own" Flow

User wants you to self-investigate. Full sequence:

### Step 1: Generate Questions

Dispatch `og-deep-grill` sub-agent with:
- Current phase context (what phase you're in, what's established so far)
- The specific area that needs deeper investigation
- What's already been answered (to avoid re-asking)

Receive back: 5-10 penetrating questions about the current investigation area.

### Step 2: Answer Each Question

For each question from Step 1, dispatch `brainstorming` sub-agent with:
- The question itself
- All evidence gathered so far (code paths, values, conditions)
- The codebase context (files read, git history found)
- Constraints: answer must be grounded in evidence, not speculation

Receive back: an evidence-based answer or "cannot determine without [X]".

### Step 3: Validate Answers

Bundle all question-answer pairs and dispatch `og-gang` sub-agent with:
- The full Q&A set
- The bug context
- Ask for: which answers are solid, which are weak, which are wrong

Receive back: verdict per answer (solid / weak / rejected) with reasoning.

### Step 4: Handle Verdict

- **All solid:** Collect findings. Exit loop. Present to user.
- **Some weak:** Take weak answers back to Step 2 with og-gang's feedback as additional constraint. This is iteration 2.
- **Some rejected:** Discard rejected answers. Re-grill (Step 1) on the rejected areas specifically. This is iteration 2.
- **All rejected:** Something is fundamentally wrong with the investigation direction. Exit loop. Tell user what happened and propose a pivot.

### Step 5: Present

After loop exits (success or max iterations):

Structure findings as:
```
Investigated [N] questions autonomously. Here's what I found:

CONFIRMED (og-gang validated):
- [finding 1] — evidence: [specific code/line/condition]
- [finding 2] — evidence: [specific code/line/condition]

LIKELY (brainstormed, not fully validated):
- [finding 3] — reasoning: [why likely]

UNRESOLVED (need your input):
- [question] — what I tried: [approach], why stuck: [reason]
```

Wait for user response before continuing.

## "Open Question" Flow

User marked a specific question as one you should answer yourself. Narrower scope than full autonomous mode.

### Step 1: Brainstorm

Dispatch `brainstorming` sub-agent with:
- The exact question
- All context from current investigation
- Instruction: produce 2-3 candidate answers with evidence for each

### Step 2: Validate

Dispatch `og-gang` sub-agent with:
- The question
- The candidate answers
- Ask: which answer is strongest, are any wrong, is anything missing

### Step 3: Handle Verdict

- **Clear winner:** Present that answer to user with og-gang's endorsement and your evidence.
- **No clear winner:** Loop once. Refine top 2 candidates via brainstorming with og-gang's feedback. Re-validate.
- **All rejected:** Present the rejection reasoning to user. Ask for guidance.

### Step 4: Present

```
For your open question "[question]":

PROPOSED ANSWER: [answer]
Evidence: [specific code/line/condition]
OG-Gang says: [one-line verdict]

Approve, reject, or want me to think more?
```

## "Think More" Flow

User rejected a proposal. Back through the loop with rejection context.

### Step 1: Understand Rejection

What specifically was rejected? Identify the weak point.

### Step 2: Re-brainstorm

Dispatch `brainstorming` sub-agent with:
- Original question/proposal
- User's rejection (their words, not your interpretation)
- Constraint: the previous answer was wrong/insufficient because [X], find a different angle

### Step 3: Validate

Dispatch `og-gang` with the new proposal. Include the rejection context so og-gang knows what was already tried.

### Step 4: Present Revised

If validated, present with: "Revised after your feedback. Previous approach failed because [X]. New direction: [Y]."

If still failing validation after 2 loops, be honest: "I've tried [N] angles and og-gang keeps finding holes. Here's what I have. Want to give me a hint, or should I try a completely different framing?"

## Context Passing Rules

Every sub-agent dispatch must include:
- The bug statement (one sentence, from Phase 0)
- Current phase and what's been established
- Evidence collected so far (summarized, not raw dumps)
- What's been tried and rejected (to prevent loops)

Never pass raw file contents to sub-agents. Summarize what matters. Quote only the specific lines relevant to the question.

## Loop Limits

| Trigger | Max iterations | On max reached |
|---------|---------------|----------------|
| "grill more on your own" | 3 | Present partial findings with uncertainty markers |
| "open question" | 3 | Present best candidate with "low confidence" label |
| "think more" | 2 | Admit stuck, ask user for direction |

These limits prevent infinite token burn. Reaching the limit is not failure. It means the problem needs human insight at this point.
