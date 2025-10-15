---
title: "Math"
---

# The Problem
The NBA and NHL schedules are structured so that every team plays every other team on the road. I enjoy away days and love road trips, which got me thinking: how can I watch my Canucks play 31 road games against 31 opponents while driving the least amount?

This is simultaneously a graph and an optimization problem. There are a set of games to be visited and the cost to travel between games varies, which sounds an awful lot like the:

# Travelling Salesman Problem (TSP)
TSP asks: *given a list of cities and the costs to travel between them, what is the route that passes through each city exactly once, finally returning to the original city, with the lowest total cost?*

TSP on large graphs is usually solved with approximation algorithms, many of which have very good worst case bounds. Our problem size (41 games/cities for NBA/NHL and 81 for MLB) permits using exact algorithms. Among these, the one with the best complexity is the [Held-Karp algorithm](https://en.wikipedia.org/wiki/Held%E2%80%93Karp_algorithm) taking $O(2^nn^2)$ time and $O(n2^n)$ space. In practice though, [branch-and-bound algorithms](https://en.wikipedia.org/wiki/Travelling_salesman_problem#Exact_algorithms) are usually faster despite the factorial complexity.

But we must also contend with the constraint of seeing every opponent once and exactly once, which naturally leads us to consider linear programming.

## Miller-Tucker-Zemlin (MTZ) Formulation
The solver implemented for this website is a heavily modified form of the [MTZ formulation](https://en.wikipedia.org/wiki/Travelling_salesman_problem#Miller%E2%80%93Tucker%E2%80%93Zemlin_formulation), so it is worth spending some time understanding it.

Label the cities from 1 to $n$, and let $c_{ij}$ be the cost of traveling from city $i$ to city $j$.

Now define the $n^2 - n$ binary variables $x_{ij}$ that are 1 if the tour goes directly from city $i$ to city $j$ and 0 otherwise. The optimization criterion is then:

$$\min \sum_{i=1}^n \sum_{j=1, j \neq i}^n x_{ij}c_{ij}$$

To ensure that the tour is well-formed, each city should have exactly one inedge and one outedge, which is expressed by the $2n$ constraints:

$$\sum_{i = 1, i \neq j}^n x_{ij} = 1 \quad \forall 1 \leq j \leq n$$

$$\sum_{j = 1, j \neq i}^n x_{ij} = 1 \quad \forall 1 \leq i \leq n$$

These constraints alone leave the possibility for subtours. For example, if there are six cities named A to F, then the disjoint tours A-B-C-A and D-E-F-D do not violate any constraint.

The MTZ formulation addresses this issue by creating $n$ variables $u_1$ through $u_n$ that capture the order in which the cities are visited. As implied by the definition, $1 \leq u_i \leq n \quad \forall 1 \leq i \leq n$.

Without loss of generality, consider city 1 as the start and end city and define $u_1 = 1$. Then we can use the following $(n-1)(n-2)$ constraints:

$$ u_i - u_j + 1 \leq (n-1)(1-x_{ij}) \quad \forall 2 \leq i \neq j \leq n$$

When $x_{ij} = 0$, the constraint simplifies to $u_i - u_j \leq n - 2$, which simply restates the range of the $u$ variables.

When $x_{ij} = 1$, the constraint becomes $u_i - u_j \leq -1$. That is, the ordering variables must increase by 1 at every step. The only place where this constraint can be violated is at the start/end city (city 1). This achieves the desired effect of eliminating subtours.

This formulation uses $n^2$ variables and roughly $n^2$ constraints.

# Our Formulation
For our formulation, the cities become the games, and the costs for traveling between games can be any criterion we seek to optimize (driving distance, driving duration, time between games, etc.). If we label the games from $1$ to $n$ in chronological order and represent the cost $c_{ij}$ as a matrix $\mathbf{C}$, then this matrix would be "upper triangular" since you cannot travel to a game in the past. $\mathbf{C}$ thus should be considered to have zeros on the diagonal and infinite values below the diagonal.

In practice, this is modeled by not creating variables $x_{ij}$ where it is infeasible to travel from event $i$ to event $j$, even if event $j$ takes place after event $i$.

MLB schedules are structured around series in the same location. When optimizing, for example, driving distance, traveling between games in the same series would technically be free. So the optimization criterion is tweaked slightly to minimize the number of games attended as well.

$$\min \sum_{i=1}^n \sum_{j=i+1}^n x_{ij}(c_{ij} + 1)$$

There are two issues with using the indegree and outdegree constraints of the MTZ formulation. The first is that we do not care about, and in fact cannot, return to the initial game. This is solved by having a dummy game zero that is reachable to and from every other game at zero cost.

The second being that we do not intend to attend all games, so the indegrees and outdegrees may be zero as long as they are equal.

The modified $3n$ degree constraints:

$$\sum_{i = 0, i < j}^n x_{ij} \leq 1 \quad \forall 0 \leq j \leq n$$

$$x_{i0} + \sum_{j = 1, j > i}^n x_{ij} \leq 1 \quad \forall 0 \leq i \leq n$$

$$\sum_{i = 0, i < j}^n x_{ij} - \sum_{k = 1, k > j}^n x_{jk} - x_{j0} = 0 \quad \forall 0 \leq j \leq n$$

Finally, define a matchup matrix $\mathbf{M}$ where $M_{ij} = 1$ if and only if team $j$ participates in event $i$. If there are $n_t$ teams that we want to see play at least once each, the constraint can be represented as:

$$\sum_{i=0}^n \sum_{j = i+1}^n x_{ij}M_{jk} \geq 1 \quad \forall 1 \leq k \leq n_t$$

A major eureka moment late in this project was realizing that the structure of our problem already precludes the possibility of subtours! Ignoring the dummy event, the graph is oriented (directed and containing no parallel edges) and acyclic, so any cycle on the graph must pass through the dummy event.

Dropping the subtour elimination constraint means we only need roughly $\frac{n^2}{2}$ variables and $3n + n_t$ constraints, the latter of which is in a better complexity class compared to the MTZ formulation.

This is what finally made the problem computationally feasible. Running on a single 12th gen i9 desktop core, solving the linear program with the subtour elimination constraint requires on the order of $10^1$ minutes on open-source solvers and on the order of $10^0$ minutes on commercial solvers. Without the subtour elimination constraint, both open-source and commercial solvers are capable of solving the program in the order of $10^{-1}$ minutes.

# Notes
This website presents only one particular use case for the linear program formulation. The matchup matrix is a very flexible construct that can be easily adapted to encode other aspects of the games. For example, it would be trivial to instead solve for the optimal trips to visit a set of arenas.
