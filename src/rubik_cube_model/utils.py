'''Permutation utilities for cube analysis.'''

from __future__ import annotations

from collections.abc import Hashable, Sequence

def permutation_cycles[T: Hashable](
  start: Sequence[T],
  end: Sequence[T],
) -> list[list[T]]:
  '''Return the cycle decomposition of the permutation from start to end.

  Both sequences must contain the same set of distinct elements.
  The returned cycles are disjoint and cover all elements that move.
  Fixed points are omitted.
  '''
  index: dict[T, int] = {v: i for i, v in enumerate(end)}
  visited: set[int] = set()
  cycles: list[list[T]] = []
  for i, v in enumerate(start):
    if i in visited:
      continue
    j: int = index[v]
    if i == j:
      visited.add(i)
      continue
    cycle: list[T] = []
    k: int = i
    while k not in visited:
      visited.add(k)
      cycle.append(start[k])
      k = index[start[k]]
    cycles.append(cycle)
  return cycles

def even_permutation[T: Hashable](
  start: Sequence[T],
  end: Sequence[T],
) -> bool:
  '''Return True if the permutation from start to end is even.

  A permutation is even if the number of cycles of even length is even.
  '''
  cycles: list[list[T]] = permutation_cycles(start, end)
  even_count: int = sum(
    1 for c in cycles if len(c) % 2 == 0
  )
  return even_count % 2 == 0
