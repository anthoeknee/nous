from typing import Dict, Any, Optional
from datetime import datetime
from string import Template
from src.storage.interfaces import StorageKey, StorageScope, StorageValue
from src.storage.manager import storage


class PromptTemplate:
    def __init__(self, template: str, conditions: Optional[Dict[str, str]] = None):
        self.template = template
        self.conditions = conditions or {}


class PromptManager:
    def __init__(self):
        self.namespace = "llm_prompts"
        self._default_variables = {
            "current_time": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bot_name": lambda: "Assistant",
            "version": lambda: "1.0",
        }

    def _make_key(self, prompt_name: str) -> StorageKey:
        return StorageKey(
            name=f"prompt_{prompt_name}",
            scope=StorageScope.GLOBAL,
            namespace=self.namespace,
        )

    async def save_prompt(self, name: str, template: PromptTemplate) -> None:
        """Save a prompt template to storage"""
        key = self._make_key(name)
        value = {"template": template.template, "conditions": template.conditions}
        await storage.get_storage().set(key, StorageValue(value=value))

    async def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve a prompt template from storage"""
        try:
            key = self._make_key(name)
            value = await storage.get_storage().get(key)
            data = value.value
            return PromptTemplate(data["template"], data["conditions"])
        except KeyError:
            return None

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate a condition string with given context"""
        try:
            # Create a safe evaluation environment with context variables
            env = {**context}
            return eval(condition, {"__builtins__": {}}, env)
        except Exception:
            return False

    async def render_prompt(
        self,
        name: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Render a prompt with variables and conditions"""
        template = await self.get_prompt(name)
        if not template:
            return None

        # Prepare variables
        vars_dict = {}

        # Add default variables
        for key, func in self._default_variables.items():
            if callable(func):
                vars_dict[key] = func()
            else:
                vars_dict[key] = func

        # Add custom variables
        if variables:
            vars_dict.update(variables)

        # Check conditions if they exist and context is provided
        if template.conditions and context:
            for condition, sub_template in template.conditions.items():
                if self.evaluate_condition(condition, context):
                    template.template = sub_template
                    break

        # Render the template
        try:
            return Template(template.template).safe_substitute(vars_dict)
        except Exception as e:
            print(f"Error rendering prompt: {e}")
            return None

    def register_variable(self, name: str, value: Any) -> None:
        """Register a new default variable or function"""
        self._default_variables[name] = value
