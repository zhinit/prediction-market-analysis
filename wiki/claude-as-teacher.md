# Claude as Teacher

Techniques and prompting strategies for using Claude as a learning tool. Covers both the built-in [[claude-learning-mode]] and manual approaches using standard Claude or Claude Projects.

## Two Core Roles

Northeastern University identifies two complementary teaching roles Claude can play (source: northeastern-ai-personal-tutor.md):

### Tutor Role

Provides structured, multi-layered explanations:
- Baseline knowledge check first
- Concise definitions (25 words or fewer)
- Step-by-step breakdowns in everyday language
- Real-world analogies matched to the learner's background
- Checkpoint questions before advancing to harder material

### Socratic Challenger Role

Guides discovery through questioning:
- Logically sequenced questions rather than direct answers
- Gentle hints when the learner gets stuck
- Summaries only after core ideas emerge through dialogue

### When to Switch

- **Tutor** for unfamiliar material (you need the foundation)
- **Socratic** once you have partial knowledge (you need to solidify it)
- **Back to tutor** for consolidation after Socratic exploration

"Concepts stick better when they're explained in multiple ways and when you discover insights through guided questioning." (source: northeastern-ai-personal-tutor.md)

## Prompting Techniques

Nine effective prompt patterns for learning (source: claude-prompts-for-learning.md):

### 1. Feynman Technique
Ask Claude to explain a concept as if you're 12, then quiz you on it. Exposes knowledge gaps.

### 2. Personalized Study Plan
Provide: goal, timeline, current knowledge level, daily study time. Get: structured week-by-week roadmap.

### 3. Socratic Dialogue
Ask Claude to guide you through a topic using only questions. No direct answers.

### 4. Flashcards and Quizzes
Generate Q&A pairs in specific formats (multiple choice, short answer) from your study materials.

### 5. Concept Analogies
Request explanations using analogies from domains you already know (sports, cooking, music, etc.).

### 6. Material Summarization
Have Claude distill dense text into key arguments and exam-relevant points within a word limit.

### 7. Targeted Gap Filling
Describe your specific confusion ("I understand X but not how it connects to Y"). Get focused explanations addressing exactly that gap.

### 8. Concept Mapping
Ask for visual/textual maps of relationships between interconnected ideas in a subject area.

### 9. Practice Exams
Have Claude role-play as a professor or interviewer conducting a simulated exam with real-time feedback.

## How to Frame Questions

The key principle is specificity — more context produces more tailored output (source: claude-prompts-for-learning.md).

**Weak framing** (gets a generic answer):
- "What is machine learning?"
- "How do I solve this integration problem?"

**Strong framing** (gets targeted teaching):
- "I understand supervised learning but can't see how backpropagation actually updates weights — walk me through a 2-layer network"
- "I think substitution applies here; here's what I've tried so far..."

Share partial attempts and confused thinking rather than asking for clean answers (source: northeastern-claude-learning-mode.md).

## Using Projects for Sustained Learning

Claude Projects allow uploading resource documents and setting custom system prompts for persistent context. This creates a dedicated tutor that knows your course materials and maintains consistency across sessions (source: northeastern-claude-learning-mode.md).

Setup:
1. Create a new Project
2. Upload course materials (PDFs, articles, notes)
3. Set a custom system prompt defining the teaching approach (tutor, Socratic, or hybrid)
4. Use the project for all study sessions on that subject

## See Also

- [[claude-learning-mode]] — the built-in Learning Mode feature and Claude for Education program
- [[claude-code-learning-style]] — the Claude Code output style for learn-by-doing coding
