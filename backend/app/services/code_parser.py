"""
Code parser service using Python AST and regex-based extraction.
Analyzes source files to extract functions, classes, routes, models, and components.
"""

import ast
import re
import os
from pathlib import Path

from app.models.schemas import CodeElement, FileAnalysis, DetectedFramework
from app.utils.logger import get_logger

logger = get_logger("code_parser")


class CodeParser:
    """Parse source code files and extract structural elements."""

    def parse_file(self, file_path: str, relative_path: str, content: str) -> FileAnalysis:
        """Parse a single file and return its analysis."""
        ext = Path(relative_path).suffix.lower()
        language = self._detect_language(ext)

        analysis = FileAnalysis(
            file_path=relative_path,
            language=language,
            line_count=content.count("\n") + 1,
            has_tests=self._is_test_file(relative_path),
        )

        if language == "python":
            analysis.elements = self._parse_python(content, relative_path)
            analysis.imports = self._extract_python_imports(content)
            analysis.framework = self._detect_python_framework(content)
        elif language in ("javascript", "typescript"):
            analysis.elements = self._parse_javascript(content, relative_path)
            analysis.imports = self._extract_js_imports(content)
            analysis.framework = self._detect_js_framework(content)

        return analysis

    def _detect_language(self, ext: str) -> str:
        mapping = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript",
            ".java": "java", ".cs": "csharp", ".go": "go",
        }
        return mapping.get(ext, "other")

    def _is_test_file(self, path: str) -> bool:
        name = os.path.basename(path).lower()
        return (name.startswith("test_") or name.endswith("_test.py") or
                name.endswith(".test.ts") or name.endswith(".test.tsx") or
                name.endswith(".spec.ts") or name.endswith(".spec.tsx") or
                "tests/" in path or "__tests__/" in path)

    # ─── Python parsing ──────────────────────────────────────────────────────

    def _parse_python(self, content: str, file_path: str) -> list[CodeElement]:
        elements = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return elements

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                params = [a.arg for a in node.args.args if a.arg != "self"]
                docstring = ast.get_docstring(node) or ""
                element = CodeElement(
                    name=node.name, element_type="function", file_path=file_path,
                    line_number=node.lineno, decorators=decorators,
                    parameters=params, docstring=docstring,
                )
                # Detect routes
                for dec in decorators:
                    route_match = re.search(r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', dec)
                    if route_match:
                        element.http_method = route_match.group(1).upper()
                        element.route_path = route_match.group(2)
                        element.element_type = "route"
                elements.append(element)

            elif isinstance(node, ast.ClassDef):
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                bases = [self._get_base_name(b) for b in node.bases]
                docstring = ast.get_docstring(node) or ""
                etype = "class"
                if any("BaseModel" in b or "Base" in b for b in bases):
                    etype = "model"
                element = CodeElement(
                    name=node.name, element_type=etype, file_path=file_path,
                    line_number=node.lineno, decorators=decorators,
                    docstring=docstring, parent_class=", ".join(bases),
                )
                elements.append(element)
        return elements

    def _get_decorator_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        elif isinstance(node, ast.Call):
            return ast.unparse(node)
        return ""

    def _get_base_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ""

    def _extract_python_imports(self, content: str) -> list[str]:
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError:
            pass
        return imports

    def _detect_python_framework(self, content: str) -> DetectedFramework:
        if "from fastapi" in content or "import fastapi" in content:
            return DetectedFramework.FASTAPI
        if "from flask" in content or "import flask" in content:
            return DetectedFramework.FLASK
        if "from django" in content or "import django" in content:
            return DetectedFramework.DJANGO
        return DetectedFramework.UNKNOWN

    # ─── JavaScript/TypeScript parsing ───────────────────────────────────────

    def _parse_javascript(self, content: str, file_path: str) -> list[CodeElement]:
        elements = []

        # React components (function declarations)
        for m in re.finditer(r'(?:export\s+(?:default\s+)?)?(?:const|function)\s+(\w+)\s*(?::\s*React\.FC)?.*?=?\s*\(([^)]*)\)\s*(?:=>|{)', content):
            name = m.group(1)
            if name[0].isupper():  # React component convention
                elements.append(CodeElement(
                    name=name, element_type="component", file_path=file_path,
                    line_number=content[:m.start()].count("\n") + 1,
                    parameters=[p.strip().split(":")[0].strip() for p in m.group(2).split(",") if p.strip()],
                ))

        # Express/Fastify routes
        for m in re.finditer(r'(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', content):
            elements.append(CodeElement(
                name=f"{m.group(1).upper()} {m.group(2)}", element_type="route",
                file_path=file_path,
                line_number=content[:m.start()].count("\n") + 1,
                http_method=m.group(1).upper(), route_path=m.group(2),
            ))

        # Exported functions
        for m in re.finditer(r'export\s+(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', content):
            name = m.group(1)
            if not name[0].isupper():
                elements.append(CodeElement(
                    name=name, element_type="function", file_path=file_path,
                    line_number=content[:m.start()].count("\n") + 1,
                ))

        # Class declarations
        for m in re.finditer(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{', content):
            elements.append(CodeElement(
                name=m.group(1), element_type="class", file_path=file_path,
                line_number=content[:m.start()].count("\n") + 1,
                parent_class=m.group(2) or "",
            ))

        return elements

    def _extract_js_imports(self, content: str) -> list[str]:
        imports = []
        for m in re.finditer(r'(?:import|require)\s*\(?[^)]*["\']([^"\']+)', content):
            imports.append(m.group(1))
        return imports

    def _detect_js_framework(self, content: str) -> DetectedFramework:
        if "from 'react'" in content or 'from "react"' in content:
            return DetectedFramework.REACT
        if "from 'next'" in content or 'from "next"' in content:
            return DetectedFramework.NEXTJS
        if "from 'vue'" in content or 'from "vue"' in content:
            return DetectedFramework.VUE
        if "'express'" in content or '"express"' in content:
            return DetectedFramework.EXPRESS
        return DetectedFramework.UNKNOWN


def get_code_parser() -> CodeParser:
    return CodeParser()
