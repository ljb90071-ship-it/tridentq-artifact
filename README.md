# TridentQ: Scheduling the Last Consumer in Heterogeneous Query Execution

This repository implements release-causing action evaluation and legal-prefix
sampling, with scheduling examples, checks and paper result tables. The central
mechanism finishes **all remaining readers** of a resident copy and uses the
released capacity for another query. Complete-continuation scoring accounts for
displaced work and query tails.

## Navigate

- [Paper map](paper-map.md): sections, algorithms, figures and tables.
- [Three-task input](examples/three_tasks.json): durations, memory bounds and reader sets.
- [Implementation](src/reference.py), [mechanism guide](docs/reference-model.md), and [tests](tests/test_reference.py).
- [Result definitions](data/README.md) and [experiment configuration](configs/experiment.json).
- [Evaluation protocol](docs/evaluation-protocol.md): cohort selection, drain, baseline adaptations, oracle collection, accepted-plan categories and duration perturbations.
- [Continuation scoring protocol](docs/continuation-protocol.md): resolved transfer, capacity and suffix-order constraints.

## Run

Use Python 3.10 or newer. The commands below use only the standard library;
run them from this directory, after extracting the ZIP if necessary.

```sh
python -B scripts/run_example.py examples/three_tasks.json
python -B scripts/run_example.py examples/two_readers.json
python -B -m unittest discover -s tests -v
python -B scripts/analyze_results.py
```

The first example reports an incumbent objective of 20 seconds and a best
objective of 18 seconds, with order `r, b, a`. The two-reader example discovers
a three-task release action and shows that `X` survives the first reader.
The executor models one serialized GPU lane and resident input copies, with
copy-group enumeration, pending-ancestor closure, bounded action size, atomic
copy accounting, serial continuation scoring and fixed protected prefixes.
The sampling diagnostic uses three endpoint indices, with index zero as the
local fastest endpoint.

Tests vary durations, output allocation, reader count, dependency closure,
protected prefixes, reservation state, DMA acknowledgement and proposal seeds.
`analyze_results.py` reads aggregate result tables and calculates percentage
comparisons. The [data dictionary](data/README.md) defines their units; paired
trace means and search statistics accompany the tables.

## Resolved event example

Run `python -B scripts/check_resolved_events.py` to evaluate the supplied two-GPU
event graph, whose response objective is 17.2 seconds. Transfer, capacity and
suffix-order constraints are explicit inputs. The
[continuation protocol](docs/continuation-protocol.md) explains event scoring,
while the [mechanism guide](docs/reference-model.md) describes candidate generation
and its relationship to the heterogeneous execution engine.
