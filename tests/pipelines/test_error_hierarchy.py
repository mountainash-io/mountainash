"""StepEmptyError relocates to pipelines.errors with an always-on back-compat shim."""
from __future__ import annotations

import pickle


def test_new_location_under_root():
    from mountainash.core.errors import MountainashError
    from mountainash.pipelines.errors import StepEmptyError
    assert issubclass(StepEmptyError, MountainashError)


def test_old_path_is_same_object():
    from mountainash.pipelines.errors import StepEmptyError as NewLoc
    from mountainash.pipelines.orchestration.simple import StepEmptyError as OldLoc
    assert OldLoc is NewLoc


def test_class_defined_in_new_module():
    # New pickles must reference the new path, so __module__ must be the new home.
    from mountainash.pipelines.errors import StepEmptyError
    assert StepEmptyError.__module__ == "mountainash.pipelines.errors"


def test_pickle_round_trip():
    # Guards the qualname-resolution break the relocation could otherwise cause.
    from mountainash.pipelines.errors import StepEmptyError
    restored = pickle.loads(pickle.dumps(StepEmptyError("x")))
    assert isinstance(restored, StepEmptyError)
    assert restored.args == ("x",)


def test_old_path_pickle_compat():
    # Simulate a pre-relocation pickle whose global references the OLD module path,
    # and assert the shim lets it restore to the relocated class. This is the
    # backward-compat case the relocation could otherwise silently break.
    from mountainash.pipelines.errors import StepEmptyError

    # Build a pickle referencing the OLD module path.
    # We do this by creating an instance, pickling it, then manually reconstructing
    # the pickle bytes with the old module path. Because the old path is longer,
    # we need to use GLOBAL opcode (which uses CRLF as delimiter) instead of SHORT_BINUNICODE.

    # Pickle protocol: use GLOBAL (opcode 'c') which takes lines of module\nclass\n
    import io
    import pickletools

    fresh = pickle.dumps(StepEmptyError("x"))

    # We'll use a helper: create a pickle with protocol 2 which uses the TEXT-based
    # GLOBAL opcode, then manually edit it
    fresh_p2 = pickle.dumps(StepEmptyError("x"), protocol=2)

    # For protocol 2, GLOBAL is opcode 'c', taking "module\nclass\n" lines.
    # Find the GLOBAL opcode and replace module name
    old_style = fresh_p2.replace(
        b"mountainash.pipelines.errors\n",
        b"mountainash.pipelines.orchestration.simple\n",
    )

    restored = pickle.loads(old_style)
    assert type(restored) is StepEmptyError
    assert restored.args == ("x",)
