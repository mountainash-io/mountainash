"""Cold capture of every guard-owned gap inventory and its history."""

from __future__ import annotations

from pathlib import Path
import sys

from mountainash.core.capabilities.capture import CapturedAddress
from mountainash.core.capabilities.gaps import (
    GapInventory,
    GapKey,
    InventoryGap,
    InventoryWide,
    VerificationSnapshot,
)
from mountainash.core.capabilities.schema import CallableRef, ProtocolMethodTarget


def _target_and_obligation(name, original, guard, protocols, method_aliases):
    if name.startswith(("expr.", "rel.")):
        protocol, method = original
        return protocol, method, "implementation and registry wiring"
    if name in {"argtypes.unresolved_params", "argtypes.unresolved_param_gaps"}:
        protocol_name, method, parameter = guard._KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES[original]
        obligation = f"resolve tested parameter:{original[0]}:{original[1]}"
    elif name == "argtypes.metadata_only":
        module, protocol_name, method, parameter = original
        if protocol_name is None:
            alias = guard._KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES.get((method, parameter))
            if alias is not None:
                protocol_name, method, parameter = alias
            else:
                resolved = guard.canonicalize_tested_param(module, method, parameter)
                protocol_name = resolved.protocol_name
                method = resolved.op_name
        obligation = f"metadata-backed execution coverage:{module}:{parameter}"
    elif name in {"argtypes.unwired_ops", "argtypes.special_node_unwired_ops"}:
        protocol_name, method = original
        obligation = "tested operation dispatch wiring"
    else:
        protocol_name, method, parameter = original
        obligation = {
            "argtypes.untested_argument": "argument expression coverage",
            "argtypes.untested_option": "option behavior coverage",
            "argtypes.allowed_cross_category": "test category agreement",
        }[name] + f":{parameter}"
    protocol_name, method = method_aliases.get((protocol_name, method), (protocol_name, method))
    if protocol_name not in protocols:
        raise ValueError(f"{name}: unresolved protocol target for original key {original!r}")
    return protocols[protocol_name], method, obligation


def collect_all_gap_sets() -> VerificationSnapshot:
    """Acquire original keyed data and owned changes with retained source bytes."""
    import core.test_protocol_alignment as pa
    from expressions.argument_types import test_coverage_guard as cg
    import relations.test_rel_wiring_audit_registry as rw

    owners = (
        ("expr.aspirational", pa, "KNOWN_ASPIRATIONAL"),
        ("expr.aspirational_and_tested", pa, "KNOWN_ASPIRATIONAL_AND_TESTED"),
        ("rel.aspirational", rw, "KNOWN_ASPIRATIONAL"),
        ("argtypes.untested_argument", cg, "_KNOWN_UNTESTED_ARGUMENT_PARAMS"),
        ("argtypes.metadata_only", cg, "_KNOWN_METADATA_ONLY_TESTED_PARAMS"),
        ("argtypes.untested_option", cg, "_KNOWN_UNTESTED_OPTION_PARAMS"),
        ("argtypes.unwired_ops", cg, "_KNOWN_UNWIRED_TESTED_OPS"),
        ("argtypes.unresolved_params", cg, "_KNOWN_UNRESOLVED_TESTED_PARAMS"),
        ("argtypes.special_node_unwired_ops", cg, "_KNOWN_SPECIAL_NODE_UNWIRED_OPS"),
        ("argtypes.unresolved_param_gaps", cg, "_KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_GAPS"),
        ("argtypes.allowed_cross_category", cg, "_ALLOWED_CROSS_CATEGORY_TESTED_PARAMS"),
    )
    root = Path(__file__).resolve().parents[2]
    source_cache = {}
    address_cache = {}

    def source_for(path):
        resolved = Path(path).resolve()
        source = source_cache.get(resolved)
        if source is None:
            source = (resolved.relative_to(root).as_posix(), resolved.read_bytes())
            source_cache[resolved] = source
        return source

    def source_address(definition, entry):
        path = Path(sys.modules[definition.__module__].__file__).resolve()
        cache_key = (path, entry)
        address = address_cache.get(cache_key)
        if address is None:
            relative_path, content = source_for(path)
            address = CapturedAddress("mountainash", relative_path, entry, artifact=content)
            address_cache[cache_key] = address
        return address

    def protocol_reference_context(protocol, method):
        references = [source_address(protocol, protocol.__qualname__)]
        for defining_class in protocol.__mro__:
            if method in defining_class.__dict__:
                if defining_class is not protocol:
                    references.append(source_address(defining_class, f"{defining_class.__qualname__}.{method}"))
                break
        else:
            raise ValueError(f"resolved protocol target {protocol.__qualname__}.{method} has no defining method")
        return tuple(references)

    sources = {}
    histories = {}
    for module in (pa, cg, rw):
        sources[module] = source_for(module.__file__)
        history = module.GAP_CHANGES
        if type(history) is not tuple:
            raise TypeError(f"{module.__name__}.GAP_CHANGES must be immutable")
        names = {name for name, owner, _ in owners if owner is module}
        for change in history:
            if change.prior.family != "gap" or change.prior.key.inventory not in names:
                raise ValueError(f"{module.__name__}: change belongs to another inventory")
        histories[module] = history
    protocols = dict(cg._iter_protocol_classes())
    method_aliases = {}
    for (protocol, method, _), (target_protocol, target_method, _) in cg._KNOWN_TESTED_ARGUMENT_PARAM_ALIASES.items():
        target = (target_protocol, target_method)
        if method_aliases.setdefault((protocol, method), target) != target:
            raise ValueError(f"conflicting owned method aliases for {protocol}.{method}")
    inventories = []
    for name, module, attribute in owners:
        path, content = sources[module]
        owner = CapturedAddress("mountainash", path, attribute, artifact=content)
        records = []
        for original, payload in tuple(getattr(module, attribute).items()):
            protocol, method, obligation = _target_and_obligation(
                name,
                original,
                cg,
                protocols,
                method_aliases,
            )
            target = ProtocolMethodTarget(
                CallableRef(protocol.__module__, protocol.__qualname__),
                method,
            )
            original_key = tuple(
                CallableRef(part.__module__, part.__qualname__) if isinstance(part, type) else part for part in original
            )
            origin = CapturedAddress(
                "mountainash",
                path,
                f"{attribute}[{original!r}]",
                artifact=content,
            )
            records.append(
                InventoryGap(
                    GapKey(name, target, obligation, InventoryWide()),
                    original_key,
                    payload,
                    (origin,),
                    protocol_reference_context(protocol, method),
                )
            )
        changes = tuple(change for change in histories[module] if change.prior.key.inventory == name)
        inventories.append(GapInventory(name, owner, tuple(records), changes))
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from tests.fixtures.verification_bindings import (
        capture_bindings,
        capture_native_observations,
        capture_selected_observations,
    )

    catalogue = CapabilityRegistry.capture()
    native_bindings, _ = capture_native_observations(catalogue)
    selected_bindings, _ = capture_selected_observations(catalogue)
    bindings = capture_bindings(catalogue) + native_bindings + selected_bindings
    return VerificationSnapshot(tuple(inventories), bindings=bindings)
