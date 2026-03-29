#!/usr/bin/env python3
"""Generate protocol scaffolding from Substrait extension YAMLs.

This script performs a one-time (or periodic) code generation to bootstrap
our protocol definitions from the canonical Substrait extension files.

Usage:
    python scripts/generate_from_substrait.py --output-dir generated/
    python scripts/generate_from_substrait.py --dry-run
    python scripts/generate_from_substrait.py --category comparison
    python scripts/generate_from_substrait.py --all

Generated artifacts:
    - enums.py: SUBSTRAIT_* enum classes
    - definitions.py: FunctionDef registry entries
    - protocols.py: Protocol method stubs
    - report.md: Human-readable alignment report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


# =============================================================================
# Substrait YAML Sources
# =============================================================================

SUBSTRAIT_BASE_URL = "https://raw.githubusercontent.com/substrait-io/substrait/main/extensions"

SUBSTRAIT_EXTENSIONS = {
    "aggregate_approx": f"{SUBSTRAIT_BASE_URL}/functions_aggregate_approx.yaml",
    "aggregate_generic": f"{SUBSTRAIT_BASE_URL}/functions_aggregate_generic.yaml",
    "aggregate_decimal": f"{SUBSTRAIT_BASE_URL}/functions_aggregate_decimal_output.yaml",
    "arithmetic": f"{SUBSTRAIT_BASE_URL}/functions_arithmetic.yaml",
    "arithmetic_decimal": f"{SUBSTRAIT_BASE_URL}/functions_arithmetic_decimal.yaml",
    "boolean": f"{SUBSTRAIT_BASE_URL}/functions_boolean.yaml",
    "comparison": f"{SUBSTRAIT_BASE_URL}/functions_comparison.yaml",
    "datetime": f"{SUBSTRAIT_BASE_URL}/functions_datetime.yaml",
    "geometry": f"{SUBSTRAIT_BASE_URL}/functions_geometry.yaml",
    "logarithmic": f"{SUBSTRAIT_BASE_URL}/functions_logarithmic.yaml",
    "rounding": f"{SUBSTRAIT_BASE_URL}/functions_rounding.yaml",
    "rounding_decimal": f"{SUBSTRAIT_BASE_URL}/functions_rounding_decimal.yaml",
    "set": f"{SUBSTRAIT_BASE_URL}/functions_set.yaml",
    "string": f"{SUBSTRAIT_BASE_URL}/functions_string.yaml",
}

# Map Substrait categories to our protocol classes
CATEGORY_TO_PROTOCOL = {
    "comparison": "BooleanExpressionProtocol",
    "boolean": "BooleanExpressionProtocol",
    "arithmetic": "ArithmeticExpressionProtocol",
    "string": "StringExpressionProtocol",
    "datetime": "TemporalExpressionProtocol",
    "rounding": "ArithmeticExpressionProtocol",
    "logarithmic": "ArithmeticExpressionProtocol",
}

# Python reserved words that need trailing underscore
PYTHON_RESERVED = {"and", "or", "not", "in", "is", "from", "import", "class", "def", "return", "if", "else", "for", "while", "try", "except", "with", "as", "lambda", "yield", "raise", "pass", "break", "continue", "global", "nonlocal", "assert", "del", "exec", "print"}


# =============================================================================
# Function Type Classification
# =============================================================================

class FunctionType(Enum):
    """Classification of Substrait function types.

    Substrait YAMLs distinguish three function types:
    - SCALAR: Row-level operations (add, subtract, and, or)
    - AGGREGATE: Collapse many rows to one (sum, avg, count)
    - WINDOW: Operate over partitions (row_number, rank, lead, lag)
    """
    SCALAR = "scalar"
    AGGREGATE = "aggregate"
    WINDOW = "window"


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class SubstraitArg:
    """A function argument from Substrait YAML."""
    name: str
    value_type: str | None = None  # "value" argument
    enum_values: list[str] | None = None  # "enum" argument
    is_type_arg: bool = False  # "type" argument (no runtime value)


@dataclass
class SubstraitImpl:
    """A function implementation variant from Substrait YAML."""
    args: list[SubstraitArg]
    return_type: str
    nullability: str
    variadic: dict | None = None
    options: dict[str, list[str]] = field(default_factory=dict)
    deterministic: bool = True


@dataclass
class SubstraitFunction:
    """A parsed function from Substrait YAML."""
    name: str
    description: str
    category: str  # Domain: arithmetic, boolean, comparison, etc.
    function_type: FunctionType  # scalar, aggregate, or window
    extension_uri: str
    impls: list[SubstraitImpl]

    @property
    def python_name(self) -> str:
        """Convert to valid Python identifier."""
        name = self.name.replace("-", "_")
        if name in PYTHON_RESERVED:
            return f"{name}_"
        return name

    @property
    def enum_name(self) -> str:
        """Convert to UPPER_CASE enum name."""
        return self.python_name.upper()

    @property
    def primary_impl(self) -> SubstraitImpl:
        """Get the most general implementation."""
        # Prefer implementations with 'any' types
        for impl in self.impls:
            if any("any" in (a.value_type or "") for a in impl.args):
                return impl
        return self.impls[0] if self.impls else SubstraitImpl([], "unknown", "MIRROR")

    @property
    def arg_count(self) -> int | None:
        """Number of arguments, or None if variadic."""
        impl = self.primary_impl
        if impl.variadic:
            return None
        return len([a for a in impl.args if not a.is_type_arg])

    @property
    def option_names(self) -> tuple[str, ...]:
        """Names of configurable options."""
        return tuple(self.primary_impl.options.keys())


# =============================================================================
# YAML Parsing
# =============================================================================

def fetch_yaml(url: str, cache_dir: Path | None = None) -> str:
    """Fetch YAML content, with optional caching."""
    if cache_dir:
        cache_file = cache_dir / url.split("/")[-1]
        if cache_file.exists():
            print(f"  Using cached: {cache_file.name}")
            return cache_file.read_text()

    print(f"  Fetching: {url.split('/')[-1]}")
    with urllib.request.urlopen(url, timeout=30) as response:
        content = response.read().decode("utf-8")

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(content)

    return content


def parse_arg(arg_data: dict) -> SubstraitArg:
    """Parse a single argument definition."""
    name = arg_data.get("name", "arg")

    if "value" in arg_data:
        return SubstraitArg(name=name, value_type=arg_data["value"])
    elif "enum" in arg_data:
        return SubstraitArg(name=name, enum_values=arg_data["enum"])
    elif "type" in arg_data:
        return SubstraitArg(name=name, is_type_arg=True)
    else:
        return SubstraitArg(name=name, value_type="unknown")


def parse_impl(impl_data: dict) -> SubstraitImpl:
    """Parse a single implementation variant."""
    args = [parse_arg(a) for a in impl_data.get("args", [])]

    options = {}
    for opt_name, opt_data in impl_data.get("options", {}).items():
        if isinstance(opt_data, dict) and "values" in opt_data:
            options[opt_name] = opt_data["values"]
        elif isinstance(opt_data, list):
            options[opt_name] = opt_data

    return SubstraitImpl(
        args=args,
        return_type=impl_data.get("return", "unknown"),
        nullability=impl_data.get("nullability", "MIRROR"),
        variadic=impl_data.get("variadic"),
        options=options,
        deterministic=impl_data.get("deterministic", True),
    )


def parse_yaml(content: str, category: str, extension_uri: str) -> list[SubstraitFunction]:
    """Parse a Substrait extension YAML into function definitions.

    Substrait YAMLs contain up to three function type sections:
    - scalar_functions: Row-level operations
    - aggregate_functions: Collapse many rows to one
    - window_functions: Operate over partitions (only in functions_arithmetic.yaml)
    """
    data = yaml.safe_load(content)
    functions = []

    # Parse scalar functions
    for func_data in data.get("scalar_functions", []):
        impls = [parse_impl(i) for i in func_data.get("impls", [])]
        functions.append(SubstraitFunction(
            name=func_data["name"],
            description=func_data.get("description", ""),
            category=category,
            function_type=FunctionType.SCALAR,
            extension_uri=extension_uri,
            impls=impls,
        ))

    # Parse aggregate functions
    for func_data in data.get("aggregate_functions", []):
        impls = [parse_impl(i) for i in func_data.get("impls", [])]
        functions.append(SubstraitFunction(
            name=func_data["name"],
            description=func_data.get("description", ""),
            category=category,
            function_type=FunctionType.AGGREGATE,
            extension_uri=extension_uri,
            impls=impls,
        ))

    # Parse window functions (only exists in functions_arithmetic.yaml)
    for func_data in data.get("window_functions", []):
        impls = [parse_impl(i) for i in func_data.get("impls", [])]
        functions.append(SubstraitFunction(
            name=func_data["name"],
            description=func_data.get("description", ""),
            category=category,
            function_type=FunctionType.WINDOW,
            extension_uri=extension_uri,
            impls=impls,
        ))

    return functions


def load_all_substrait(
    categories: list[str] | None = None,
    cache_dir: Path | None = None,
) -> dict[str, list[SubstraitFunction]]:
    """Load all Substrait extension YAMLs."""
    if categories is None:
        categories = list(SUBSTRAIT_EXTENSIONS.keys())

    print("Loading Substrait extensions...")
    all_functions: dict[str, list[SubstraitFunction]] = {}

    for category in categories:
        if category not in SUBSTRAIT_EXTENSIONS:
            print(f"  Warning: Unknown category '{category}', skipping")
            continue

        url = SUBSTRAIT_EXTENSIONS[category]
        content = fetch_yaml(url, cache_dir)
        functions = parse_yaml(content, category, url)
        all_functions[category] = functions

        # Count by function type
        n_scalar = sum(1 for f in functions if f.function_type == FunctionType.SCALAR)
        n_aggregate = sum(1 for f in functions if f.function_type == FunctionType.AGGREGATE)
        n_window = sum(1 for f in functions if f.function_type == FunctionType.WINDOW)
        type_parts = []
        if n_scalar:
            type_parts.append(f"{n_scalar} scalar")
        if n_aggregate:
            type_parts.append(f"{n_aggregate} aggregate")
        if n_window:
            type_parts.append(f"{n_window} window")
        type_breakdown = ", ".join(type_parts) if type_parts else "0"
        print(f"    Parsed {len(functions)} functions from {category} ({type_breakdown})")

    return all_functions


# =============================================================================
# Code Generation: ENUMs
# =============================================================================

def generate_enum(category: str, function_type: FunctionType, functions: list[SubstraitFunction]) -> str:
    """Generate a Python Enum class for a category and function type.

    Args:
        category: Domain category (arithmetic, boolean, comparison, etc.)
        function_type: SCALAR, AGGREGATE, or WINDOW
        functions: List of functions (already filtered by type)
    """
    type_suffix = function_type.value.upper()
    enum_name = f"SUBSTRAIT_{category.upper()}_{type_suffix}"

    lines = [
        f'class {enum_name}(str, Enum):',
        f'    """Substrait {category} {function_type.value} functions.',
        f'',
        f'    Auto-generated from: {SUBSTRAIT_EXTENSIONS.get(category, "unknown")}',
        f'    Generated: {datetime.now().isoformat()}',
        f'    """',
        f'',
    ]

    for func in functions:
        # Add docstring as comment
        if func.description:
            desc = func.description[:70] + "..." if len(func.description) > 70 else func.description
            lines.append(f'    # {desc}')
        lines.append(f'    {func.enum_name} = "{func.name}"')
        lines.append('')

    return "\n".join(lines)


def generate_all_enums(all_functions: dict[str, list[SubstraitFunction]]) -> str:
    """Generate all enum classes, grouped by category and function type."""
    header = '''"""Substrait-aligned function ENUMs.

Auto-generated from Substrait extension YAMLs.
DO NOT EDIT MANUALLY - regenerate with: python scripts/generate_from_substrait.py

To add custom extensions, use MOUNTAINASH_* enums in a separate section.

Naming convention:
- SUBSTRAIT_{CATEGORY}_{TYPE}: e.g., SUBSTRAIT_ARITHMETIC_SCALAR, SUBSTRAIT_ARITHMETIC_AGGREGATE
"""

from __future__ import annotations

from enum import Enum


# =============================================================================
# Substrait Extension URIs
# =============================================================================

class SubstraitExtension:
    """Substrait extension URIs for serialization."""
'''

    # Add URI constants
    uri_lines = []
    for category, url in SUBSTRAIT_EXTENSIONS.items():
        const_name = category.upper()
        uri_lines.append(f'    {const_name} = "{url}"')

    header += "\n".join(uri_lines)
    header += "\n\n"

    # Group functions by (category, function_type)
    grouped: dict[str, dict[FunctionType, list[SubstraitFunction]]] = {}
    for category, functions in all_functions.items():
        grouped[category] = {ft: [] for ft in FunctionType}
        for func in functions:
            grouped[category][func.function_type].append(func)

    # Generate enums for each category and function type
    enum_sections = []
    enum_names = []

    for category in all_functions.keys():
        category_enums = []
        for func_type in FunctionType:
            funcs = grouped[category][func_type]
            if not funcs:
                continue
            enum_name = f"SUBSTRAIT_{category.upper()}_{func_type.value.upper()}"
            enum_names.append(enum_name)
            category_enums.append(generate_enum(category, func_type, funcs))

        if category_enums:
            section = f"""
# =============================================================================
# {category.title()} Functions
# =============================================================================

{chr(10).join(category_enums)}
"""
            enum_sections.append(section)

    # Union types by function type
    scalar_enums = [f"SUBSTRAIT_{cat.upper()}_SCALAR" for cat in all_functions.keys()
                    if any(f.function_type == FunctionType.SCALAR for f in all_functions[cat])]
    aggregate_enums = [f"SUBSTRAIT_{cat.upper()}_AGGREGATE" for cat in all_functions.keys()
                       if any(f.function_type == FunctionType.AGGREGATE for f in all_functions[cat])]
    window_enums = [f"SUBSTRAIT_{cat.upper()}_WINDOW" for cat in all_functions.keys()
                    if any(f.function_type == FunctionType.WINDOW for f in all_functions[cat])]

    union_section = f'''
# =============================================================================
# Union Types
# =============================================================================

# All scalar functions
SubstraitScalarFunction = {" | ".join(scalar_enums) if scalar_enums else "None"}

# All aggregate functions
SubstraitAggregateFunction = {" | ".join(aggregate_enums) if aggregate_enums else "None"}

# All window functions
SubstraitWindowFunction = {" | ".join(window_enums) if window_enums else "None"}

# All functions combined
SubstraitFunction = {" | ".join(enum_names) if enum_names else "None"}
'''

    return header + "\n".join(enum_sections) + union_section


# =============================================================================
# Code Generation: FunctionDefs
# =============================================================================

def generate_function_def(func: SubstraitFunction) -> str:
    """Generate a FunctionDef entry."""
    protocol_class = CATEGORY_TO_PROTOCOL.get(func.category, "UnknownProtocol")

    # Build options tuple
    options_str = ""
    if func.option_names:
        options_str = f'\n            options={func.option_names},'

    # Variadic indicator
    n_args = "None" if func.arg_count is None else str(func.arg_count)

    return f'''        FunctionDef(
            name="{func.python_name}",
            substrait_uri=SubstraitExtension.{func.category.upper()},
            substrait_name="{func.name}",
            backend_method="{func.python_name}",  # TODO: verify backend method name
            category="{func.category}",
            function_type="{func.function_type.value}",  # scalar, aggregate, or window
            n_args={n_args},{options_str}
            protocol_method={protocol_class}.{func.python_name},  # TODO: verify exists
            # {func.description[:60]}...
        ),'''


def generate_all_function_defs(all_functions: dict[str, list[SubstraitFunction]]) -> str:
    """Generate all FunctionDef entries, organized by category and function type."""
    header = '''"""Function definitions auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

Review and adjust:
- backend_method: May differ from Substrait name (e.g., and_ vs and)
- protocol_method: Verify the protocol class and method exist
- Remove functions you don't plan to implement
- Add is_extension=True for custom functions

Organization:
- Functions are grouped by category (arithmetic, boolean, etc.)
- Within each category, functions are sub-grouped by type (scalar, aggregate, window)
"""

from .registry import FunctionRegistry, FunctionDef, SubstraitExtension
from ..protocols import (
    BooleanExpressionProtocol,
    ArithmeticExpressionProtocol,
    StringExpressionProtocol,
    TemporalExpressionProtocol,
    NullExpressionProtocol,
    HorizontalExpressionProtocol,
)


def register_substrait_functions() -> None:
    """Register all Substrait-standard functions."""
'''

    # Group functions by (category, function_type)
    grouped: dict[str, dict[FunctionType, list[SubstraitFunction]]] = {}
    for category, functions in all_functions.items():
        grouped[category] = {ft: [] for ft in FunctionType}
        for func in functions:
            grouped[category][func.function_type].append(func)

    sections = []
    list_names = []

    for category in all_functions.keys():
        category_sections = []

        for func_type in FunctionType:
            funcs = grouped[category][func_type]
            if not funcs:
                continue

            func_defs = "\n".join(generate_function_def(f) for f in funcs)
            list_name = f"{category.upper()}_{func_type.value.upper()}_FUNCTIONS"
            list_names.append(list_name)

            category_sections.append(f'''
    # {func_type.value.title()} functions ({len(funcs)})
    {list_name} = [
{func_defs}
    ]
''')

        if category_sections:
            section = f'''
    # ========================================
    # {category.title()} Functions
    # ========================================
{"".join(category_sections)}'''
            sections.append(section)

    # Registration
    registration = f'''
    # ========================================
    # Register All
    # ========================================

    all_functions = (
        {" + ".join(list_names)}
    )

    for func in all_functions:
        FunctionRegistry.register(func)
'''

    return header + "\n".join(sections) + registration


# =============================================================================
# Code Generation: Protocol Stubs
# =============================================================================

def generate_protocol_method(func: SubstraitFunction) -> str:
    """Generate a protocol method stub."""
    # Build argument list
    args = ["self"]
    impl = func.primary_impl

    for arg in impl.args:
        if arg.is_type_arg:
            continue
        arg_name = arg.name if arg.name not in PYTHON_RESERVED else f"{arg.name}_"
        args.append(f"{arg_name}: SupportedExpressions")

    # Add options as keyword args
    for opt_name in impl.options:
        opt_name_safe = opt_name if opt_name not in PYTHON_RESERVED else f"{opt_name}_"
        args.append(f"{opt_name_safe}: Any = None")

    args_str = ", ".join(args)

    # Docstring
    desc = func.description or f"Substrait {func.name} function."

    return f'''    def {func.python_name}({args_str}) -> SupportedExpressions:
        """{desc}

        Substrait: {func.name}
        URI: {func.extension_uri}
        """
        ...
'''


def generate_protocol_file(category: str, function_type: FunctionType, functions: list[SubstraitFunction]) -> str:
    """Generate a complete protocol file for a category and function type.

    Args:
        category: Domain category (arithmetic, boolean, comparison, etc.)
        function_type: SCALAR, AGGREGATE, or WINDOW
        functions: List of functions (already filtered by type)

    Returns:
        Complete file content for the protocol.
    """
    type_name = function_type.value.title()  # "Scalar", "Aggregate", "Window"
    # Class name: SubstraitScalarArithmeticExpressionSystemProtocol
    class_name = f"Substrait{type_name}{category.title().replace('_', '')}ExpressionSystemProtocol"

    methods = "\n".join(generate_protocol_method(f) for f in functions)

    return f'''"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class {class_name}(Protocol):
    """Protocol for {function_type.value} {category} operations.

    Auto-generated from Substrait {category} extension.
    Function type: {function_type.value}
    """

{methods}
'''


def get_protocol_filename(category: str, function_type: FunctionType) -> str:
    """Generate the filename for a protocol file.

    Convention: prtcl_expsys_{type}_{category}.py
    Examples:
        - prtcl_expsys_scalar_arithmetic.py
        - prtcl_expsys_aggregate_boolean.py
        - prtcl_expsys_window_arithmetic.py
    """
    type_name = function_type.value.lower()  # "scalar", "aggregate", "window"
    return f"prtcl_expsys_{type_name}_{category}.py"


def generate_all_protocol_files(all_functions: dict[str, list[SubstraitFunction]]) -> dict[str, str]:
    """Generate individual protocol files for each category and function type.

    Returns:
        Dictionary mapping filename to file content.
    """
    # Group functions by (category, function_type)
    grouped: dict[str, dict[FunctionType, list[SubstraitFunction]]] = {}
    for category, functions in all_functions.items():
        grouped[category] = {ft: [] for ft in FunctionType}
        for func in functions:
            grouped[category][func.function_type].append(func)

    # Generate individual files
    files: dict[str, str] = {}

    for category in all_functions.keys():
        for func_type in FunctionType:
            funcs = grouped[category][func_type]
            if not funcs:
                continue

            filename = get_protocol_filename(category, func_type)
            content = generate_protocol_file(category, func_type, funcs)
            files[filename] = content

    return files


def generate_protocol_init(all_functions: dict[str, list[SubstraitFunction]]) -> str:
    """Generate the __init__.py file for the protocols directory."""
    # Group functions by (category, function_type)
    grouped: dict[str, dict[FunctionType, list[SubstraitFunction]]] = {}
    for category, functions in all_functions.items():
        grouped[category] = {ft: [] for ft in FunctionType}
        for func in functions:
            grouped[category][func.function_type].append(func)

    imports = []
    exports = []

    for category in all_functions.keys():
        for func_type in FunctionType:
            funcs = grouped[category][func_type]
            if not funcs:
                continue

            type_name = func_type.value.title()
            class_name = f"Substrait{type_name}{category.title().replace('_', '')}ExpressionSystemProtocol"
            module_name = f"prtcl_expsys_{func_type.value.lower()}_{category}"

            imports.append(f"from .{module_name} import {class_name}")
            exports.append(f'    "{class_name}",')

    return f'''"""Substrait-aligned expression system protocols.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

This module exports ExpressionSystem protocols aligned with the Substrait specification.
Protocols are organized by function type (scalar, aggregate, window) and category.
"""

{chr(10).join(imports)}

__all__ = [
{chr(10).join(exports)}
]
'''


def generate_all_protocols(all_functions: dict[str, list[SubstraitFunction]]) -> str:
    """Generate a single combined protocols file (legacy mode).

    For individual files, use generate_all_protocol_files() instead.
    """
    header = '''"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

NOTE: This is a combined file. For production, use --protocols-dir to generate
individual files matching the existing codebase structure.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions

'''

    # Group functions by (category, function_type)
    grouped: dict[str, dict[FunctionType, list[SubstraitFunction]]] = {}
    for category, functions in all_functions.items():
        grouped[category] = {ft: [] for ft in FunctionType}
        for func in functions:
            grouped[category][func.function_type].append(func)

    # Generate protocols
    protocols = []
    for category in all_functions.keys():
        for func_type in FunctionType:
            funcs = grouped[category][func_type]
            if not funcs:
                continue

            type_name = func_type.value.title()
            class_name = f"Substrait{type_name}{category.title().replace('_', '')}ExpressionSystemProtocol"
            methods = "\n".join(generate_protocol_method(f) for f in funcs)

            protocol = f'''
class {class_name}(Protocol):
    """Protocol for {func_type.value} {category} operations.

    Auto-generated from Substrait {category} extension.
    """

{methods}
'''
            protocols.append(protocol)

    return header + "\n".join(protocols)


# =============================================================================
# Code Generation: Markdown Report
# =============================================================================

def generate_report(all_functions: dict[str, list[SubstraitFunction]]) -> str:
    """Generate a human-readable markdown report with function type breakdown."""
    lines = [
        "# Substrait Functions Report",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
    ]

    # Calculate totals by function type
    total = sum(len(funcs) for funcs in all_functions.values())
    total_scalar = sum(1 for funcs in all_functions.values() for f in funcs if f.function_type == FunctionType.SCALAR)
    total_aggregate = sum(1 for funcs in all_functions.values() for f in funcs if f.function_type == FunctionType.AGGREGATE)
    total_window = sum(1 for funcs in all_functions.values() for f in funcs if f.function_type == FunctionType.WINDOW)

    lines.append(f"Total functions: **{total}**")
    lines.append("")
    lines.append("| Function Type | Count |")
    lines.append("|---------------|-------|")
    lines.append(f"| Scalar | {total_scalar} |")
    lines.append(f"| Aggregate | {total_aggregate} |")
    lines.append(f"| Window | {total_window} |")
    lines.append("")

    # Summary by category with type breakdown
    lines.append("### By Category")
    lines.append("")
    lines.append("| Category | Scalar | Aggregate | Window | Total |")
    lines.append("|----------|--------|-----------|--------|-------|")

    for category, functions in all_functions.items():
        n_scalar = sum(1 for f in functions if f.function_type == FunctionType.SCALAR)
        n_aggregate = sum(1 for f in functions if f.function_type == FunctionType.AGGREGATE)
        n_window = sum(1 for f in functions if f.function_type == FunctionType.WINDOW)
        n_total = len(functions)
        lines.append(f"| {category} | {n_scalar} | {n_aggregate} | {n_window} | {n_total} |")

    lines.append("")
    lines.append("## Functions by Category and Type")
    lines.append("")

    for category, functions in all_functions.items():
        lines.append(f"### {category.title()}")
        lines.append("")

        # Group by function type
        by_type: dict[FunctionType, list[SubstraitFunction]] = {ft: [] for ft in FunctionType}
        for func in functions:
            by_type[func.function_type].append(func)

        for func_type in FunctionType:
            type_funcs = by_type[func_type]
            if not type_funcs:
                continue

            lines.append(f"#### {func_type.value.title()} Functions ({len(type_funcs)})")
            lines.append("")
            lines.append("| Substrait Name | Python Name | Args | Options | Description |")
            lines.append("|----------------|-------------|------|---------|-------------|")

            for func in type_funcs:
                args = str(func.arg_count) if func.arg_count is not None else "variadic"
                opts = ", ".join(func.option_names) if func.option_names else "-"
                desc = func.description[:50] + "..." if len(func.description) > 50 else func.description
                lines.append(f"| `{func.name}` | `{func.python_name}` | {args} | {opts} | {desc} |")

            lines.append("")

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate protocol scaffolding from Substrait YAMLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("generated"),
        help="Output directory for generated files",
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".substrait_cache"),
        help="Directory to cache downloaded YAMLs",
    )

    parser.add_argument(
        "--category", "-c",
        action="append",
        dest="categories",
        help="Specific categories to process (can be repeated)",
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Process all categories",
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print to stdout instead of writing files",
    )

    parser.add_argument(
        "--enums-only",
        action="store_true",
        help="Only generate enum file",
    )

    parser.add_argument(
        "--defs-only",
        action="store_true",
        help="Only generate function definitions",
    )

    parser.add_argument(
        "--protocols-only",
        action="store_true",
        help="Only generate protocol stubs",
    )

    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate markdown report",
    )

    parser.add_argument(
        "--protocols-dir",
        type=Path,
        help="Generate individual protocol files to this directory (matches codebase structure)",
    )

    args = parser.parse_args()

    # Determine categories
    if args.all or args.categories is None:
        categories = None  # All
    else:
        categories = args.categories

    # Load Substrait YAMLs
    all_functions = load_all_substrait(categories, args.cache_dir)

    # Determine what to generate
    generate_all = not (args.enums_only or args.defs_only or args.protocols_only or args.report_only)

    outputs: dict[str, str] = {}
    protocol_files: dict[str, str] = {}

    if generate_all or args.enums_only:
        outputs["enums.py"] = generate_all_enums(all_functions)

    if generate_all or args.defs_only:
        outputs["definitions_generated.py"] = generate_all_function_defs(all_functions)

    if generate_all or args.protocols_only:
        if args.protocols_dir:
            # Generate individual files
            protocol_files = generate_all_protocol_files(all_functions)
            protocol_files["__init__.py"] = generate_protocol_init(all_functions)
        else:
            # Generate single combined file
            outputs["protocols_generated.py"] = generate_all_protocols(all_functions)

    if generate_all or args.report_only:
        outputs["SUBSTRAIT_FUNCTIONS.md"] = generate_report(all_functions)

    # Output
    if args.dry_run:
        for filename, content in outputs.items():
            print(f"\n{'=' * 60}")
            print(f"FILE: {filename}")
            print('=' * 60)
            print(content[:2000])
            if len(content) > 2000:
                print(f"\n... ({len(content) - 2000} more characters)")

        for filename, content in protocol_files.items():
            print(f"\n{'=' * 60}")
            print(f"PROTOCOL FILE: {filename}")
            print('=' * 60)
            print(content[:2000])
            if len(content) > 2000:
                print(f"\n... ({len(content) - 2000} more characters)")
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in outputs.items():
            output_path = args.output_dir / filename
            output_path.write_text(content)
            print(f"Wrote: {output_path}")

        # Write protocol files to separate directory if specified
        if protocol_files and args.protocols_dir:
            args.protocols_dir.mkdir(parents=True, exist_ok=True)
            for filename, content in protocol_files.items():
                output_path = args.protocols_dir / filename
                output_path.write_text(content)
                print(f"Wrote: {output_path}")

    # Summary
    total_files = len(outputs) + len(protocol_files)
    print(f"\nGenerated {total_files} files")
    total_funcs = sum(len(f) for f in all_functions.values())
    print(f"Total Substrait functions: {total_funcs}")


if __name__ == "__main__":
    main()
