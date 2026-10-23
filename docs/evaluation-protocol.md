# Evaluation protocol

## Common query cohort

For each family and trace, the measurement cohort is the set of query IDs with
arrival times in [0, 1200) seconds. IDs and parameters are shared by policies.
Warm-up arrivals in [-120, 0) are not measured queries, but their residual execution
can interfere with the cohort. Stop arrivals at 1200; continue admitting externally
queued cohort queries and drain them all. Each cohort ID contributes one response
time from arrival to final output, including admission wait. No query is removed
because admission or completion falls outside the arrival window. Ten trace means
and ten trace p95 values are averaged separately, with equal trace weight.

Mechanism integration starts at time zero and ends at the last cohort completion.
It includes active warm-up residual work. The blocked-time denominator is two GPU
lanes times that interval's duration. DMA volume and allocated-byte-time cover the
same interval and divide by the number of completed cohort queries. They describe
resource use while serving the cohort, not individual query ownership of every byte.
No raw query logs or reconstructed query counts are included in the aggregate files.

## Policy adaptations

All policies use the same memory bounds, age prefix, supported devices, duration
models, source paths and runtime guard. Query DAGs and materializations are fixed.
These rules define the `-Q` adaptations in the paper, not the original systems.

| Policy | Priority/selection | Placement and ties |
|---|---|---|
| Transfer-EFT | Ready fragments by decreasing remaining-path rank | Earliest feasible predicted finish; transfer bytes, device ID, slot ID break ties. |
| HEFTM-Q | Input-communication-aware bottom-level rank selected on tuning traces | Same placement; evict only eligible unpinned copies with protected backing; earliest next use retained first, copy ID breaks ties. |
| Locality-Q | Seed with highest remaining-path ready task; greedily add ready tasks by shared-input bytes with group, then remaining-path rank | Endpoint with largest already-resident input bytes, then feasible finish and endpoint ID. Recompute after each dispatch. |
| DARTS-Q | Per endpoint, consider compatible data choices in increasing transfer-time / enabled-work-time order; enabled work sums predicted durations on that endpoint | Compare the next enabled task across endpoints by feasible finish, then transfer bytes and stable IDs. Planned/pulled inputs are retained before other evictable copies. |
| Release-Greedy | Net input bytes released by the next task / minimum service time; zero if any other obligation survives | Common completion-time replay decides acceptance. |

HEFTM-Q tuning uses three separate traces per family, with the evaluation workload
rates and a disjoint seed namespace `20261010:tuning`. Compare bottom-level,
input-communication-aware bottom-level, and memory-oriented task orders by the
equal-family mean of response time normalized to Transfer-EFT on each tuning trace.
The selected order is input-communication-aware bottom-level. Ties prefer that
order, then bottom-level, then memory-oriented. Tuning inputs are separate from the
ten evaluation traces and the oracle collector traces. The artifact records this
selection protocol, not tuning run logs.

The DARTS-Q enabled-work denominator uses device-specific predictions, floored at
1e-6 seconds. This accounts for heterogeneous speeds in the query-engine adaptation.
Data selection ranks opportunities; it does not itself determine the final endpoint
or remove live pins. Eviction and transfer staging remain subject to the common
capacity checks. A data choice with no supported enabled work is skipped.

## Search comparisons

Cover-64 and TridentQ have the same resolved action neighborhood and source resolver.
They use one global 32-entry H-ranked pool, 32 initial raw proposal slots and four
refill slots before each subsequent evaluation. Cover uses generic slots only;
TridentQ alternates generic/frontier slots and lends exhausted frontier slots back
to generic. Rejected or duplicate proposals consume slots and elapsed time.
The cap of 64 counts completed candidate evaluations, including infeasible results.
The two-millisecond limit charges indexing, generation, projection, resolution,
replay and final validation. Runtime dispatch validation remains mandatory.

Oracle snapshots are collected by Transfer-EFT on separate traces, using the common
allocator, repair and age rule. The first eligible blocked event in each 60-second
window is retained until each family has 80 states. Eligibility is fixed before
search: at most 12 mutable tasks and a complete feasible incumbent. Both searches
start from the same snapshot and incumbent; no search score selects a snapshot.
An exhaustive local reference covers resolved tuples up to k=3 plus no-op. The
24 no-op-optimal states count in 240 all states but not the 216 improvable states.
All frozen scores use zero added planning delay and normalized tie tolerance 1e-6 s.
The exported hit counts are aggregates; full collector snapshots are not included.

## Accepted-plan classifications

The denominator is 10,000 epochs across the ten Branch-Mix traces in which the final
selected continuation originates from a frontier proposal. Rejected candidates
and multiple improvements within the same epoch do not add observations. These
are **predicted plans**; only the earliest action is committed and later replanning
may replace the suffix. Device classes use CPU-move precedence: any CPU move,
otherwise any inter-GPU move, otherwise unchanged. The one-copy/multiple-or-canceled
classification concerns predicted allocation changes of the selected plan. Executed
blocked time and retained area are separate metrics in `mechanism.csv`.

## Duration perturbation

Let z be a standard normal draw keyed by trace, kernel and device. Multiply a
prediction by exp(-sigma^2/2 + sigma*z), giving a mean-one factor. Share z across
policies and noise levels and hold it fixed within the trace. The exact key and
seed encoding are in `configs/experiment.json`, implemented in `src/noise.py`.
Allocation bounds do not change with duration noise.
