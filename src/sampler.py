"""Candidate-generation diagnostic only; no performance or source/replay model."""
import heapq
import json
import random

def old_stream(length, n):
    zero = (0,) * (2*length)
    heap, seen = [(0, zero)], {zero}
    while heap:
        _, a = heapq.heappop(heap)
        for i, bound in enumerate([n, 3]*length):
            if a[i]+1 < bound:
                b = a[:i]+(a[i]+1,)+a[i+1:]
                if b not in seen:
                    seen.add(b)
                    heapq.heappush(heap, (sum(b), b))
        yield a

def old(n, count):
    streams = [old_stream(j, n) for j in (1,2,3)]
    active, output = [0,1,2], []
    while len(output) < count and active:
        i = active.pop(0)
        try:
            a = next(streams[i])
        except StopIteration:
            continue
        active.append(i)
        output.append(a if len(set(a[::2])) == i+1 else None)
    return output

class Diverse:
    def __init__(self, n, parents, seed):
        self.n, self.parents = n, parents
        self.rng = random.Random(seed)
        self.anchors = {j: [] for j in range(1,min(3,n)+1)}
        self.width = (n+3)//4
    def band(self, v):
        return min(v//self.width,3)
    def randindex(self, n):
        return int(self.rng.random()*n)
    def shuffle(self, xs):
        for i in range(len(xs)-1,0,-1):
            j = self.randindex(i+1)
            xs[i], xs[j] = xs[j], xs[i]
    def refill_anchor(self, length):
        bands = [[v for v in range(self.n) if not self.parents[v] and self.band(v)==b] for b in range(4)]
        for band in bands:
            self.shuffle(band)
        result = []
        while any(bands):
            for b in (0,1,0,2,0,3):
                if bands[b]:
                    result.append(bands[b].pop())
        self.anchors[length] = result
    def next(self, length):
        if not self.anchors[length]:
            self.refill_anchor(length)
        selected = [self.anchors[length].pop(0)]
        while len(selected) < length:
            eligible = [v for v in range(self.n) if v not in selected and self.parents[v].issubset(selected)]
            assert eligible
            bands = [[v for v in eligible if self.band(v)==b] for b in range(4)]
            tickets = [b for b in (0,0,0,1,2,3) if bands[b]]
            band = bands[tickets[self.randindex(len(tickets))]]
            selected.append(band[self.randindex(len(band))])
        a = []
        for v in selected:
            # Device index 0 is local predicted-fastest; all three supported here.
            d = 0 if self.rng.random() < .5 else self.randindex(3)
            a += [v,d]
        return tuple(a)

def summarize(rows):
    result = {'attempts':len(rows),'legal':sum(a is not None for a in rows)}
    for j in (1,2,3):
        selected = [a for a in rows if a is not None and len(a)==2*j]
        result[str(j)] = {'proposals':len(selected), 'unique_task_device_tuples':len(set(selected)),
            'task_sets':len({tuple(sorted(a[::2])) for a in selected}),
            'root_tasks':len({a[0] for a in selected}),
            'max_task_rank':max((max(a[::2])+1 for a in selected),default=None)}
    return result


def epoch_seed(trace_id, epoch_id):
    import hashlib
    return int.from_bytes(hashlib.sha256(f"20261011:{trace_id}:{epoch_id}".encode()).digest()[:4], "big")
