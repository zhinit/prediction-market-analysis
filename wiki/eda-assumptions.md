# EDA Assumptions

Every measurement process has four underlying assumptions that must hold for analysis to produce valid, repeatable conclusions. Testing these assumptions is a core function of [[exploratory-data-analysis]]. (source: nist-eda-handbook.md)

## The Four Assumptions

1. **Random drawings** — observations are independent of each other
2. **Fixed distribution** — the underlying process generating data does not change its distributional form
3. **Fixed location** — the distribution has a constant center (e.g., constant mean)
4. **Fixed variation** — the distribution has constant spread (e.g., constant standard deviation)

(source: nist-eda-handbook.md)

## Univariate Model

For single-variable problems, the relationship simplifies to:

```
response = constant + error
```

This requires: independence among observations, a constant distribution for the random component, a deterministic component consisting only of a constant, and fixed variation. (source: nist-eda-handbook.md)

## Testing Assumptions with Residuals

A properly fitted model should produce residuals that themselves satisfy all four assumptions. If residuals behave like the ideal (random, fixed distribution, fixed location, fixed variation), this validates the model's quality of fit. When residuals violate any assumption, the model needs refinement. (source: nist-eda-handbook.md)

This connects to the [[eda-four-rs|Residuals principle]]: RESIDUAL = DATA - FIT, then check the residuals against the four assumptions.

## The 4-Plot

A single diagnostic display that tests all four assumptions simultaneously:

1. **Run sequence plot** — tests fixed location and fixed variation (look for trends or changing spread)
2. **Lag plot** — tests randomness/independence (look for structure)
3. **Histogram** — tests fixed distribution (look for the shape)
4. **Normal probability plot** — tests whether the distribution is normal specifically

(source: nist-eda-handbook.md)

## Consequences of Violation

When assumptions are violated, standard analytical results (confidence intervals, hypothesis tests, parameter estimates) may be unreliable. EDA's role is to detect these violations *before* formal analysis, so the analyst can address them — through transformation ([[eda-four-rs|reexpression]]), model modification, or different analytical methods. (source: nist-eda-handbook.md)
