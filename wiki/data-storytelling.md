# Data Storytelling

How to communicate data analysis results so they land with an audience. Covers narrative structure, the role of text in visualization, and audience awareness.

## Text Carries the Message

Research analyzing 171 visualizations in Scientific American found that two-thirds of reader-articulated messages changed when textual elements (titles, annotations, captions) were added to charts. Text reshapes interpretation through three mechanisms (source: arxiv-visual-data-communication.md):

- **Abstraction** — moves readers from detailed observations to higher-level patterns
- **Explanatory reasoning** — clarifies relationships and mechanisms
- **Recontextualization** — connects the visualization to broader context

Implication: a chart without text is an incomplete communication. Every visualization needs at minimum:
- A descriptive title (what this shows)
- Labeled axes (with units)
- A takeaway annotation (what the reader should conclude)

## The Message Gap

The same research found that intended messages (what the creator planned) and interpreted messages (what readers took away) "only partially aligned." This reflects different emphasis rather than misunderstanding. Messages vary across six dimensions (source: arxiv-visual-data-communication.md):

| Dimension | Range |
|-----------|-------|
| Granularity | General ↔ Specific |
| Structure | Simple (one insight) ↔ Additive (multiple) |
| Articulation | Example-based, hedged, chart-referential |
| Relations | Comparative ↔ Causal/associative |
| Inference | Descriptive ↔ Interpretative ↔ Evaluative |
| Content | Geospatial, temporal, change-oriented |

The lesson: be explicit about what you want the reader to take away. Don't assume the chart speaks for itself.

## Narrative Structure

Every analysis presentation follows a three-act structure (source: storytelling-with-data-knaflic.md, plos-ten-rules-jupyter-notebooks.md):

### Act 1: Context
- What is the question?
- Who cares and why?
- What would change if we had the answer?

### Act 2: Data
- What data did we use?
- How did we clean/transform it?
- What does the analysis show? (charts, tables, statistics)

### Act 3: Insight → Action
- What does this mean?
- What should the audience do differently?
- What are the limitations?

## Audience Awareness

Tailor complexity to who's reading (source: tableau-visual-best-practices.md):

- **Executive/general audience** — aggregated KPIs, clear headlines, minimal methodology
- **Technical peers** — show the work, include methodology, link to code
- **Future self** — document reasoning, dead ends, and decisions in real-time

The PLOS paper's observation: "your future self will likely be your primary reader" (source: plos-ten-rules-jupyter-notebooks.md).

## Practical Rules

1. **Title every chart.** Effective dashboards incorporate titles, captions, units, and commentary (source: tableau-visual-best-practices.md).
2. **Don't assume the chart speaks for itself.** Textual elements reshape what readers take away, so make the intended message explicit in the text around the chart (source: arxiv-visual-data-communication.md).
3. **Plan the message early.** Producers who plan messages early use them as central design guides (source: arxiv-visual-data-communication.md).

## Related Pages

- [[data-visualization-principles]] — the design theory behind charts
- [[chart-selection]] — picking the right visual
- [[notebook-presentation]] — structuring notebooks as narratives
- [[presentable-data-analysis]] — hub page
- [[portfolio-presentation]] — applying storytelling to portfolio work
