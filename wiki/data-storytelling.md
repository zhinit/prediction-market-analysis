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

## Communication Factors

Four factors affect how data science results are communicated (from research on data science intermediate communication):

1. **Goals** — what you want the audience to understand or do
2. **Artifacts** — what you're sharing (chart, table, notebook, dashboard)
3. **Mode** — how you're sharing (presentation, document, interactive)
4. **Audience** — who's receiving it and what they know

Breakdowns occur when analytical decisions, assumptions, and uncertainties are not clearly communicated.

## Practical Rules

1. **Title every chart** with what it shows, not what it is ("Sales declined 12% in Q3" not "Q3 Sales Chart")
2. **Annotate the insight** directly on the visualization when possible
3. **State limitations** explicitly — what the data can't tell you
4. **One chart, one message** — if a chart makes two points, split it into two charts
5. **Lead with the conclusion** — don't make the reader work to find the answer

## Related Pages

- [[data-visualization-principles]] — the design theory behind charts
- [[chart-selection]] — picking the right visual
- [[notebook-presentation]] — structuring notebooks as narratives
- [[presentable-data-analysis]] — hub page
- [[portfolio-presentation]] — applying storytelling to portfolio work
