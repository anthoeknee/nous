import re
from typing import Any, Dict, Optional, Set
import ast
from datetime import datetime


class SafeNodeTransformer(ast.NodeTransformer):
    """A NodeTransformer that only allows safe operations."""

    SAFE_OPERATIONS = {
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,  # Basic arithmetic
        ast.Pow,
        ast.USub,
        ast.UAdd,  # Unary operations
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,  # Comparisons
        ast.And,
        ast.Or,
        ast.Not,  # Boolean operations
    }

    def __init__(self, allowed_names: Set[str]):
        self.allowed_names = allowed_names

    def visit(self, node):
        """Verify node type is allowed before visiting."""
        if isinstance(
            node,
            (
                ast.Expression,
                ast.Constant,
                ast.Name,
                ast.BoolOp,
                ast.BinOp,
                ast.UnaryOp,
                ast.Compare,
                ast.Call,
            ),
        ):
            return super().visit(node)
        raise ValueError(f"Disallowed expression type: {type(node).__name__}")

    def visit_Name(self, node):
        """Only allow access to explicitly allowed names."""
        if node.id not in self.allowed_names:
            raise ValueError(f"Access to name '{node.id}' is not allowed")
        return node

    def visit_Call(self, node):
        """Only allow calls to explicitly allowed functions."""
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id not in self.allowed_names
        ):
            raise ValueError(
                f"Function calls to '{getattr(node.func, 'id', '?')}' are not allowed"
            )
        return ast.Call(
            func=self.visit(node.func),
            args=[self.visit(arg) for arg in node.args],
            keywords=[],
        )

    def visit_BinOp(self, node):
        """Only allow safe binary operations."""
        if not isinstance(node.op, tuple(self.SAFE_OPERATIONS)):
            raise ValueError(f"Operation {type(node.op).__name__} is not allowed")
        return super().visit_BinOp(node)

    def visit_UnaryOp(self, node):
        """Only allow safe unary operations."""
        if not isinstance(node.op, tuple(self.SAFE_OPERATIONS)):
            raise ValueError(f"Operation {type(node.op).__name__} is not allowed")
        return super().visit_UnaryOp(node)


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

            # Transform and validate the AST
            allowed_names = set(all_vars.keys()) | set(self.functions.keys())
            transformer = SafeNodeTransformer(allowed_names)
            safe_tree = transformer.visit(tree)

            # Compile and evaluate with restricted environment
            code = compile(safe_tree, "<string>", "eval")
            restricted_builtins = {
                "True": True,
                "False": False,
                "None": None,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
            }
            return eval(
                code,
                {"__builtins__": restricted_builtins},
                {**all_vars, **self.functions},
            )
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
