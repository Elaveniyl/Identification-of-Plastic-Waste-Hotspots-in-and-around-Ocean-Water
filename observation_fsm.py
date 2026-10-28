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

from typing import Dict, Set, Tuple, List, Optional, Union, Any


class InvalidTransitionError(ValueError):
    """Raised when an input symbol cannot be accepted from the current state."""
    pass


class WasteObservationFSM:
    """
    Deterministic Finite Automaton for Waste Observation Lifecycle.
    
    Formal Definition:
        M = (Q, Σ, δ, q_0, F)
    """

    TRAP_STATE: str = "TRAP"

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

    @classmethod
    def get_formal_definition(cls) -> Dict[str, Any]:
        """
        Returns the formal 5-tuple M = (Q, Σ, δ, q_0, F) dynamically extracted from the class definition.
        """
        transitions_list = [
            {"from": src, "symbol": sym, "to": dst}
            for (src, sym), dst in sorted(cls.TRANSITIONS.items())
        ]
        return {
            "states": sorted(list(cls.STATES)),
            "alphabet": sorted(list(cls.ALPHABET)),
            "initial_state": cls.INITIAL_STATE,
            "accepting_states": sorted(list(cls.ACCEPTING_STATES)),
            "transitions": transitions_list,
            "is_total": False,
            "trap_state": cls.TRAP_STATE
        }

    @classmethod
    def get_completed_dfa(cls) -> Dict[str, Any]:
        """
        Transforms the partial transition function δ into a total transition function δ_complete
        by explicitly routing all undefined (q, σ) pairs to a trap/dead sink state (TRAP).
        For the TRAP state, δ_complete(TRAP, σ) = TRAP for all σ ∈ Σ.
        """
        complete_states = sorted(list(cls.STATES | {cls.TRAP_STATE}))
        alphabet = sorted(list(cls.ALPHABET))
        complete_transitions = {}

        for state in complete_states:
            for sym in alphabet:
                if state == cls.TRAP_STATE:
                    complete_transitions[(state, sym)] = cls.TRAP_STATE
                else:
                    complete_transitions[(state, sym)] = cls.TRANSITIONS.get((state, sym), cls.TRAP_STATE)

        transitions_list = [
            {"from": src, "symbol": sym, "to": dst}
            for (src, sym), dst in sorted(complete_transitions.items())
        ]

        return {
            "states": complete_states,
            "alphabet": alphabet,
            "initial_state": cls.INITIAL_STATE,
            "accepting_states": sorted(list(cls.ACCEPTING_STATES)),
            "trap_state": cls.TRAP_STATE,
            "transitions": transitions_list,
            "is_total": True
        }

    @classmethod
    def accepts_word(cls, symbols: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Evaluates whether an input word w ∈ Σ* is accepted by M = (Q, Σ, δ, q_0, F).
        Returns:
            accepted (bool): True if execution ends in an accepting state F.
            final_state (str): The state reached after processing or trap.
            state_path (List[str]): Sequence of states visited [q_0, q_1, ..., q_k].
            failing_position (Optional[int]): 0-indexed position of rejected symbol or end if not accepted.
            failing_symbol (Optional[str]): Symbol that caused transition failure.
            error (Optional[str]): Diagnostic message detailing rejection reason.
        """
        if isinstance(symbols, str):
            if not symbols.strip():
                sym_list = []
            elif "," in symbols:
                sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
            else:
                sym_list = symbols.strip().split()
        elif isinstance(symbols, (list, tuple)):
            sym_list = list(symbols)
        else:
            return {
                "accepted": False,
                "final_state": cls.INITIAL_STATE,
                "state_path": [cls.INITIAL_STATE],
                "failing_position": 0,
                "failing_symbol": None,
                "error": f"Invalid input type: expected str or list, got {type(symbols).__name__}"
            }

        curr = cls.INITIAL_STATE
        path = [curr]

        for idx, sym in enumerate(sym_list):
            if sym not in cls.ALPHABET:
                path.append(cls.TRAP_STATE)
                return {
                    "accepted": False,
                    "final_state": cls.TRAP_STATE,
                    "state_path": path,
                    "failing_position": idx,
                    "failing_symbol": sym,
                    "error": f"Symbol '{sym}' at position {idx} is not in alphabet Σ."
                }

            key = (curr, sym)
            if key not in cls.TRANSITIONS:
                path.append(cls.TRAP_STATE)
                return {
                    "accepted": False,
                    "final_state": cls.TRAP_STATE,
                    "state_path": path,
                    "failing_position": idx,
                    "failing_symbol": sym,
                    "error": f"Undefined transition δ('{curr}', '{sym}') at position {idx} routes to {cls.TRAP_STATE}."
                }

            curr = cls.TRANSITIONS[key]
            path.append(curr)

        is_acc = curr in cls.ACCEPTING_STATES
        return {
            "accepted": is_acc,
            "final_state": curr,
            "state_path": path,
            "failing_position": None if is_acc else len(sym_list),
            "failing_symbol": None,
            "error": None if is_acc else f"Execution completed in non-accepting state '{curr}'."
        }
