"""
Formal Languages and Automata (FLA) Module: Waste Observation Lifecycle Automaton

Defines a Deterministic Finite Automaton (DFA) representing the formal state transitions
of a plastic waste observation from initial field reporting through GIS prioritisation
and eventual remediation or archival.

Formal Definition:
    M = (Q, Σ, δ, q_0, F)
    Q: States
    Σ: Alphabet of input events / symbols
    δ: Transition function (Q × Σ -> Q)
    q_0: Initial state (DRAFT)
    F: Accepting / Terminal states (ARCHIVED, REJECTED)
"""

from typing import Dict, Set, Tuple, List, Optional


class InvalidTransitionError(ValueError):
    """Raised when an input symbol cannot be accepted from the current state."""
    pass


class WasteObservationFSM:
    """
    Deterministic Finite Automaton for Waste Observation Lifecycle.
    
    States (Q):
        - DRAFT: Initial raw submission without verified coordinates or classification.
        - GEO_TAGGED: Observation bound to verified WGS84 coordinates.
        - CLASSIFIED: Visual classifier has completed inference on waste material.
        - HOTSPOT_FLAGGED: Spatial concentration exceeds priority threshold.
        - VERIFIED: Observation validated by GIS operator / survey team.
        - DISPATCHED: Clean-up / remediation resources assigned to location.
        - ARCHIVED: Observation completed, documented, and archived (Accepting state).
        - REJECTED: Observation rejected due to corrupt data, out-of-bounds, or invalid survey (Accepting state).
    
    Alphabet (Σ):
        - 'add_coords': Attach verified latitude and longitude.
        - 'classify_image': Run visual classifier on observation imagery.
        - 'flag_hotspot': Spatial analysis confirms high plastic concentration.
        - 'operator_verify': Manual or algorithmic validation of observation.
        - 'dispatch_cleanup': Assign field intervention team.
        - 'complete_archive': Clean-up finished or baseline record archived.
        - 'invalidate': Reject observation due to invalid data or false alarm.
    """

    STATES: Set[str] = {
        "DRAFT",
        "GEO_TAGGED",
        "CLASSIFIED",
        "HOTSPOT_FLAGGED",
        "VERIFIED",
        "DISPATCHED",
        "ARCHIVED",
        "REJECTED"
    }

    ALPHABET: Set[str] = {
        "add_coords",
        "classify_image",
        "flag_hotspot",
        "operator_verify",
        "dispatch_cleanup",
        "complete_archive",
        "invalidate"
    }

    INITIAL_STATE: str = "DRAFT"

    ACCEPTING_STATES: Set[str] = {
        "ARCHIVED",
        "REJECTED"
    }

    # Transition table δ: (state, symbol) -> next_state
    TRANSITIONS: Dict[Tuple[str, str], str] = {
        # From DRAFT
        ("DRAFT", "add_coords"): "GEO_TAGGED",
        ("DRAFT", "classify_image"): "CLASSIFIED",
        ("DRAFT", "invalidate"): "REJECTED",

        # From GEO_TAGGED
        ("GEO_TAGGED", "classify_image"): "HOTSPOT_FLAGGED",
        ("GEO_TAGGED", "flag_hotspot"): "HOTSPOT_FLAGGED",
        ("GEO_TAGGED", "operator_verify"): "VERIFIED",
        ("GEO_TAGGED", "invalidate"): "REJECTED",

        # From CLASSIFIED
        ("CLASSIFIED", "add_coords"): "HOTSPOT_FLAGGED",
        ("CLASSIFIED", "operator_verify"): "VERIFIED",
        ("CLASSIFIED", "invalidate"): "REJECTED",

        # From HOTSPOT_FLAGGED
        ("HOTSPOT_FLAGGED", "operator_verify"): "VERIFIED",
        ("HOTSPOT_FLAGGED", "dispatch_cleanup"): "DISPATCHED",
        ("HOTSPOT_FLAGGED", "invalidate"): "REJECTED",

        # From VERIFIED
        ("VERIFIED", "dispatch_cleanup"): "DISPATCHED",
        ("VERIFIED", "complete_archive"): "ARCHIVED",
        ("VERIFIED", "invalidate"): "REJECTED",

        # From DISPATCHED
        ("DISPATCHED", "complete_archive"): "ARCHIVED",
        ("DISPATCHED", "invalidate"): "REJECTED",
    }

    def __init__(self, initial_state: Optional[str] = None):
        start = initial_state or self.INITIAL_STATE
        if start not in self.STATES:
            raise ValueError(f"Unknown initial state: {start}")
        self.current_state: str = start
        self.history: List[Tuple[str, str, str]] = []  # (from_state, symbol, to_state)

    def transition(self, symbol: str) -> str:
        """
        Executes a single state transition δ(current_state, symbol).
        Raises InvalidTransitionError if the transition is undefined.
        """
        if symbol not in self.ALPHABET:
            raise InvalidTransitionError(
                f"Symbol '{symbol}' not in alphabet Σ: {sorted(self.ALPHABET)}"
            )

        key = (self.current_state, symbol)
        if key not in self.TRANSITIONS:
            raise InvalidTransitionError(
                f"Transition undefined: delta('{self.current_state}', '{symbol}') has no valid rule."
            )

        next_state = self.TRANSITIONS[key]
        self.history.append((self.current_state, symbol, next_state))
        self.current_state = next_state
        return self.current_state

    def process_word(self, symbols: List[str]) -> Tuple[bool, str, List[Tuple[str, str, str]]]:
        """
        Processes a sequence of input symbols w = σ_1 σ_2 ... σ_k ∈ Σ*.
        Returns (is_accepted, final_state, execution_trace).
        """
        for s in symbols:
            self.transition(s)
        return self.is_accepted(), self.current_state, self.history

    def is_accepted(self) -> bool:
        """Returns True if the current state is in accepting states F."""
        return self.current_state in self.ACCEPTING_STATES

    def get_valid_transitions(self) -> Dict[str, str]:
        """Returns map of {symbol: destination_state} valid from the current state."""
        return {
            sym: dest for (src, sym), dest in self.TRANSITIONS.items()
            if src == self.current_state
        }

    def to_dict(self) -> Dict:
        """Serializes current FSM state for API responses."""
        return {
            "current_state": self.current_state,
            "is_accepted": self.is_accepted(),
            "valid_inputs": list(self.get_valid_transitions().keys()),
            "history_length": len(self.history),
            "history": [
                {"from": h[0], "symbol": h[1], "to": h[2]}
                for h in self.history
            ]
        }
