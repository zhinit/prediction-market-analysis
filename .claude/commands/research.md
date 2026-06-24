# research

Research a topic and fold it into the wiki. Searches the web and arXiv for
primary sources, archives them into `raw/` (immutable), and ingests them into
`wiki/`.

Usage: `/research <topic or question>`

## 1. Discover sources

Search for high-quality primary sources across these classes:

1. **The open web** — blogs, guides, production write-ups, GitHub repos.
2. **arXiv** — academic papers for theory (market microstructure, pricing
   models, probability, statistics, prediction markets).

**Programming topics** — when the topic is a programming framework, language,
or library, pull in a large amount of official documentation. The goal is to
learn the current, idiomatic API surface so that code written in this project
uses modern, up-to-date syntax. Fetch multiple doc pages (guides, API
references, tutorials, migration notes) — not just a single overview. Check
GitHub first — if the docs live in a repo (e.g. a `docs/` folder or markdown
files), pull from there directly. Raw markdown from GitHub is much more
efficient than fetching HTML and converting.

Prefer primary sources over aggregators. Present the candidate sources to the
user as a list with titles and URLs, then wait for approval — unless the user
says to grab them all.

## 2. Archive raw sources

For each approved source:

1. Fetch the full raw HTML and save it to `raw/html/<descriptive-name>.html`.
2. Convert it to faithful markdown and save it to `raw/md/<same-name>.md`.

Use a descriptive, lowercase-hyphenated filename (e.g.
`kalshi-fee-schedule-2026.md`). The markdown in `raw/md/` is the source of
truth: it must be the **full source content as-is**, not a summary or
interpretation.

Files in `raw/html/` and `raw/md/` are **immutable** once saved — never modify
them. If a source can't be fetched (paywall, 429, etc.), note it and move on.

## 3. Ingest into the wiki

1. Read the full source document(s).
2. Discuss key takeaways with the user before writing anything.
3. Create a summary page in `wiki/` named after the source.
4. Create or update concept pages for each major idea or entity.
5. Add wiki-links (`[[page-name]]`) to connect related pages.
6. Update `wiki/index.md` with new pages and one-line descriptions.
7. Append an entry to `wiki/log.md` with the date, source name, and what changed.

A single source may touch 10–15 wiki pages. That is normal.

Follow the **page format** and **citation rules** in CLAUDE.md: every factual
claim cites its source file `(source: filename.md)`, and contradictions between
sources are noted explicitly. Never fabricate market data, endpoints, fees, or
regulatory claims — if it's not in a source, it's not known.
