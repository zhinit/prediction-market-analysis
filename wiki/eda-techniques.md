# EDA Techniques

[[exploratory-data-analysis]] techniques divide into graphical and quantitative, with graphical methods taking priority for initial exploration. (source: nist-eda-handbook.md)

## Graphical Techniques

EDA relies heavily on graphical methods because they leverage human pattern-recognition abilities. The NIST handbook catalogs 33 graphical techniques. (source: nist-eda-handbook.md)

### Core Plots (most commonly used)

| Plot | Purpose |
|------|---------|
| Histogram | Frequency distribution shape |
| Box plot | Median, quartiles, outlier detection (resistant) |
| Scatter plot | Relationship between two variables |
| Normal probability plot | Test for normality |
| Run sequence plot | Detect trends, shifts, drift over time |
| Lag plot | Test for randomness/autocorrelation |
| Stem-and-leaf | Distribution shape while preserving individual values |

### Assumption Testing Plots

| Plot | Tests |
|------|-------|
| 4-Plot | All four [[eda-assumptions]] at once |
| 6-Plot | Extended diagnostic (run sequence, lag, histogram, normal probability + more) |
| Autocorrelation plot | Independence assumption |
| Probability plot | Distribution fit |
| Q-Q plot | Compare two distributions |

### Comparison and Relationship Plots

| Plot | Purpose |
|------|---------|
| Bihistogram | Compare two distributions side-by-side |
| Block plot | Factor effects in designed experiments |
| Contour plot | 3D surface relationships in 2D |
| DOE mean/scatter/SD plots | Experimental design analysis |
| Star plot | Multivariate comparison across cases |
| Youden plot | Paired measurements |

### Model Diagnostic Plots

| Plot | Purpose |
|------|---------|
| Box-Cox linearity plot | Find best power transformation for linearity |
| Box-Cox normality plot | Find best power transformation for normality |
| Bootstrap plot | Uncertainty of estimates via resampling |
| Linear correlation/intercept/slope plots | Regression diagnostics |
| Residual standard deviation plot | Heteroscedasticity detection |

### Time-Domain and Frequency-Domain

| Plot | Purpose |
|------|---------|
| Spectrum | Frequency content / periodicities |
| Complex demodulation (amplitude) | Time-varying amplitude of periodic signal |
| Complex demodulation (phase) | Time-varying phase of periodic signal |
| Weibull plot | Reliability / failure analysis |

(source: nist-eda-handbook.md)

## Quantitative Techniques

Classical statistical methods complement graphical approaches. Two main categories: interval estimation and hypothesis tests. (source: nist-eda-handbook.md)

### By Category

| Category | Methods |
|----------|---------|
| Location | Mean, confidence intervals, two-sample t-test, one-factor ANOVA, multi-factor ANOVA |
| Scale | Variance, Bartlett's test, Chi-Square test, F-test, Levene's test |
| Shape | Skewness, kurtosis measures |
| Randomness | Autocorrelation, runs test |
| Distribution | Anderson-Darling, Chi-Square goodness-of-fit, Kolmogorov-Smirnov |
| Outliers | Grubbs test, Tietjen-Moore test |
| Factorial designs | Yates algorithm |

(source: nist-eda-handbook.md)

### Dimensionality Reduction

- Principal Component Analysis (PCA)
- Multidimensional Scaling (MDS)

(source: wikipedia-exploratory-data-analysis.md)

### Other Quantitative Methods

- Median polish
- Trimean
- Ordination
- Bootstrap methods (empirical intervals when analytic derivation isn't feasible)

(source: wikipedia-exploratory-data-analysis.md, nist-eda-handbook.md)

## Important Distinction

Statistical significance ≠ practical significance. Rejecting a null hypothesis statistically does not mean the effect has real practical importance. EDA counsels against blind application of quantitative tests without engineering/domain judgment. (source: nist-eda-handbook.md)

## Software

Common EDA platforms: R, Python (Matplotlib, Seaborn), JMP, KNIME, Minitab. (source: wikipedia-exploratory-data-analysis.md)
