# Claude Skills Writing Guide

How to write a good [[claude-skills|skill]]. Covers the description field, writing instructions, patterns, and common mistakes.

## The Description Field

The description is how Claude decides whether to load your skill. It is the most important part (source: anthropic-complete-guide-building-skills.md).

Structure: `[What it does] + [When to use it] + [Key capabilities]`

Combined `description` + `when_to_use` text is truncated at 1,536 characters (source: claude-code-skills-docs.md).

### Good Descriptions

```yaml
# Specific and actionable
description: Analyzes Figma design files and generates developer handoff
  documentation. Use when user uploads .fig files, asks for "design specs",
  "component documentation", or "design-to-code handoff".

# Includes trigger phrases
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".
```

### Bad Descriptions

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

(source: anthropic-complete-guide-building-skills.md)

## Writing Instructions

Use imperative/infinitive form (verb-first), not second person. "To accomplish X, do Y" rather than "You should do X" (source: skill-development-plugin-skill.md).

Keep SKILL.md concise. Every line is a recurring token cost once loaded (source: claude-code-skills-docs.md). State what to do, not narrate how or why.

### Be Specific and Actionable

Good: `Run python scripts/validate.py --input {filename} to check data format. If validation fails, common issues include: missing required fields, invalid date formats (use YYYY-MM-DD).`

Bad: `Validate the data before proceeding.`

(source: anthropic-complete-guide-building-skills.md)

### Reference Bundled Resources Clearly

```markdown
Before writing queries, consult `references/api-patterns.md` for:
- Rate limiting guidance
- Pagination patterns
- Error codes and handling
```

Move detailed documentation to `references/` and link to it from SKILL.md (source: anthropic-complete-guide-building-skills.md).

### Explain Why, Not Just Rules

Avoid excessive capitalization (MUSTs/NEVERs signal yellow flags). Modern LLMs understand context and respond better to principled guidance than rigid commands (source: skill-creator-skill.md).

### Include Examples

Include examples with clear Input/Output formatting. A single well-structured example is worth many lines of instruction (source: skill-creator-skill.md).

## Skill Patterns

Five patterns from early adopters and internal teams (source: anthropic-complete-guide-building-skills.md):

### 1. Sequential Workflow Orchestration
Use when: multi-step processes in a specific order. Techniques: explicit step ordering, dependencies between steps, validation at each stage, rollback for failures.

### 2. Multi-MCP Coordination
Use when: workflows span multiple services (e.g., Figma -> Drive -> Linear -> Slack). Techniques: clear phase separation, data passing between MCPs, validation before next phase.

### 3. Iterative Refinement
Use when: output quality improves with iteration (e.g., report generation). Techniques: explicit quality criteria, validation scripts, know when to stop iterating.

### 4. Context-aware Tool Selection
Use when: same outcome, different tools depending on context. Techniques: clear decision criteria, fallback options, transparency about choices.

### 5. Domain-specific Intelligence
Use when: skill adds specialized knowledge beyond tool access. Techniques: domain expertise embedded in logic, compliance before action, comprehensive documentation.

## Problem-first vs Tool-first

**Problem-first**: "I need to set up a project workspace" -- your skill orchestrates the right tool calls in sequence. Users describe outcomes.

**Tool-first**: "I have Notion MCP connected" -- your skill teaches Claude optimal workflows and best practices. Users have access; the skill provides expertise.

(source: anthropic-complete-guide-building-skills.md)

## Advanced Features

### Dynamic Context Injection

`` !`command` `` runs shell commands before Claude sees the skill content. Output replaces the placeholder (source: claude-code-skills-docs.md):

```yaml
---
description: Summarizes uncommitted changes and flags risks.
---

## Current changes
!`git diff HEAD`

## Instructions
Summarize the changes above in two or three bullet points...
```

### Running in a Subagent

Add `context: fork` to run the skill in an isolated subagent. The skill content becomes the subagent's prompt (no conversation history). Set `agent: Explore` or `agent: Plan` for specialized execution (source: claude-code-skills-docs.md).

### Controlling Invocation

`disable-model-invocation: true` -- only user can invoke (use for side-effect workflows like deploy, commit). `user-invocable: false` -- only Claude can invoke (use for background knowledge) (source: claude-code-skills-docs.md).

## Common Mistakes

1. **Weak descriptions** lacking specific trigger phrases (source: skill-development-plugin-skill.md)
2. **Excessive content** in SKILL.md without using references/ (source: skill-development-plugin-skill.md)
3. **Second-person voice** instead of imperative form (source: skill-development-plugin-skill.md)
4. **Unreferenced supporting files** -- Claude won't discover files it doesn't know about (source: skill-development-plugin-skill.md)
5. **Instructions too verbose** -- keep concise, use bullet points and numbered lists (source: anthropic-complete-guide-building-skills.md)
6. **Critical instructions buried** -- put them at the top with ## Important headers (source: anthropic-complete-guide-building-skills.md)
7. **Ambiguous language** -- "Make sure to validate things properly" vs specific validation checks (source: anthropic-complete-guide-building-skills.md)

## See Also

- [[claude-skills]] — what skills are, structure, where they live
- [[claude-skills-frontmatter]] — complete frontmatter reference
- [[claude-skills-testing]] — testing, evaluation, and iteration
