# TridentQ: Scheduling the Last Consumer in Heterogeneous Query Execution

This supplement provides an executable reference model of release-causing actions,
the legal-prefix sampling diagnostic, and structured result tables for the paper.
The central mechanism is to finish **all remaining readers** of a resident copy,
then use the released capacity for another query. Candidate evaluation includes
the complete continuation so that displaced work and query tails affect acceptance.

## Start here

1. Read the [paper map](paper-map.md) for section, algorithm, figure, and table links.
2. Run the [three-task example](examples/three_tasks.json). It computes the
   paper's response objective from durations, memory bounds, and reader sets.
3. Inspect [the core implementation](src/reference.py),
   [mechanism details](docs/reference-model.md), and [tests](tests/test_reference.py).
4. Browse [result definitions](data/README.md) and the
   [experiment configuration](configs/experiment.json).

## Run

Use Python 3.10 or newer. The commands below use only the standard library;
run them from this directory, after extracting the ZIP if necessary.

```sh
python -B scripts/run_example.py examples/three_tasks.json
python -B scripts/run_example.py examples/two_readers.json
python -B -m unittest discover -s tests -v
python -B scripts/analyze_results.py
```

The first command reports an incumbent objective of 20 seconds and a best
objective of 18 seconds, with order `r, b, a`. The two-reader example discovers
a three-task release action and shows that `X` survives the first reader.
The tests vary durations, output allocation, reader count, dependency closure,
protected prefixes, reservation state, DMA acknowledgement, and proposal seeds.
The last command checks archived aggregates and calculates percentage reductions;
it is results analysis, not a workload execution command.

## Implementation boundary

The reference executor uses one serialized GPU lane and resident input copies.
It implements exact copy-group enumeration for small examples, pending-ancestor
closure, bounded action size, atomic copy accounting, full serial continuation
scoring, and fixed protected prefixes. The sampler diagnostic uses three
supported endpoint indices with index zero as the local fastest endpoint.

The paper's heterogeneous engine, source/helper resolver, beam search, shared
H-ranked pool, wall-clock deadline controller, SQL kernels, and physical DMA are
described in the paper and [implementation notes](docs/reference-model.md).
They are outside the executable reference subset. Experiment configuration and
result tables provide the corresponding settings and reported aggregates;
the supplied commands do not rerun those engine experiments.

All paths are relative to this repository. No GPU, database installation,
network download, or external dataset is needed for these commands.

The [evaluation protocol](docs/evaluation-protocol.md) defines cohort selection, drain, baseline adaptations, the oracle collector, accepted-plan categories and duration perturbations. Paired trace means and supplementary search statistics accompany the aggregate tables.

For the full scoring protocol, read [continuation-protocol.md](docs/continuation-protocol.md). Run `python -B scripts/check_resolved_events.py` for the resolved two-GPU event example (objective 17.2 seconds). This computes a supplied event graph with transfer, capacity and suffix-order constraints; it is separate from candidate generation.
