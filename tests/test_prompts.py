import pytest

from idea_forge.prompts import (
    MissingPromptVariableError,
    PromptRenderer,
    load_prompt,
    render_prompt,
)


def test_loads_prompt_file() -> None:
    prompt = load_prompt("idea_generation.md")

    assert "Idea Generation Prompt" in prompt
    assert "{seed}" in prompt
    assert "{creative_technique}" in prompt


def test_renders_prompt_with_variables() -> None:
    rendered = render_prompt(
        "idea_generation.md",
        {
            "seed": "Local newsletter gaps",
            "portfolio": "Writing and content",
            "idea_agent": "Quirky Professor",
            "creative_technique": "Analogy Transfer",
            "novelty_mode": "practical",
            "context": "Use a local-first MVP lens.",
            "anti_sludge_rules": "Avoid generic dashboards.",
        },
    )

    assert "Local newsletter gaps" in rendered
    assert "Quirky Professor" in rendered
    assert "{seed}" not in rendered


def test_missing_required_variables_fail_clearly() -> None:
    renderer = PromptRenderer()

    with pytest.raises(MissingPromptVariableError) as error:
        renderer.render(
            "critic.md",
            {
                "idea": "A focused validation service",
                "portfolio": "Money now",
                "evaluation_dimensions": "overall_score",
            },
        )

    assert error.value.prompt_name == "critic.md"
    assert error.value.missing_variables == {"context"}
    assert "context" in str(error.value)


def test_renderer_can_load_prompts_from_explicit_directory(tmp_path) -> None:
    prompt_file = tmp_path / "custom.txt"
    prompt_file.write_text("Hello {name}", encoding="utf-8")
    renderer = PromptRenderer(prompts_dir=tmp_path)

    assert renderer.load("custom.txt") == "Hello {name}"
    assert renderer.render("custom.txt", {"name": "Andrew"}) == "Hello Andrew"
