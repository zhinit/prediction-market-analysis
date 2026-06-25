# Presentable Data Analysis

Hub page for making data analysis portfolio-ready: clear, honest, and compelling.

This page synthesizes principles from data visualization theory, notebook presentation research, and portfolio design into a practical framework. Sub-pages cover each area in depth.

## The Core Loop

Presentable analysis follows a three-part structure regardless of format:

1. **Question** — state the problem, the audience, and why it matters
2. **Method** — show the work transparently (data, cleaning, analysis steps)
3. **Answer** — deliver the insight with supporting evidence, then state what to do with it

This maps to Knaflic's narrative arc (context → data → insight → action) and the PLOS paper's computational narrative (beginning, middle, end) (source: storytelling-with-data-knaflic.md, plos-ten-rules-jupyter-notebooks.md).

## Five Principles

### 1. Start with the question, not the chart

The analytical task determines the visual form. Trend analysis needs a line chart; category comparison needs a bar chart; distribution needs a histogram. Picking a chart type first and fitting data into it inverts the logic (source: tableau-chart-type-selection.md).

See [[chart-selection]] for the full question-to-chart mapping.

### 2. Maximize data, minimize everything else

Tufte's data-ink ratio: every visual element must carry information. Remove gridlines, decorations, 3D effects, backgrounds, and unnecessary labels. What remains should change when the data changes (source: tufte-visualization-principles.md).

Knaflic's version: every unnecessary element adds cognitive load. "Simple beats sexy" (source: storytelling-with-data-knaflic.md).

See [[data-visualization-principles]] for the complete framework.

### 3. Text does most of the work

Research on Scientific American visualizations found that two-thirds of messages changed when text was added. Annotations, titles, axis labels, and narrative context carry more meaning than the chart alone (source: arxiv-visual-data-communication.md).

Implication: a chart without a title, clear axis labels, and a one-sentence takeaway is an incomplete chart.

See [[data-storytelling]] for the full communication framework.

### 4. Structure notebooks for humans

One analytical step per cell. Markdown headers between sections. Parameters at the top. Dependencies recorded. Designed to be read, not just run (source: plos-ten-rules-jupyter-notebooks.md).

See [[notebook-presentation]] for the ten rules.

### 5. Show fewer things, better

The best portfolios show 3–5 well-presented analyses, not 20 sloppy ones. Each project leads with the business question, shows methodology transparently, and ends with actionable insight (source: careerfoundry-portfolio-examples.md).

See [[portfolio-presentation]] for examples and patterns.

## Related Pages

- [[data-visualization-principles]] — Tufte + Knaflic + JHU consolidated
- [[chart-selection]] — question-driven chart picking
- [[notebook-presentation]] — PLOS ten rules for notebook structure
- [[data-storytelling]] — narrative structure and communication
- [[portfolio-presentation]] — portfolio design patterns
- [[eda-workflow]] — the analysis process itself
- [[eda-techniques]] — catalog of graphical and quantitative methods
