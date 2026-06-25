# Chart Selection

Question-driven framework for choosing chart types. Based on Tableau's chart selection guide: start with the analytical question, then pick the chart (source: tableau-chart-type-selection.md, tableau-visual-best-practices.md).

## The Rule

"Form follows function." The visualization depends on three factors:
1. The question you're asking
2. Your data's properties
3. How you want to communicate the insight

Never pick a chart type first and fit data into it.

## Question → Chart Type

### Change Over Time
*How has this measure changed? When? How quickly?*

| Chart | When to use |
|-------|-------------|
| Line chart | Continuous trend over time |
| Slope chart | Comparing two time points |
| Highlight table | Discrete time periods with magnitude |

### Correlation
*Are these two measures related? How strongly?*

| Chart | When to use |
|-------|-------------|
| Scatter plot | Two continuous variables |
| Highlight table | Categorical cross-tabulation |

Add trend lines and R² for quantifying strength. "Correlation does not always equal causation."

### Magnitude
*Which items are biggest? How large is the gap?*

| Chart | When to use |
|-------|-------------|
| Bar chart | Comparing categories (default choice) |
| Packed bubble | Many categories, approximate comparison |

### Deviation
*How far from the baseline? Is there a pattern?*

| Chart | When to use |
|-------|-------------|
| Bullet chart | Actual vs target |
| Bar chart | Variance from average/median |
| Combination chart | Overlaying deviation on trend |

### Distribution
*How are values spread? Are there clusters?*

| Chart | When to use |
|-------|-------------|
| Histogram | Frequency distribution |
| Box plot | Summary statistics + outliers |
| Population pyramid | Two-sided distribution comparison |
| Pareto chart | Cumulative contribution |

### Ranking
*What's the ordering? How steep is the dropoff?*

| Chart | When to use |
|-------|-------------|
| Bar chart (sorted) | Ordered comparison |
| Top-N set | Focus on leaders/laggards |

### Part-to-Whole
*What share does each part contribute?*

| Chart | When to use |
|-------|-------------|
| Stacked bar chart | Parts across categories |
| Treemap | Hierarchical proportions |
| Area chart | Parts changing over time |
| Pie chart | Only with 2–3 slices, use sparingly |

### Spatial
*Where are the patterns geographically?*

| Chart | When to use |
|-------|-------------|
| Filled/choropleth map | Regional aggregates |
| Point/symbol map | Individual locations |
| Density map | Concentration patterns |

### Flow
*What are the paths, durations, or movements?*

| Chart | When to use |
|-------|-------------|
| Sankey diagram | Flow between stages |
| Path map | Movement over geography |
| Gantt chart | Duration and sequencing |

## Design Defaults

From Tableau's visual best practices (source: tableau-visual-best-practices.md):

- **Layout**: most important chart in the top-left (newspaper/Z-layout)
- **White space**: group related charts, separate unrelated ones
- **Color**: neutral primary palette, accent color for emphasis; consider color-blind accessibility
- **Tooltips**: use for detail-on-demand instead of cramming labels onto the chart
- **Titles**: every chart needs a descriptive title that states what it shows

## Related Pages

- [[data-visualization-principles]] — the underlying design theory
- [[data-storytelling]] — how to frame the chart in narrative
- [[presentable-data-analysis]] — hub page
- [[eda-techniques]] — catalog of graphical techniques
