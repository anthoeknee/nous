import re
from typing import Any, Dict, Optional
import ast
from datetime import datetime


class TemplateEngine:
    def __init__(self):
        self.functions = {
            "current_time": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "upper": str.upper,
            "lower": str.lower,
        }

    def _evaluate_expression(
        self, expr: str, variables: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Safely evaluate a Python expression with given variables and context."""
        # Combine variables and context
        all_vars = {**variables, **(context or {})}

        try:
            # Parse the expression
            tree = ast.parse(expr, mode="eval")

            # Custom NodeTransformer could be added here for additional security

            # Compile and evaluate
            code = compile(tree, "<string>", "eval")
            return eval(code, {"__builtins__": {}}, {**all_vars, **self.functions})
        except Exception as e:
            return f"[Error: {str(e)}]"

    def _handle_conditional(
        self, match: re.Match, variables: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Handle if/else conditions in the template."""
        condition = match.group(1)
        if_content = match.group(2)
        else_content = match.group(3) if match.group(3) else ""

        try:
            result = self._evaluate_expression(condition, variables, context)
            return if_content if result else else_content
        except Exception:
            return f"[Error in condition: {condition}]"

    def _handle_variable(
        self, match: re.Match, variables: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Handle variable substitution in the template."""
        expr = match.group(1)
        result = self._evaluate_expression(expr, variables, context)
        return str(result)

    def render(
        self,
        template: str,
        variables: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a template with given variables and context."""
        # Handle conditionals first
        template = re.sub(
            r"{%\s*if\s+(.*?)\s*%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}",
            lambda m: self._handle_conditional(m, variables, context),
            template,
            flags=re.DOTALL,
        )

        # Handle variables and function calls
        template = re.sub(
            r"\${(.*?)}",
            lambda m: self._handle_variable(m, variables, context),
            template,
        )

        return template

    def add_function(self, name: str, func: callable):
        """Add a custom function to the template engine."""
        self.functions[name] = func
