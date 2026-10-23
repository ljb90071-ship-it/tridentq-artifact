# Result data dictionary

CSV files use UTF-8, comma delimiters, one header row, decimal points, and no missing
values. These are paper-level aggregates, not raw query logs. Latency means and
p95 values are arithmetic means of ten trace-level summaries; p95 values must not
be interpreted as pooled query percentiles. Configuration is in
[experiment.json](../configs/experiment.json). Analysis is in
[analyze_results.py](../scripts/analyze_results.py).

| File | Fields and interpretation |
|---|---|
| [toy.csv](toy.csv) | Table 1; task order, query completion seconds, summed response seconds. |
| [main.csv](main.csv) | Table 3; policy, workload, mean seconds, mean trace-p95 seconds. |
| [mechanism.csv](mechanism.csv) | Table 4; blocked idle-lane time as percent of available GPU lane-seconds; transferred GiB per completed query; allocated GiB-seconds across host and both GPUs per completed query. |
| [factorial.csv](factorial.csv) | Table 5; proposal source, scoring mode, Branch-Mix mean seconds. All rows use the exact runtime allocator. Time-only removes the candidate cap. |
| [memory.csv](memory.csv) | Table 6; per-GPU query pool in GiB, three policies' mean seconds, reduction versus Cover-64 in percent (rounded to one decimal). |
| [overhead.csv](overhead.csv) | Table 7; median and p95 planner milliseconds, deadline-hit percentage of invocations, planner CPU time as percent of one core. Includes generation. |
| [fanout.csv](fanout.csv) | Figure 2; nominal fan-out, response reduction versus Cover-64 percent, blocked attempts with a closure fitting k=3 percent. These are strata, not an additive decomposition of the mixed workload. |
| [oracle.csv](oracle.csv) | Section 7.3; search policy, evaluation ceiling, hit counts and state denominators. All-state hits include 24 no-op-optimal states. Same two-millisecond deadline for both ceilings. |
| [prediction.csv](prediction.csv) | Section 7.5; lognormal log standard deviation and mean response seconds. Allocation bounds remain unchanged. |
| [paired_summary.csv](paired_summary.csv) | Section 7.1; ten paired traces per family, mean/minimum/maximum of Cover-64 minus TridentQ trace means in seconds, number of positive pairs. |
| [accepted_actions.json](accepted_actions.json) | Section 7.2; two separate category partitions of accepted frontier actions; each sums to 100 percent. |
| [budget_sensitivity.json](budget_sensitivity.json) | Section 7.5; Cover-256 deadlines, Branch-Mix mean seconds, CPU cost, and low-rate mean seconds. |

GiB is 2^30 bytes, MiB is 2^20 bytes. Configured transfer rates in GB/s use 10^9
bytes. Policy names ending in `-Q` are the paper's query-engine adaptations;
these tables are not measurements reported by the original referenced systems.
The oracle is an optimum over the resolved local neighborhood of at most three
mutable tasks, not the full online workload. Its normalized tie tolerance is
1e-6 seconds, using a zero added planning-delay gate for matched frozen snapshots.

The [evaluation protocol](../docs/evaluation-protocol.md) defines the common arrival cohort, drain interval, oracle collector and accepted-plan categories. [paired_trace_means.csv](paired_trace_means.csv) contains the thirty paired trace-mean values behind the descriptive summaries, not per-query records. [search_diagnostics.json](search_diagnostics.json) records the untargeted-group comparison, completed-evaluation counts, timeout/fallback fractions and epoch-state distributions. Planning fractions are percentages of epochs; closure fit is a percentage of blocked attempts.
