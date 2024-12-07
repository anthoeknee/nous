from typing import Dict, Any, Optional
from dataclasses import dataclass
from .templating import TemplateEngine
from src.storage.interfaces import StorageKey, StorageScope, StorageValue
from src.storage.manager import storage


@dataclass
class PromptTemplate:
    template: str
    conditions: Dict[str, str] = None
    description: str = ""

    def to_dict(self):
        return {
            "template": self.template,
            "conditions": self.conditions,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class PromptManager:
    def __init__(self):
        self.engine = TemplateEngine()
        self.namespace = "prompt_templates"

    def _make_key(self, template_name: str) -> StorageKey:
        return StorageKey(
            name=f"template_{template_name}",
            scope=StorageScope.GLOBAL,
            scope_id=0,
            namespace=self.namespace,
        )

    async def save_prompt(self, name: str, template: PromptTemplate) -> None:
        """Save a prompt template to storage."""
        key = self._make_key(name)
        await storage.get_storage().set(key, StorageValue(value=template.to_dict()))

    async def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve a prompt template from storage."""
        key = self._make_key(name)
        try:
            value = await storage.get_storage().get(key)
            return PromptTemplate.from_dict(value.value)
        except KeyError:
            return None

    async def render_prompt(
        self,
        name: str,
        variables: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Render a prompt template with given variables and context."""
        template = await self.get_prompt(name)
        if not template:
            return None

        # Add conditional content based on conditions
        if template.conditions:
            for condition, content in template.conditions.items():
                template_str = f"{template.template}\n{{% if {condition} %}}\n{content}\n{{% endif %}}"
                template = PromptTemplate(template=template_str)

        return self.engine.render(template.template, variables, context)

    def add_function(self, name: str, func: callable):
        """Add a custom function to the template engine."""
        self.engine.add_function(name, func)
