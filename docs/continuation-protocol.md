# Common continuation and repair

This protocol fixes the common scoring substrate used by generic and frontier
proposals. A continuation stores devices, source-copy identities, helper graphs,
and resource-acquisition order, as well as predicted times. Candidate search
changes a short prefix against that fixed base; repair handles invalid runtime
state before search. The serial reference executor implements a smaller subset.

## Initialization

For each fragment v, compute rank(v) = pmin(v) + max over successors u of
[cmin(v,u) + rank(u)]. Here pmin is minimum supported compute duration and cmin is
minimum compatible edge transfer/conversion duration; an empty maximum is zero.
Freeze ranks at initialization/repair. At an event, scan dependency-ready tasks
by decreasing rank, then arrival, query ID and fragment ID. The protected age prefix
takes precedence. Consider supported endpoints using the paper's same deterministic
source resolver and logical-input order. A launch bundle reserves scratch, outputs,
destination and staging bounds before its first helper starts; existing allocations
are not charged again. Eligibility requires the first operation to be able to start
now and the reservations to preserve fixed-boundary feasibility.

Choose the first ready fragment with an eligible placement. Minimize predicted
finish, then helper bytes, endpoint ID, source/path identifiers and CPU-slot ID.
Install its bundle, updating resource calendars and obligations; repeat at the same
time. If no bundle fits, advance to the next named completion. If none can enable
progress, invoke the bounded CPU/spill contract: oldest pending query, then its
highest-ranked ready task; establish required host backing in logical-input order.
The contract supplies bounded chunk operations and their stable order. A failed
attempt to obtain a complete continuation does not produce a score.

## Resolve a candidate and retain its suffix

Take the base continuation's first-dispatch order, using IDs for simultaneous ties.
Build the candidate order as protected prefix, tuple members, then every remaining
task in its old relative order. Remove selected tasks' old pending helpers and add
their newly resolved helpers. Unselected tasks keep their valid device, source-copy
and helper choices. Update protections, including any unselected users of moved
outputs. Reject an invalid unchanged source contract; do not silently find a better
replacement source during candidate scoring. Running and protected work stays fixed.

Each operation's priority is (task position, local helper order, operation ID).
Local helpers follow dependency order with logical-input ID and path-leg index as
ties. Apply this order to compute/transfer lanes and each endpoint's acquisition
queue. A multi-endpoint acquisition is atomic and must head every queue it needs.
Queue position is released when an operation starts; its allocations and pins remain
charged until their actual modeled discharge. Thus independent lanes can overlap.
A waiting acquisition cannot be bypassed on the same endpoint. If the resulting
ordered graph has no enabling event, reject the candidate rather than reinitializing
its suffix. This restriction is common to both proposal sources and the local oracle.

At equal timestamps, complete operations, materialize reserved outputs, discharge
pins, perform valid protected rebindings and collect unprotected copies before new
acquisitions. Use endpoint and allocation/operation IDs within an event class.
Continue zero-duration administrative events to closure. Score final delivered
outputs of **all** admitted queries by sum_q weight_q*(completion_q-arrival_q).
Accept only a strict improvement; an exact tie keeps the incumbent. The oracle's
1e-6-second normalized hit tolerance is separate from online acceptance.

## Runtime repair and timeout

Remove acknowledged actions, append newly admitted work in the common initial
order, register demands, and revalidate. A timeout alone preserves the old order.
An invalid source, dependency, allocation contract or age prefix triggers repair:
keep actual running work, real reservations and pins; construct the mandatory age
prefix; discard speculative schedules for the other mutable work and rebuild it
with the common initializer. Never discard a submitted DMA as speculative work.

At final validation, both incumbent and alternative use the same elapsed-time
snapshot and dispatch gate. Only a completed feasible comparison can replace the
incumbent. Commit the earliest guarded operation, which may be DMA, a kernel or a
named wait, and retain the rest. No incomplete score is treated as an improvement.
Initialization, repair and helper resolution consume the same time budget but do
not count toward the candidate replay cap. The event-propagation complexity in the
paper applies to an already resolved graph, with helper and resource-order edges
included; it does not bound graph construction or repair.

## Frozen heterogeneous illustration

The [resolved event example](../examples/heterogeneous_events.json) is an illustrative
state, separate from the oracle dataset. GPU0 and GPU1 each have 10 GiB. GPU0 holds
X=6 GiB for r; a takes 4 seconds and 2 GiB scratch, b takes 1 second and 6 GiB scratch,
and r takes 1 second without extra scratch. A CPU branch of r's query is already
running until time 10. All arrivals are zero. The incumbent a,r,b gives completions
(4,6,10) and F=20. The migrated tuple (r,GPU1;b,GPU0) uses a host-staged route with
two illustrative 0.3-second legs. They include calibrated overhead; they do not
replace the experiment's bandwidth settings.

Reserve host and GPU1 copies before D2H. At 0.3 the host copy materializes, but X0
retains r's demand. At 0.6 H2D completes, X1 is protected, r rebinds, and X0 and host
staging are released. Then r on GPU1 and b on GPU0 overlap over [0.6,1.6]. Retained
a follows b over [1.6,5.6]. Completions (5.6,1.6,10) give F=17.2, while CPU work
masks r's own advance. GPU0, GPU1 and host each peak at 6 GiB. The first committed
operation is D2H, not the whole tuple.

Run `python -B scripts/check_resolved_events.py` to propagate the supplied resolved
event DAG, derive completions and verify capacity events. Its edges include resource
order and the capacity release enabling b; they are not new query dependencies.
This finite example scorer does not choose sources, discover those edges, implement
the online pool, or reproduce the database performance results.
