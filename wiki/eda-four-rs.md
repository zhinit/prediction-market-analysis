# The Four R's of EDA

Four principles that guide [[exploratory-data-analysis]], formalized from Tukey's methodology. (source: bayesball-eda-course-introduction.md)

## 1. Revelation

Use graphical displays to identify patterns before computing summary statistics. Look at the data first; compute later.

Graphical techniques leverage human pattern-recognition abilities — no quantitative method substitutes for seeing the data. [[anscombes-quartet]] is the canonical demonstration: identical statistics, completely different structures. (source: nist-eda-handbook.md, bayesball-eda-course-introduction.md)

## 2. Resistance

Prefer methods insensitive to outliers. A single extreme value can dramatically shift a mean but not a median. Resistant methods give reliable summaries even when data contains unusual values.

Examples: median over mean, trimmed means, boxplots (which flag outliers separately from the central summary). (source: bayesball-eda-course-introduction.md)

## 3. Reexpression

Transform data to alternative scales when the original scale obscures patterns. Common transformations: logarithmic, square root, reciprocal.

Data that is heavily skewed or has unequal spread across groups often becomes more symmetric and easier to analyze after transformation. Example: immigration data with extreme right skew becomes analyzable after log transformation. (source: bayesball-eda-course-introduction.md)

## 4. Residuals

Analyze deviations from fitted patterns:

```
RESIDUAL = DATA - FIT
```

Once a pattern is identified and subtracted, the residuals may reveal additional patterns hidden by the dominant one. Residual analysis is also the primary tool for validating model fit — if residuals satisfy the [[eda-assumptions|four underlying assumptions]], the model is adequate. (source: bayesball-eda-course-introduction.md, nist-eda-handbook.md)

## Tukey's Tools Embodying the Four R's

- **Stem-and-leaf plots** — display individual data values while showing distribution shape (revelation)
- **Boxplots** — summarize distribution via median, quartiles, and outlier flagging (resistance, revelation)
- **Resistant smoothing** — fit trends without undue influence from extreme points (resistance)
- **Rootograms** — compare observed frequencies to theoretical distributions (residuals)

(source: bayesball-eda-course-introduction.md)
