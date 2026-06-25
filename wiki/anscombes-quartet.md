# Anscombe's Quartet

A classic demonstration of why graphical analysis is essential in [[exploratory-data-analysis]]. (source: nist-eda-handbook.md)

## The Setup

Four datasets of 11 (x, y) pairs each. All four produce identical summary statistics:

- Mean of X = 9.0
- Mean of Y = 7.5
- Linear regression: intercept = 3, slope = 0.5
- Residual standard deviation: same across all four
- Correlation = 0.816

(source: nist-eda-handbook.md)

## What the Plots Reveal

Despite identical statistics, scatter plots show completely different structures:

| Dataset | Pattern |
|---------|---------|
| 1 | Linear relationship with random scatter — the only dataset where the linear model is appropriate |
| 2 | Clearly quadratic (curved) relationship — linear regression is the wrong model |
| 3 | Perfect linear relationship except for one outlier — the outlier drives the regression |
| 4 | All points at one X value except one extreme point — the regression is determined entirely by that single point |

(source: nist-eda-handbook.md)

## The Lesson

Quantitative statistics are not wrong per se, but they are incomplete. Numerical summaries filter data, necessarily omitting and screening out other sometimes crucial information. (source: nist-eda-handbook.md)

This is the strongest argument for the [[eda-four-rs|Revelation]] principle: always plot data before computing summaries. A mean, slope, or correlation coefficient tells you nothing about whether the model generating those numbers is appropriate. Only a plot can show that.
