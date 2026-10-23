"""Copy lifetime accounting and bounded serial-GPU continuation search.

Times are seconds; memory is GiB. This executable model has one compute lane,
resident inputs, atomic reservations, DAG precedence, and fixed query tails.
"""
from copy import deepcopy
from itertools import combinations, permutations


class Infeasible(ValueError):
    pass


class Ledger:
    """Allocated copies plus disjoint outstanding reservations.

    Obligations survive conversion from demand to a kernel/DMA pin. Only an
    acknowledged completion removes a pin. Remap protects destination first.
    """
    def __init__(self, capacity, copies=()):
        self.capacity = capacity
        self.copies = {c['id']: {'size': c['size_GiB'],
                       'uses': {u: 'demand' for u in c['readers']}}
                       for c in copies}
        self.reservations = {}
        if self.used > capacity:
            raise Infeasible('initial allocation exceeds capacity')

    @property
    def used(self):
        return sum(c['size'] for c in self.copies.values()) + sum(self.reservations.values())

    def reserve(self, key, size):
        if size < 0 or key in self.reservations or key in self.copies:
            raise ValueError('invalid or duplicate reservation')
        if self.used + size > self.capacity + 1e-12:
            raise Infeasible('capacity guard rejected reservation')
        self.reservations[key] = size

    def materialize(self, key, readers):
        size = self.reservations.pop(key)
        self.copies[key] = {'size': size, 'uses': {u: 'demand' for u in readers}}

    def pin(self, copy, user, kind='kernel'):
        if kind not in ('kernel', 'dma') or self.copies[copy]['uses'].get(user) != 'demand':
            raise ValueError('pin requires an existing logical demand')
        self.copies[copy]['uses'][user] = kind

    def acknowledge(self, copy, user):
        if self.copies[copy]['uses'].get(user) not in ('kernel', 'dma'):
            raise ValueError('completion requires a live pin')
        del self.copies[copy]['uses'][user]

    def remap(self, source, destination, user):
        if self.copies[source]['uses'].get(user) != 'demand':
            raise ValueError('only an unlaunched demand can be remapped')
        if user in self.copies[destination]['uses']:
            raise ValueError('destination already owns this obligation')
        self.copies[destination]['uses'][user] = 'demand'
        del self.copies[source]['uses'][user]

    def collect(self):
        freed = [k for k, c in self.copies.items() if not c['uses']]
        for k in freed:
            del self.copies[k]
        return freed


def validate(case):
    tasks = {t['id']: t for t in case['tasks']}
    if len(tasks) != len(case['tasks']):
        raise ValueError('duplicate task id')
    known = set(tasks)
    for t in tasks.values():
        if t['duration_s'] <= 0 or t['scratch_GiB'] < 0:
            raise ValueError('invalid task resource bound')
        if not set(t.get('parents', [])) <= known or t['query'] not in case['queries']:
            raise ValueError('unknown parent or query')
    copies = list(case['copies']) + [o for t in tasks.values() for o in t.get('outputs', [])]
    if len({c['id'] for c in copies}) != len(copies):
        raise ValueError('duplicate copy id')
    for c in copies:
        if c['size_GiB'] < 0 or not set(c['readers']) <= known:
            raise ValueError('invalid copy bound or reader')
    return tasks


def replay(case, order):
    """Replay every task; peak counts outputs before releasing input copies."""
    tasks = validate(case)
    if len(order) != len(tasks) or set(order) != set(tasks):
        raise Infeasible('continuation must contain every task exactly once')
    prefix = case.get('protected_prefix', [])
    if list(order[:len(prefix)]) != prefix:
        raise Infeasible('protected prefix changed')
    ledger = Ledger(case['capacity_GiB'], case['copies'])
    ledger.collect()
    now = case.get('planning_gate_s', 0)
    peak, finish, events = ledger.used, {}, []
    for ident in order:
        t = tasks[ident]
        if not set(t.get('parents', [])) <= finish.keys():
            raise Infeasible('predecessor not complete')
        # All modeled inputs must exist before launch; produced copies use DAG edges.
        inputs = [c['id'] for c in case['copies'] if ident in c['readers']]
        inputs += [c['id'] for v in tasks.values() for c in v.get('outputs', []) if ident in c['readers']]
        if not all(c in ledger.copies for c in inputs):
            raise Infeasible('input not materialized')
        ledger.reserve('scratch:' + ident, t['scratch_GiB'])
        for out in t.get('outputs', []):
            ledger.reserve(out['id'], out['size_GiB'])
        peak = max(peak, ledger.used)
        for c in inputs:
            ledger.pin(c, ident)
        start = now
        now += t['duration_s']
        finish[ident] = now
        del ledger.reservations['scratch:' + ident]
        for out in t.get('outputs', []):
            ledger.materialize(out['id'], out['readers'])
        for c in inputs:
            ledger.acknowledge(c, ident)
        freed = ledger.collect()
        events.append({'task': ident, 'start_s': start, 'end_s': now,
                       'freed': freed, 'memory_after_GiB': ledger.used})
    completions = {q: max([spec.get('fixed_tail_s', 0)] +
                   [finish[t['id']] for t in tasks.values() if t['query'] == q])
                   for q, spec in case['queries'].items()}
    objective = sum(spec.get('weight', 1) * (completions[q] - spec.get('arrival_s', 0))
                    for q, spec in case['queries'].items())
    return {'order': list(order), 'objective_s': objective, 'peak_GiB': peak,
            'completion_s': completions, 'events': events}


def frontier_prefixes(case, beneficiary, k=3):
    """Small-state exact copy-group enumeration (not the online beam).

    Enumerate gross-release groups covering the beneficiary's initial deficit;
    close readers and beneficiary over pending ancestors, then order readers
    before beneficiary. Replay decides whether outputs erase the gross release.
    Protected-prefix tasks are fixed boundary tasks and do not consume k.
    """
    tasks = validate(case)
    fixed = set(case.get('protected_prefix', []))
    if beneficiary in fixed:
        return []
    target = tasks[beneficiary]
    demand = target['scratch_GiB'] + sum(c['size_GiB'] for c in target.get('outputs', []))
    live_copies = [c for c in case['copies'] if c['readers']]
    deficit = sum(c['size_GiB'] for c in live_copies) + demand - case['capacity_GiB']
    if deficit <= 0:
        return []
    found = set()
    for size in range(1, len(live_copies) + 1):
        for group in combinations(live_copies, size):
            if sum(c['size_GiB'] for c in group) < deficit:
                continue
            readers = {r for c in group for r in c['readers']}
            if beneficiary in readers:
                continue
            closure = (readers | {beneficiary}) - fixed
            while True:
                expanded = closure | {p for v in closure for p in tasks[v].get('parents', []) if p not in fixed}
                if expanded == closure:
                    break
                closure = expanded
            if len(closure) > k:
                continue
            for order in permutations(sorted(closure)):
                seen = set(fixed)
                for v in order:
                    if not set(tasks[v].get('parents', [])) <= seen:
                        break
                    if v == beneficiary and not readers <= seen:
                        break
                    seen.add(v)
                else:
                    found.add(order)
    return sorted(found)


def search(case, beneficiary, k=3):
    incumbent = case['incumbent']
    best = replay(case, incumbent)
    evaluated = []
    fixed = case.get('protected_prefix', [])
    for prefix in frontier_prefixes(case, beneficiary, k):
        order = fixed + list(prefix) + [v for v in incumbent if v not in prefix and v not in fixed]
        try:
            result = replay(case, order)
            evaluated.append(result)
            if result['objective_s'] < best['objective_s']:
                best = result
        except Infeasible as error:
            evaluated.append({'order': order, 'infeasible': str(error)})
    return {'incumbent': replay(case, incumbent), 'best': best, 'candidates': evaluated}
