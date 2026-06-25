# Data Visualization Principles

Consolidated framework from Tufte, Knaflic, and the Johns Hopkins visualization guide. These are the rules for making charts that communicate honestly and clearly.

## Tufte's Three Themes

Edward Tufte's *The Visual Display of Quantitative Information* (1983) organizes data visualization around three themes (source: tufte-visualization-principles.md):

1. **Graphical Excellence** — charts should be information-rich
2. **Graphical Integrity** — charts must represent quantities honestly and proportionally
3. **Analytical Design** — charts should support serious analysis

## Data-Ink Ratio

The proportion of ink used to present actual data versus total ink in the display. The goal is to maximize it (source: tufte-visualization-principles.md, eu-chart-junk-data-ink.md).

- Data-ink: the portion dedicated to measured quantities
- Non-data-ink: everything else (decorations, heavy gridlines, backgrounds)
- If the ink doesn't change when the data changes, it's non-data-ink

### What to remove

- Heavy gridlines (lighten or remove)
- Background colors and images
- 3D effects and perspective
- Moiré patterns
- Decorative elements
- Redundant labels
- Unnecessary axes and tick marks

## Graphical Integrity

Tufte's "Lie Factor": the ratio of graphical effect size to actual data effect size. When it exceeds 1, the visualization exaggerates (source: tufte-visualization-principles.md).

Rules:
- Start scales at zero when showing magnitude
- Use consistent units
- Show data variation, not design variation
- Adjust for inflation/deflation when comparing over time
- Don't quote data out of context

## Chartjunk

Tufte's term for visual elements that don't contribute to understanding. Two categories (source: eu-chart-junk-data-ink.md):

- **Ducks** — decorative graphics that overwhelm the data (named after the Big Duck building on Long Island, where the architecture IS the advertisement)
- **Non-data-ink** — gridlines, borders, backgrounds, and patterns that add visual noise

Counter-argument: some research suggests that decoration can aid memorability and engagement without harming comprehension. For analytical work, the consensus favors minimalism (source: eu-chart-junk-data-ink.md).

## Data Density and Small Multiples

- Pack substantial information into the available space
- The "Shrink Principle": most graphs can be reduced significantly without sacrificing legibility
- **Small multiples**: repeat identical small graphs to show variation across a dimension (e.g., one chart per category, all with the same axes)
- **Sparklines**: minimal, word-sized inline graphics for showing trends

(source: tufte-visualization-principles.md)

## Preattentive Attributes

Visual elements the brain processes before conscious attention. Use these to direct the viewer's eye (source: jhu-data-visualization-design.md, storytelling-with-data-knaflic.md):

- **Color** — strongest attention-grabber; use sparingly
- **Size** — larger elements appear more important
- **Position** — spatial placement implies relationship and hierarchy
- **Shape** — useful for categorical distinction

### Precision Hierarchy (JHU)

For encoding quantitative data, some visual channels are more precise than others (source: jhu-data-visualization-design.md):

| Precision | Encoding | Example |
|-----------|----------|---------|
| High | Length, position | Bar charts, scatter plots |
| Medium | Width, area | Bubble charts |
| Low | Color intensity, angle | Heatmaps, pie charts |

Implication: bar charts and scatter plots communicate quantities more accurately than bubble charts or pie charts.

## Color Palettes

Three palette types for three data types (source: jhu-data-visualization-design.md):

- **Qualitative** — categorical data with no ordering. Distinct hues (e.g., red, blue, green for product categories)
- **Sequential** — numeric/ordered data. Single hue varying in lightness (e.g., light blue to dark blue for revenue)
- **Diverging** — data deviating from a midpoint. Two hues from a neutral center (e.g., red-white-blue for profit/loss)

## Knaflic's Process

Cole Nussbaumer Knaflic's *Storytelling with Data* (2015) adds a process layer (source: storytelling-with-data-knaflic.md):

1. **Understand the context** — who is the audience? what do they need?
2. **Choose the right visual** — simple text for single data points, charts for patterns
3. **Eliminate clutter** — apply Gestalt principles, use white space
4. **Direct attention** — preattentive attributes for visual hierarchy
5. **Design with purpose** — function over aesthetics
6. **Tell a story** — beginning (context), middle (data), end (insight + action)

Core philosophy: "Don't be a data fashion victim." "Simple beats sexy."

## Related Pages

- [[chart-selection]] — which chart for which question
- [[data-storytelling]] — narrative structure and the role of text
- [[presentable-data-analysis]] — hub page
- [[eda-techniques]] — catalog of graphical techniques
