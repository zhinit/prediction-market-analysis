# Claude Code Learning Style

The Learning output style is a built-in Claude Code mode for learn-by-doing coding. Claude shares educational "Insights" while working and asks you to contribute code yourself by inserting `TODO(human)` markers (source: claude-code-output-styles.md).

## What It Does

- Shares insights about implementation choices and codebase patterns as it works
- Inserts `TODO(human)` markers at strategic points for you to implement
- Produces longer responses than the Default style (more educational context)

## Setup

Run `/config` and select **Output style** > **Learning**.

Or edit `.claude/settings.local.json` directly:

```json
{
  "outputStyle": "Learning"
}
```

Changes take effect after `/clear` or a new session (source: claude-code-output-styles.md).

## Other Built-in Styles

| Style | Behavior |
|:------|:---------|
| Default | Standard software engineering assistant |
| Proactive | Executes immediately, makes assumptions, prefers action over planning |
| Explanatory | Shares educational insights but does all the coding itself |
| Learning | Shares insights AND asks you to write code (`TODO(human)`) |

The difference between Explanatory and Learning: Explanatory teaches while doing the work for you. Learning teaches while making you do part of the work (source: claude-code-output-styles.md).

## Custom Output Styles

You can create custom teaching styles as markdown files in:
- `~/.claude/output-styles` (user-level)
- `.claude/output-styles` (project-level)

Frontmatter fields: `name`, `description`, `keep-coding-instructions` (boolean — set true to retain Claude Code's engineering instructions alongside your custom teaching instructions) (source: claude-code-output-styles.md).

## See Also

- [[claude-learning-mode]] — the Socratic tutoring mode in claude.com
- [[claude-as-teacher]] — general techniques for learning with Claude
