#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Nelson Daniel Spence
# SPDX-License-Identifier: CC-BY-4.0
"""Reproduce the finite checks in frankl-conjecture-audit.tex.

The implementation below follows Algorithm A2 as printed in
J. K. Abdurakhmanov, arXiv:2601.18450 and HAL hal-05482771v1:

* one row and more than one column -> True;
* one column -> True iff ones >= zeros;
* for each column k, return True immediately when the zero-fibre has
  exactly one row;
* otherwise reject if either nonempty fibre, after deleting k, has
  strictly more zeros than ones in every column;
* recursively reject if any such fibre is rejected;
* return True after all columns are processed.

No third-party packages are required.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from itertools import combinations, permutations
from typing import Iterable, Sequence, TypeAlias

BitRow: TypeAlias = tuple[int, ...]
Matrix: TypeAlias = tuple[BitRow, ...]

COUNTEREXAMPLE: Matrix = (
    (0, 0, 0, 0),
    (0, 0, 1, 1),
    (0, 1, 0, 1),
    (1, 0, 1, 0),
    (1, 1, 0, 0),
)


def validate_matrix(matrix: Matrix) -> tuple[int, int]:
    if not matrix:
        raise ValueError("matrix must contain at least one row")
    n = len(matrix[0])
    if n == 0:
        raise ValueError("matrix must contain at least one column")
    if any(len(row) != n for row in matrix):
        raise ValueError("rows must have equal length")
    if any(bit not in (0, 1) for row in matrix for bit in row):
        raise ValueError("matrix entries must be 0 or 1")
    return len(matrix), n


def columns(matrix: Matrix) -> tuple[BitRow, ...]:
    m, n = validate_matrix(matrix)
    return tuple(tuple(matrix[r][c] for r in range(m)) for c in range(n))


def delete_column(rows: Sequence[BitRow], k: int) -> Matrix:
    return tuple(row[:k] + row[k + 1 :] for row in rows)


def all_columns_light(matrix: Matrix) -> bool:
    """Return True iff every column has strictly more zeros than ones."""
    m, n = validate_matrix(matrix)
    return all(sum(row[j] for row in matrix) < m / 2 for j in range(n))


def matrix_text(matrix: Matrix) -> str:
    return "{" + ",".join("".join(map(str, row)) for row in matrix) + "}"


def a2(matrix: Matrix, *, trace: list[str] | None = None, depth: int = 0) -> bool:
    """Evaluate Algorithm A2 exactly, optionally appending a readable trace."""
    m, n = validate_matrix(matrix)
    indent = "  " * depth

    def log(message: str) -> None:
        if trace is not None:
            trace.append(f"{indent}{message}")

    log(f"A2{matrix_text(matrix)} [m={m}, n={n}]")

    if m == 1 and n > 1:
        log("return True: one-row base case")
        return True

    if n == 1:
        ones = sum(row[0] for row in matrix)
        result = ones >= m - ones
        log(f"return {result}: one-column base case ({ones} ones, {m - ones} zeros)")
        return result

    for k in range(n):
        zero_rows = tuple(row for row in matrix if row[k] == 0)
        one_rows = tuple(row for row in matrix if row[k] == 1)
        log(
            f"column {k + 1}: zero-fibre={matrix_text(zero_rows)}, "
            f"one-fibre={matrix_text(one_rows)}"
        )

        if len(zero_rows) == 1:
            log(f"return True: column {k + 1} has a unique zero")
            return True

        children: list[Matrix] = []
        for rows in (zero_rows, one_rows):
            if rows:
                children.append(delete_column(rows, k))

        for child in children:
            if all_columns_light(child):
                log(f"return False: all-light child {matrix_text(child)}")
                return False

        for child in children:
            if not a2(child, trace=trace, depth=depth + 1):
                log(f"return False: recursive child {matrix_text(child)} rejected")
                return False

    log("return True: all columns processed")
    return True


def has_heavy_column(matrix: Matrix) -> bool:
    m, _ = validate_matrix(matrix)
    threshold = (m + 1) // 2
    return any(sum(col) >= threshold for col in columns(matrix))


def satisfies_stated_hypotheses(matrix: Matrix) -> bool:
    m, n = validate_matrix(matrix)
    cols = columns(matrix)
    return (
        len(set(matrix)) == m
        and len(set(cols)) == n
        and all(any(col) for col in cols)
    )


def matrix_from_columns(cols: Sequence[BitRow]) -> Matrix:
    if not cols:
        raise ValueError("at least one column is required")
    m = len(cols[0])
    if any(len(col) != m for col in cols):
        raise ValueError("columns must have equal length")
    return tuple(tuple(col[r] for col in cols) for r in range(m))


def nonzero_nonheavy_column_patterns(m: int) -> tuple[BitRow, ...]:
    threshold = (m + 1) // 2
    patterns: list[BitRow] = []
    for weight in range(1, threshold):
        for support in combinations(range(m), weight):
            support_set = set(support)
            patterns.append(tuple(int(i in support_set) for i in range(m)))
    return tuple(patterns)


def exhaustive_no_example(max_rows: int = 4) -> tuple[int, int]:
    """Exhaustively verify row-minimality for all matrices with <= max_rows.

    Because columns are required to be distinct, nonzero, and nonheavy, there
    are finitely many eligible column patterns for each row count.  Every
    ordered selection of distinct eligible columns is checked.
    """
    checked = 0
    candidates = 0
    for m in range(1, max_rows + 1):
        patterns = nonzero_nonheavy_column_patterns(m)
        for n in range(1, len(patterns) + 1):
            for chosen in combinations(patterns, n):
                for ordered in permutations(chosen):
                    checked += 1
                    matrix = matrix_from_columns(ordered)
                    if len(set(matrix)) != m:
                        continue
                    candidates += 1
                    if a2(matrix):
                        raise AssertionError(
                            "found a smaller counterexample: " + matrix_text(matrix)
                        )
    return checked, candidates


def exhaustive_no_five_row_example_with_at_most_three_columns() -> tuple[int, int]:
    """Supplementary finite check: no 5-row example has <= 3 columns."""
    m = 5
    patterns = nonzero_nonheavy_column_patterns(m)
    checked = 0
    candidates = 0
    for n in range(1, 4):
        for chosen in combinations(patterns, n):
            for ordered in permutations(chosen):
                checked += 1
                matrix = matrix_from_columns(ordered)
                if len(set(matrix)) != m:
                    continue
                candidates += 1
                if a2(matrix):
                    raise AssertionError(
                        "found a 5-row counterexample with <=3 columns: "
                        + matrix_text(matrix)
                    )
    return checked, candidates


def verify_schrader_example() -> dict[str, object]:
    """Return the explicit t^i calculation for the four-set example."""
    # F = {empty, {1}, {2}, {3}} on [3].  Each H listed below is the
    # no-root excluded collection from Schrader's definition.
    h2_1 = frozenset({frozenset({1, 2}), frozenset({1, 2, 3})})
    h3_1 = frozenset({frozenset({1, 3})})
    h3_2 = frozenset({frozenset({2, 3})})

    t0 = 2 ** (3 - 1)
    t1 = t0
    t2 = t1 - len(h2_1)
    t3 = t2 - len(h3_1) - len(h3_2)
    f3_size = 1

    excluded = (h2_1, h3_1, h3_2)
    pairwise_disjoint = all(
        excluded[i].isdisjoint(excluded[j])
        for i in range(len(excluded))
        for j in range(i + 1, len(excluded))
    )

    assert (t0, t1, t2, t3) == (4, 4, 2, 0)
    assert pairwise_disjoint
    assert t3 < f3_size

    return {
        "t-values": (t0, t1, t2, t3),
        "|F_3|": f3_size,
        "pairwise_disjoint_H": pairwise_disjoint,
    }


def run(trace_requested: bool, exhaustive_requested: bool) -> None:
    assert satisfies_stated_hypotheses(COUNTEREXAMPLE)
    assert not has_heavy_column(COUNTEREXAMPLE)

    trace: list[str] | None = [] if trace_requested else None
    accepted = a2(COUNTEREXAMPLE, trace=trace)
    assert accepted

    print("A2 counterexample verified")
    print(f"  matrix: {matrix_text(COUNTEREXAMPLE)}")
    print(f"  column sums: {[sum(col) for col in columns(COUNTEREXAMPLE)]}")
    print(f"  A2 result: {accepted}")
    print(f"  has heavy column: {has_heavy_column(COUNTEREXAMPLE)}")

    if trace is not None:
        print("\nA2 execution trace")
        print("\n".join(trace))

    schrader = verify_schrader_example()
    print("\nSchrader example verified")
    print(f"  t-values: {schrader['t-values']}")
    print(f"  |F_3|: {schrader['|F_3|']}")
    print(f"  H-collections pairwise disjoint: {schrader['pairwise_disjoint_H']}")

    if exhaustive_requested:
        checked, candidates = exhaustive_no_example(4)
        print("\nExhaustive row-minimality check passed")
        print(f"  ordered matrices checked: {checked}")
        print(f"  matrices also having distinct rows: {candidates}")

        checked_5, candidates_5 = exhaustive_no_five_row_example_with_at_most_three_columns()
        print("\nSupplementary column-minimality check passed")
        print(f"  ordered 5-row matrices with <=3 columns checked: {checked_5}")
        print(f"  matrices also having distinct rows: {candidates_5}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trace",
        action="store_true",
        help="print the complete recursive A2 execution trace",
    )
    parser.add_argument(
        "--exhaustive",
        action="store_true",
        help="run finite minimality searches in addition to direct checks",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(trace_requested=args.trace, exhaustive_requested=args.exhaustive)
