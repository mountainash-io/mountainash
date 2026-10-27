"""Transfer-spy support: tell plan transfers apart from the terminal's own egress."""
from __future__ import annotations

import pytest


class TerminalEgress:
    """True while ``CompilationSession.egress`` (the terminal's representation change) runs."""

    def __init__(self) -> None:
        self.depth = 0

    @property
    def active(self) -> bool:
        return self.depth > 0


@pytest.fixture
def terminal_egress(monkeypatch) -> TerminalEgress:
    from mountainash.relations.core.execution.compilation import CompilationSession

    state = TerminalEgress()
    real = CompilationSession.egress

    def egress(self, location):
        state.depth += 1
        try:
            return real(self, location)
        finally:
            state.depth -= 1

    monkeypatch.setattr(CompilationSession, "egress", egress)
    return state
