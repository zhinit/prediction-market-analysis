# Portfolio Presentation

How to present data analysis projects as portfolio-ready work. Based on analysis of nine effective data analytics portfolios (source: careerfoundry-portfolio-examples.md).

## What Makes a Portfolio Project Work

Every effective portfolio project has five components:

1. **A business question** — not "I analyzed this dataset" but "I investigated whether X"
2. **A real dataset** — with documented source and any cleaning steps
3. **Analysis with visualizations** — charts that support the narrative
4. **Written interpretation** — what the results mean, not just what they show
5. **Clear structure** — navigable, with the important stuff up front

The README/introduction is as important as the code. It's what people read first (source: careerfoundry-portfolio-examples.md).

## Portfolio Patterns That Work

From the nine examples studied:

### Selective showcase (Harrison Jansma)
Show your best 3–5 projects, not everything you've ever done. Provide an option to read more for those who want depth. Quality over quantity.

### Values-aligned storytelling (Naledi Hollbruegge)
Connect projects to what you care about. Combine technical skill demonstration with genuine interest in the domain.

### Interactive results (Ger Inberg)
When possible, make results explorable — interactive visualizations, apps, or dashboards. An interactive chart communicates more than a static screenshot.

### Notebooks as presentation (James Le)
Jupyter notebooks with clear narrative flow, polished visualizations, and compelling visual frontends. Hide technical implementation behind readable results.

### Minimal and clear (Anubhav Gupta)
Single-page portfolio emphasizing clarity. "Less is sometimes more" — restraint signals confidence.

### Blog-based journey (Jessie-Raye Bauer)
Present analysis as a narrative readers can follow. Blogs enable deeper engagement than project listings.

## Anti-Patterns

- Listing skills without demonstrating them
- Projects without context (what was the question?)
- Raw notebooks with no narrative markdown
- Too many projects, none well-presented
- Charts without titles, labels, or interpretation
- No clear structure or navigation

## Structure for This Project

Given that pma is a portfolio-ready analysis project, each analysis should follow this template:

```
Title: [What we investigated]
Question: [The specific question, stated plainly]
Data: [Source, size, time range, any cleaning notes]
Method: [What we did, briefly]
Key Findings: [2-3 bullet points with supporting charts]
Limitations: [What the data can't tell us]
```

The analysis/ directory holds the work. Each analysis is a self-contained notebook or set of notebooks that runs top-to-bottom.

## Related Pages

- [[presentable-data-analysis]] — hub page
- [[notebook-presentation]] — structuring individual notebooks
- [[data-storytelling]] — narrative techniques
- [[data-visualization-principles]] — chart design
