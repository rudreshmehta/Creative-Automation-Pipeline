from pathlib import Path
from typing import Dict


class PromptLoader:
    def __init__(self, prompts_dir: Path = Path("prompts")):
        self.prompts_dir = prompts_dir
        self._prompts = {}

    def load(self, prompt_name: str) -> str:
        if prompt_name in self._prompts:
            return self._prompts[prompt_name]

        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            template = f.read().strip()

        self._prompts[prompt_name] = template
        return template

    def format(self, prompt_name: str, **kwargs) -> str:
        template = self.load(prompt_name)
        return template.format(**kwargs)