# Paper-to-material map

The following map uses the final paper's numbering. Source entry points describe
the implemented subset; archived tables support static inspection and analysis.

| Paper item | Material | Coverage |
|---|---|---|
| Section 2, Table 1, exchange equation | [three_tasks.json](examples/three_tasks.json), [reference.py](src/reference.py), [tests](tests/test_reference.py), [toy.csv](data/toy.csv) | Executable three-order objective; 64 duration assignments and peak-memory separation cases. |
| Figure 1 | [two_readers.json](examples/two_readers.json), [model notes](docs/reference-model.md) | Joint-release mechanism; intentionally different other-work granularity, not a pixel recreation of the figure. |
| Section 3, Table 2 notation, release/capacity/objective equations | [Ledger and replay](src/reference.py), [model interface](docs/reference-model.md) | Copy obligations, reservation accounting, query tails and weighted completion objective; serialized reference model. |
| Section 4.1, release frontier | [frontier_prefixes](src/reference.py), [two-reader example](examples/two_readers.json) | Copy-group coverage, reader/ancestor closure, beneficiary, mutable cap; exact small-state enumeration. |
| Section 4.2–4.3, source resolution and H | [integration contract](docs/reference-model.md) | Technical interface description; full heterogeneous resolver and H projection are not executable components here. |
| Section 4.4 and Section 7.3 generator diagnostic | [sampler.py](src/sampler.py), [protocol](docs/sampling-protocol.txt), [tests](tests/test_reference.py) | Cartesian versus diversified legal prefixes; reproduces 2/71 and 2/94 three-task-set counts in 284 proposals. |
| Algorithm 1, Section 4.5 | [search and replay](src/reference.py), [integration contract](docs/reference-model.md) | Incumbent retention, fresh candidate replay, strict objective acceptance; online pool/deadline/dispatch loop described separately. |
| Section 5, release and safety propositions | [Ledger](src/reference.py), [tests](tests/test_reference.py) | Last-reader, DMA pin, remap, capacity, output allocation and protected-prefix cases. Age-prefix construction and physical runtime are integration contracts. |
| Section 6 | [experiment.json](configs/experiment.json), [data dictionary](data/README.md) | Hardware, workloads, aggregation, memory bounds and search settings. |
| Table 3, Section 7.1 | [main.csv](data/main.csv), [paired_summary.csv](data/paired_summary.csv) | All table rows and paired-summary statements. |
| Table 4, Section 7.2 | [mechanism.csv](data/mechanism.csv), [accepted_actions.json](data/accepted_actions.json) | All table rows and accepted-action partitions. |
| Table 5, Section 7.3 | [factorial.csv](data/factorial.csv), [oracle.csv](data/oracle.csv) | Scoring ablation and frozen-search hit counts; oracle snapshots are outside this repository. |
| Table 6, Figure 2, Section 7.4 | [memory.csv](data/memory.csv), [fanout.csv](data/fanout.csv) | Full aggregate series and percentage checks. |
| Table 7, Section 7.5 | [overhead.csv](data/overhead.csv), [prediction.csv](data/prediction.csv), [budget_sensitivity.json](data/budget_sensitivity.json) | Planner cost, prediction perturbation, budget and low-rate comparisons. |
| Section 7.6 | [tests](tests/test_reference.py) | Multiple readers and output-erases-release example; mechanism checks rather than SQL execution. |

Run [analyze_results.py](scripts/analyze_results.py) to validate aggregates and
derive comparisons. Run [run_example.py](scripts/run_example.py) to execute the
reference scheduler on editable inputs. The two paths have separate purposes.

Measurement definitions are consolidated in [evaluation-protocol.md](docs/evaluation-protocol.md). The paired evidence for Section 7.1 is in [paired_trace_means.csv](data/paired_trace_means.csv); further Section 6/7 state and budget aggregates are in [search_diagnostics.json](data/search_diagnostics.json). [noise.py](src/noise.py) implements the keyed mean-one duration perturbation.

The common continuation/repair rules and the illustrative heterogeneous state are in [continuation-protocol.md](docs/continuation-protocol.md). [check_resolved_events.py](scripts/check_resolved_events.py) propagates its fixed event graph and checks capacity; it does not implement source discovery or online search. Full generic traversal details moved out of the paper are retained in [generic-traversal.txt](docs/generic-traversal.txt).
