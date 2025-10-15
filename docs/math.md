---
title: "Math"
---

# The Problem

The NBA and NHL schedules are structured so that every team plays every other team on the road. As a fan who enjoys away days and road trips, I wondered: **How can I watch my Canucks play 31 road games against 31 opponents while driving the least amount?**

This is both a graph and an optimization problem. Each game is a node, and the cost to travel between games varies. This is essentially the classic:

# Travelling Salesman Problem (TSP)

The TSP asks: *Given a list of cities and the costs to travel between them, what is the shortest route that visits each city exactly once and returns to the starting city?*

For large graphs, TSP is usually solved with approximation algorithms, many of which have strong worst-case guarantees. However, our problem size (41 games/cities for NBA/NHL and 81 for MLB) allows for exact algorithms. The [Held-Karp algorithm](https://en.wikipedia.org/wiki/Held%E2%80%93Karp_algorithm) is the most efficient exact method, with $O(2^n n^2)$ time and $O(n2^n)$ space complexity. In practice, [branch-and-bound algorithms](https://en.wikipedia.org/wiki/Travelling_salesman_problem#Exact_algorithms) are often faster, despite their factorial complexity.

However, we must also ensure that we see every opponent once and only once, which leads us to consider linear programming.

## Miller-Tucker-Zemlin (MTZ) Formulation

The solver implemented for this website is a heavily modified form of the [MTZ formulation](https://en.wikipedia.org/wiki/Travelling_salesman_problem#Miller%E2%80%93Tucker%E2%80%93Zemlin_formulation), so it's worth understanding.

- **Label the cities** from 1 to $n$, and let $c_{ij}$ be the cost of traveling from city $i$ to city $j$.
- **Define binary variables** $x_{ij}$: $x_{ij} = 1$ if the tour goes directly from $i$ to $j$, otherwise $0$.

The optimization criterion:

$$\min \sum_{i=1}^n \sum_{j=1, j \neq i}^n x_{ij}c_{ij}$$

**Constraints:**
- Each city has exactly one incoming and one outgoing edge:

  $$
  \sum_{i = 1, i \neq j}^n x_{ij} = 1 \quad \forall 1 \leq j \leq n
  $$
  $$
  \sum_{j = 1, j \neq i}^n x_{ij} = 1 \quad \forall 1 \leq i \leq n
  $$

These alone allow for subtours (e.g., two disjoint cycles). The MTZ formulation prevents this by introducing $n$ variables $u_1, \ldots, u_n$ representing the order of visits, with $1 \leq u_i \leq n$.

Assume city 1 is the start/end, with $u_1 = 1$. The subtour elimination constraints:

$$
u_i - u_j + 1 \leq (n-1)(1-x_{ij}) \quad \forall 2 \leq i \neq j \leq n
$$

- If $x_{ij} = 0$: $u_i - u_j \leq n-2$ (just restates the range).
- If $x_{ij} = 1$: $u_i - u_j \leq -1$ (forces order to increase).

This eliminates subtours, using $n^2$ variables and about $n^2$ constraints.

# Our Formulation

In our case:
- **Cities become games.**
- **Costs** ($c_{ij}$) can be any criterion (distance, duration, time between games, etc.).
- **Games are labeled** $1$ to $n$ in chronological order.
- The cost matrix $\mathbf{C}$ is "upper triangular" (can't travel to a past game): zeros on the diagonal, infinite below.

In practice, we do **not** create variables $x_{ij}$ where travel from $i$ to $j$ is infeasible.

For MLB, series in the same location mean traveling between games in a series is free. So, we tweak the objective to also minimize the number of games attended:

$$
\min \sum_{i=1}^n \sum_{j=i+1}^n x_{ij}(c_{ij} + 1)
$$

**Degree constraints:**
- We can't (and don't want to) return to the initial game. We introduce a dummy game 0, reachable to/from every other game at zero cost.
- We may not attend all games, so in/out degrees can be zero as long as they're equal.

Modified $3n$ degree constraints:

$$
\sum_{i = 0, i < j}^n x_{ij} \leq 1 \quad \forall 0 \leq j \leq n
$$

$$
x_{i0} + \sum_{j = 1, j > i}^n x_{ij} \leq 1 \quad \forall 0 \leq i \leq n
$$

$$
\sum_{i = 0, i < j}^n x_{ij} - \sum_{k = 1, k > j}^n x_{jk} - x_{j0} = 0 \quad \forall 0 \leq j \leq n
$$

**Matchup constraint:**
- Let $\mathbf{M}$ be the matchup matrix, where $M_{ij} = 1$ if team $j$ participates in event $i$.
- For $n_t$ teams to see at least once each:

$$
\sum_{i=0}^n \sum_{j = i+1}^n x_{ij}M_{jk} \geq 1 \quad \forall 1 \leq k \leq n_t
$$

A key insight: the structure of our problem already precludes subtours! Ignoring the dummy event, the graph is directed and acyclic, so any cycle must pass through the dummy event.

**Dropping the subtour elimination constraint** reduces the problem to about $\frac{n^2}{2}$ variables and $3n + n_t$ constraints—much more tractable than the MTZ formulation.

- With the subtour constraint: open-source solvers take ~10 minutes, commercial solvers ~1 minute.
- Without it: both solve in under a second.

# Notes

This website presents just one use case for the linear program. The matchup matrix is flexible and can encode other constraints, such as visiting a set of arenas. Adapting the formulation for other goals is straightforward.
