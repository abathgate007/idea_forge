"""Prompt file loading and rendering utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from typing import Mapping


DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class PromptError(RuntimeError):
    """Base exception for prompt loading and rendering failures."""


class PromptNotFoundError(PromptError):
    """Raised when a requested prompt file does not exist."""


class MissingPromptVariableError(PromptError):
    """Raised when rendering is missing a required prompt variable."""

    def __init__(self, prompt_name: str, missing_variables: set[str]) -> None:
        self.prompt_name = prompt_name
        self.missing_variables = missing_variables
        names = ", ".join(sorted(missing_variables))
        super().__init__(f"Prompt '{prompt_name}' is missing required variables: {names}")


@dataclass(frozen=True)
class PromptRenderer:
    """Load prompt files and render them with explicit variables."""

    prompts_dir: Path = DEFAULT_PROMPTS_DIR

    def load(self, prompt_name: str) -> str:
        """Load a prompt file by name."""
        prompt_path = self._prompt_path(prompt_name)
        if not prompt_path.is_file():
            raise PromptNotFoundError(f"Prompt file not found: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")

    def render(self, prompt_name: str, variables: Mapping[str, object]) -> str:
        """Render a prompt file with explicit variables."""
        template = self.load(prompt_name)
        required_variables = _template_variables(template)
        missing_variables = required_variables.difference(variables)
        if missing_variables:
            raise MissingPromptVariableError(prompt_name, missing_variables)

        return template.format(**variables)

    def _prompt_path(self, prompt_name: str) -> Path:
        return self.prompts_dir / prompt_name


def load_prompt(prompt_name: str) -> str:
    """Load a prompt file from the default prompts directory."""
    return PromptRenderer().load(prompt_name)


def render_prompt(prompt_name: str, variables: Mapping[str, object]) -> str:
    """Render a prompt file from the default prompts directory."""
    return PromptRenderer().render(prompt_name, variables)


def _template_variables(template: str) -> set[str]:
    variables = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name:
            variables.add(field_name)
    return variables
