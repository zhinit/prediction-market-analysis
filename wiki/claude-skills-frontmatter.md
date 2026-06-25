# Claude Skills Frontmatter Reference

Complete reference for YAML frontmatter fields in [[claude-skills|SKILL.md]] files. All fields are optional; only `description` is recommended (source: claude-code-skills-docs.md).

## Format

```yaml
---
name: my-skill
description: What this skill does. Use when user asks to [specific phrases].
---

Your skill instructions here...
```

Frontmatter must be between `---` markers. Missing delimiters or unclosed quotes cause parsing failure (Claude Code loads the body with empty metadata) (source: anthropic-complete-guide-building-skills.md).

## Fields

| Field                      | Purpose                                                                           |
|:---------------------------|:----------------------------------------------------------------------------------|
| `name`                     | Display name. Defaults to directory name. Kebab-case, no spaces/capitals.         |
| `description`              | What skill does + when to use it. Truncated at 1,536 chars with when_to_use.      |
| `when_to_use`              | Additional trigger context. Appended to description, shares the 1,536-char cap.   |
| `argument-hint`            | Autocomplete hint, e.g. `[issue-number]` or `[filename] [format]`.                |
| `arguments`                | Named positional args for `$name` substitution. Space-separated string or list.   |
| `disable-model-invocation` | `true` = only user can invoke. Hides from Claude's context entirely.              |
| `user-invocable`           | `false` = hidden from `/` menu. Only Claude can invoke.                           |
| `allowed-tools`            | Tools Claude can use without permission while skill is active.                    |
| `disallowed-tools`         | Tools removed from Claude's pool while skill is active. Clears on next message.   |
| `model`                    | Model override for the current turn. Not saved to settings.                       |
| `effort`                   | Effort level override: low, medium, high, xhigh, max.                            |
| `context`                  | `fork` to run in an isolated subagent context.                                    |
| `agent`                    | Subagent type with `context: fork` (Explore, Plan, general-purpose, or custom).   |
| `hooks`                    | Hooks scoped to this skill's lifecycle.                                           |
| `paths`                    | Glob patterns limiting when skill auto-activates by file path.                    |
| `shell`                    | Shell for `!`command`` blocks: `bash` (default) or `powershell`.                  |

(source: claude-code-skills-docs.md)

## Optional Metadata Fields

| Field           | Purpose                                           |
|:----------------|:--------------------------------------------------|
| `license`       | MIT, Apache-2.0, etc. (for open source skills)    |
| `compatibility` | Environment requirements (1-500 chars)             |
| `metadata`      | Custom key-value pairs (author, version, etc.)     |

(source: anthropic-complete-guide-building-skills.md)

## Security Restrictions

- No XML angle brackets (`<` `>`) in frontmatter -- could inject into system prompt
- No "claude" or "anthropic" in the name field

(source: anthropic-complete-guide-building-skills.md)

## String Substitutions

Available in skill content (source: claude-code-skills-docs.md):

| Variable               | Description                                           |
|:-----------------------|:------------------------------------------------------|
| `$ARGUMENTS`           | All arguments passed when invoking                    |
| `$ARGUMENTS[N]` / `$N`| Specific argument by 0-based index                    |
| `$name`                | Named argument from `arguments` list                  |
| `${CLAUDE_SESSION_ID}` | Current session ID                                    |
| `${CLAUDE_EFFORT}`     | Current effort level (low/medium/high/xhigh/max)      |
| `${CLAUDE_SKILL_DIR}`  | Directory containing the SKILL.md file                |

Escape literal `$` before digits or argument names with backslash: `\$1.00`.

## Invocation Control

| Setting                          | User can invoke | Claude can invoke | Description loaded |
|:---------------------------------|:----------------|:------------------|:-------------------|
| (default)                        | Yes             | Yes               | Yes                |
| `disable-model-invocation: true` | Yes             | No                | No                 |
| `user-invocable: false`          | No              | Yes               | Yes                |

(source: claude-code-skills-docs.md)

## Command Name Resolution

The command you type comes from the file/directory location, not the `name` field (except for plugin-root SKILL.md):

- `.claude/skills/deploy-staging/SKILL.md` -> `/deploy-staging`
- `.claude/commands/deploy.md` -> `/deploy`
- `my-plugin/skills/review/SKILL.md` -> `/my-plugin:review`

(source: claude-code-skills-docs.md)

## See Also

- [[claude-skills]] — what skills are, structure, where they live
- [[claude-skills-writing-guide]] — how to write a good skill
- [[claude-skills-testing]] — testing, evaluation, and iteration
