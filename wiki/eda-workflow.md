# EDA Workflow in Practice

How [[exploratory-data-analysis]] is actually done, based on an empirical study of 18 data analysts. (source: eda-interview-study-wongsuphasawat-2019.md)

## Two Goals of Exploration

### Profiling
Assessing data quality and understanding data contents: checking data types, distributions, missing values, anomalies, verifying that data matches expectations. Universal — all analysts do this across all analysis types. (source: eda-interview-study-wongsuphasawat-2019.md)

### Discovery
Gaining genuinely new insights about the domain or phenomenon. Occurs reliably only in open-ended analyses where the analyst has freedom to explore without a predetermined question. Goal-directed analyses (answering a specific question) rarely produce genuine discovery. (source: eda-interview-study-wongsuphasawat-2019.md)

Most EDA literature emphasizes discovery, but in practice profiling is more prevalent and more consistently performed. (source: eda-interview-study-wongsuphasawat-2019.md)

## The Analysis Cycle

Data analysis is an iterative cycle of five tasks, not a linear pipeline:

1. **Acquisition** — finding, collecting, integrating data sources
2. **Wrangling** — cleaning, transforming, reshaping into usable form
3. **Exploration** — examining via visualization and summary statistics
4. **Modeling** — statistical or ML models
5. **Reporting** — communicating findings

Analysts oscillate between tasks constantly. Exploration is not a discrete phase — it occurs throughout. (source: eda-interview-study-wongsuphasawat-2019.md)

## Major Challenges

### Data wrangling dominates time
Analysts often spend the majority of their analysis time wrangling and cleaning data. Tasks: combining datasets, handling volume, format conversion, managing erroneous values, missing data. (source: eda-interview-study-wongsuphasawat-2019.md)

### Variable selection
With many variables, choosing what to explore is hard. Strategies: domain knowledge, correlation analysis, dimensionality reduction. Risk of overlooking important variables when relying on intuition alone. (source: eda-interview-study-wongsuphasawat-2019.md)

### Repetitive tasks
Similar operations performed across multiple variables or datasets. Lack of automation support means redundant effort. (source: eda-interview-study-wongsuphasawat-2019.md)

### No clear stopping criteria
Analysts stop based on: goal satisfaction, stakeholder feedback, time constraints, or diminishing returns — not clear completion criteria. (source: eda-interview-study-wongsuphasawat-2019.md)

### Limited support for unstructured data
Most EDA tools and techniques assume tabular data. Text, audio, images, and other non-tabular formats have limited exploration methods. (source: eda-interview-study-wongsuphasawat-2019.md)

## Domain Knowledge Matters

Domain-specific analysts form stronger hypotheses, choose variables more effectively, and interpret patterns more accurately than consultants serving multiple domains. Consultants rely more heavily on stakeholder consultation. (source: eda-interview-study-wongsuphasawat-2019.md)

## Tool Usage

No single tool covers the full workflow. Analysts switch between multiple tools:
- **Application users:** spreadsheets, Tableau
- **Programmers:** Python, R, MATLAB, SAS with Jupyter notebooks

(source: eda-interview-study-wongsuphasawat-2019.md)
