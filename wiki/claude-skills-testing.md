# Claude Skills Testing

How to test, evaluate, and iterate on [[claude-skills|skills]].

## Testing Levels

Three levels of rigor (source: anthropic-complete-guide-building-skills.md):

1. **Manual testing in Claude.ai** -- Run queries and observe. Fast iteration, no setup.
2. **Scripted testing in Claude Code** -- Automate validation across changes using skill-creator plugin.
3. **Programmatic testing via Skills API** -- Build evaluation suites against defined test sets.

Pro tip: iterate on a single challenging task until Claude succeeds, then extract the winning approach into a skill. In-context learning provides faster signal than broad testing (source: anthropic-complete-guide-building-skills.md).

## What to Test

### 1. Triggering

Does the skill load at the right times? (source: anthropic-complete-guide-building-skills.md)

- Triggers on obvious tasks
- Triggers on paraphrased requests
- Does NOT trigger on unrelated topics

Example test suite:
```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet"
```

### 2. Functional Output

Does the skill produce correct results?

- Valid outputs generated
- API/tool calls succeed
- Error handling works
- Edge cases covered

### 3. Performance Comparison

Does the skill improve results vs baseline?

Compare with vs without skill:
```
Without skill:                    With skill:
- User provides instructions      - Automatic workflow execution
- 15 back-and-forth messages      - 2 clarifying questions only
- 3 failed API calls              - 0 failed API calls
- 12,000 tokens consumed          - 6,000 tokens consumed
```

(source: anthropic-complete-guide-building-skills.md)

## The skill-creator Plugin

Install in Claude Code (source: claude-code-skills-docs.md):
```
/plugin install skill-creator@claude-plugins-official
```

Then `/reload-plugins` and ask Claude to evaluate a skill.

The plugin automates:
- **Test cases**: stored in `evals/evals.json` inside the skill directory
- **Isolated runs**: subagent per test case with clean context, recording tokens and duration
- **Grading**: assertions checked against output, pass/fail with evidence to `grading.json`
- **Benchmark**: aggregates pass rate, time, tokens for with-skill vs without-skill into `benchmark.json`
- **Version comparison**: blind A/B between two versions
- **Description tuning**: measures trigger hit rate, proposes description edits
- **Review viewer**: HTML report for qualitative inspection

### The Evaluation Loop

1. Define skill purpose
2. Draft implementation
3. Create 2-3 test prompts (evals/evals.json)
4. Run with-skill and baseline in parallel subagents
5. Grade with quantitative assertions
6. Aggregate benchmarks
7. Review qualitatively
8. Iterate (source: skill-creator-skill.md)

## Iteration Signals

### Undertriggering

Symptoms: skill doesn't load when it should, users manually enabling it, support questions about when to use it.

Fix: add more detail and nuance to the description, especially keywords and trigger phrases (source: anthropic-complete-guide-building-skills.md).

### Overtriggering

Symptoms: skill loads for irrelevant queries, users disabling it, confusion about purpose.

Fix: add negative triggers ("Do NOT use for simple data exploration"), be more specific, clarify scope (source: anthropic-complete-guide-building-skills.md).

### Instructions Not Followed

Common causes (source: anthropic-complete-guide-building-skills.md):
- **Too verbose**: keep concise, use bullet points and numbered lists
- **Instructions buried**: put critical instructions at the top with `##` headers
- **Ambiguous language**: "Make sure to validate things properly" -> specify exactly what to validate
- **Context too large**: move detailed docs to `references/`, keep SKILL.md under 5,000 words (1,500-2,000 ideal) (source: skill-development-plugin-skill.md)

Advanced technique: for critical validations, bundle a deterministic script rather than relying on language instructions. Code is deterministic; language interpretation is not.

## Debug Tips

- Ask Claude: "When would you use the [skill name] skill?" -- it will quote the description back, revealing what's missing
- Test in a fresh session (leftover context from authoring masks gaps)
- Run with `--debug` to see frontmatter parse errors
- Check `/doctor` to see if skill descriptions are being truncated by the budget

(source: claude-code-skills-docs.md, anthropic-complete-guide-building-skills.md)

## Success Criteria

**Quantitative** (source: anthropic-complete-guide-building-skills.md):
- Skill triggers on 90% of relevant queries
- Completes workflow in X tool calls (compare with/without)
- 0 failed API calls per workflow

**Qualitative**:
- Users don't need to prompt Claude about next steps
- Workflows complete without user correction
- Consistent results across sessions

## See Also

- [[claude-skills]] — what skills are, structure, where they live
- [[claude-skills-writing-guide]] — how to write a good skill
- [[claude-skills-frontmatter]] — complete frontmatter reference
