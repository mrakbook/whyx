"""AST analyzer and call resolution for whyx static analysis (logic preserved)."""

import ast
from typing import Dict, List, Optional, Set, Tuple


class StaticAnalyzer(ast.NodeVisitor):
    """AST visitor that builds a static call graph for a single Python module."""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.imports: Dict[str, str] = {}
        self.classes: Set[str] = set()
        self.local_functions: Set[str] = set()
        self.functions: List[str] = []
        self.edges: List[Tuple[str, str]] = []
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            mod_name = alias.name
            asname = alias.asname if alias.asname else mod_name.split(".")[-1]
            self.imports[asname] = mod_name

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Handle absolute and relative imports.

        Examples:
            module_name='acmeproj.a'
              from .b import b1        -> imports['b1'] = 'acmeproj.b.b1'
              from .c import c1 as x   -> imports['x']  = 'acmeproj.c.c1'
              from . import helper     -> imports['helper'] = 'acmeproj.helper'
        """

        base_parts: List[str] = self.module_name.split(".")[:-1]

        level = getattr(node, "level", 0) or 0
        if level > 1:
            trim = min(level - 1, len(base_parts))
            if trim:
                base_parts = base_parts[:-trim]

        if node.module:
            root = ".".join(base_parts + [node.module]) if base_parts else node.module
        else:
            root = ".".join(base_parts)

        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.name
            asname = alias.asname if alias.asname else name
            full_name = f"{root}.{name}" if root else name
            self.imports[asname] = full_name

    def generic_visit(self, node: ast.AST):
        if isinstance(node, ast.ClassDef):
            prev_class = self.current_class
            self.current_class = node.name
            self.classes.add(node.name)
            for child in node.body:
                self.visit(child)
            self.current_class = prev_class
            return
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if self.current_class:
                func_name = f"{self.module_name}.{self.current_class}.{node.name}"
            else:
                func_name = f"{self.module_name}.{node.name}"
                self.local_functions.add(node.name)
            self.functions.append(func_name)
            prev_func = self.current_function
            self.current_function = func_name
            for child in node.body:
                self.visit(child)
            self.current_function = prev_func
            return
        elif isinstance(node, ast.Call):
            if self.current_function:
                callee = self._resolve_call(node)
                if callee:
                    self.edges.append((self.current_function, callee))
            for child in ast.iter_child_nodes(node):
                self.visit(child)
            return
        super().generic_visit(node)

    def _resolve_call(self, call_node: ast.Call) -> Optional[str]:
        """Resolve the function being called to a fully qualified name if possible."""
        target = call_node.func

        def get_name(expr: ast.AST) -> Optional[str]:
            if isinstance(expr, ast.Name):
                return expr.id
            elif isinstance(expr, ast.Attribute):
                base = get_name(expr.value)
                if base is None:
                    return None
                return f"{base}.{expr.attr}"
            else:
                return None

        target_name = get_name(target)
        if not target_name:
            return None
        parts = target_name.split(".")
        if not parts:
            return None
        top = parts[0]

        if top in ("self", "cls") and self.current_class:
            parts[0] = f"{self.module_name}.{self.current_class}"
            return ".".join(parts)

        if top in self.imports:
            imported_target = self.imports[top]
            parts[0] = imported_target
            return ".".join(parts)

        if top in self.classes:
            if len(parts) == 1:
                return f"{self.module_name}.{top}.__init__"
            else:
                parts[0] = f"{self.module_name}.{top}"
                return ".".join(parts)

        if top in self.local_functions:
            if len(parts) == 1:
                return f"{self.module_name}.{top}"
            return None

        return None
