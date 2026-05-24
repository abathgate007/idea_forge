# Idea Forge Product Brief

## Product Vision

Idea Forge is a local-first idea foundry for generating, critiquing, scoring, tagging, searching, and evolving ideas.

The product uses local Ollama models to keep repeated idea-generation costs near zero. The application should build durable memory through stored ideas, feedback, prompt recipes, critiques, and generation history rather than relying on one endless chat context.

## Core Split

- Codex CLI builds the application.
- Ollama powers idea generation inside the application.
- Idea Forge stores and improves idea quality over time through feedback and memory.
- Self-improvement and autonomous code modification are deferred until after the MVP.

## Primary User

The initial user is Andrew: a technically sophisticated security and AI leader, author, entrepreneur, and real estate marketing supporter who wants a system for producing practical, original, high-leverage ideas.

## Product Goals

Idea Forge should help generate ideas that are:

- original
- useful
- concrete
- actionable
- low-sludge
- aligned with the user's unfair advantages
- capable of being validated quickly
- categorized by portfolio
- improved through feedback

## Idea Portfolios

Initial portfolios:

| Portfolio | Purpose |
|---|---|
| Money now | Near-term revenue, services, lead generation, consulting offers, and quick validation. |
| Long-term business | Larger products or platforms that may require compounding effort. |
| AI-related ideas | Software, workflow, content, and automation ideas centered on AI. |
| Cybersecurity and AppSec | Security leadership, AppSec workflows, design review, threat modeling, and AI security. |
| Writing and content | Books, stories, newsletters, LinkedIn posts, workshops, and authority-building content. |
| Health and lifestyle | Fitness, habits, energy, pain reduction, happiness, and retirement quality. |
| Vlatka and real estate | Realtor marketing, Lamorinda content, listing prep, neighborhood pages, lead generation, and workflow ideas. |
| Retirement income | Low-burden income systems aligned with retirement goals. |
| Wild moonshots | High-novelty ideas that may be impractical now but useful as creative raw material. |

Self-improvement is intentionally deferred from MVP.

## Idea Council

Idea Forge should not use one generic generator. It should use an idea council: agents with different cognitive lenses and biases. The persona is a thinking lens, not theatrical roleplay.

Initial idea agents:

- Quirky Professor: weird synthesis, analogy, hidden connections, and original frameworks.
- Seasoned VC: market size, timing, buyer, moat, distribution, and scale realism.
- Money-Hungry Operator: cash flow, fast validation, services, upsells, and practical selling.
- AppSec War Veteran: enterprise AppSec reality, buyer trust, review burden, evidence, and workflow fit.
- Lazy Genius: automation, low maintenance, minimum effort, and high leverage.
- Highly Intelligent Teenage Goth Punk: anti-bullshit, cultural edge, emotional charge, branding, and cringe detection.
- Environmentalist Girl: long-term consequence, sustainability, resilience, and moral legitimacy.

## Creative Techniques

The Creative Engine should select or combine techniques before generation. Each run should combine:

- seed
- portfolio
- agent
- technique
- novelty mode
- memory constraints
- anti-sludge rules

Initial techniques:

- Word Association Ladder
- Random Word Collision
- Inversion
- Constraint Forcing
- Analogy Transfer
- SCAMPER
- Future-Backward
- Failure-First
- Forbidden Obvious Answers
- Cross-Pollination Matrix
- Metaphor Mining
- Tiny Wedge
- Buyer Objection Reversal
- Pain-to-Product Ladder
- Reputation Flywheel

## Critic Stage

Generated ideas should be scored by critics.

Initial critic:

- Brutal Critic

Later critics:

- Seasoned VC
- Skeptical Accountant
- AppSec War Veteran
- Lifestyle Critic
- Ethics/Risk Critic
- Implementation Critic

Initial critique dimensions:

- originality
- usefulness
- money_potential
- time_to_market
- capital_needed
- technical_difficulty
- operational_burden
- legal_risk
- reputational_risk
- personal_fit
- lifestyle_fit
- strategic_alignment
- overall_score

Critic output should include:

- strongest reason to build
- strongest reason to kill
- fatal flaws
- first validation experiment
- success signal
- failure signal
- kill criteria
- next action

## Feedback System

Fast feedback controls:

- thumbs up
- thumbs down
- star
- reject
- duplicate
- test this
- expand
- more like this

Reason chips:

- too generic
- too hard
- too expensive
- boring
- interesting
- good fit
- could make money
- bad lifestyle fit
- good for Vlatka
- good for AppSec
- good book idea
- weekend MVP
- needs research
- low maintenance
- high burden

The system should eventually learn at multiple levels:

- idea
- agent
- creative technique
- seed
- prompt recipe
- portfolio
- critic accuracy

## Memory Design

Avoid one endless chat session. Use stateless model calls plus persistent memory.

Each generation run should assemble context from:

- system instructions
- user preference memory
- seed
- portfolio
- agent persona
- creative technique
- recent duplicate warnings
- anti-sludge rules
- relevant domain memory

Memory types:

- preference memory
- daily summary
- domain summary
- recent generation summary
- anti-sludge rule
- user profile summary

## Anti-Sludge Rules

Avoid:

- generic AI wrappers
- generic chatbots
- vague dashboards
- unclear buyers
- network effects required from day one
- venture funding required before validation
- generic wellness advice
- derivative app-for-X ideas
- obvious vulnerability scanners
- generic SOC copilots
- generic phishing detectors
- compliance chatbots without differentiation

Favor:

- specific buyer
- specific pain
- concrete first validation step
- low maintenance burden
- low test cost
- Andrew's unfair advantages
- content/product/consulting potential
- local-first or privacy-conscious design where relevant

## MVP Scope

MVP should include:

1. Create seed
2. Select portfolio
3. Select idea agent
4. Select creative technique
5. Generate ideas through Ollama
6. Store ideas in SQLite
7. Show ideas in a simple UI
8. Add thumbs up/down/star/reject feedback
9. Run one critic pass
10. Search stored ideas

MVP should not include:

- self-improvement
- autonomous code modification
- custom coding agent
- scheduled background ideation
- cloud sync
- multi-user support
