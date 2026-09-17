"""Fact types for the capability spine (spec 2026-07-05, Section 1).

Three fact kinds:
- CapabilityFact  — what a backend can/cannot do per (op, param); gates dispatch.
- DivergenceKind  — result-difference classification; scoped assertions live in declarations.
- KnownGap        — mountainash-side incompleteness; drives verification guards.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from functools import lru_cache
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from mountainash.core.capabilities.identity import Scope
    from mountainash.core.constants import CONST_BACKEND

WILDCARD_PARAM = "*"

_SINCE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_UPSTREAM_REF_RE = re.compile(r"^[A-Z]+-[A-Z]+-\d+$")  # e.g. NW-STR-01, IB-CAST-01
_STALE_AFTER = timedelta(days=183)  # ~6 months (closed-by-default R2)


@dataclass(frozen=True, order=True)
class InputDataRef:
    """Content-addressed immutable data used by a descriptive scenario."""

    content: str
    entry: str

    def __post_init__(self) -> None:
        if type(self.content) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", self.content) is None:
            raise ValueError("input data content must be a lowercase sha256 address")
        if type(self.entry) is not str or not self.entry:
            raise ValueError("input data requires a nonempty entry locator")


def _enum_authorities() -> dict[tuple[str, str], type[Enum]]:
    """Known canonical enum classes; never import an authority by text."""
    from mountainash.core import constants
    from mountainash.core.dtypes.canonical import MountainashDtype
    from mountainash.expressions.core.expression_system.function_keys import enums as function_enums
    from mountainash.relations.core.relation_system.relation_keys import enums as relation_enums
    from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
        CaseFailureBehaviour,
    )

    authorities: dict[tuple[str, str], type[Enum]] = {}
    for module in (constants, function_enums, relation_enums):
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, Enum):
                authorities[(value.__module__, value.__qualname__)] = value
    for value in (
        MountainashDtype,
        CaseFailureBehaviour,
        CapabilityLevel,
        Boundary,
        Enforcement,
        ResidueSignal,
        TargetKind,
        Fidelity,
        ValueClass,
        ClauseOp,
        DivergenceKind,
        GapKind,
        TargetSurface,
        EntrypointStage,
    ):
        authorities[(value.__module__, value.__qualname__)] = value
    return authorities


def _canonical_enum_reference(value: Enum) -> tuple[str, str, str]:
    authority_ref = (type(value).__module__, type(value).__qualname__)
    authority = _enum_authorities().get(authority_ref)
    if authority is None or not isinstance(value, authority):
        raise ValueError(f"unknown enum authority {authority_ref!r}")
    member = authority.__members__.get(value.name)
    if member is None or member is not value:
        raise ValueError(f"unknown enum member {authority_ref!r}.{value.name}")
    return (*authority_ref, member.name)


def _canonical_enum_capture(value: tuple) -> tuple[str, str, str]:
    if len(value) != 3 or any(type(part) is not str or not part for part in value):
        raise ValueError("enum capture requires module, authority and member")
    module, authority_name, member_name = value
    authority = _enum_authorities().get((module, authority_name))
    if authority is None:
        raise ValueError(f"unknown enum authority {(module, authority_name)!r}")
    member = authority.__members__.get(member_name)
    if member is None:
        raise ValueError(f"unknown enum member {(module, authority_name)!r}.{member_name}")
    return module, authority_name, member.name


@dataclass(frozen=True, order=True)
class CaptureValue:
    """Closed canonical value used by descriptive scenario identities."""

    tag: str
    value: str | tuple | InputDataRef

    def __post_init__(self) -> None:
        scalar_tags = {"null", "bool", "integer", "float", "text", "bytes"}
        if self.tag in scalar_tags:
            if type(self.value) is not str:
                raise TypeError("capture scalar content must be canonical text")
            valid = True
            if self.tag == "null":
                valid = self.value == ""
            elif self.tag == "bool":
                valid = self.value in {"true", "false"}
            elif self.tag == "integer":
                valid = str(int(self.value)) == self.value
            elif self.tag == "float":
                valid = self.value in {"nan", "+inf", "-inf"} or (float.fromhex(self.value).hex() == self.value)
            elif self.tag == "bytes":
                valid = bytes.fromhex(self.value).hex() == self.value
            if not valid:
                raise ValueError(f"noncanonical {self.tag} capture")
            return
        if self.tag == "input_data":
            if type(self.value) is not InputDataRef:
                raise TypeError("input-data capture requires InputDataRef")
            return
        if type(self.value) is not tuple:
            raise TypeError("capture containers require immutable tuples")
        if self.tag in {"sequence", "set"}:
            if any(type(item) is not CaptureValue for item in self.value):
                raise TypeError("capture members must be CaptureValue")
            if self.tag == "set":
                object.__setattr__(self, "value", tuple(sorted(set(self.value))))
        elif self.tag == "mapping":
            object.__setattr__(self, "value", _capture_fields(self.value))
        elif self.tag == "enum":
            object.__setattr__(self, "value", _canonical_enum_capture(self.value))
        else:
            raise ValueError(f"unknown capture tag {self.tag!r}")

    @classmethod
    def of(cls, value: Any) -> CaptureValue:
        if value is None:
            return cls("null", "")
        if isinstance(value, Enum):
            return cls("enum", _canonical_enum_reference(value))
        if type(value) is bool:
            return cls("bool", "true" if value else "false")
        if type(value) is int:
            return cls("integer", str(value))
        if type(value) is float:
            encoded = value.hex()
            if encoded == "inf":
                encoded = "+inf"
            return cls("float", encoded)
        if type(value) is str:
            return cls("text", value)
        if type(value) is bytes:
            return cls("bytes", value.hex())
        if type(value) is InputDataRef:
            return cls("input_data", value)
        if type(value) in (tuple, list):
            return cls("sequence", tuple(cls.of(item) for item in value))
        if type(value) in (set, frozenset):
            return cls("set", tuple(cls.of(item) for item in value))
        if type(value) is dict:
            return cls("mapping", tuple((key, cls.of(item)) for key, item in value.items()))
        raise TypeError(f"unsupported capture value type: {type(value).__name__}")


def _capture_fields(fields: tuple) -> tuple:
    if type(fields) is not tuple:
        raise TypeError("scenario fields require an immutable tuple")
    names: set[str] = set()
    for pair in fields:
        if type(pair) is not tuple or len(pair) != 2:
            raise TypeError("scenario fields require (name, CaptureValue) pairs")
        name, value = pair
        if type(name) is not str or type(value) is not CaptureValue:
            raise TypeError("scenario fields require text names and CaptureValue values")
        if name in names:
            raise ValueError(f"duplicate scenario field {name!r}")
        names.add(name)
    return tuple(sorted(fields))


@dataclass(frozen=True, order=True)
class Scenario:
    arguments: tuple[tuple[str, CaptureValue], ...] = ()
    options: tuple[tuple[str, CaptureValue], ...] = ()
    input_schema: tuple[tuple[str, CaptureValue], ...] = ()
    input_data: tuple[tuple[str, CaptureValue], ...] = ()
    execution: tuple[tuple[str, CaptureValue], ...] = ()

    def __post_init__(self) -> None:
        for name in ("arguments", "options", "input_schema", "input_data", "execution"):
            object.__setattr__(self, name, _capture_fields(getattr(self, name)))


class TargetSurface(Enum):
    EXPRESSION = "expression"
    RELATION = "relation"


class EntrypointStage(Enum):
    CONSTRUCTION = "construction"
    COMPILATION = "compilation"
    MATERIALIZATION = "materialization"


def _callable_address(value: Any) -> tuple[str, str] | None:
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if type(module) is str and type(qualname) is str:
        return module, qualname
    return None


def _record_callable(
    inventory: dict[tuple[str, str], tuple[tuple[str, str], Any]],
    module: str,
    qualname: str,
    value: Any,
) -> None:
    canonical = _callable_address(value)
    if canonical is not None:
        authority = canonical, value
        inventory[(module, qualname)] = authority
        inventory.setdefault(canonical, authority)


def _record_class(
    inventory: dict[tuple[str, str], tuple[tuple[str, str], Any]],
    module: str,
    name: str,
    cls: type,
) -> None:
    _record_callable(inventory, module, name, cls)
    for base in cls.__mro__:
        for method_name, member in vars(base).items():
            if method_name.startswith("_") or not callable(member):
                continue
            _record_callable(inventory, module, f"{name}.{method_name}", member)


@lru_cache(maxsize=1)
def _target_inventory() -> tuple[
    dict[tuple[str, str], tuple[tuple[str, str], Any]],
    dict[tuple[str, str], TargetSurface],
    dict[tuple[str, str], tuple[type, TargetSurface]],
]:
    """Discover the fixed public callable and protocol authorities."""
    import mountainash.expressions.core.expression_api as expression_api_package
    import mountainash.expressions.core.expression_api.boolean as expression_api
    import mountainash.relations.core.relation_api as relation_api_package
    import mountainash.validation as validation_api
    from mountainash.expressions.core.expression_api import entrypoints
    from mountainash.expressions.core.utils import temporal as temporal_utilities
    from mountainash.relations.core.relation_api.relation import (
        GroupedRelation,
        Relation,
        concat,
        relation,
    )
    from mountainash.expressions.core.expression_api.api_builders import (
        extensions_mountainash as expression_extension_builders,
    )
    from mountainash.expressions.core.expression_api.api_builders import (
        substrait as expression_substrait_builders,
    )
    from mountainash.expressions.core.expression_protocols.api_builders import (
        extensions_mountainash as expression_extension_builder_protocols,
    )
    from mountainash.expressions.core.expression_protocols.api_builders import (
        substrait as expression_substrait_builder_protocols,
    )
    from mountainash.expressions.core.expression_protocols.expression_systems import (
        extensions_mountainash as expression_extension_protocols,
    )
    from mountainash.expressions.core.expression_protocols.expression_systems import (
        substrait as expression_substrait_protocols,
    )
    from mountainash.relations.core.relation_api import api_builders as relation_builders
    from mountainash.relations.core import relation_protocols
    from mountainash.relations.core.relation_protocols import (
        api_builders as relation_builder_protocols,
    )
    from mountainash.relations.core.relation_protocols.relation_systems import (
        extensions_mountainash as relation_extension_protocols,
    )
    from mountainash.relations.core.relation_protocols.relation_systems import (
        substrait as relation_substrait_protocols,
    )

    inventory: dict[tuple[str, str], tuple[tuple[str, str], Any]] = {}
    surfaces: dict[tuple[str, str], TargetSurface] = {}
    protocols: dict[tuple[str, str], tuple[type, TargetSurface]] = {}

    for name in ("within_last", "older_than", "between_last"):
        value = getattr(temporal_utilities, name)
        _record_callable(inventory, temporal_utilities.__name__, name, value)
        canonical = _callable_address(value)
        if canonical is not None:
            surfaces[canonical] = TargetSurface.EXPRESSION
    for name in entrypoints.__all__:
        value = getattr(entrypoints, name)
        _record_callable(inventory, entrypoints.__name__, name, value)
        canonical = _callable_address(value)
        if canonical is not None:
            surfaces[canonical] = TargetSurface.EXPRESSION
    for name in entrypoints.__all__:
        if hasattr(expression_api_package, name):
            _record_callable(
                inventory,
                expression_api_package.__name__,
                name,
                getattr(expression_api_package, name),
            )

    for module, surface in (
        (expression_substrait_builders, TargetSurface.EXPRESSION),
        (expression_extension_builders, TargetSurface.EXPRESSION),
        (relation_builders, TargetSurface.RELATION),
    ):
        for name in module.__all__:
            value = getattr(module, name)
            if not inspect.isclass(value):
                continue
            _record_class(inventory, module.__name__, name, value)
            canonical = _callable_address(value)
            if canonical is not None:
                surfaces[canonical] = surface
            for base in value.__mro__:
                for method_name, member in vars(base).items():
                    if method_name.startswith("_") or not callable(member):
                        continue
                    address = _callable_address(member)
                    if address is not None:
                        surfaces[address] = surface
    _record_class(
        inventory,
        validation_api.__name__,
        "ValidationRunner",
        validation_api.ValidationRunner,
    )
    for cls in (
        expression_api.BooleanExpressionAPI,
        expression_api.StringAPIBuilder,
        expression_api.DatetimeAPIBuilder,
        expression_api.StructAPIBuilder,
        expression_api.ListAPIBuilder,
        expression_api.CategoricalAPIBuilder,
        expression_api.GeospatialAPIBuilder,
        Relation,
        GroupedRelation,
        validation_api.ValidationRunner,
    ):
        _record_class(inventory, cls.__module__, cls.__qualname__, cls)
        surface = (
            TargetSurface.EXPRESSION
            if cls.__module__.startswith("mountainash.expressions.")
            else TargetSurface.RELATION
        )
        canonical = _callable_address(cls)
        if canonical is not None:
            surfaces[canonical] = surface
        for base in cls.__mro__:
            for method_name, member in vars(base).items():
                if method_name.startswith("_") or not callable(member):
                    continue
                address = _callable_address(member)
                if address is not None:
                    surfaces[address] = surface
    for name, value in (("relation", relation), ("concat", concat)):
        _record_callable(inventory, value.__module__, name, value)
        _record_callable(
            inventory,
            relation_api_package.__name__,
            name,
            getattr(relation_api_package, name),
        )
        canonical = _callable_address(value)
        if canonical is not None:
            surfaces[canonical] = TargetSurface.RELATION

    for module, surface in (
        (expression_substrait_protocols, TargetSurface.EXPRESSION),
        (expression_extension_protocols, TargetSurface.EXPRESSION),
        (expression_substrait_builder_protocols, TargetSurface.EXPRESSION),
        (expression_extension_builder_protocols, TargetSurface.EXPRESSION),
        (relation_protocols, TargetSurface.RELATION),
        (relation_builder_protocols, TargetSurface.RELATION),
        (relation_substrait_protocols, TargetSurface.RELATION),
        (relation_extension_protocols, TargetSurface.RELATION),
    ):
        for name in module.__all__:
            value = getattr(module, name)
            if not inspect.isclass(value):
                continue
            _record_class(inventory, module.__name__, name, value)
            canonical = _callable_address(value)
            if canonical is not None:
                protocols[canonical] = (value, surface)

    import sys

    root_exports = vars(sys.modules["mountainash"]).get("_LAZY_EXPORTS", ())
    for module_name in ("mountainash.expressions", "mountainash.relations"):
        exports = vars(sys.modules[module_name])
        for name in exports["__all__"]:
            value = exports.get(name)
            canonical = _callable_address(value)
            if canonical not in surfaces:
                continue
            if inspect.isclass(value):
                _record_class(inventory, module_name, name, value)
                if name in root_exports:
                    _record_class(inventory, "mountainash", name, value)
            else:
                _record_callable(inventory, module_name, name, value)
                if name in root_exports:
                    _record_callable(inventory, "mountainash", name, value)

    return inventory, surfaces, protocols


@dataclass(frozen=True, order=True)
class CallableRef:
    module: str
    qualname: str

    def __post_init__(self) -> None:
        if type(self.module) is not str or type(self.qualname) is not str:
            raise TypeError("callable reference requires text module and qualname")
        authority = _target_inventory()[0].get((self.module, self.qualname))
        if authority is None:
            raise ValueError(
                f"unknown callable reference {self.module}.{self.qualname}; "
                "references must name a captured public callable"
            )
        canonical = authority[0]
        object.__setattr__(self, "module", canonical[0])
        object.__setattr__(self, "qualname", canonical[1])


def _resolve_operation(operation: Enum) -> None:
    if not isinstance(operation, Enum):
        raise TypeError("operation target requires an enum member")
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    try:
        ExpressionFunctionRegistry.get(operation)
    except KeyError:
        try:
            RelationOperationRegistry.get(operation)
        except KeyError:
            raise ValueError(f"unknown operation reference {operation!r}") from None


@dataclass(frozen=True)
class OperationTarget:
    operation: Enum

    def __post_init__(self) -> None:
        _resolve_operation(self.operation)


@dataclass(frozen=True)
class CompositionTarget:
    surface: TargetSurface
    entrypoint: CallableRef
    operations: tuple[Enum, ...]

    def __post_init__(self) -> None:
        if type(self.surface) is not TargetSurface:
            raise TypeError("composition target surface must be TargetSurface")
        if type(self.entrypoint) is not CallableRef:
            raise TypeError("composition target entrypoint must be CallableRef")
        if type(self.operations) is not tuple or not self.operations:
            raise ValueError("composition target operations must be a nonempty immutable tuple")
        entrypoint_surface = _target_inventory()[1].get((self.entrypoint.module, self.entrypoint.qualname))
        if entrypoint_surface is not self.surface:
            raise ValueError("composition target surface does not match entrypoint")
        for operation in self.operations:
            _resolve_operation(operation)


@dataclass(frozen=True)
class ProtocolMethodTarget:
    protocol: CallableRef
    method: str

    def __post_init__(self) -> None:
        if type(self.protocol) is not CallableRef:
            raise TypeError("protocol method target protocol must be CallableRef")
        if type(self.method) is not str or not self.method:
            raise ValueError("protocol method target requires a nonempty method name")
        protocol = _target_inventory()[2].get((self.protocol.module, self.protocol.qualname))
        if protocol is None:
            raise ValueError("protocol method target requires a public protocol reference")
        if not callable(getattr(protocol[0], self.method, None)):
            raise ValueError(f"unknown protocol method {self.protocol.module}.{self.protocol.qualname}.{self.method}")


@dataclass(frozen=True)
class EntrypointStageTarget:
    surface: TargetSurface
    entrypoint: CallableRef
    stage: EntrypointStage

    def __post_init__(self) -> None:
        if type(self.surface) is not TargetSurface:
            raise TypeError("entrypoint target surface must be TargetSurface")
        if type(self.entrypoint) is not CallableRef:
            raise TypeError("entrypoint target entrypoint must be CallableRef")
        if type(self.stage) is not EntrypointStage:
            raise TypeError("entrypoint target stage must be EntrypointStage")
        entrypoint_surface = _target_inventory()[1].get((self.entrypoint.module, self.entrypoint.qualname))
        if entrypoint_surface is not self.surface:
            raise ValueError("entrypoint target surface does not match entrypoint")


# Descriptive native contracts, not imports or callable dispatch. Verified against
# Ibis native signatures; optional-package presence must not change target identity.
_EXTERNAL_ENTRYPOINTS = MappingProxyType(
    {
        ("ibis.backends.duckdb", "Backend.create_table"): "ibis-duckdb",
        ("ibis.backends.sqlite", "Backend.create_table"): "ibis-sqlite",
    }
)
_EXTERNAL_TABLE_SIGNATURE = inspect.Signature(
    (
        inspect.Parameter("name", inspect.Parameter.POSITIONAL_ONLY),
        inspect.Parameter("obj", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
        inspect.Parameter("schema", inspect.Parameter.KEYWORD_ONLY, default=None),
        inspect.Parameter("database", inspect.Parameter.KEYWORD_ONLY, default=None),
        inspect.Parameter("temp", inspect.Parameter.KEYWORD_ONLY, default=False),
        inspect.Parameter("overwrite", inspect.Parameter.KEYWORD_ONLY, default=False),
    )
)
_EXTERNAL_TABLE_OPTIONS = frozenset({"name", "schema", "database", "temp", "overwrite"})


@dataclass(frozen=True, order=True)
class ExternalCallableRef:
    """A known defining native address; resolving it never imports the library."""

    module: str
    qualname: str

    def __post_init__(self) -> None:
        if type(self.module) is not str or type(self.qualname) is not str:
            raise TypeError("external callable reference requires text module and qualname")
        if (self.module, self.qualname) not in _EXTERNAL_ENTRYPOINTS:
            raise ValueError(f"unknown external callable reference {self.module}.{self.qualname}")


@dataclass(frozen=True)
class ExternalEntrypointTarget:
    """A native construction contract, distinct from Mountainash entrypoints.

    Use an ExternalCallableRef to the defining Ibis DuckDB/SQLite
    ``Backend.create_table`` and ``EntrypointStage.CONSTRUCTION``.
    Manifestations belong to the exact native dialect's
    ``relations/.../extensions_mountainash/native_input`` segment.
    The scenario's ``obj`` is an argument; the remaining native parameters
    are literal options. This descriptor never imports or invokes Ibis.
    """

    entrypoint: ExternalCallableRef
    stage: EntrypointStage

    def __post_init__(self) -> None:
        if type(self.entrypoint) is not ExternalCallableRef:
            raise TypeError("external target requires ExternalCallableRef")
        if type(self.stage) is not EntrypointStage:
            raise TypeError("external target stage requires EntrypointStage")
        if self.stage is not EntrypointStage.CONSTRUCTION:
            raise ValueError("registered external entrypoints require construction stage")


Target: TypeAlias = (
    OperationTarget | CompositionTarget | ProtocolMethodTarget | EntrypointStageTarget | ExternalEntrypointTarget
)


def _validate_external_target_scope(target: Target, scope: Scope) -> None:
    if type(target) is ExternalEntrypointTarget:
        from mountainash.core.constants import CONST_BACKEND

        dialect = _EXTERNAL_ENTRYPOINTS[(target.entrypoint.module, target.entrypoint.qualname)]
        if scope.backend is not CONST_BACKEND.IBIS or scope.dialect != dialect:
            raise ValueError("external entrypoint requires its exact native dialect scope")


def _target_callable(target: Target) -> Any:
    """Return a callable captured with the target authority inventory."""
    if type(target) is ProtocolMethodTarget:
        protocol = _target_inventory()[2][(target.protocol.module, target.protocol.qualname)][0]
        return getattr(protocol, target.method)
    if type(target) is CompositionTarget or type(target) is EntrypointStageTarget:
        return _target_inventory()[0][(target.entrypoint.module, target.entrypoint.qualname)][1]
    raise TypeError("target requires a callable authority")


def _operation_home(operation: Enum) -> tuple[str, Any, Any]:
    _resolve_operation(operation)
    from mountainash.core.capabilities.declarations import classify_domain, classify_source

    root = "relations" if type(operation).__name__.startswith("RKEY_") else "expressions"
    return root, classify_source(operation), classify_domain(operation)


def target_home(target: Target) -> tuple[str, Any, Any]:
    """Return the canonical physical root, source and domain of ``target``."""
    if type(target) is ExternalEntrypointTarget:
        from mountainash.core.capabilities.declarations import Domain, FactSource

        return "relations", FactSource.MOUNTAINASH, Domain.NATIVE_INPUT
    if type(target) is OperationTarget:
        return _operation_home(target.operation)
    if type(target) is CompositionTarget or type(target) is EntrypointStageTarget:
        from mountainash.core.capabilities.declarations import Domain, FactSource

        return (
            target.surface.value + "s",
            FactSource.MOUNTAINASH,
            Domain.VALUE if target.surface is TargetSurface.EXPRESSION else Domain.RELATION,
        )
    if type(target) is ProtocolMethodTarget:
        protocol, surface = _target_inventory()[2][(target.protocol.module, target.protocol.qualname)]
        method = getattr(protocol, target.method)
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )

        mapped: list[Enum] = []
        for operation in ExpressionFunctionRegistry.list_all():
            if ExpressionFunctionRegistry.get(operation).protocol_method is method:
                mapped.append(operation)
        for operation in RelationOperationRegistry.list_all():
            if RelationOperationRegistry.get(operation).protocol_method is method:
                mapped.append(operation)
        if mapped:
            homes = {_operation_home(operation) for operation in mapped}
            if len(homes) != 1:
                raise ValueError(
                    f"protocol method {target.protocol.module}.{target.protocol.qualname}."
                    f"{target.method} maps to multiple physical homes"
                )
            return homes.pop()
        from mountainash.core.capabilities.declarations import Domain, FactSource

        return (
            surface.value + "s",
            FactSource.MOUNTAINASH,
            Domain.VALUE if surface is TargetSurface.EXPRESSION else Domain.RELATION,
        )
    raise TypeError("target_home requires a concrete Target")


def _operation_order_key(operation: Enum) -> tuple[str, str, str]:
    _resolve_operation(operation)
    return type(operation).__module__, type(operation).__qualname__, operation.name


def target_order_key(target: Target) -> tuple:
    """Canonical ordering key for all Target variants."""
    if type(target) is ExternalEntrypointTarget:
        return (
            "external_entrypoint",
            (target.entrypoint.module, target.entrypoint.qualname),
            target.stage.value,
        )
    if type(target) is OperationTarget:
        return ("operation", _operation_order_key(target.operation))
    if type(target) is CompositionTarget:
        return (
            "composition",
            target.surface.value,
            (target.entrypoint.module, target.entrypoint.qualname),
            tuple(_operation_order_key(operation) for operation in target.operations),
        )
    if type(target) is ProtocolMethodTarget:
        return (
            "protocol_method",
            (target.protocol.module, target.protocol.qualname),
            target.method,
        )
    if type(target) is EntrypointStageTarget:
        return (
            "entrypoint_stage",
            target.surface.value,
            (target.entrypoint.module, target.entrypoint.qualname),
            target.stage.value,
        )
    raise TypeError("target_order_key requires a concrete Target")


class CapabilityLevel(Enum):
    EXPR_CAPABLE = "expr_capable"  # implicit default; explicit ONLY as a dialect-scoped refinement
    LITERAL_ONLY = "literal_only"  # literal args → raw value; dynamic args → compile-time error
    POLYMORPHIC = "polymorphic"  # literal collection OR expression (ex-_raw_value_functions)
    UNSUPPORTED = "unsupported"  # op/param unavailable on this backend/dialect entirely


class Boundary(Enum):
    BUILD = "build"  # gated at visitor dispatch
    MATERIALIZE = "materialize"  # runtime-enrichment residue (value/dtype-dependent)


class Enforcement(Enum):
    """What the system DOES about a limitation (spec 2026-07-28, backlog 66a).

    A separate axis from Boundary, which says WHEN the limitation manifests.
    The two are not orthogonal — each role admits exactly one boundary — but
    Boundary.BUILD admits two roles, so it cannot distinguish a gate from a
    router declaration on its own. The default is the strict role: a fact whose
    author did not think about enforcement gates, rather than silently not
    gating. `condition` is prose and is read by nothing that decides anything.

    enforcement           | legal boundary
    ----------------------|---------------
    GATE                  | BUILD
    ROUTER_METADATA       | BUILD
    MATERIALIZE_RESIDUE   | MATERIALIZE
    """

    GATE = "gate"  # visitor raises before backend dispatch
    ROUTER_METADATA = "router_metadata"  # a backend router consumes this; never raises
    MATERIALIZE_RESIDUE = (
        "materialize_residue"  # enriches a native error raised during dispatch or materialization (item 88)
    )


class ResidueSignal(Enum):
    EXCEPTION = "exception"
    NON_NULL_TO_NULL = "non_null_to_null"


_LEGAL_BOUNDARY = {
    Enforcement.GATE: Boundary.BUILD,
    Enforcement.ROUTER_METADATA: Boundary.BUILD,
    Enforcement.MATERIALIZE_RESIDUE: Boundary.MATERIALIZE,
}


class TargetKind(Enum):
    """Forward-compat identity axis (spec 2026-07-06 serialization-targets).

    Phase 1 registers only EXECUTE identities; SERIALIZE targets (substrait,
    frictionless-pipeline) arrive with the serialization workstream's
    register_target(). Declared now so the registry schema never migrates.
    """

    EXECUTE = "execute"  # polars/ibis/narwhals — facts feed the dispatch gate
    SERIALIZE = "serialize"  # emit targets — facts feed pre-emit validation


class Fidelity(Enum):
    """How an op serializes to a SERIALIZE target (spec 2026-07-06, Section 5).

    Reserved for SERIALIZE-target facts; EXECUTE facts must leave
    CapabilityFact.fidelity as None (validated at registration).
    """

    NATIVE = "native"  # standard target vocabulary (Substrait catalog fn / standard step)
    EXTENSION = "extension"  # mountainash URN / custom step — foreign consumers need the declaration


class ValueClass(Enum):
    """Unbounded value-space a fact matches by predicate (spec 2026-07-25).

    A value-class fact gates the *entire* class on a backend; register one only
    where a representative slice agrees (see value_classes.REPRESENTATIVE_SLICES
    and the spec's backend-binary agreement rule). A class is usable for gating
    ONLY when the api-builder validates the param to exactly that predicate's
    domain (gate-domain == production-domain, spec §3.2). strftime is open
    (unvalidated) so it has NO value-class — it gates value-agnostically.
    """

    DURATION_MULTIPLIER = "duration_multiplier"  # <int> >= 2 + unit, e.g. 2d, 3h
    IANA_TIMEZONE = "iana_timezone"  # tz-database membership
    POLARS_OFFSET = "polars_offset"  # signed Polars duration string


class ClauseOp(Enum):
    """Closed predicate operator set (spec §4.2). Extending is a spec change."""

    EQ = "eq"  # resolved value equals a scalar/enum operand
    IN = "in"  # resolved value is a member of a frozenset
    IS_SET = "is_set"  # resolved value is non-None
    IS_NULL = "is_null"  # resolved value is None
    IS_LITERAL = "is_literal"  # root param's bound value is a LiteralNode
    MATCHES_CLASS = "matches_class"  # value_classes.matches(operand, value)


# Closed, hashable operand union (spec §4.3). ValueClass is an Enum, so EQ
# validation must exclude it explicitly.
Operand = str | int | bool | Enum | frozenset[str | int] | ValueClass | None


def _operand_key(operand: Operand) -> tuple:
    if operand is None:
        return (0,)
    if isinstance(operand, frozenset):
        return (1, tuple(sorted(str(m) for m in operand)))
    if isinstance(operand, ValueClass):
        return (2, operand.value)
    if isinstance(operand, Enum):
        return (3, type(operand).__name__, operand.value)
    return (4, operand)


def _clause_key(clause: "Clause") -> tuple:
    return (clause.path, clause.op.name, _operand_key(clause.operand))


def _validate_clause(clause: "Clause") -> None:
    if not clause.path:
        raise ValueError("Clause path must be non-empty")
    op, operand = clause.op, clause.operand
    if op in (ClauseOp.IS_SET, ClauseOp.IS_NULL, ClauseOp.IS_LITERAL):
        if operand is not None:
            raise ValueError(f"Clause {op.name} takes no operand, got {operand!r}")
    elif op is ClauseOp.EQ:
        if isinstance(operand, ValueClass) or not isinstance(operand, (str, int, bool, Enum)):
            raise ValueError(f"Clause EQ operand must be a scalar/enum, got {operand!r}")
    elif op is ClauseOp.IN:
        if not isinstance(operand, frozenset) or not all(isinstance(m, (str, int)) for m in operand):
            raise ValueError(f"Clause IN operand must be frozenset[str|int], got {operand!r}")
    elif op is ClauseOp.MATCHES_CLASS:
        if not isinstance(operand, ValueClass):
            raise ValueError(f"Clause MATCHES_CLASS operand must be a ValueClass, got {operand!r}")
    else:
        raise ValueError(f"unknown ClauseOp {op!r}")


@dataclass(frozen=True)
class Clause:
    path: str
    op: ClauseOp
    operand: Operand = None

    def __post_init__(self) -> None:
        _validate_clause(self)


@dataclass(frozen=True)
class Predicate:
    """Immutable conjunction of clauses; canonical order, order-insensitive eq/hash."""

    clauses: tuple[Clause, ...]

    def __post_init__(self) -> None:
        clauses = self.clauses
        if not clauses:
            raise ValueError("Predicate must have at least one clause")
        if len(set(clauses)) != len(clauses):
            raise ValueError("Predicate must not contain duplicate clauses")
        object.__setattr__(self, "clauses", tuple(sorted(clauses, key=_clause_key)))


def _normalized_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset):
        normalized = [_normalized_value(item) for item in value]
        return sorted(normalized, key=lambda item: (type(item).__name__, repr(item)))
    if isinstance(value, tuple):
        return [_normalized_value(item) for item in value]
    return value


def _predicate_digest(fact: "CapabilityFact") -> str:
    clauses = (
        [(clause.path, clause.op.value, _normalized_value(clause.operand)) for clause in fact.predicate.clauses]
        if fact.predicate is not None
        else []
    )
    payload = {
        "option_value": _normalized_value(fact.option_value),
        "value_class": _normalized_value(fact.value_class),
        "predicate": clauses,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_since(since: str, owner: str) -> None:
    if not _SINCE_RE.match(since):
        raise ValueError(f"{owner}: since must be YYYY-MM-DD, got {since!r}")


@dataclass(frozen=True)
class CapabilityFact:
    operation_key: Any  # FKEY or RKEY enum member
    param: str  # param name, or WILDCARD_PARAM
    level: CapabilityLevel
    backend: CONST_BACKEND | str  # str only for SERIALIZE families via register_target
    # (spec 2026-07-06; CONST_BACKEND is a StrEnum so mixed
    #  keying is well-behaved; register_backend rejects str)
    dialect: str | None = None  # None = whole family; set = dialect-scoped refinement
    message: str = ""
    workaround: str | None = None
    upstream_ref: str | None = None  # typed ID into registry/upstream-issues.yaml
    since: str = ""
    boundary: Boundary = Boundary.BUILD
    native_errors: tuple[type[Exception], ...] = ()
    condition: str | None = None  # human-readable value/option condition; None = unconditional
    option_value: str | None = None  # value-scoped option gate; None = value-agnostic (arg facts)
    probe_exempt: str | None = None  # reason when no probe is possible
    fidelity: Fidelity | None = None  # SERIALIZE targets only; must be None on EXECUTE facts
    # (validated in register_backend — spec 2026-07-06)
    value_class: ValueClass | None = None  # value-class fact; option_value MUST be None
    enforcement: Enforcement = Enforcement.GATE  # what the system does; condition is prose only
    predicate: Predicate | None = None  # compound co-value limit (§4); None = param-keyed fact
    residue_signal: ResidueSignal = ResidueSignal.EXCEPTION

    def __post_init__(self) -> None:
        if self.residue_signal is not ResidueSignal.EXCEPTION and (
            self.enforcement is not Enforcement.MATERIALIZE_RESIDUE
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "both materialization residue signals require "
                "MATERIALIZE_RESIDUE enforcement"
            )
        if (
            self.enforcement is Enforcement.MATERIALIZE_RESIDUE
            and self.residue_signal is ResidueSignal.NON_NULL_TO_NULL
            and self.native_errors
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "NON_NULL_TO_NULL residue facts must have empty native_errors"
            )
        if (
            self.enforcement is Enforcement.MATERIALIZE_RESIDUE
            and self.residue_signal is ResidueSignal.EXCEPTION
            and not self.native_errors
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "EXCEPTION residue facts must declare native_errors"
            )
        _validate_since(self.since, f"CapabilityFact({self.operation_key}, {self.param})")
        if self.level is CapabilityLevel.EXPR_CAPABLE and self.dialect is None:
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): explicit "
                "EXPR_CAPABLE is only legal as a dialect-scoped refinement "
                "(family default is already expr-capable)"
            )
        if self.upstream_ref is not None and not _UPSTREAM_REF_RE.match(self.upstream_ref):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): upstream_ref "
                f"{self.upstream_ref!r} does not match PROJ-CAT-NN grammar"
            )
        if self.value_class is not None:
            if self.option_value is not None:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a fact is "
                    "exactly one of exact-value (option_value), value-class "
                    "(value_class), or value-agnostic (neither) — not both "
                    "option_value and value_class"
                )
            if self.param == WILDCARD_PARAM:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): value-class facts cannot use WILDCARD_PARAM"
                )
            if self.boundary is not Boundary.BUILD:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): value-class facts must use the BUILD boundary"
                )
        if (
            self.param == WILDCARD_PARAM
            and self.enforcement is Enforcement.GATE
            and self.level is CapabilityLevel.LITERAL_ONLY
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): a GATE WILDCARD_PARAM "
                f"(whole-op) fact may be UNSUPPORTED (whole-op gate), POLYMORPHIC (whole-op "
                f"literal-or-expression args), or a dialect-scoped EXPR_CAPABLE refinement — "
                f"never LITERAL_ONLY, which at the whole-op level means every argument is "
                f"literal-only and must therefore be an option, not an argument "
                f"(arguments-vs-options.md)"
            )
        expected = _LEGAL_BOUNDARY[self.enforcement]
        if self.boundary is not expected:
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                f"{self.enforcement.name} enforcement requires the "
                f"{expected.name} boundary, got {self.boundary.name} — routing "
                "is a build-time path choice and residue is a materialize-time "
                "enrichment; see the 66a compatibility table"
            )

        if self.predicate is not None:
            if self.boundary is not Boundary.BUILD:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): predicate "
                    "facts must use the BUILD boundary (§4.5)"
                )
            if self.value_class is not None:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate fact cannot also use value_class"
                )
            if self.option_value is not None:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact is value-agnostic and cannot also use option_value"
                )
            if self.param == WILDCARD_PARAM:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate fact cannot use WILDCARD_PARAM"
                )
            if self.enforcement is not Enforcement.GATE:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact has no consuming path for non-GATE enforcement roles — "
                    "predicate facts gate"
                )
            if self.level not in (CapabilityLevel.UNSUPPORTED, CapabilityLevel.EXPR_CAPABLE):
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact must be UNSUPPORTED (blocking) or EXPR_CAPABLE (permitting "
                    "refinement) — LITERAL_ONLY/POLYMORPHIC have no predicate enforcement path"
                )
            roots = {c.path.split(".")[0] for c in self.predicate.clauses}
            roots.update(
                c.path.split(".")[1]
                for c in self.predicate.clauses
                if c.path.startswith("__operand_types__.") and len(c.path.split(".")) == 3
            )
            if self.param not in roots:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param!r}): param must "
                    f"be one of the predicate's clause roots {sorted(roots)}"
                )

    @property
    def fact_key(self) -> str:
        operation_type = f"{type(self.operation_key).__module__}.{type(self.operation_key).__qualname__}"
        operation = getattr(self.operation_key, "name", str(self.operation_key))
        backend = getattr(self.backend, "value", str(self.backend))
        dialect = self.dialect or ""
        return "|".join(
            (
                operation_type,
                str(operation),
                self.param,
                str(backend),
                dialect,
                self.boundary.value,
                self.residue_signal.value,
                _predicate_digest(self),
            )
        )


class DivergenceKind(Enum):
    SEMANTICS = "semantics"
    TYPE_INFERENCE = "type_inference"
    NAMING = "naming"
    PRECISION = "precision"
    ENGINE_LENIENCY = "engine_leniency"


class GapKind(Enum):
    ASPIRATIONAL = "aspirational"
    UNTESTED_OPTION = "untested_option"
    UNTESTED_ARGUMENT = "untested_argument"
    SIGNATURE_DIVERGENCE = "signature_divergence"
    UNRESOLVED_PARAM = "unresolved_param"
    OTHER = "other"


@dataclass(frozen=True)
class KnownGap:
    gap_kind: GapKind
    reason: str
    since: str

    def __post_init__(self) -> None:
        _validate_since(self.since, f"KnownGap({self.reason!r})")

    def is_stale(self, *, today: date | None = None) -> bool:
        """True when the gap is older than ~6 months (closed-by-default R2 warning)."""
        today = today or date.today()
        return date.fromisoformat(self.since) + _STALE_AFTER < today
