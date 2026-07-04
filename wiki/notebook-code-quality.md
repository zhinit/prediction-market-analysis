# Notebook Code Quality

How to keep the code inside computational notebooks clean, testable, and free of bloat. Complements [[notebook-presentation]], which covers narrative structure and sharing; this page covers the code itself: modularization, packaging, testing, linting, refactoring, and the empirical evidence for why these practices matter.

## Empirical state of notebook quality

A study of 1.4 million Jupyter notebooks from GitHub (1,159,166 unique notebooks from 264,023 repositories after removing duplicates) measured how notebooks are actually written and whether they reproduce (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md). Of 863,878 attempted executions of valid notebooks, only 24.11% executed without errors, and only 4.03% produced the same results as stored in the notebook. Other findings from the same study:

- 30.93% of notebooks have no markdown cell at all; where markdown exists, it concentrates at the beginning of the notebook, and the bottom of notebooks has fewer markdown cells and fewer executed code cells (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md).
- Among notebooks with an unambiguous execution order, 36.36% have cells out of order, and 21.11% of executed notebooks had non-executed code cells (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md).
- Only 1.54% of valid Python notebooks import a known testing module (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md).
- Common failure causes in the reproducibility runs were undeclared or missing dependencies and file-access errors (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md).

Follow-up research confirms that notebook practitioners are generally aware of published best practices but often do not apply them, deeming them unfeasible or counterproductive in context, mainly for lack of time and tool support (source: arxiv-notebook-quality-exploration-to-production.md). The same research program collected a validated catalog of 17 best practices for collaborative notebook use and built a notebook linter (pynblint) to check compliance (source: arxiv-notebook-quality-exploration-to-production.md).

## Eight practices from the large-scale study

Based on its findings, the GitHub study proposes eight best practices (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md):

1. Use short titles with a restricted charset (A-Z a-z 0-9 . -) for notebook files; put complex titles in markdown headings inside the body.
2. Pay attention to the bottom of the notebook — check whether it needs descriptive markdown or has code cells to execute or remove.
3. Abstract code into functions, classes, and modules, and test them.
4. Declare dependencies in requirement files and pin the versions of all packages.
5. Test dependencies in a clean environment to check that all of them are declared.
6. Put imports at the beginning of the notebook.
7. Use relative paths for accessing data in the repository.
8. Re-run notebooks top to bottom before committing, to restore execution counters and minimize hidden states and out-of-order cells.

## Keep logic out of the notebook

A clean notebook is effectively a series of lines of code with few to no control structures (source: ploomber-clean-jupyter-notebooks.md). Two kinds of code should be extracted from cells into functions: snippets called more than once, and snippets with control structures — a single simple `if` or `for` may stay inline, but nested or multi-structure code should become a function even if used only once (source: ploomber-clean-jupyter-notebooks.md). Cyclomatic complexity can be measured on notebooks by converting them to scripts and running the mccabe checker, flagging any section with complexity of 3 or higher (source: ploomber-clean-jupyter-notebooks.md).

Function and class definitions belong in separate `.py` files imported by the notebook, not in the notebook itself — defining them in cells makes them unimportable elsewhere and harder to reason about (source: ploomber-clean-jupyter-notebooks.md). Extracting repeated code into named functions reduces duplication, promotes reuse, makes the code testable, and makes it self-documenting (source: domino-notebook-structure-coding-style-refactoring.md).

To import local modules without `sys.path.append` hacks (which break when files move), package the project with a `setup.py` and install it editable (`pip install --editable .`), after which any module in the package is importable from any directory (source: ploomber-clean-jupyter-notebooks.md). Add `%load_ext autoreload` / `%autoreload 2` at the top of the notebook so edits to external modules are picked up without kernel restarts (source: ploomber-clean-jupyter-notebooks.md).

## Section structure

One published per-notebook skeleton: import statements, then configuration (e.g., database connections), then data loading, then content — with each content section consisting of a markdown header, a one-to-two-line description, a few takeaway bullets, and finally the code (source: ploomber-clean-jupyter-notebooks.md).

Notebook-level structure can follow the model of a scientific paper: title, preamble, table of contents, sections in a deliberate order (e.g., exploration and data preparation before model training and evaluation), a conclusion, and references (source: domino-notebook-structure-coding-style-refactoring.md). Where there is no single goal, split the work into multiple notebooks with a master document linking to each (source: domino-notebook-structure-coding-style-refactoring.md).

## Write shorter notebooks

Re-using variable names across a long notebook (e.g., assigning `df` twice, 100 cells apart) is a significant source of errors; the longer the notebook, the higher the chance of such side effects (source: ploomber-clean-jupyter-notebooks.md). Published rules of thumb for splitting: different datasets go in different notebooks; joining datasets starts a new notebook; data cleaning and plotting (or feature generation) get separate notebooks (source: ploomber-clean-jupyter-notebooks.md). Split notebooks connect by having each one serialize key intermediate results to disk for the next to load (source: arxiv-ten-simple-rules-reproducible-jupyter.md).

Mutable data structures are a related hazard: a mutation hidden inside a function defined dozens of cells earlier (or in another file) makes the state of a DataFrame unpredictable. Two documented mitigations are pure functions that copy their input (at a memory cost) or keeping all mutations of a given column explicit and in one place (source: ploomber-clean-jupyter-notebooks.md).

## Testing

Manual interactive testing of processing functions wastes time and misses cases; the documented alternative is writing the same checks as unit tests (e.g., pytest with parametrized input/expected pairs) that run on every code change, testing at the smallest data unit possible — value level before column level before whole-DataFrame level (source: ploomber-clean-jupyter-notebooks.md). Notebook code moved into modules can be covered by standard frameworks (`unittest`, pytest); assertions catch conditions that should never happen, while comprehensive test cases define the function's contract (source: domino-notebook-structure-coding-style-refactoring.md).

## Linting and formatting

Linters catch leftovers that refactoring misses, such as unused imports (source: ploomber-clean-jupyter-notebooks.md). One documented workflow converts notebooks to `.py` files with jupytext (which still open as notebooks in Jupyter), lints them with flake8 in a standard editor, and optionally pairs the `.py` with an `.ipynb` to preserve outputs; auto-formatters such as black then fix layout automatically (source: ploomber-clean-jupyter-notebooks.md). The pycodestyle extension can flag PEP-8 violations directly inside a notebook via a cell magic (source: domino-notebook-structure-coding-style-refactoring.md). PEP-8 conventions — meaningful names, import grouping with one import per line and no wildcards, sparing blank lines — apply to notebook code as to any Python (source: domino-notebook-structure-coding-style-refactoring.md).

## The refactoring cycle

A documented process for cleaning up an existing notebook (source: domino-notebook-structure-coding-style-refactoring.md):

1. Restart the kernel and run all cells — refactoring only starts from a working, hidden-state-free notebook.
2. Make a copy of the notebook.
3. Convert the notebook to a script with `jupyter nbconvert --to script`.
4. Tidy up: remove irrelevant outputs, transform cells to functions.
5. Refactor: pick a piece of code to extract, write a unit test that defines it, move it into a module, confirm tests pass, replace the notebook code with a call to the function.
6. Repeat step 5 as needed, then restart the kernel and re-run all cells to confirm the final notebook executes properly.

The result is a concise, self-documenting notebook plus a standalone module reusable across other notebooks and scripts (source: domino-notebook-structure-coding-style-refactoring.md).

## Dependencies

Every third-party package belongs in a `requirements.txt` (or `environment.yml`), with an exhaustive pinned lockfile generated via `pip freeze` so the notebook still runs when re-executed later; work happens in a virtual environment built only from these files (source: ploomber-clean-jupyter-notebooks.md). The GitHub study found `requirements.txt` files failed less often than other dependency formats during reproduction attempts (source: pimentel-2019-quality-reproducibility-jupyter-notebooks.md). Critical dependency versions can additionally be printed at the bottom of the notebook itself with a tool such as watermark (source: arxiv-ten-simple-rules-reproducible-jupyter.md).

## Related pages

- [[notebook-presentation]] — narrative structure, the PLOS ten rules, output formats
- [[presentable-data-analysis]] — hub page
- [[eda-workflow]] — the analysis process these notebooks document
