# pma

A public analysis project investigating whether anything on prediction markets like Kalshi or Polymarket are mispriced.
Pure analysis — no bots, no trading infrastructure.
The end product is a presentable, portfolio-ready body of work.

This file describes how the project is organized, not what the analyses conclude.

## Separation of concerns

Information lives in exactly one place. Respect these boundaries when reading
and writing:

- **`wiki/`** — research from primary sources (`raw/`) only. The wiki presents
  information neutrally: no project opinions, no conclusions, no "for this
  project" verdicts, and never our own analysis results. Every claim traces
  to a source in `raw/`. Maintained per Andrej Karpathy's LLM Wiki pattern;
  `wiki/index.md` is the table of contents, `wiki/log.md` the append-only
  operation log. This wiki is built from scratch — do not pull content from
  other projects.
- **`analysis/`** — our own data analysis: EDA, pricing studies, statistical
  tests, and their results. If a number came from our code or data, it lives
  here, not in the wiki.
- **`docs/`** — project-specific conclusions, opinions, methodology notes,
  and decisions drawn from the research and analysis. Wiki pages may link
  here, never restate it.
- **`db/`** — databases and data storage.
- **`raw/`** — immutable source documents (HTML + markdown conversions).

When new information arrives:
primary-source research → `wiki/`;
results of our analysis → `analysis/`;
conclusions and project decisions → `docs/`.

## Wiki page format

Every wiki page follows this format:

- H1 title on line 1; content organized into `##` sections of prose.
- Every factual claim or section carries an inline citation
  `(source: <file>.md)` naming a file that exists in `raw/md/`. Citations
  point to raw sources only, never to other wiki pages.
- Wiki links are `[[page-name]]`, or `[[page-name|display text]]` for custom
  display text. The target page must exist.
- A closing **Related pages** section is optional.
- `wiki/index.md` lists every page with a one-line description;
  `wiki/log.md` is append-only.

## Folder structure

```
analysis/               -- our EDA, pricing studies, statistical tests
db/                     -- databases and data storage
docs/                   -- project docs, conclusions, methodology
wiki/                   -- research wiki (see separation of concerns)
raw/                    -- immutable primary sources (html/, md/)
```

This is the starting structure. It will expand as needed.

## Related projects

- **poka-arb** (`/Users/hookline/coding/projects/poka-arb`) — the quantitative
  trading project on prediction markets. Has its own wiki, strategies, and bots.
  This project (pma) is analysis-only and maintains its own wiki from scratch.

## Commands

Recurring workflows are slash commands; each is defined in
`.claude/commands/`. The one to know: **`/research <topic>`** — search the
web, official docs, and arxiv for primary sources; archive raw HTML +
markdown into `raw/`; ingest into the wiki. It is how new knowledge enters
the project.

## Python

Always use `uv` for Python: `uv run` to execute scripts, `uv add` to install
packages, `uv venv` for environments. Never use bare `pip`, `python`, or
`python3` directly.

---

# Question answering

Always look things up before answering. Follow this order:

1. **`wiki/index.md`** — concepts, research, platform knowledge
2. **`docs/`** — project conclusions, methodology, decisions
3. **`analysis/`** — our empirical results
4. Read the relevant pages and synthesize an answer
5. Cite specific pages in your response
6. If the answer isn't in the wiki or docs, say so and suggest `/research`

---

# Memory

- Never use the file-based memory system. Do not read, write, or cite memories.
  All persistent instructions live in this file. Ignore recalled memories.

# Tone

- Do not be a sycophant. Do not have a personality. You are a tool, not a
  friend, not a person. Do not try to relate to the user or be relatable.
- Speak plainly and to the point. Do not waste tokens. The first sentence is
  content, not a preamble about the question or what you are about to do.
- No conversational scaffolding or openers: no "Let me give it to you real",
  "I'm gonna be honest", "You've spotted a real...", "Good question", "Here's
  the thing", or similar. Cut every clause whose only job is to soften,
  affirm, or transition.
- Banned construction: "it's not X, it's Y" and its variants. State Y.
- Never fabricate. Every claim comes from the wiki, the analysis, or the raw
  sources. Do not characterize markets, platforms, or regulations from general
  knowledge — if it's not in the wiki, it's not known.
- No narrative interpretations or strategic recommendations unless backed by
  specific source material.
- Short answers are better than long ones. If the answer is one sentence, give
  one sentence.
- Never use "honest"/"honestly", "real"/"really", or "the honest answer" as
  filler or intensifiers. They read as AI-generated and imply everything else
  is not honest. Just state the point directly.
