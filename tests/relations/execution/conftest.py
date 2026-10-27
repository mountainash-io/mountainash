"""Transfer-spy support: tell plan transfers apart from the terminal's own egress."""
from __future__ import annotations

import pytest


class TerminalEgress:
    """True only while the terminal requirement's own transfer runs.

    A replayed prepared root transfer inside ``CompilationSession.egress`` is a
    plan transfer and stays visible to spies.
    """

    def __init__(self) -> None:
        self.depth = 0
        self.destination = None

    @property
    def active(self) -> bool:
        return self.depth > 0


@pytest.fixture
def terminal_egress(monkeypatch) -> TerminalEgress:
    from mountainash.relations.core.execution.compilation import CompilationSession
    from mountainash.relations.core.execution.transport import TransportSession

    state = TerminalEgress()
    real_egress = CompilationSession.egress
    real_transfer = TransportSession.transfer

    def egress(self, location, **kwargs):
        previous, state.destination = state.destination, location
        try:
            return real_egress(self, location, **kwargs)
        finally:
            state.destination = previous

    def transfer(self, source, requirement):
        if state.destination is not None and requirement.destination is state.destination:
            state.depth += 1
            try:
                return real_transfer(self, source, requirement)
            finally:
                state.depth -= 1
        return real_transfer(self, source, requirement)

    monkeypatch.setattr(CompilationSession, "egress", egress)
    monkeypatch.setattr(TransportSession, "transfer", transfer)
    return state
