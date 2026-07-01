# Notebook Presentation

How to structure computational notebooks (Jupyter, Quarto, etc.) so they are readable, reproducible, and presentable. Based primarily on the PLOS Computational Biology ten rules (source: plos-ten-rules-jupyter-notebooks.md) and the Jupyter reproducibility guide (source: jupyter-guide-reproducible-research.md).

## The Ten Rules

### Phase 1: Organize and Document (Rules 1–3)

**Rule 1: Tell a story for an audience.** Create a computational narrative with beginning, middle, and end. Your most likely reader is your future self. Tailor the level of explanation to who will read it.

**Rule 2: Document the process, not just results.** Record explorations, dead ends, and reasoning in real-time. Include metadata: authorship, dates, contact information. Write narrative markdown between code cells — code comments cannot replace scientific narrative.

**Rule 3: Use cell divisions to make steps clear.** One meaningful analytical step per cell. Keep cells under 100 lines. Use descriptive markdown headers. Split long analyses into linked notebooks.

### Phase 2: Code Quality (Rules 4–7)

**Rule 4: Modularize code.** Extract reusable code into functions and packages. Don't copy-paste cells. This supports maintenance, debugging, and interactive parameter exploration.

**Rule 5: Record dependencies.** Use package managers (pip, Conda) to pin versions. Include `requirements.txt` or `environment.yml`. Optionally display versions in-notebook using watermark or similar.

**Rule 6: Use version control.** Git for tracking changes and bug history. Use notebook-specific diffing tools (nbdime) since notebook JSON is hard to diff.

**Rule 7: Build a pipeline.** Place configurable parameters at the top of the notebook. Automate data cleaning. Use tools like papermill for parameterized execution. Integrate continuous testing.

### Phase 3: Share and Explore (Rules 8–10)

**Rule 8: Share and explain your data.** Make data publicly available (Zenodo, Figshare) or provide tiered access for sensitive/large datasets. Document upstream processing. Provide DOIs.

**Rule 9: Design notebooks to be read, run, and explored.** Provide:
- Static versions (HTML, PDF)
- Online viewing (Nbviewer)
- Cloud execution (Binder)
- Interactive widgets (ipywidgets) for parameter exploration

**Rule 10: Advocate for open research.** Promote reproducible practices. Collaborative notebook review. Transparent computational workflows.

Project-specific choices are recorded in `docs/project-conventions.md`.

## Output Formats

Ways to deliver a notebook beyond the raw `.ipynb` (source: plos-ten-rules-jupyter-notebooks.md):

| Format | Use Case |
|--------|----------|
| Static HTML / PDF | Readable versions for sharing |
| Nbviewer | Online viewing |
| Binder | Cloud execution — letting others run your analysis |
| ipywidgets | Interactive parameter exploration |

## Related Pages

- [[presentable-data-analysis]] — hub page
- [[data-visualization-principles]] — chart design within notebooks
- [[data-storytelling]] — narrative structure
- [[eda-workflow]] — the analysis process
