# Exploratory Data Analysis

An approach to data analysis that employs mostly graphical techniques to maximize insight into a dataset, uncover underlying structure, and let data suggest appropriate models — rather than imposing models before examining the data. (source: nist-eda-handbook.md)

Coined and promoted by John Tukey starting in 1970 and formalized in his 1977 book *Exploratory Data Analysis*. Tukey characterized it as "numerical detective work." (source: wikipedia-exploratory-data-analysis.md, bayesball-eda-course-introduction.md)

## Philosophy

EDA is a philosophy, not a set of techniques — an attitude about how a data analysis should be carried out. It dictates what we look for, how we look, and how we interpret. (source: nist-eda-handbook.md)

The core commitment: let data reveal its inherent structure rather than imposing predetermined models. This contrasts with both classical analysis (which fits a pre-chosen model) and Bayesian analysis (which also starts from a model plus prior). (source: nist-eda-handbook.md)

## EDA vs. Classical vs. Bayesian

The three approaches differ in when the model enters:

| Approach | Sequence |
|----------|----------|
| Classical | Problem → Data → **Model** → Analysis → Conclusions |
| EDA | Problem → Data → Analysis → **Model** → Conclusions |
| Bayesian | Problem → Data → **Model** → Prior → Analysis → Conclusions |

In classical analysis, the model is imposed before examining the data. In EDA, analysis comes first, with the goal of inferring what model would be appropriate. (source: nist-eda-handbook.md)

Six dimensions distinguish EDA from classical analysis: models (data-suggested vs. imposed), focus (data vs. parameters), techniques (graphical vs. quantitative), rigor (informal insight vs. formal inference), data treatment (values to explore vs. observations from a model), assumptions (tested vs. relied upon). (source: nist-eda-handbook.md)

## EDA vs. Confirmatory Data Analysis

Confirmatory Data Analysis (CDA) assumes data represent random samples from normally distributed populations and focuses on parameter estimation and hypothesis testing. EDA makes no population assumptions, treats data as values worthy of exploration, and does not make inferential claims about hypothetical populations. (source: bayesball-eda-course-introduction.md)

The two are complementary: EDA generates hypotheses; CDA tests them. (source: wikipedia-exploratory-data-analysis.md)

## EDA Detects Phenomena, Not Explanations

EDA operates at the level of pattern detection — identifying stable, recurring phenomena in data. It does not explain why those patterns exist. Explanatory work (abductive reasoning, causal inference) is a separate, subsequent phase. Conflating the two risks treating descriptive hypotheses as explanatory ones when no explanatory work has been done. (source: haig-commentary-eda-2015.md)

## Seven Objectives

1. Maximize insight into a data set
2. Uncover underlying structure
3. Extract important variables
4. Detect outliers and anomalies
5. Test underlying assumptions
6. Develop parsimonious models
7. Determine optimal factor settings

(source: nist-eda-handbook.md)

## Graphics Are Non-Negotiable

The "feel" for a data set comes almost exclusively from graphical techniques. No quantitative analogues give the same insight as well-chosen graphics. [[anscombes-quartet]] demonstrates this: four datasets with identical summary statistics show completely different structures when plotted. (source: nist-eda-handbook.md)

## Foundational Works

- Tukey (1977) — *Exploratory Data Analysis*
- Mosteller and Tukey (1977) — *Data Analysis and Regression*
- Hoaglin (1977) — *Interactive Data Analysis*
- Velleman and Hoaglin (1981) — *The ABC's of EDA*

(source: nist-eda-handbook.md)

Tukey's work influenced the development of S, S-PLUS, and R at Bell Labs. (source: wikipedia-exploratory-data-analysis.md)

## See Also

- [[eda-four-rs]] — The four principles: Revelation, Resistance, Reexpression, Residuals
- [[eda-assumptions]] — The four underlying assumptions of measurement processes
- [[eda-techniques]] — Catalog of graphical and quantitative techniques
- [[eda-workflow]] — Practical process: profiling, discovery, challenges
- [[anscombes-quartet]] — Why graphics cannot be skipped
