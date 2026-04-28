# Nested Data & Duration Expression Gaps — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `.struct` and `.list` accessor namespaces plus a `ma.duration()` constructor and `.dt.total_*()` extraction methods, closing gaps 5, 6, and 15 from the PromptBase pipeline backlog.

**Architecture:** All three gaps follow the established mountainash extension pattern — Polars-style public API, `ScalarFunctionNode` with mountainash extension function keys, wired through all 6 architecture layers. Duration constructor is a thin wrapper over `LiteralNode(timedelta(...))` with no new node types.

**Tech Stack:** Python, Polars, Narwhals, Ibis. Cross-backend parametrised tests.

**Spec:** `docs/superpowers/specs/2026-04-28-expression-gaps-nested-duration-design.md`

---

## File Structure

### New files (10)

| File | Responsibility |
|------|---------------|
| `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_struct.py` | Protocol for struct operations |
| `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_list.py` | Protocol for list operations |
| `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_struct.py` | API builder for `.struct` namespace |
| `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_list.py` | API builder for `.list` namespace |
| `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_struct.py` | Polars struct backend |
| `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_list.py` | Polars list backend |
| `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_struct.py` | Narwhals struct backend |
| `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_list.py` | Narwhals list backend |
| `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_struct.py` | Ibis struct backend |
| `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_list.py` | Ibis list backend |

### Modified files (14)

| File | Changes |
|------|---------|
| `src/mountainash/expressions/core/expression_system/function_keys/enums.py` | Add `FKEY_MOUNTAINASH_SCALAR_STRUCT`, `FKEY_MOUNTAINASH_SCALAR_LIST`, add 4 members to `FKEY_MOUNTAINASH_SCALAR_DATETIME` |
| `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py` | Register struct (1), list (8), and datetime extraction (4) function defs |
| `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py` | Import + export struct and list protocols |
| `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py` | Import + export struct and list API builders |
| `src/mountainash/expressions/core/expression_api/boolean.py` | Add `struct` and `list` NamespaceDescriptors + composed builder classes |
| `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py` | Add `total_seconds/minutes/milliseconds/microseconds` methods |
| `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py` | Add 4 `total_*` protocol methods |
| `src/mountainash/expressions/core/expression_api/entrypoints.py` | Add `duration()` free function |
| `src/mountainash/__init__.py` | Re-export `duration` |
| `src/mountainash/expressions/backends/expression_systems/polars/__init__.py` | Add struct + list backends to composition |
| `src/mountainash/expressions/backends/expression_systems/narwhals/__init__.py` | Add struct + list backends to composition |
| `src/mountainash/expressions/backends/expression_systems/ibis/__init__.py` | Add struct + list backends to composition |
| `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py` | Add `total_*` methods |
| `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py` | Add `total_*` methods |

### Test files (3)

| File | Coverage |
|------|----------|
| `tests/nested/test_struct_field.py` | Struct field extraction, chaining, aggregation |
| `tests/nested/test_list_operations.py` | List sum/min/max/mean/len/contains/sort/unique, Ibis descending guard |
| `tests/temporal/test_duration.py` | Duration constructor, arithmetic, comparison, extraction, sub-second precision |

---

### Task 1: Struct — Full Wiring (Enum → Protocol → API Builder → Function Mapping → Descriptor)

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_keys/enums.py`
- Create: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_struct.py`
- Create: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_struct.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py`
- Modify: `src/mountainash/expressions/core/expression_api/boolean.py`

- [ ] **Step 1: Add FKEY_MOUNTAINASH_SCALAR_STRUCT enum**

In `src/mountainash/expressions/core/expression_system/function_keys/enums.py`, add after the `FKEY_MOUNTAINASH_SCALAR_SET` class (around line 578):

```python
class FKEY_MOUNTAINASH_SCALAR_STRUCT(Enum):
    """Mountainash struct field operations."""
    FIELD = auto()
```

- [ ] **Step 2: Create struct protocol**

Create `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_struct.py`:

```python
"""Protocol for mountainash struct field operations."""
from __future__ import annotations

from typing import Protocol, TypeVar

ExpressionT = TypeVar("ExpressionT")


class MountainAshScalarStructExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for struct field access across backends."""

    def struct_field(self, x: ExpressionT, /, *, field_name: str) -> ExpressionT: ...
```

- [ ] **Step 3: Create struct API builder**

Create `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_struct.py`:

```python
"""Struct operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarStructAPIBuilder(BaseExpressionAPIBuilder):
    """API builder for the .struct namespace."""

    def field(self, name: str) -> BaseExpressionAPI:
        """Extract a named field from a struct column.

        Args:
            name: Field name to extract.

        Returns:
            Expression containing the extracted field value.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
            arguments=[self._node],
            options={"field_name": name},
        )
        return self._build(node)
```

- [ ] **Step 4: Register struct function in definitions.py**

In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`:

Add import at the top (with the other protocol imports):
```python
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash.prtcl_expsys_ext_ma_scalar_struct import MountainAshScalarStructExpressionSystemProtocol
```

Add import for the enum (with the other FKEY imports):
```python
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
```

Add a new function list before the `register_all_functions` aggregation (before line ~1947):
```python
    MOUNTAINASH_STRUCT_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            options=("field_name",),
            protocol_method=MountainAshScalarStructExpressionSystemProtocol.struct_field,
        ),
    ]
```

Add `+ MOUNTAINASH_STRUCT_FUNCTIONS` to the `all_functions` concatenation (after `MOUNTAINASH_NAME_FUNCTIONS` on line 1973).

- [ ] **Step 5: Export struct protocol and API builder**

In `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py`, add:
```python
from .prtcl_expsys_ext_ma_scalar_struct import MountainAshScalarStructExpressionSystemProtocol
```
And add `"MountainAshScalarStructExpressionSystemProtocol"` to `__all__`.

In `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py`, add:
```python
from .api_bldr_ext_ma_scalar_struct import MountainAshScalarStructAPIBuilder
```
And add `"MountainAshScalarStructAPIBuilder"` to `__all__`.

- [ ] **Step 6: Register .struct descriptor on BooleanExpressionAPI**

In `src/mountainash/expressions/core/expression_api/boolean.py`:

Add import (with the other extension builder imports around line 34):
```python
from .api_builders.extensions_mountainash import MountainAshScalarStructAPIBuilder
```

Add composed builder class (after `StringAPIBuilder`, around line 70):
```python
class StructAPIBuilder(MountainAshScalarStructAPIBuilder):
    """Unified struct builder for the .struct namespace."""
    pass
```

Add descriptor to `BooleanExpressionAPI` class (after the existing `name = NamespaceDescriptor(...)` line):
```python
    struct = NamespaceDescriptor(StructAPIBuilder)
```

- [ ] **Step 7: Verify import chain works**

Run: `~/.venv/bin/hatch -e dev run python -c "import mountainash as ma; expr = ma.col('x').struct; print(type(expr))"`

Expected: Prints the `StructAPIBuilder` class type without import errors.

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/expressions/core/expression_system/function_keys/enums.py \
       src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_struct.py \
       src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py \
       src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_struct.py \
       src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py \
       src/mountainash/expressions/core/expression_api/boolean.py \
       src/mountainash/expressions/core/expression_system/function_mapping/definitions.py
git commit -m "feat: wire struct.field() through enum, protocol, API builder, and function mapping"
```

---

### Task 2: Struct — Backend Implementations + Tests

**Files:**
- Create: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_struct.py`
- Create: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_struct.py`
- Create: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_struct.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/__init__.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/__init__.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/__init__.py`
- Create: `tests/nested/test_struct_field.py`

- [ ] **Step 1: Create Polars struct backend**

Create `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_struct.py`:

```python
"""Polars backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem


class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem):
    """Polars implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
```

- [ ] **Step 2: Create Narwhals struct backend**

Create `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_struct.py`:

```python
"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem


class MountainAshNarwhalsScalarStructExpressionSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
```

- [ ] **Step 3: Create Ibis struct backend**

Create `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_struct.py`:

```python
"""Ibis backend for mountainash struct operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem


class MountainAshIbisScalarStructExpressionSystem(IbisBaseExpressionSystem):
    """Ibis implementation of struct field access."""

    def struct_field(self, x, /, *, field_name: str):
        return x[field_name]
```

- [ ] **Step 4: Compose backends into ExpressionSystem classes**

In `src/mountainash/expressions/backends/expression_systems/polars/__init__.py`:

Add import (after `MountainAshPolarsWindowExpressionSystem` import, line 48):
```python
from .extensions_mountainash.expsys_pl_ext_ma_scalar_struct import MountainAshPolarsScalarStructExpressionSystem
```

Add to `PolarsExpressionSystem` base classes (after `MountainAshPolarsWindowExpressionSystem`, line 86):
```python
    MountainAshPolarsScalarStructExpressionSystem,
```

**Repeat the same pattern for Narwhals and Ibis `__init__.py` files**, using the corresponding class names:
- Narwhals: `MountainAshNarwhalsScalarStructExpressionSystem`
- Ibis: `MountainAshIbisScalarStructExpressionSystem`

- [ ] **Step 5: Write struct tests**

Create `tests/nested/__init__.py` (empty file).

Create `tests/nested/test_struct_field.py`:

```python
"""Tests for struct field access."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def struct_df():
    return pl.DataFrame({
        "reaction": [
            {"emoji": "thumbs_up", "count": 5},
            {"emoji": "heart", "count": 3},
            {"emoji": "laugh", "count": 10},
        ],
    })


class TestStructField:
    def test_extract_string_field(self, struct_df):
        """struct.field() extracts a named field from a struct column."""
        expr = ma.col("reaction").struct.field("emoji")
        result = struct_df.with_columns(expr.compile(struct_df).alias("emoji"))
        assert result["emoji"].to_list() == ["thumbs_up", "heart", "laugh"]

    def test_extract_numeric_field(self, struct_df):
        """struct.field() extracts numeric fields."""
        expr = ma.col("reaction").struct.field("count")
        result = struct_df.with_columns(expr.compile(struct_df).alias("count"))
        assert result["count"].to_list() == [5, 3, 10]

    def test_chain_into_string_namespace(self, struct_df):
        """Extracted field chains into typed namespace."""
        expr = ma.col("reaction").struct.field("emoji").str.upper()
        result = struct_df.with_columns(expr.compile(struct_df).alias("upper_emoji"))
        assert result["upper_emoji"].to_list() == ["THUMBS_UP", "HEART", "LAUGH"]

    def test_aggregate_extracted_field(self, struct_df):
        """Extracted numeric field can be aggregated."""
        expr = ma.col("reaction").struct.field("count").sum()
        result = struct_df.select(expr.compile(struct_df).alias("total"))
        assert result["total"].to_list() == [18]

    def test_filter_on_extracted_field(self, struct_df):
        """Extracted field can be used in filter predicates."""
        expr = ma.col("reaction").struct.field("count") > ma.lit(4)
        result = struct_df.with_columns(expr.compile(struct_df).alias("popular"))
        assert result["popular"].to_list() == [True, False, True]
```

- [ ] **Step 6: Run tests**

Run: `~/.venv/bin/hatch -e dev run pytest tests/nested/test_struct_field.py -v`

Expected: All 5 tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_struct.py \
       src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_struct.py \
       src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_struct.py \
       src/mountainash/expressions/backends/expression_systems/polars/__init__.py \
       src/mountainash/expressions/backends/expression_systems/narwhals/__init__.py \
       src/mountainash/expressions/backends/expression_systems/ibis/__init__.py \
       tests/nested/__init__.py \
       tests/nested/test_struct_field.py
git commit -m "feat: add struct.field() backend implementations and tests"
```

---

### Task 3: List — Full Wiring (Enum → Protocol → API Builder → Function Mapping → Descriptor)

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_keys/enums.py`
- Create: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_list.py`
- Create: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_list.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py`
- Modify: `src/mountainash/expressions/core/expression_api/boolean.py`

- [ ] **Step 1: Add FKEY_MOUNTAINASH_SCALAR_LIST enum**

In `src/mountainash/expressions/core/expression_system/function_keys/enums.py`, add after the `FKEY_MOUNTAINASH_SCALAR_STRUCT` class:

```python
class FKEY_MOUNTAINASH_SCALAR_LIST(Enum):
    """Mountainash list operations."""
    SUM = auto()
    MIN = auto()
    MAX = auto()
    MEAN = auto()
    LEN = auto()
    CONTAINS = auto()
    SORT = auto()
    UNIQUE = auto()
```

- [ ] **Step 2: Create list protocol**

Create `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_list.py`:

```python
"""Protocol for mountainash list operations."""
from __future__ import annotations

from typing import Protocol, TypeVar

ExpressionT = TypeVar("ExpressionT")


class MountainAshScalarListExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for list operations across backends."""

    def list_sum(self, x: ExpressionT, /) -> ExpressionT: ...

    def list_min(self, x: ExpressionT, /) -> ExpressionT: ...

    def list_max(self, x: ExpressionT, /) -> ExpressionT: ...

    def list_mean(self, x: ExpressionT, /) -> ExpressionT: ...

    def list_len(self, x: ExpressionT, /) -> ExpressionT: ...

    def list_contains(self, x: ExpressionT, /, item: ExpressionT) -> ExpressionT: ...

    def list_sort(self, x: ExpressionT, /, *, descending: bool = False) -> ExpressionT: ...

    def list_unique(self, x: ExpressionT, /) -> ExpressionT: ...
```

- [ ] **Step 3: Create list API builder**

Create `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_list.py`:

```python
"""List operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarListAPIBuilder(BaseExpressionAPIBuilder):
    """API builder for the .list namespace."""

    def sum(self) -> BaseExpressionAPI:
        """Sum all elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
            arguments=[self._node],
        )
        return self._build(node)

    def min(self) -> BaseExpressionAPI:
        """Minimum element in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MIN,
            arguments=[self._node],
        )
        return self._build(node)

    def max(self) -> BaseExpressionAPI:
        """Maximum element in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MAX,
            arguments=[self._node],
        )
        return self._build(node)

    def mean(self) -> BaseExpressionAPI:
        """Mean of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEAN,
            arguments=[self._node],
        )
        return self._build(node)

    def len(self) -> BaseExpressionAPI:
        """Count of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.LEN,
            arguments=[self._node],
        )
        return self._build(node)

    def contains(self, item: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Check if each list contains the given item.

        Args:
            item: Value or expression to search for.
        """
        item_node = self._to_substrait_node(item)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS,
            arguments=[self._node, item_node],
        )
        return self._build(node)

    def sort(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Sort elements in each list.

        Args:
            descending: Sort in descending order. Not supported on Ibis.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            arguments=[self._node],
            options={"descending": descending},
        )
        return self._build(node)

    def unique(self) -> BaseExpressionAPI:
        """Distinct elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.UNIQUE,
            arguments=[self._node],
        )
        return self._build(node)
```

- [ ] **Step 4: Register list functions in definitions.py**

In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`:

Add imports at the top:
```python
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash.prtcl_expsys_ext_ma_scalar_list import MountainAshScalarListExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
```

Add a new function list before the `register_all_functions` aggregation:
```python
    MOUNTAINASH_LIST_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_sum,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MIN,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_min,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MAX,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_max,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEAN,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_mean,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.LEN,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_len,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_contains,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            options=("descending",),
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_sort,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.UNIQUE,
            substrait_uri=None,
            substrait_name=None,
            is_extension=True,
            protocol_method=MountainAshScalarListExpressionSystemProtocol.list_unique,
        ),
    ]
```

Add `+ MOUNTAINASH_LIST_FUNCTIONS` to the `all_functions` concatenation.

- [ ] **Step 5: Export list protocol and API builder**

In `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py`, add:
```python
from .prtcl_expsys_ext_ma_scalar_list import MountainAshScalarListExpressionSystemProtocol
```
And add `"MountainAshScalarListExpressionSystemProtocol"` to `__all__`.

In `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py`, add:
```python
from .api_bldr_ext_ma_scalar_list import MountainAshScalarListAPIBuilder
```
And add `"MountainAshScalarListAPIBuilder"` to `__all__`.

- [ ] **Step 6: Register .list descriptor on BooleanExpressionAPI**

In `src/mountainash/expressions/core/expression_api/boolean.py`:

Add import:
```python
from .api_builders.extensions_mountainash import MountainAshScalarListAPIBuilder
```

Add composed builder class (after `StructAPIBuilder`):
```python
class ListAPIBuilder(MountainAshScalarListAPIBuilder):
    """Unified list builder for the .list namespace."""
    pass
```

Add descriptor to `BooleanExpressionAPI`:
```python
    list = NamespaceDescriptor(ListAPIBuilder)
```

- [ ] **Step 7: Verify import chain**

Run: `~/.venv/bin/hatch -e dev run python -c "import mountainash as ma; expr = ma.col('x').list; print(type(expr))"`

Expected: Prints the `ListAPIBuilder` class type without import errors.

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/expressions/core/expression_system/function_keys/enums.py \
       src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_list.py \
       src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/__init__.py \
       src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_list.py \
       src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/__init__.py \
       src/mountainash/expressions/core/expression_api/boolean.py \
       src/mountainash/expressions/core/expression_system/function_mapping/definitions.py
git commit -m "feat: wire list operations through enum, protocol, API builder, and function mapping"
```

---

### Task 4: List — Backend Implementations + Tests

**Files:**
- Create: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_list.py`
- Create: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_list.py`
- Create: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_list.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/__init__.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/__init__.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/__init__.py`
- Create: `tests/nested/test_list_operations.py`

- [ ] **Step 1: Create Polars list backend**

Create `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_list.py`:

```python
"""Polars backend for mountainash list operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem


class MountainAshPolarsScalarListExpressionSystem(PolarsBaseExpressionSystem):
    """Polars implementation of list operations."""

    def list_sum(self, x, /):
        return x.list.sum()

    def list_min(self, x, /):
        return x.list.min()

    def list_max(self, x, /):
        return x.list.max()

    def list_mean(self, x, /):
        return x.list.mean()

    def list_len(self, x, /):
        return x.list.len()

    def list_contains(self, x, /, item):
        return x.list.contains(item)

    def list_sort(self, x, /, *, descending: bool = False):
        return x.list.sort(descending=descending)

    def list_unique(self, x, /):
        return x.list.unique()
```

- [ ] **Step 2: Create Narwhals list backend**

Create `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_list.py`:

```python
"""Narwhals backend for mountainash list operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem


class MountainAshNarwhalsScalarListExpressionSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of list operations."""

    def list_sum(self, x, /):
        return x.list.sum()

    def list_min(self, x, /):
        return x.list.min()

    def list_max(self, x, /):
        return x.list.max()

    def list_mean(self, x, /):
        return x.list.mean()

    def list_len(self, x, /):
        return x.list.len()

    def list_contains(self, x, /, item):
        return x.list.contains(item)

    def list_sort(self, x, /, *, descending: bool = False):
        return x.list.sort(descending=descending)

    def list_unique(self, x, /):
        return x.list.unique()
```

- [ ] **Step 3: Create Ibis list backend**

Create `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_list.py`:

```python
"""Ibis backend for mountainash list operations."""
from __future__ import annotations

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem


class MountainAshIbisScalarListExpressionSystem(IbisBaseExpressionSystem):
    """Ibis implementation of list operations."""

    def list_sum(self, x, /):
        return x.sums()

    def list_min(self, x, /):
        return x.mins()

    def list_max(self, x, /):
        return x.maxs()

    def list_mean(self, x, /):
        return x.means()

    def list_len(self, x, /):
        return x.length()

    def list_contains(self, x, /, item):
        return x.contains(item)

    def list_sort(self, x, /, *, descending: bool = False):
        if descending:
            raise BackendCapabilityError(
                "Ibis ArrayValue.sort() does not support descending order. "
                "Use ascending sort, or use Polars/Narwhals backend for descending list sort."
            )
        return x.sort()

    def list_unique(self, x, /):
        return x.unique()
```

- [ ] **Step 4: Compose backends into ExpressionSystem classes**

In each backend's `__init__.py`:

**Polars** — add import and base class:
```python
from .extensions_mountainash.expsys_pl_ext_ma_scalar_list import MountainAshPolarsScalarListExpressionSystem
```
Add `MountainAshPolarsScalarListExpressionSystem,` to `PolarsExpressionSystem` base classes.

**Narwhals** — same pattern with `MountainAshNarwhalsScalarListExpressionSystem`.

**Ibis** — same pattern with `MountainAshIbisScalarListExpressionSystem`.

- [ ] **Step 5: Write list tests**

Create `tests/nested/test_list_operations.py`:

```python
"""Tests for list operations."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError


@pytest.fixture
def list_df():
    return pl.DataFrame({
        "scores": [[10, 20, 30], [5, 15], [100]],
        "tags": [["python", "rust"], ["python"], ["go", "rust", "python"]],
    })


class TestListAggregates:
    def test_list_sum(self, list_df):
        expr = ma.col("scores").list.sum()
        result = list_df.with_columns(expr.compile(list_df).alias("total"))
        assert result["total"].to_list() == [60, 20, 100]

    def test_list_min(self, list_df):
        expr = ma.col("scores").list.min()
        result = list_df.with_columns(expr.compile(list_df).alias("lo"))
        assert result["lo"].to_list() == [10, 5, 100]

    def test_list_max(self, list_df):
        expr = ma.col("scores").list.max()
        result = list_df.with_columns(expr.compile(list_df).alias("hi"))
        assert result["hi"].to_list() == [30, 15, 100]

    def test_list_mean(self, list_df):
        expr = ma.col("scores").list.mean()
        result = list_df.with_columns(expr.compile(list_df).alias("avg"))
        assert result["avg"].to_list() == [20.0, 10.0, 100.0]

    def test_list_len(self, list_df):
        expr = ma.col("scores").list.len()
        result = list_df.with_columns(expr.compile(list_df).alias("n"))
        assert result["n"].to_list() == [3, 2, 1]


class TestListContains:
    def test_contains_literal(self, list_df):
        expr = ma.col("tags").list.contains("python")
        result = list_df.with_columns(expr.compile(list_df).alias("has_py"))
        assert result["has_py"].to_list() == [True, True, True]

    def test_contains_literal_miss(self, list_df):
        expr = ma.col("tags").list.contains("java")
        result = list_df.with_columns(expr.compile(list_df).alias("has_java"))
        assert result["has_java"].to_list() == [False, False, False]


class TestListSort:
    def test_sort_ascending(self, list_df):
        expr = ma.col("scores").list.sort()
        result = list_df.with_columns(expr.compile(list_df).alias("sorted"))
        assert result["sorted"].to_list() == [[10, 20, 30], [5, 15], [100]]

    def test_sort_descending(self, list_df):
        expr = ma.col("scores").list.sort(descending=True)
        result = list_df.with_columns(expr.compile(list_df).alias("sorted"))
        assert result["sorted"].to_list() == [[30, 20, 10], [15, 5], [100]]


class TestListUnique:
    def test_unique(self):
        df = pl.DataFrame({"vals": [[1, 2, 2, 3], [5, 5, 5]]})
        expr = ma.col("vals").list.unique()
        result = df.with_columns(expr.compile(df).alias("uniq"))
        uniq_lists = result["uniq"].to_list()
        assert sorted(uniq_lists[0]) == [1, 2, 3]
        assert sorted(uniq_lists[1]) == [5]


class TestListChaining:
    def test_sum_gt(self, list_df):
        """Chaining: list aggregate result used in comparison."""
        expr = ma.col("scores").list.sum() > ma.lit(50)
        result = list_df.with_columns(expr.compile(list_df).alias("big"))
        assert result["big"].to_list() == [True, False, True]


class TestIbisDescendingSortGuard:
    def test_ibis_descending_raises(self):
        """Ibis must raise BackendCapabilityError for descending list sort."""
        import ibis

        con = ibis.duckdb.connect()
        t = con.create_table("_test_list", {"scores": [[3, 1, 2]]})

        expr = ma.col("scores").list.sort(descending=True)
        with pytest.raises(BackendCapabilityError, match="descending"):
            expr.compile(t)
```

- [ ] **Step 6: Run tests**

Run: `~/.venv/bin/hatch -e dev run pytest tests/nested/test_list_operations.py -v`

Expected: All tests pass, including the Ibis descending guard test.

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_list.py \
       src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_list.py \
       src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_list.py \
       src/mountainash/expressions/backends/expression_systems/polars/__init__.py \
       src/mountainash/expressions/backends/expression_systems/narwhals/__init__.py \
       src/mountainash/expressions/backends/expression_systems/ibis/__init__.py \
       tests/nested/test_list_operations.py
git commit -m "feat: add list operations backend implementations and tests"
```

---

### Task 5: Duration — Constructor + Re-export

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/entrypoints.py`
- Modify: `src/mountainash/__init__.py`
- Create: `tests/temporal/test_duration.py` (constructor tests only — extraction tests in Task 7)

- [ ] **Step 1: Add duration() to entrypoints.py**

In `src/mountainash/expressions/core/expression_api/entrypoints.py`, add (after the `lit()` function):

```python
def duration(
    *,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    milliseconds: int = 0,
    microseconds: int = 0,
) -> BaseExpressionAPI:
    """Create a duration literal expression.

    All parameters are keyword-only and literal-only (int, not Expr).

    Args:
        weeks: Number of weeks.
        days: Number of days.
        hours: Number of hours.
        minutes: Number of minutes.
        seconds: Number of seconds.
        milliseconds: Number of milliseconds.
        microseconds: Number of microseconds.

    Returns:
        Expression wrapping a timedelta literal.
    """
    from datetime import timedelta

    td = timedelta(
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
        microseconds=microseconds,
    )
    return lit(td)
```

Add `"duration"` to the `__all__` list in entrypoints.py.

- [ ] **Step 2: Re-export duration in top-level __init__.py**

In `src/mountainash/__init__.py`, add `duration` to the import from `mountainash.expressions`:

```python
from mountainash.expressions import (
    # ... existing imports ...
    duration,
)
```

Also ensure `duration` is exported from `src/mountainash/expressions/__init__.py` — add it to the imports from `entrypoints` if not already there.

- [ ] **Step 3: Write constructor and arithmetic tests**

Create `tests/temporal/test_duration.py`:

```python
"""Tests for duration constructor and arithmetic."""
from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl
import pytest

import mountainash as ma


class TestDurationConstructor:
    def test_basic_construction(self):
        """ma.duration() creates a timedelta-backed literal."""
        expr = ma.duration(hours=4)
        node = expr._node
        assert node.value == timedelta(hours=4)

    def test_combined_units(self):
        """Multiple units combine correctly."""
        expr = ma.duration(days=1, hours=2, minutes=30)
        node = expr._node
        assert node.value == timedelta(days=1, hours=2, minutes=30)

    def test_keyword_only(self):
        """duration() rejects positional arguments."""
        with pytest.raises(TypeError):
            ma.duration(1)

    def test_sub_second_precision(self):
        """Millisecond and microsecond precision preserved."""
        expr = ma.duration(milliseconds=500)
        assert expr._node.value == timedelta(milliseconds=500)

        expr2 = ma.duration(microseconds=1500)
        assert expr2._node.value == timedelta(microseconds=1500)


class TestDurationArithmetic:
    @pytest.fixture
    def ts_df(self):
        return pl.DataFrame({
            "ts": [datetime(2026, 1, 1, 12, 0, 0)],
        })

    def test_add_duration(self, ts_df):
        """col + ma.duration() offsets the timestamp."""
        expr = ma.col("ts") + ma.duration(days=7)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        assert result["offset"][0] == datetime(2026, 1, 8, 12, 0, 0)

    def test_subtract_duration(self, ts_df):
        """col - ma.duration() offsets the timestamp backwards."""
        expr = ma.col("ts") - ma.duration(hours=1)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        assert result["offset"][0] == datetime(2026, 1, 1, 11, 0, 0)

    def test_sub_second_arithmetic(self, ts_df):
        """Sub-second duration arithmetic preserves precision."""
        expr = ma.col("ts") + ma.duration(milliseconds=500)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        expected = datetime(2026, 1, 1, 12, 0, 0, 500_000)
        assert result["offset"][0] == expected

    def test_microsecond_arithmetic(self, ts_df):
        """Microsecond duration arithmetic preserves precision."""
        expr = ma.col("ts") + ma.duration(microseconds=1500)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        expected = datetime(2026, 1, 1, 12, 0, 0, 1500)
        assert result["offset"][0] == expected


class TestDurationComparison:
    def test_duration_gt(self):
        """Duration comparison works on Polars."""
        df = pl.DataFrame({
            "gap": [timedelta(hours=1), timedelta(hours=5), timedelta(hours=10)],
        })
        expr = ma.col("gap") > ma.duration(hours=4)
        result = df.with_columns(expr.compile(df).alias("long_gap"))
        assert result["long_gap"].to_list() == [False, True, True]
```

- [ ] **Step 4: Run tests**

Run: `~/.venv/bin/hatch -e dev run pytest tests/temporal/test_duration.py -v`

Expected: All tests pass. If `timedelta` literal handling fails on any backend, the test will reveal which backend's `lit()` method needs a `timedelta` branch.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/entrypoints.py \
       src/mountainash/__init__.py \
       src/mountainash/expressions/__init__.py \
       tests/temporal/test_duration.py
git commit -m "feat: add ma.duration() constructor with timedelta literal support"
```

---

### Task 6: Duration — Extraction Methods (total_seconds/minutes/milliseconds/microseconds)

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_keys/enums.py`
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`

- [ ] **Step 1: Add TOTAL_* enum members**

In `src/mountainash/expressions/core/expression_system/function_keys/enums.py`, add to the `FKEY_MOUNTAINASH_SCALAR_DATETIME` enum (after `DIFF_MILLISECONDS`):

```python
    # Duration extraction (total elapsed)
    TOTAL_SECONDS = auto()
    TOTAL_MINUTES = auto()
    TOTAL_MILLISECONDS = auto()
    TOTAL_MICROSECONDS = auto()
```

- [ ] **Step 2: Add protocol methods**

In `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py`, add (after `days_in_month`):

```python
    def total_seconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total seconds in a duration."""
        ...

    def total_minutes(self, x: ExpressionT, /) -> ExpressionT:
        """Total minutes in a duration."""
        ...

    def total_milliseconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total milliseconds in a duration."""
        ...

    def total_microseconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total microseconds in a duration."""
        ...
```

- [ ] **Step 3: Add API builder methods**

In `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py`, add (before the aliases block at the end):

```python
    def total_seconds(self) -> BaseExpressionAPI:
        """Total seconds in a duration."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS,
            arguments=[self._node],
        )
        return self._build(node)

    def total_minutes(self) -> BaseExpressionAPI:
        """Total minutes in a duration."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES,
            arguments=[self._node],
        )
        return self._build(node)

    def total_milliseconds(self) -> BaseExpressionAPI:
        """Total milliseconds in a duration."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS,
            arguments=[self._node],
        )
        return self._build(node)

    def total_microseconds(self) -> BaseExpressionAPI:
        """Total microseconds in a duration."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS,
            arguments=[self._node],
        )
        return self._build(node)
```

- [ ] **Step 4: Register function mappings**

In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`, add to the `MOUNTAINASH_DATETIME_FUNCTIONS` list:

```python
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_seconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_seconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_minutes",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_minutes,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_milliseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_milliseconds,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS,
            substrait_uri=MountainashExtension.DATETIME,
            substrait_name="total_microseconds",
            is_extension=True,
            protocol_method=MountainAshScalarDatetimeExpressionSystemProtocol.total_microseconds,
        ),
```

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/core/expression_system/function_keys/enums.py \
       src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py \
       src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py \
       src/mountainash/expressions/core/expression_system/function_mapping/definitions.py
git commit -m "feat: wire duration extraction methods through enum, protocol, API builder, and function mapping"
```

---

### Task 7: Duration — Extraction Backend Implementations + Tests

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py`
- Modify: `tests/temporal/test_duration.py`

- [ ] **Step 1: Add Polars total_* implementations**

In `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py`, add (after `days_in_month`):

```python
    def total_seconds(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.total_seconds()

    def total_minutes(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.total_minutes()

    def total_milliseconds(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.total_milliseconds()

    def total_microseconds(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.total_microseconds()
```

- [ ] **Step 2: Add Narwhals total_* implementations**

In `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py`, add:

```python
    def total_seconds(self, input, /):
        return input.dt.total_seconds()

    def total_minutes(self, input, /):
        return input.dt.total_minutes()

    def total_milliseconds(self, input, /):
        return input.dt.total_milliseconds()

    def total_microseconds(self, input, /):
        return input.dt.total_microseconds()
```

- [ ] **Step 3: Add Ibis total_* implementations (raise NotImplementedError)**

In `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py`, add:

```python
    def total_seconds(self, input, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_seconds() method. "
            "Use dt.diff_minutes() or dt.diff_seconds() for integer-based extraction."
        )

    def total_minutes(self, input, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_minutes() method. "
            "Use dt.diff_minutes() for integer-based extraction."
        )

    def total_milliseconds(self, input, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_milliseconds() method. "
            "Use dt.diff_milliseconds() for integer-based extraction."
        )

    def total_microseconds(self, input, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_microseconds() method. "
            "Use integer arithmetic on dt.diff_seconds() for sub-second extraction."
        )
```

- [ ] **Step 4: Add extraction tests**

Append to `tests/temporal/test_duration.py`:

```python
class TestDurationExtraction:
    @pytest.fixture
    def duration_df(self):
        return pl.DataFrame({
            "gap": [
                timedelta(hours=1, minutes=30),
                timedelta(hours=2, seconds=45),
                timedelta(days=1, hours=12),
            ],
        })

    def test_total_seconds(self, duration_df):
        expr = ma.col("gap").dt.total_seconds()
        result = duration_df.with_columns(expr.compile(duration_df).alias("secs"))
        assert result["secs"].to_list() == [5400, 7245, 129600]

    def test_total_minutes(self, duration_df):
        expr = ma.col("gap").dt.total_minutes()
        result = duration_df.with_columns(expr.compile(duration_df).alias("mins"))
        assert result["mins"].to_list() == [90, 120, 2160]

    def test_total_milliseconds(self, duration_df):
        expr = ma.col("gap").dt.total_milliseconds()
        result = duration_df.with_columns(expr.compile(duration_df).alias("ms"))
        assert result["ms"].to_list() == [5400000, 7245000, 129600000]

    def test_total_microseconds(self, duration_df):
        expr = ma.col("gap").dt.total_microseconds()
        result = duration_df.with_columns(expr.compile(duration_df).alias("us"))
        assert result["us"].to_list() == [5400000000, 7245000000, 129600000000]
```

- [ ] **Step 5: Run all duration tests**

Run: `~/.venv/bin/hatch -e dev run pytest tests/temporal/test_duration.py -v`

Expected: All tests pass on Polars.

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py \
       src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py \
       src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py \
       tests/temporal/test_duration.py
git commit -m "feat: add duration extraction backends and tests"
```

---

### Task 8: Full Test Suite Run + Ruff

**Files:**
- Possibly any file that needs lint fixes

- [ ] **Step 1: Run ruff check**

Run: `~/.venv/bin/hatch run ruff:check`

Fix any lint issues (unused imports, missing `__future__` annotations, etc.).

- [ ] **Step 2: Run full test suite**

Run: `~/.venv/bin/hatch -e dev run pytest tests/ -x -q`

Expected: All existing tests pass. No regressions from adding new namespaces or enum members.

- [ ] **Step 3: Run the argument type coverage guard**

Run: `~/.venv/bin/hatch -e dev run pytest tests/cross_backend/argument_types/ -v`

If the coverage guard (`test_every_argument_param_is_tested`) fails because the new struct/list/duration function keys have parameters not covered by `TESTED_PARAMS`, add the missing entries to the appropriate `test_arg_types_*.py` file (or create a new one).

Follow the pattern in `tests/cross_backend/argument_types/test_arg_types_window.py`:

```python
TESTED_PARAMS: list[tuple] = [
    (FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD, "field_name"),
    (FKEY_MOUNTAINASH_SCALAR_LIST.SUM, "x"),
    (FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, "x"),
    (FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, "item"),
    (FKEY_MOUNTAINASH_SCALAR_LIST.SORT, "descending"),
    # ... etc for all introspected params
]
```

- [ ] **Step 4: Fix any failures**

Address any test failures. Common issues:
- Missing `__init__.py` files in new test directories
- Ruff formatting/import issues
- Coverage guard entries for new function parameters

- [ ] **Step 5: Commit fixes**

```bash
git add -A
git commit -m "chore: fix lint and test coverage guard for struct/list/duration additions"
```

---

## Self-Review Checklist

### Spec coverage
- [x] Gap 5 (struct.field): Tasks 1-2
- [x] Gap 6 (list ops subset — 8 operations): Tasks 3-4
- [x] Gap 15 Duration constructor: Task 5
- [x] Gap 15 Duration extraction (total_*): Tasks 6-7
- [x] Gap 15 Sub-second precision tests: Task 5 (millisecond + microsecond arithmetic tests)
- [x] Ibis descending list sort guard: Task 4 (explicit BackendCapabilityError + test)
- [x] Ibis duration literal precision: Task 5 (uses lit(timedelta) not ibis.interval(seconds=int(...)))
- [x] Re-export ma.duration: Task 5
- [x] KNOWN_EXPR_LIMITATIONS for Ibis extraction: Task 7 (raises NotImplementedError)
- [x] Full test suite + lint: Task 8

### Placeholder scan
- No TBD, TODO, or "fill in later" in any task
- All code blocks are complete
- All file paths are exact

### Type consistency
- `field_name: str` consistent across protocol, API builder, backend, and function mapping
- `descending: bool` consistent in list_sort across all layers
- `FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD` used consistently (not `.FIELD_GET` or `.STRUCT_FIELD`)
- `struct_field` method name consistent across protocol and backends
- `list_sum/min/max/mean/len/contains/sort/unique` method names consistent across protocol and backends
- `total_seconds/minutes/milliseconds/microseconds` consistent across enum, protocol, API builder, and backends
