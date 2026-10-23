# Reference model and interface

## Input and objective

Each example JSON specifies `capacity_GiB`, initially resident `copies`, `tasks`,
`queries`, an `incumbent` task order, a `beneficiary`, and a mutable closure cap `k`.
Task IDs and copy IDs are unique. A task has a positive `duration_s`, nonnegative
`scratch_GiB`, optional `parents`, and optional `outputs` in the same format as
initial copies. Each copy declares its `size_GiB` allocation bound and all remaining
`readers`. An output reader must execute after its producer; declare that producer
as a parent to make the dependency visible to the frontier closure.

Query fields are `arrival_s` (default 0), `weight` (default 1), and `fixed_tail_s`
(default 0). The tail is the absolute completion time of independent already
scheduled work, not a duration added after the modeled tasks. Query completion is
the maximum of this tail and all of its modeled task finishes. The objective is
`sum_q weight_q * (completion_q - arrival_q)` over **every query**.
`planning_gate_s` sets the common start time (default 0). These examples assume
all tasks are admitted and available at that gate except for declared dependencies.

## Copy accounting

The ledger charges allocated copies plus outstanding reservations. Reserving an
output does not create a second charge when it materializes. Scratch and all output
bounds are reserved before dispatch, while inputs remain allocated. A demand
changes to a kernel or DMA pin; only acknowledgement discharges that pin. Collection
removes a copy only after its last obligation disappears. A remap adds the demand
to an existing destination before deleting it from the source. The caller supplies
the destination copy after transfer completion; remap does not perform a transfer.
Prediction never calls acknowledgement on the runtime's behalf.

Before the first reservation, replay collects initially resident copies with no
remaining readers. Frontier deficit and group construction use that same live-copy
state. The initial allocated snapshot itself must fit the declared capacity.

`replay` starts from a fresh ledger for each candidate. It returns event start/end
times, released copy IDs, post-event allocated memory, peak charged memory, query
completions, and objective. A capacity or precedence failure raises `Infeasible`.
There are no concurrent threads in this executable model; atomicity is represented
by indivisible ledger operations.

## Frontier construction and retained suffix

For an initially blocked beneficiary, enumerate resident-copy groups whose gross
size covers its initial deficit. Include every remaining reader, the beneficiary,
and their pending ancestors. Reject groups requiring the beneficiary itself as a
reader before its own launch. Remove fixed protected-prefix tasks from the mutable
closure and enforce `k`. Enumerate topological permutations in which the selected
readers precede the beneficiary. For each candidate, retain the incumbent order of
all unselected tasks after the candidate prefix. Replay accounts for new outputs
and scratch; gross release is only a proposal filter. A candidate replaces the
incumbent only on a strict reduction of the full objective. Equal objectives retain
the earlier incumbent. The optional `protected_prefix` is enforced before any
candidate; the model accepts this prefix as input rather than implementing the
paper's age-trigger construction.

This small-state enumerator uses all copy subsets and permutations. Its exponential
cost is intentional for inspectable examples; it does not implement the paper's
16-state beam or the two-millisecond online budget. It targets initial resident
copies, not all future incumbent blocking events. The two-reader input illustrates
joint release with a single seven-second other-work task; Figure 1 additionally
splits other work around the illustrated action. Their precise timelines differ.

## Legal-prefix diagnostic

`src/sampler.py` preserves the generator-only experiment in Section 7.3. `Diverse`
accepts tasks already in merged-rank order and a list of mutable pending-parent
sets. Input must be a nonempty acyclic DAG; every parent is in the task index range.
For each length, shuffled root anchors cycle through four rank bands using
`0,1,0,2,0,3`. Later eligible tasks use band weights `3:1:1:1`. Each task has three
supported devices; index zero is the fastest, selected with probability one half
before the alternative uniform draw. Root cycles are independent per prefix length.
`old` enumerates the Cartesian diagnostic in index-sum order. Both return alternating
task/device index tuples. The fixed diagnostic uses seed 20261011; production-style
epoch seeds can be obtained with `epoch_seed(trace_id, epoch_id)`, following the
[sampling convention](sampling-protocol.txt).

The caller serves lengths 1 through `min(3, n)` round-robin. Task indices in this diagnostic
are also stable identifiers. RRF rank construction, supported-device filtering,
source resolution, H ranking, pool eviction, replay limits, and timing are not
performed by this module. The coverage test therefore compares proposal diversity,
not end-to-end scheduler performance.

## Heterogeneous integration contract

The full algorithm resolves sources from existing copies, running/protected
producer outputs, and earlier tuple outputs; no read precedes production.
CPU/GPU compute lanes and both host-staged GPU-transfer legs contribute events.
Output, scratch, and staging reservations are disjoint from materialized copies.
The cheap H projection ranks candidates using slack-adjusted query gains and
displacement penalties. Acceptance instead uses complete continuation replay.
All candidates start from the same epoch snapshot and common planning gate.
The 32-entry pool receives 32 initial proposal slots and four refill slots before
subsequent evaluations; frontier and generic slots alternate, lending exhausted
frontier slots to generic generation. Invalid and duplicate proposals still incur
generation cost. A timeout retains a usable old continuation, executes only its
guarded next action, or invokes bounded CPU/spill fallback if no usable suffix exists.
These contracts explain how the executable primitives connect to Algorithm 1.

The exact common continuation design is specified in [continuation-protocol.md](continuation-protocol.md), including retained source choices, acquisition order, initialization and repair. These are the full-model contracts; the serial executable above retains its stated scope.
