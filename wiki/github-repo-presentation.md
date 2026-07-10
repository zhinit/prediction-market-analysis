# GitHub Repo Presentation

How to make a GitHub repository clean and presentable for portfolio or resume viewing. Covers README structure, repo hygiene, profile optimization, and what hiring managers prioritize.

## What Hiring Managers Look At

A survey of 500+ hiring managers ranked these factors when evaluating GitHub portfolios (source: hakia-developer-portfolio-guide-2026.md):

| Factor | Priority | What They Want |
|--------|----------|----------------|
| Code quality | Critical | Clean, readable, well-structured code |
| Live demos | Critical | Functional applications with real features |
| Problem solving | High | Original solutions, not tutorials |
| Documentation | High | Clear READMEs and architecture explanations |
| Tech stack variety | Medium | 2-3 stacks demonstrated with depth |
| Visual design | Low | Functional over flashy |

73% of hiring managers consider a strong portfolio more important than a perfect resume. Employers spend an average of 15 seconds on portfolio sites during initial screening (source: hakia-developer-portfolio-guide-2026.md).

3-5 polished projects demonstrating depth outperform 10 basic projects in employer evaluation (source: hakia-developer-portfolio-guide-2026.md). Tutorial projects are acceptable only if substantially modified — 70%+ original work (source: hakia-developer-portfolio-guide-2026.md).

## README Structure

The README is the most important file in a portfolio repo. It addresses the what, why, and how of the project and is the first thing visitors encounter (source: freecodecamp-readme-file-guide.md).

### Essential Sections

1. **Project title** — a single sentence establishing the main goal (source: freecodecamp-readme-file-guide.md)
2. **Project description** — what the application does, technology choices, challenges faced, planned features. Avoid vague descriptions like "analysis using Python and Pandas" — instead provide context like "This project explores X using Y" (source: dataquest-data-science-portfolio-github.md)
3. **Installation and setup** — step-by-step guidance for dependencies and environment configuration (source: freecodecamp-readme-file-guide.md)
4. **Usage guide** — instructions and examples, including screenshots (source: freecodecamp-readme-file-guide.md)
5. **Credits** — collaborators and reference materials (source: freecodecamp-readme-file-guide.md)
6. **License** — what others can and cannot do with the work (source: freecodecamp-readme-file-guide.md)

### Enhanced Sections

- **Badges** — project statistics via shields.io (source: freecodecamp-readme-file-guide.md)
- **Table of contents** — for longer READMEs (source: freecodecamp-readme-file-guide.md)
- **Tests** — demonstrate confidence in functionality with code examples (source: freecodecamp-readme-file-guide.md)
- **Repository structure** — explain folder layout with short descriptions (source: bulldogjob-readme-guide.md)

### Data Analysis READMEs

For data projects, the README should also include (source: dataquest-data-science-portfolio-github.md):

- Project goals and the specific question being investigated
- Methodology and thought process
- Interesting findings and observations
- Charts, visualizations, or diagrams
- Model information (algorithms, error rates) if applicable
- Real-world applicability notes

Start with a compelling narrative explaining why the project was built and its relevance. Test installation instructions in a clean environment to verify accuracy (source: dataquest-data-science-portfolio-github.md).

## Repository Hygiene

### .gitignore

Exclude unnecessary files from version control (source: dataquest-data-science-portfolio-github.md):

- `*.pyc` — compiled Python files
- `__pycache__/` — Python cache directories
- `.DS_Store` — macOS metadata
- Temporary files (`temp.json`, scratch notebooks)
- Configuration files with sensitive data

GitHub maintains .gitignore templates for hundreds of languages as a starting point (source: dataquest-data-science-portfolio-github.md).

### Secrets and Credentials

Never commit API keys, database credentials, or authentication tokens. The recommended pattern (source: dataquest-data-science-portfolio-github.md):

1. Create a `settings.py` with placeholder variables
2. Create a `private.py` (added to `.gitignore`) containing actual secrets
3. Import private settings conditionally
4. Reference credentials through the settings module

### File Paths

Replace hardcoded absolute paths like `/Users/username/Documents/data.csv` with relative paths. Store data files in the project folder or subfolders for portability across machines (source: dataquest-data-science-portfolio-github.md).

### Dependencies

Document all dependencies with specific versions so others can reproduce the environment. Test that installation instructions work from scratch (source: dataquest-data-science-portfolio-github.md).

### Large and Restricted Data

Add large or restricted data files to `.gitignore`. Document download instructions in the README so users can obtain the data themselves, respecting licensing agreements (source: dataquest-data-science-portfolio-github.md).

### Pre-Publication Checklist

Before making a repository public (source: dataquest-data-science-portfolio-github.md):

1. Review the entire project for errors and clarity
2. Verify all installation steps work from scratch
3. Confirm file paths use relative references
4. Check that sensitive information is excluded
5. Ensure README quality and completeness

## GitHub Profile Optimization

### Profile README

Create a repository with the same name as your GitHub username and initialize it with a README. Include (source: github-docs-profile-enhance-resume.md):

- Brief professional background
- Technical skills and proficiencies
- Notable projects with commentary
- Certifications and awards

### Pinned Repositories

Pin 3-5 repositories to highlight work prominently. Select projects demonstrating diverse skills relevant to target roles. Include both owned projects and open source contributions to show independence and collaboration (source: github-docs-profile-enhance-resume.md).

### Repository Details

Update each repository with (source: github-docs-profile-enhance-resume.md):

- A project description (the short text under the repo name)
- A live website link if applicable
- Topic tags for discoverability

### Code Presentation

Make code understandable through consistent styling, descriptive naming, and adherence to style guides. Keep dependencies current (source: github-docs-profile-enhance-resume.md).

## Repo Organization

For profiles with many repositories, GitHub lacks native folder functionality. Strategies for cleanup (source: medium-tds-cleaning-github-data-science.md):

- **Delete old repos** — remove abandoned, low-value, and outdated course projects. Trade-off: deleted repos remove contributions from the activity graph
- **Organizations** — group repos under organization names to remove them from the main profile page, creating a directory-like structure. Caveat: moving repos to organizations also removes contributions from the personal graph
- **Subtree vs submodule** — subtrees move code into a parent repo (harder setup, easier maintenance); submodules place pointers to external repos (easier setup, harder maintenance)

A clean profile with ~20 visible repositories reads better than hundreds of accumulated repos (source: medium-tds-cleaning-github-data-science.md).

## Common Mistakes

From the Hakia survey of hiring managers (source: hakia-developer-portfolio-guide-2026.md):

- Building only tutorial projects without original modifications
- Broken demo links indicating poor maintenance
- Lack of live deployments — showing only code repositories
- Overly complicated design distracting from technical work
- Attempting to showcase too many technologies without depth
- Poor code organization and unclear naming conventions

## Jupyter Notebook Presentation

For data analysis repos, notebooks need particular attention. Maintain a roughly 1:2 ratio of markdown explanations to code cells. Verify notebooks render correctly in GitHub's web interface. Link to notebooks from the README with brief summaries (source: dataquest-data-science-portfolio-github.md).

See [[notebook-presentation]] and [[notebook-code-quality]] for detailed notebook standards.

## Related Pages

- [[portfolio-presentation]] — content and narrative patterns for portfolio projects
- [[presentable-data-analysis]] — hub page for presentable analysis
- [[notebook-presentation]] — structuring individual notebooks
- [[notebook-code-quality]] — clean code practices in notebooks
