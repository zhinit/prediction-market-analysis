# Claude Skills

A skill is a folder containing a `SKILL.md` file with YAML frontmatter and markdown instructions. It teaches Claude how to handle a specific task or workflow. Unlike CLAUDE.md content, a skill's body loads only when used, so long reference material costs almost nothing until needed (source: claude-code-skills-docs.md).

Skills follow the Agent Skills open standard (agentskills.io) and work across Claude.ai, Claude Code, and the API (source: anthropic-complete-guide-building-skills.md).

## When to Create a Skill

Create a skill when you keep pasting the same instructions into chat, or when a CLAUDE.md section has grown into a procedure rather than a fact (source: claude-code-skills-docs.md).

Rule of thumb: have you done this task at least 5 times? Will you do it at least 10 more? If yes, a skill makes sense (source: claude-blog-create-skills.md).

## Structure

```
my-skill/
├── SKILL.md           # Required — main instructions
├── scripts/           # Optional — executable code (Python, Bash)
├── references/        # Optional — documentation loaded as needed
└── assets/            # Optional — templates, fonts, icons
```

The file must be exactly `SKILL.md` (case-sensitive). The folder name must be kebab-case (no spaces, underscores, or capitals). No README.md inside the skill folder (source: anthropic-complete-guide-building-skills.md).

## Where Skills Live

| Scope      | Path                                           | Applies to              |
|:-----------|:-----------------------------------------------|:------------------------|
| Enterprise | Managed settings directory                     | All org users           |
| Personal   | `~/.claude/skills/<name>/SKILL.md`             | All your projects       |
| Project    | `.claude/skills/<name>/SKILL.md`               | This project only       |
| Plugin     | `<plugin>/skills/<name>/SKILL.md`              | Where plugin is enabled |

(source: claude-code-skills-docs.md)

Enterprise overrides personal, personal overrides project. Any level overrides a bundled skill with the same name. Nested `.claude/skills/` directories support monorepos with directory-qualified names like `apps/web:deploy` (source: claude-code-skills-docs.md).

## Progressive Disclosure

Skills use a three-level context system (source: anthropic-complete-guide-building-skills.md):

1. **Frontmatter** (always loaded): ~100 words. Enough for Claude to decide when to use the skill.
2. **SKILL.md body** (loaded on trigger): Full instructions. Keep under 5,000 words (1,500-2,000 ideal) (source: skill-development-plugin-skill.md).
3. **Bundled files** (loaded as needed): Reference docs, scripts, assets. Claude discovers and reads them on demand.

## Content Lifecycle

When invoked, rendered SKILL.md enters the conversation as a message and stays for the rest of the session. After auto-compaction, the first 5,000 tokens of each skill are re-attached (combined budget: 25,000 tokens). Most recently invoked skills take priority (source: claude-code-skills-docs.md).

## Commands Backward Compatibility

`.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`. Existing command files keep working, but skills support additional features (supporting files, frontmatter, auto-triggering) (source: claude-code-skills-docs.md).

## Bundled Skills

Claude Code ships with: `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/run`, `/verify`, `/run-skill-generator` (source: claude-code-skills-docs.md).

## See Also

- [[claude-skills-writing-guide]] — how to write a good skill
- [[claude-skills-frontmatter]] — complete frontmatter reference
- [[claude-skills-testing]] — testing, evaluation, and iteration
