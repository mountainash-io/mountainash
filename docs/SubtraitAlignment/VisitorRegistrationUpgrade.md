 Visitor System Upgrade Architecture & Plan

  Executive Summary

  Upgrade the UnifiedExpressionVisitor to support handler registration while preserving the clean Substrait-aligned architecture. This enables:
  - Custom node type handlers
  - Backend-specific optimizations
  - Pre/post processing hooks
  - User extensibility without modifying core visitor

  ---
  Part 1: Architecture Design

  1.1 High-Level Architecture

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                        UnifiedExpressionVisitor                             │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │  Class-level Registries:                                                    │
  │  ├─ _custom_handlers: Dict[Type[SubstraitNode], NodeHandler]               │
  │  ├─ _pre_hooks: Dict[Type[SubstraitNode], List[PreHook]]                   │
  │  ├─ _post_hooks: Dict[Type[SubstraitNode], List[PostHook]]                 │
  │  └─ _signature_cache: Dict[str, Signature]  (existing)                     │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │  Registration API (class methods):                                          │
  │  ├─ register_handler(node_type, handler, override=False)                   │
  │  ├─ register_pre_hook(node_type, hook)                                     │
  │  ├─ register_post_hook(node_type, hook)                                    │
  │  ├─ unregister_handler(node_type)                                          │
  │  └─ clear_registrations()                                                  │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │  Dispatch Chain:                                                            │
  │  visit(node) → pre_hooks → dispatch(node) → post_hooks → return            │
  │                               ↓                                             │
  │               ┌───────────────┴───────────────┐                            │
  │               ↓                               ↓                             │
  │        Custom Handler?              Built-in Handler?                       │
  │        (registry lookup)            (node.accept(self))                     │
  │               ↓                               ↓                             │
  │        _custom_handlers[type]       visit_literal/field_ref/...            │
  │                                              ↓                              │
  │                               visit_default (NotImplementedError)           │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │  Built-in Handlers (6 Substrait node types):                               │
  │  ├─ visit_literal(LiteralNode)                                             │
  │  ├─ visit_field_reference(FieldReferenceNode)                              │
  │  ├─ visit_scalar_function(ScalarFunctionNode)                              │
  │  ├─ visit_if_then(IfThenNode)                                              │
  │  ├─ visit_cast(CastNode)                                                   │
  │  └─ visit_singular_or_list(SingularOrListNode)                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  1.2 Type Definitions

  # core/unified_visitor/types.py

  from typing import Any, Callable, TypeVar, Protocol, TYPE_CHECKING
  from ..substrait_nodes import SubstraitNode

  if TYPE_CHECKING:
      from .visitor import UnifiedExpressionVisitor
      from ...types import SupportedExpressions

  # Type variables
  N = TypeVar("N", bound=SubstraitNode)

  # Handler function signature
  NodeHandler = Callable[["UnifiedExpressionVisitor", SubstraitNode], "SupportedExpressions"]

  # Pre-hook: called before handler, can modify node or perform side effects
  # Signature: (visitor, node) -> Optional[node]  (return None to keep original)
  PreHook = Callable[["UnifiedExpressionVisitor", SubstraitNode], SubstraitNode | None]

  # Post-hook: called after handler, can transform result
  # Signature: (visitor, node, result) -> result
  PostHook = Callable[["UnifiedExpressionVisitor", SubstraitNode, "SupportedExpressions"], "SupportedExpressions"]


  class HandlerRegistration(Protocol):
      """Protocol for handler registration metadata."""
      node_type: type[SubstraitNode]
      handler: NodeHandler
      override: bool
      priority: int

  1.3 Handler Registry Design

  # core/unified_visitor/registry.py

  from __future__ import annotations
  from dataclasses import dataclass, field
  from typing import Dict, List, Type, Optional, Callable, Any
  from ..substrait_nodes import SubstraitNode

  @dataclass
  class HandlerEntry:
      """Metadata for a registered handler."""
      handler: Callable
      override: bool = False
      priority: int = 0
      source: str = "custom"  # "builtin" or "custom" or module path

  @dataclass
  class HookEntry:
      """Metadata for a registered hook."""
      hook: Callable
      priority: int = 0
      source: str = "custom"


  class VisitorRegistry:
      """Centralized registry for visitor handlers and hooks.

      Separates registration logic from visitor implementation.
      Supports inheritance-aware handler lookup.
      """

      def __init__(self) -> None:
          self._handlers: Dict[Type[SubstraitNode], HandlerEntry] = {}
          self._pre_hooks: Dict[Type[SubstraitNode], List[HookEntry]] = {}
          self._post_hooks: Dict[Type[SubstraitNode], List[HookEntry]] = {}
          self._builtin_types: set[Type[SubstraitNode]] = set()

      def mark_builtin(self, node_type: Type[SubstraitNode]) -> None:
          """Mark a node type as having a built-in handler."""
          self._builtin_types.add(node_type)

      def register_handler(
          self,
          node_type: Type[SubstraitNode],
          handler: Callable,
          *,
          override: bool = False,
          priority: int = 0,
          source: str = "custom",
      ) -> None:
          """Register a handler for a node type."""
          if node_type in self._builtin_types and not override:
              raise ValueError(
                  f"Cannot override built-in handler for {node_type.__name__}. "
                  f"Use override=True if intentional."
              )

          if node_type in self._handlers and not override:
              existing = self._handlers[node_type]
              raise ValueError(
                  f"Handler already registered for {node_type.__name__} "
                  f"(source: {existing.source}). Use override=True to replace."
              )

          self._handlers[node_type] = HandlerEntry(
              handler=handler,
              override=override,
              priority=priority,
              source=source,
          )

      def register_pre_hook(
          self,
          node_type: Type[SubstraitNode],
          hook: Callable,
          *,
          priority: int = 0,
          source: str = "custom",
      ) -> None:
          """Register a pre-visit hook."""
          if node_type not in self._pre_hooks:
              self._pre_hooks[node_type] = []

          entry = HookEntry(hook=hook, priority=priority, source=source)
          self._pre_hooks[node_type].append(entry)
          # Sort by priority (higher first)
          self._pre_hooks[node_type].sort(key=lambda e: -e.priority)

      def register_post_hook(
          self,
          node_type: Type[SubstraitNode],
          hook: Callable,
          *,
          priority: int = 0,
          source: str = "custom",
      ) -> None:
          """Register a post-visit hook."""
          if node_type not in self._post_hooks:
              self._post_hooks[node_type] = []

          entry = HookEntry(hook=hook, priority=priority, source=source)
          self._post_hooks[node_type].append(entry)
          self._post_hooks[node_type].sort(key=lambda e: -e.priority)

      def get_handler(self, node_type: Type[SubstraitNode]) -> Optional[HandlerEntry]:
          """Get handler for node type, checking MRO for inheritance."""
          for check_type in node_type.__mro__:
              if check_type in self._handlers:
                  return self._handlers[check_type]
              if not isinstance(check_type, type):
                  continue
              if not issubclass(check_type, SubstraitNode):
                  break
          return None

      def get_pre_hooks(self, node_type: Type[SubstraitNode]) -> List[HookEntry]:
          """Get all pre-hooks for node type (including inherited)."""
          hooks = []
          for check_type in node_type.__mro__:
              if check_type in self._pre_hooks:
                  hooks.extend(self._pre_hooks[check_type])
              if not isinstance(check_type, type):
                  continue
              if not issubclass(check_type, SubstraitNode):
                  break
          return sorted(hooks, key=lambda e: -e.priority)

      def get_post_hooks(self, node_type: Type[SubstraitNode]) -> List[HookEntry]:
          """Get all post-hooks for node type (including inherited)."""
          hooks = []
          for check_type in node_type.__mro__:
              if check_type in self._post_hooks:
                  hooks.extend(self._post_hooks[check_type])
              if not isinstance(check_type, type):
                  continue
              if not issubclass(check_type, SubstraitNode):
                  break
          return sorted(hooks, key=lambda e: -e.priority)

      def unregister_handler(self, node_type: Type[SubstraitNode]) -> bool:
          """Remove a custom handler. Returns True if removed."""
          if node_type in self._handlers:
              del self._handlers[node_type]
              return True
          return False

      def clear_custom(self) -> None:
          """Clear all custom handlers and hooks (preserve builtins)."""
          self._handlers = {
              k: v for k, v in self._handlers.items()
              if v.source == "builtin"
          }
          self._pre_hooks.clear()
          self._post_hooks.clear()

      def list_handlers(self) -> Dict[str, str]:
          """List all registered handlers for debugging."""
          result = {}
          for node_type in self._builtin_types:
              result[node_type.__name__] = "built-in"
          for node_type, entry in self._handlers.items():
              result[node_type.__name__] = f"{entry.handler.__name__} ({entry.source})"
          return result

  1.4 Updated Visitor Implementation

  # core/unified_visitor/visitor.py

  from __future__ import annotations
  from typing import Any, Dict, Optional, Type, Callable, TYPE_CHECKING
  import inspect

  from ..substrait_nodes import (
      SubstraitNode,
      LiteralNode,
      FieldReferenceNode,
      ScalarFunctionNode,
      IfThenNode,
      CastNode,
      SingularOrListNode,
  )
  from ..functions import FunctionRegistry
  from .registry import VisitorRegistry
  from .types import NodeHandler, PreHook, PostHook

  if TYPE_CHECKING:
      from ...types import SupportedExpressions


  class UnifiedExpressionVisitor:
      """Single visitor with extensible handler registration.

      Built-in handlers cover Substrait-aligned nodes. Custom handlers can be
      registered for user-defined node types or to override default behavior.

      Architecture:
          - Class-level registry shared across instances
          - Instance-level backend (ExpressionSystem)
          - Double-dispatch via node.accept() for built-ins
          - Registry lookup for custom handlers

      Extension Patterns:
          1. Register handler for custom node type
          2. Override built-in handler for optimization
          3. Add pre/post hooks for cross-cutting concerns

      Example:
          >>> @UnifiedExpressionVisitor.register_handler(MyCustomNode)
          ... def handle_custom(visitor, node):
          ...     return visitor.backend.custom_op(...)

          >>> visitor = UnifiedExpressionVisitor(polars_system)
          >>> result = visitor.visit(my_node)
      """

      # =========================================================================
      # Class-level registry (shared across all instances)
      # =========================================================================

      _registry: VisitorRegistry = VisitorRegistry()
      _signature_cache: Dict[str, Optional[inspect.Signature]] = {}
      _initialized: bool = False

      # =========================================================================
      # Class Initialization
      # =========================================================================

      @classmethod
      def _ensure_initialized(cls) -> None:
          """Initialize built-in handlers on first use."""
          if cls._initialized:
              return

          # Mark built-in node types
          for node_type in [
              LiteralNode,
              FieldReferenceNode,
              ScalarFunctionNode,
              IfThenNode,
              CastNode,
              SingularOrListNode,
          ]:
              cls._registry.mark_builtin(node_type)

          cls._initialized = True

      # =========================================================================
      # Registration API (class methods)
      # =========================================================================

      @classmethod
      def register_handler(
          cls,
          node_type: Type[SubstraitNode],
          handler: Optional[NodeHandler] = None,
          *,
          override: bool = False,
          priority: int = 0,
      ) -> Callable[[NodeHandler], NodeHandler]:
          """Register a custom handler for a node type.

          Can be used as a decorator or called directly.

          Args:
              node_type: The SubstraitNode subclass to handle
              handler: Handler function (optional if used as decorator)
              override: If True, allow overriding built-in handlers
              priority: Higher priority handlers are checked first

          Returns:
              Decorator function if handler not provided, else the handler

          Examples:
              # As decorator
              @UnifiedExpressionVisitor.register_handler(MyCustomNode)
              def handle_custom(visitor, node):
                  return visitor.backend.custom_op(...)

              # Direct registration
              UnifiedExpressionVisitor.register_handler(MyNode, my_handler)

              # Override built-in (use with caution)
              @UnifiedExpressionVisitor.register_handler(LiteralNode, override=True)
              def optimized_literal(visitor, node):
                  ...
          """
          cls._ensure_initialized()

          def decorator(fn: NodeHandler) -> NodeHandler:
              cls._registry.register_handler(
                  node_type,
                  fn,
                  override=override,
                  priority=priority,
                  source=fn.__module__ or "custom",
              )
              return fn

          if handler is not None:
              return decorator(handler)
          return decorator

      @classmethod
      def register_pre_hook(
          cls,
          node_type: Type[SubstraitNode],
          hook: Optional[PreHook] = None,
          *,
          priority: int = 0,
      ) -> Callable[[PreHook], PreHook]:
          """Register a pre-visit hook for a node type.

          Pre-hooks are called before the main handler. They can:
          - Perform validation
          - Log/trace execution
          - Transform the node (return modified node)
          - Abort processing (raise exception)

          Args:
              node_type: Node type to hook (or SubstraitNode for all)
              hook: Hook function (optional if used as decorator)
              priority: Higher priority hooks run first

          Returns:
              Decorator or the hook function

          Example:
              @UnifiedExpressionVisitor.register_pre_hook(ScalarFunctionNode)
              def log_functions(visitor, node):
                  print(f"Compiling: {node.function}")
                  return None  # Don't modify node
          """
          cls._ensure_initialized()

          def decorator(fn: PreHook) -> PreHook:
              cls._registry.register_pre_hook(
                  node_type,
                  fn,
                  priority=priority,
                  source=fn.__module__ or "custom",
              )
              return fn

          if hook is not None:
              return decorator(hook)
          return decorator

      @classmethod
      def register_post_hook(
          cls,
          node_type: Type[SubstraitNode],
          hook: Optional[PostHook] = None,
          *,
          priority: int = 0,
      ) -> Callable[[PostHook], PostHook]:
          """Register a post-visit hook for a node type.

          Post-hooks receive the compilation result and can transform it.

          Args:
              node_type: Node type to hook
              hook: Hook function (optional if used as decorator)
              priority: Higher priority hooks run first

          Returns:
              Decorator or the hook function

          Example:
              @UnifiedExpressionVisitor.register_post_hook(ScalarFunctionNode)
              def add_alias(visitor, node, result):
                  if node.function == SUBSTRAIT_STRING.UPPER:
                      return result.alias("upper_result")
                  return result
          """
          cls._ensure_initialized()

          def decorator(fn: PostHook) -> PostHook:
              cls._registry.register_post_hook(
                  node_type,
                  fn,
                  priority=priority,
                  source=fn.__module__ or "custom",
              )
              return fn

          if hook is not None:
              return decorator(hook)
          return decorator

      @classmethod
      def unregister_handler(cls, node_type: Type[SubstraitNode]) -> bool:
          """Remove a custom handler. Returns True if removed."""
          cls._ensure_initialized()
          return cls._registry.unregister_handler(node_type)

      @classmethod
      def clear_custom_registrations(cls) -> None:
          """Clear all custom handlers and hooks. Useful for testing."""
          cls._ensure_initialized()
          cls._registry.clear_custom()

      @classmethod
      def clear_signature_cache(cls) -> None:
          """Clear the signature cache. Useful for testing."""
          cls._signature_cache.clear()

      @classmethod
      def list_handlers(cls) -> Dict[str, str]:
          """List all registered handlers for debugging."""
          cls._ensure_initialized()
          return cls._registry.list_handlers()

      # =========================================================================
      # Instance Methods
      # =========================================================================

      def __init__(self, expression_system: Any) -> None:
          """Initialize the visitor with a backend expression system.

          Args:
              expression_system: Backend ExpressionSystem instance
                                (PolarsExpressionSystem, IbisExpressionSystem, etc.)
          """
          self.__class__._ensure_initialized()
          self.backend = expression_system

      def visit(self, node: SubstraitNode) -> SupportedExpressions:
          """Visit a node and return the compiled backend expression.

          This is the main entry point. Execution order:
          1. Run pre-hooks (can modify node)
          2. Dispatch to handler (custom or built-in)
          3. Run post-hooks (can modify result)

          Args:
              node: Any SubstraitNode to compile

          Returns:
              Backend-native expression (pl.Expr, nw.Expr, ir.Expr, etc.)

          Raises:
              NotImplementedError: If no handler found for node type
          """
          node_type = type(node)

          # 1. Run pre-hooks
          current_node = node
          for hook_entry in self._registry.get_pre_hooks(node_type):
              modified = hook_entry.hook(self, current_node)
              if modified is not None:
                  current_node = modified

          # 2. Dispatch to handler
          result = self._dispatch(current_node)

          # 3. Run post-hooks
          for hook_entry in self._registry.get_post_hooks(node_type):
              result = hook_entry.hook(self, current_node, result)

          return result

      def _dispatch(self, node: SubstraitNode) -> SupportedExpressions:
          """Find and execute the appropriate handler.

          Resolution order:
          1. Custom handler in registry (with MRO lookup)
          2. Built-in handler via node.accept()
          3. visit_default() fallback
          """
          node_type = type(node)

          # Check custom handlers (with inheritance)
          handler_entry = self._registry.get_handler(node_type)
          if handler_entry is not None:
              return handler_entry.handler(self, node)

          # Fall back to built-in double-dispatch
          if hasattr(node, 'accept'):
              return node.accept(self)

          # No handler found
          return self.visit_default(node)

      def visit_default(self, node: SubstraitNode) -> SupportedExpressions:
          """Default handler for unknown node types.

          Override in a subclass for custom fallback behavior.

          Raises:
              NotImplementedError: Always, with helpful message
          """
          raise NotImplementedError(
              f"No handler registered for node type {type(node).__name__}. "
              f"Register a handler with:\n"
              f"  @UnifiedExpressionVisitor.register_handler({type(node).__name__})\n"
              f"  def handle_{type(node).__name__.lower()}(visitor, node):\n"
              f"      ..."
          )

      # =========================================================================
      # Built-in Handlers (existing implementation, unchanged)
      # =========================================================================

      def visit_literal(self, node: LiteralNode) -> SupportedExpressions:
          """Compile a literal value to backend expression."""
          if node.dtype == "native":
              return node.value
          if self._is_backend_expression(node.value):
              return node.value
          return self.backend.lit(node.value)

      def visit_field_reference(self, node: FieldReferenceNode) -> SupportedExpressions:
          """Compile a column reference to backend expression."""
          return self.backend.col(node.field)

      def visit_scalar_function(self, node: ScalarFunctionNode) -> SupportedExpressions:
          """Compile a scalar function call to backend expression."""
          func_def = FunctionRegistry.get(node.function)
          backend_method_name = func_def.backend_method
          func_name = node.function.value if hasattr(node.function, 'value') else node.function

          args, options = self._resolve_args_with_signature(
              func_name, node.arguments, node.options
          )

          method = getattr(self.backend, backend_method_name)
          return method(*args, **options) if options else method(*args)

      def visit_if_then(self, node: IfThenNode) -> SupportedExpressions:
          """Compile a conditional expression to backend expression."""
          if not node.conditions:
              return self.visit(node.else_clause)

          else_expr = self.visit(node.else_clause)
          current = else_expr

          for condition, result in reversed(node.conditions):
              cond_expr = self.visit(condition)
              result_expr = self.visit(result)
              current = self.backend.if_then_else(cond_expr, result_expr, current)

          return current

      def visit_cast(self, node: CastNode) -> SupportedExpressions:
          """Compile a type cast to backend expression."""
          input_expr = self.visit(node.input)
          return self.backend.cast(input_expr, node.target_type)

      def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:
          """Compile a membership test (IN operator) to backend expression."""
          value_expr = self.visit(node.value)
          options = []
          for opt in node.options:
              if isinstance(opt, LiteralNode):
                  options.append(opt.value)
              elif isinstance(opt, SubstraitNode):
                  options.append(self.visit(opt))
              else:
                  options.append(opt)
          return self.backend.is_in(value_expr, options)

      # =========================================================================
      # Helper Methods (existing implementation, unchanged)
      # =========================================================================

      # ... _get_signature, _resolve_argument, _is_backend_expression,
      # ... _resolve_options, _resolve_args_with_signature
      # ... (keep existing implementations)

  1.5 File Structure

  src/mountainash_expressions/core/unified_visitor/
  ├── __init__.py              # Public exports
  ├── visitor.py               # UnifiedExpressionVisitor (main class)
  ├── registry.py              # VisitorRegistry (handler/hook storage)
  ├── types.py                 # Type definitions (NodeHandler, PreHook, PostHook)
  ├── decorators.py            # Convenience decorators (optional)
  └── contrib/                 # Optional extension handlers
      ├── __init__.py
      ├── logging.py           # Debug logging hooks
      ├── validation.py        # Node validation hooks
      └── optimization.py      # Backend-specific optimizations

  ---
  Part 2: Implementation Plan

  Phase 1: Core Registry Infrastructure (Day 1-2)

  Files to Create:
  1. core/unified_visitor/types.py
  2. core/unified_visitor/registry.py

  Files to Modify:
  1. core/unified_visitor/visitor.py
  2. core/unified_visitor/__init__.py

  Tasks:

  | Task | Description                              | File        |
  |------|------------------------------------------|-------------|
  | 1.1  | Create type definitions                  | types.py    |
  | 1.2  | Implement VisitorRegistry class          | registry.py |
  | 1.3  | Add _registry class attribute to visitor | visitor.py  |
  | 1.4  | Add _ensure_initialized() method         | visitor.py  |
  | 1.5  | Mark built-in handlers during init       | visitor.py  |
  | 1.6  | Update __init__.py exports               | __init__.py |

  Acceptance Criteria:
  - Registry can store handlers and hooks
  - Built-in types are marked and protected
  - Existing tests pass unchanged

  ---
  Phase 2: Registration API (Day 2-3)

  Tasks:

  | Task | Description                                 | File       |
  |------|---------------------------------------------|------------|
  | 2.1  | Implement register_handler() class method   | visitor.py |
  | 2.2  | Implement register_pre_hook() class method  | visitor.py |
  | 2.3  | Implement register_post_hook() class method | visitor.py |
  | 2.4  | Implement unregister_handler()              | visitor.py |
  | 2.5  | Implement clear_custom_registrations()      | visitor.py |
  | 2.6  | Implement list_handlers() for debugging     | visitor.py |

  Acceptance Criteria:
  - Decorator syntax works: @UnifiedExpressionVisitor.register_handler(MyNode)
  - Direct call syntax works: UnifiedExpressionVisitor.register_handler(MyNode, fn)
  - Override protection works (raises without override=True)
  - Existing tests pass unchanged

  ---
  Phase 3: Dispatch Integration (Day 3-4)

  Tasks:

  | Task | Description                                | File        |
  |------|--------------------------------------------|-------------|
  | 3.1  | Update visit() to run pre-hooks            | visitor.py  |
  | 3.2  | Update visit() to run post-hooks           | visitor.py  |
  | 3.3  | Implement _dispatch() with registry lookup | visitor.py  |
  | 3.4  | Add MRO-aware handler lookup               | registry.py |
  | 3.5  | Implement visit_default() fallback         | visitor.py  |

  Acceptance Criteria:
  - Custom handlers take precedence over built-ins
  - Pre-hooks can modify nodes
  - Post-hooks can transform results
  - Inheritance-aware lookup works
  - Existing tests pass unchanged

  ---
  Phase 4: Testing (Day 4-5)

  Files to Create:
  1. tests/unit/test_visitor_registry.py
  2. tests/unit/test_visitor_hooks.py
  3. tests/unit/test_custom_handlers.py

  Tests to Write:

  # test_visitor_registry.py

  class TestHandlerRegistration:
      def test_register_custom_handler_decorator(self):
          """Custom handler via decorator syntax."""

      def test_register_custom_handler_direct(self):
          """Custom handler via direct call."""

      def test_override_protection(self):
          """Cannot override built-in without flag."""

      def test_override_allowed(self):
          """Can override built-in with flag."""

      def test_unregister_handler(self):
          """Can remove custom handler."""

      def test_list_handlers(self):
          """Can list all registered handlers."""


  class TestInheritanceAwareLookup:
      def test_handler_for_subclass(self):
          """Handler for parent type applies to subclass."""

      def test_specific_handler_precedence(self):
          """Specific handler takes precedence over parent."""


  class TestPreHooks:
      def test_pre_hook_called(self):
          """Pre-hook is called before handler."""

      def test_pre_hook_can_modify_node(self):
          """Pre-hook can return modified node."""

      def test_pre_hook_priority(self):
          """Higher priority hooks run first."""


  class TestPostHooks:
      def test_post_hook_called(self):
          """Post-hook is called after handler."""

      def test_post_hook_can_transform_result(self):
          """Post-hook can modify result."""

      def test_post_hook_priority(self):
          """Higher priority hooks run first."""


  class TestCustomNodeTypes:
      def test_custom_node_with_handler(self):
          """Custom node type compiles with registered handler."""

      def test_custom_node_without_handler_raises(self):
          """Custom node without handler raises NotImplementedError."""

  Acceptance Criteria:
  - All new tests pass
  - All existing tests pass
  - 90%+ coverage on new code

  ---
  Phase 5: Documentation & Examples (Day 5-6)

  Files to Create:
  1. docs/extending_visitor.md
  2. core/unified_visitor/contrib/logging.py
  3. core/unified_visitor/contrib/validation.py

  Documentation Sections:

  # Extending the Visitor System

  ## Overview
  ## Registering Custom Handlers
  ### Decorator Syntax
  ### Direct Registration
  ### Override Built-in Handlers

  ## Using Hooks
  ### Pre-Visit Hooks
  ### Post-Visit Hooks
  ### Hook Priority

  ## Custom Node Types
  ### Defining a Custom Node
  ### Registering the Handler
  ### Integration with Expression API

  ## Examples
  ### Logging/Tracing
  ### Backend-Specific Optimization
  ### Query Statistics Collection

  ## Best Practices
  ## API Reference

  Example Contrib Modules:

  # contrib/logging.py

  from ..visitor import UnifiedExpressionVisitor
  from ...substrait_nodes import SubstraitNode, ScalarFunctionNode
  import logging

  logger = logging.getLogger("mountainash.visitor")


  def enable_logging(level: int = logging.DEBUG) -> None:
      """Enable visitor execution logging."""

      @UnifiedExpressionVisitor.register_pre_hook(SubstraitNode)
      def log_visit(visitor, node):
          logger.log(level, f"Visiting: {type(node).__name__}")
          return None

      @UnifiedExpressionVisitor.register_pre_hook(ScalarFunctionNode)
      def log_function(visitor, node):
          func_name = node.function.value if hasattr(node.function, 'value') else node.function
          logger.log(level, f"  Function: {func_name}")
          return None


  def disable_logging() -> None:
      """Disable visitor execution logging."""
      UnifiedExpressionVisitor.clear_custom_registrations()

  # contrib/validation.py

  from ..visitor import UnifiedExpressionVisitor
  from ...substrait_nodes import ScalarFunctionNode
  from ...functions import FunctionRegistry


  def enable_validation() -> None:
      """Enable strict validation of nodes before compilation."""

      @UnifiedExpressionVisitor.register_pre_hook(ScalarFunctionNode, priority=100)
      def validate_function_registered(visitor, node):
          """Ensure function is in registry."""
          try:
              FunctionRegistry.get(node.function)
          except KeyError:
              raise ValueError(
                  f"Function {node.function} not registered. "
                  f"Available: {FunctionRegistry.list_all()}"
              )
          return None

      @UnifiedExpressionVisitor.register_pre_hook(ScalarFunctionNode, priority=99)
      def validate_argument_count(visitor, node):
          """Validate argument count matches protocol."""
          func_def = FunctionRegistry.get(node.function)
          sig = func_def.get_signature()
          if sig:
              # Check argument count
              params = [p for p in sig.parameters.values() if p.name != 'self']
              required = sum(1 for p in params if p.default is p.empty)
              if len(node.arguments) < required:
                  raise ValueError(
                      f"Function {node.function} requires {required} arguments, "
                      f"got {len(node.arguments)}"
                  )
          return None

  ---
  Phase 6: Integration & Migration (Day 6-7)

  Tasks:

  | Task | Description                                         |
  |------|-----------------------------------------------------|
  | 6.1  | Update expression API compile() to use new visitor  |
  | 6.2  | Remove any legacy visitor factory code dependencies |
  | 6.3  | Update type hints throughout                        |
  | 6.4  | Run full test suite                                 |
  | 6.5  | Performance benchmark comparison                    |

  Migration Checklist:
  - All cross-backend tests pass
  - No performance regression (within 5%)
  - Documentation updated
  - CHANGELOG updated
  - Deprecation warnings for any changed APIs

  ---
  Part 3: API Summary

  Public API

  from mountainash_expressions.core.unified_visitor import (
      UnifiedExpressionVisitor,
      NodeHandler,
      PreHook,
      PostHook,
  )

  # Registration
  UnifiedExpressionVisitor.register_handler(node_type, handler, override=False, priority=0)
  UnifiedExpressionVisitor.register_pre_hook(node_type, hook, priority=0)
  UnifiedExpressionVisitor.register_post_hook(node_type, hook, priority=0)

  # Management
  UnifiedExpressionVisitor.unregister_handler(node_type) -> bool
  UnifiedExpressionVisitor.clear_custom_registrations() -> None
  UnifiedExpressionVisitor.list_handlers() -> Dict[str, str]

  # Usage
  visitor = UnifiedExpressionVisitor(expression_system)
  result = visitor.visit(node)

  Decorator Signatures

  @UnifiedExpressionVisitor.register_handler(MyNode)
  def handle_my_node(visitor: UnifiedExpressionVisitor, node: MyNode) -> SupportedExpressions:
      ...

  @UnifiedExpressionVisitor.register_pre_hook(ScalarFunctionNode)
  def pre_process(visitor: UnifiedExpressionVisitor, node: ScalarFunctionNode) -> Optional[SubstraitNode]:
      ...  # Return None to keep original, or modified node

  @UnifiedExpressionVisitor.register_post_hook(ScalarFunctionNode)
  def post_process(visitor: UnifiedExpressionVisitor, node: ScalarFunctionNode, result: SupportedExpressions) -> SupportedExpressions:
      ...  # Must return result (possibly modified)

  ---
  Part 4: Timeline Summary

  | Phase                         | Duration | Deliverables                              |
  |-------------------------------|----------|-------------------------------------------|
  | Phase 1: Core Registry        | 1-2 days | types.py, registry.py, updated visitor.py |
  | Phase 2: Registration API     | 1-2 days | Class methods, decorator support          |
  | Phase 3: Dispatch Integration | 1-2 days | Hook execution, custom handler dispatch   |
  | Phase 4: Testing              | 1-2 days | Unit tests, integration tests             |
  | Phase 5: Documentation        | 1 day    | Docs, examples, contrib modules           |
  | Phase 6: Integration          | 1 day    | Full integration, migration, benchmarks   |

  Total: 6-10 days

  ---
  Part 5: Risks & Mitigations

  | Risk                                      | Impact | Mitigation                                       |
  |-------------------------------------------|--------|--------------------------------------------------|
  | Performance regression from hook overhead | Medium | Lazy hook lookup, benchmark early                |
  | Breaking existing tests                   | High   | Run tests after each phase                       |
  | Complex inheritance edge cases            | Low    | Comprehensive MRO tests                          |
  | Memory leaks from class-level registry    | Low    | Weak references if needed                        |
  | Thread safety issues                      | Medium | Document single-threaded assumption or add locks |

  ---
  This plan provides a complete architecture and implementation roadmap. Shall I proceed with implementing Phase 1?
