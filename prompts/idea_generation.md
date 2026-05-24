# Idea Generation Prompt

You are generating original, concrete ideas for Idea Forge.

Seed:
{seed}

Portfolio:
{portfolio}

Idea agent:
{idea_agent}

Creative technique:
{creative_technique}

Novelty mode:
{novelty_mode}

Relevant context:
{context}

Anti-sludge rules:
{anti_sludge_rules}

Return only strict JSON. Do not include markdown, code fences, commentary, or extra text.

The JSON must be an object with this shape:

{{
  "ideas": [
    {{
      "title": "Short concrete idea title",
      "summary": "One concise paragraph explaining the idea.",
      "target_buyer": "Specific buyer or user who would pay for or adopt it.",
      "first_validation_step": "One practical low-cost action to test demand.",
      "why_it_fits": "Why this idea fits the seed, selected portfolio, agent, and technique."
    }}
  ]
}}

Return multiple ideas in the "ideas" array. Every idea must include title, summary, target_buyer, first_validation_step, and why_it_fits as non-empty strings.
