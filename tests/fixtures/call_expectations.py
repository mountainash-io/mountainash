"""Explicit expectations around an ordinary test's operation and oracle."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest


@contextmanager
def expect_call_failure(
    *,
    reason: str,
    errors: tuple[type[BaseException], ...],
    when: bool = True,
) -> Iterator[None]:
    """Execute the selected call; only its exact known failure may xfail.

    Fixture setup and teardown remain outside this boundary. A corrected result
    fails strictly, while unrelated exceptions (including subtypes) propagate.
    """
    if not when:
        yield
        return
    try:
        yield
    except BaseException as error:
        if type(error) not in errors:
            raise
        pytest.xfail(reason)
    else:
        pytest.fail(f"[XPASS(strict)] {reason}", pytrace=False)
