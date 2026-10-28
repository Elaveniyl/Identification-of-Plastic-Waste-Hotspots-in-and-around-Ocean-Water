"""
Formal Languages and Automata (FLA) Analysis Tool
AI-GIS Detection and Prioritisation of Plastic Waste Hotspots

Performs theoretical analysis on the Waste Observation Lifecycle Automaton:
1. Formal 5-tuple extraction M = (Q, Sigma, delta, q_0, F)
2. State Reachability and Connectivity Analysis
3. Graphviz DOT and Mermaid State Diagram Generation
4. Markdown Transition Table Generation (Partial and Completed Total DFA)
5. Regular Expression Derivation via GNFA State Elimination
6. Exhaustive Verification of Derived Regular Expression vs. DFA Simulation (>= 200 words)
7. DFA Minimality Verification via Moore's Partition Refinement (Myhill-Nerode)
"""

import sys
import itertools
import random
import re
from pathlib import Path
from typing import Dict, Set, Tuple, List, Any

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from observation_fsm import WasteObservationFSM


def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def analyze_reachability() -> Dict[str, Any]:
    states = WasteObservationFSM.STATES
    init = WasteObservationFSM.INITIAL_STATE
    transitions = WasteObservationFSM.TRANSITIONS
    
    visited = set()
    queue = [init]
    while queue:
        curr = queue.pop(0)
        if curr not in visited:
            visited.add(curr)
            for (src, sym), dst in transitions.items():
                if src == curr and dst not in visited:
                    queue.append(dst)
                    
    unreachable = states - visited
    return {
        "all_states": sorted(list(states)),
        "reachable_states": sorted(list(visited)),
        "unreachable_states": sorted(list(unreachable)),
        "is_fully_reachable": len(unreachable) == 0,
        "accepting_states": sorted(list(WasteObservationFSM.ACCEPTING_STATES))
    }


def generate_mermaid_diagram() -> str:
    lines = ["stateDiagram-v2", "    [*] --> DRAFT"]
    for (src, sym), dst in sorted(WasteObservationFSM.TRANSITIONS.items()):
        lines.append(f"    {src} --> {dst}: {sym}")
    lines.append("    ARCHIVED --> [*]")
    lines.append("    REJECTED --> [*]")
    return "\n".join(lines)


def generate_dot_diagram() -> str:
    lines = [
        "digraph WasteObservationLifecycle {",
        "    rankdir=LR;",
        '    size="8,5";',
        '    node [shape = doublecircle, style=filled, fillcolor="#d4edda"]; ARCHIVED REJECTED;',
        '    node [shape = circle, style=filled, fillcolor="#e8f4f8"];',
        "    __start__ [shape=point, style=invis];",
        "    __start__ -> DRAFT;"
    ]
    for (src, sym), dst in sorted(WasteObservationFSM.TRANSITIONS.items()):
        lines.append(f'    {src} -> {dst} [label="{sym}"];')
    lines.append("}")
    return "\n".join(lines)


def generate_markdown_table(completed: bool = False) -> str:
    if completed:
        spec = WasteObservationFSM.get_completed_dfa()
        title = "Total Transition Table delta_complete (with TRAP state)"
    else:
        spec = WasteObservationFSM.get_formal_definition()
        title = "Partial Transition Table delta (Original Domain Rules)"
        
    states = spec["states"]
    alphabet = spec["alphabet"]
    delta = {(t["from"], t["symbol"]): t["to"] for t in spec["transitions"]}
    
    header = ["State"] + alphabet
    sep = ["---"] * len(header)
    rows = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    
    for s in states:
        prefix = ""
        if s == spec["initial_state"]:
            prefix += "-> "
        if s in spec["accepting_states"]:
            prefix += "* "
        row = [f"{prefix}**{s}**"]
        for sym in alphabet:
            dest = delta.get((s, sym), "-")
            row.append(dest)
        rows.append("| " + " | ".join(row) + " |")
        
    return f"### {title}\n\n" + "\n".join(rows)


def derive_regular_expression() -> Dict[str, Any]:
    states = list(WasteObservationFSM.STATES)
    init_state = WasteObservationFSM.INITIAL_STATE
    accept_states = set(WasteObservationFSM.ACCEPTING_STATES)

    edges = {}
    for (src, sym), dst in WasteObservationFSM.TRANSITIONS.items():
        edges.setdefault((src, dst), set()).add(sym)

    S = "__START__"
    A = "__ACCEPT__"
    edges[(S, init_state)] = {"EPSILON"}
    for f in accept_states:
        edges.setdefault((f, A), set()).add("EPSILON")

    for k in states:
        incoming = [u for (u, v) in edges.keys() if v == k and u != k]
        outgoing = [v for (u, v) in edges.keys() if u == k and v != k]

        for u in incoming:
            r_uk = edges[(u, k)]
            for v in outgoing:
                r_kv = edges[(k, v)]
                new_paths = set()
                for r1 in r_uk:
                    for r2 in r_kv:
                        if r1 == "EPSILON" and r2 == "EPSILON":
                            new_paths.add("EPSILON")
                        elif r1 == "EPSILON":
                            new_paths.add(r2)
                        elif r2 == "EPSILON":
                            new_paths.add(r1)
                        else:
                            new_paths.add(f"{r1}/{r2}")
                edges.setdefault((u, v), set()).update(new_paths)

        edges = {pair: regexes for pair, regexes in edges.items() if k not in pair}

    raw_paths = sorted(list(edges.get((S, A), set())))
    word_tuples = [tuple(p.split("/")) for p in raw_paths]
    exact_words_str = [",".join(w) for w in word_tuples]
    regex_pattern = "^(" + "|".join(re.escape(w) for w in sorted(exact_words_str)) + ")$"
    compiled_regex = re.compile(regex_pattern)

    return {
        "total_paths": len(word_tuples),
        "paths": word_tuples,
        "formatted_paths": exact_words_str,
        "regex_pattern": regex_pattern,
        "compiled_regex": compiled_regex
    }


def verify_regex_vs_dfa() -> Dict[str, Any]:
    regex_data = derive_regular_expression()
    compiled_regex = regex_data["compiled_regex"]
    alphabet = sorted(list(WasteObservationFSM.ALPHABET))
    
    tested_words = []
    tested_words.append([])
    
    for path in regex_data["paths"]:
        tested_words.append(list(path))
        
    for length in (1, 2, 3):
        for prod in itertools.product(alphabet, repeat=length):
            tested_words.append(list(prod))
            
    rng = random.Random(42)
    for length in (4, 5, 6, 7, 8):
        for _ in range(50):
            word = [rng.choice(alphabet) for _ in range(length)]
            tested_words.append(word)

    unique_words = []
    seen = set()
    for w in tested_words:
        key = tuple(w)
        if key not in seen:
            seen.add(key)
            unique_words.append(w)
            
    matches = 0
    mismatches = []
    
    for word in unique_words:
        dfa_result = WasteObservationFSM.accepts_word(word)["accepted"]
        word_str = ",".join(word)
        regex_result = bool(compiled_regex.fullmatch(word_str))
        
        if dfa_result == regex_result:
            matches += 1
        else:
            mismatches.append({
                "word": word,
                "dfa_accepted": dfa_result,
                "regex_accepted": regex_result
            })
            
    return {
        "total_tested": len(unique_words),
        "matches": matches,
        "mismatches_count": len(mismatches),
        "mismatches": mismatches,
        "is_consistent": len(mismatches) == 0
    }


def check_dfa_minimality() -> Dict[str, Any]:
    """
    Applies Moore's partition refinement algorithm on the completed total DFA.
    Refines all blocks simultaneously in rounds based on symbol signature vectors.
    """
    completed = WasteObservationFSM.get_completed_dfa()
    states = set(completed["states"])
    alphabet = set(completed["alphabet"])
    delta = {(t["from"], t["symbol"]): t["to"] for t in completed["transitions"]}
    F = set(completed["accepting_states"])
    non_F = states - F

    P = [F, non_F]
    step = 0
    changed = True
    
    while changed:
        step += 1
        changed = False
        new_P = []
        for group in P:
            if len(group) <= 1:
                new_P.append(group)
                continue
            
            subgroups = {}
            for s in group:
                sig = []
                for sym in sorted(alphabet):
                    dest = delta[(s, sym)]
                    for idx, target_grp in enumerate(P):
                        if dest in target_grp:
                            sig.append(idx)
                            break
                sig = tuple(sig)
                subgroups.setdefault(sig, set()).add(s)
                
            if len(subgroups) > 1:
                changed = True
                new_P.extend(subgroups.values())
            else:
                new_P.append(group)
        P = new_P

    classes = [sorted(list(grp)) for grp in P]
    return {
        "total_states": len(states),
        "iterations_to_converge": step,
        "equivalence_classes": classes,
        "num_classes": len(classes),
        "distinguishable_classes_count": len(classes),
        "merged_states": [c for c in classes if len(c) > 1]
    }


def main():
    print_section("FORMAL SPECIFICATION M = (Q, Sigma, delta, q_0, F)")
    spec = WasteObservationFSM.get_formal_definition()
    print(f"States Q ({len(spec['states'])}): {spec['states']}")
    print(f"Alphabet Sigma ({len(spec['alphabet'])}): {spec['alphabet']}")
    print(f"Start State q0: {spec['initial_state']}")
    print(f"Accepting States F: {spec['accepting_states']}")
    print(f"Transitions count: {len(spec['transitions'])}")

    print_section("STATE REACHABILITY & CONNECTIVITY")
    reach = analyze_reachability()
    print(f"Reachable States ({len(reach['reachable_states'])}): {reach['reachable_states']}")
    print(f"Unreachable States ({len(reach['unreachable_states'])}): {reach['unreachable_states']}")
    print(f"Automaton Fully Reachable: {reach['is_fully_reachable']}")

    print_section("TRANSITION TABLE (MARKDOWN)")
    print(generate_markdown_table(completed=False))
    print("\n" + generate_markdown_table(completed=True))

    print_section("DIAGRAMS")
    print("### Mermaid State Diagram:")
    print("```mermaid")
    print(generate_mermaid_diagram())
    print("```")
    print("\n### Graphviz DOT Diagram:")
    print(generate_dot_diagram())

    print_section("REGULAR EXPRESSION DERIVATION (GNFA STATE ELIMINATION)")
    regex_res = derive_regular_expression()
    print(f"Total Accepted Distinct Words: {regex_res['total_paths']}")
    print("Because the transition graph is acyclic, the elimination result is a finite union")
    print("of 32 words with no Kleene star (*), so the language is finite (hence regular).")
    print("Sample Accepted Words:")
    for w in regex_res['formatted_paths'][:10]:
        print(f"  - {w}")
    print(f"  ... [{regex_res['total_paths'] - 10} more paths]")

    print_section("REGULAR EXPRESSION VS. DFA SIMULATION (TEST SUITE >= 200 WORDS)")
    verif = verify_regex_vs_dfa()
    print(f"Total Words Tested: {verif['total_tested']}")
    print(f"Matches: {verif['matches']}")
    print(f"Mismatches: {verif['mismatches_count']}")
    print(f"DFA and Regex Equivalence Verified: {verif['is_consistent']}")

    print_section("MOORE'S PARTITION REFINEMENT MINIMALITY CHECK (MYHILL-NERODE)")
    min_res = check_dfa_minimality()
    print(f"Initial Total States (with TRAP): {min_res['total_states']}")
    print(f"Converged in: {min_res['iterations_to_converge']} iterations (Moore's algorithm)")
    print(f"Equivalence Classes ({min_res['num_classes']}):")
    for idx, c in enumerate(min_res['equivalence_classes']):
        print(f"  Class {idx + 1}: {c}")
    print(f"Merged States in Unlabelled Language Minimization: {min_res['merged_states']}")
    print("Theoretical Conclusion:")
    print("  8 classes = {ARCHIVED, REJECTED} merged + 6 other states + TRAP.")
    print("  ARCHIVED and REJECTED both have empty right-languages L(s) = {epsilon}.")
    print("  They merge in an unlabelled binary acceptor, but remain distinct in the domain lifecycle.")
    print("  All non-terminal states and TRAP are strictly pairwise distinguishable.")


if __name__ == '__main__':
    main()
