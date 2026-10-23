import json
import sys
import unittest
from copy import deepcopy
from itertools import permutations, product
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from reference import Ledger, Infeasible, replay, search, frontier_prefixes
from sampler import Diverse, old, summarize, epoch_seed
from noise import factor
sys.path.insert(0, str(ROOT / 'scripts'))
from check_resolved_events import score

def fixture(name='three_tasks'):
    return json.loads((ROOT/'examples'/f'{name}.json').read_text())

class ReferenceTests(unittest.TestCase):
    def test_resolved_heterogeneous_graph(self):
        c=fixture('heterogeneous_events')
        self.assertAlmostEqual(score(c)['objective_s'],17.2)
        self.assertEqual(score(c)['peak_GiB'],{'GPU0':6,'GPU1':6,'host':6})
        c['operations'][-1]['duration_s']+=1
        self.assertAlmostEqual(score(c)['objective_s'],18.2)
        c['capacity_GiB']['GPU1']=5
        with self.assertRaises(ValueError): score(c)

    def test_shared_noise_draw(self):
        import math
        self.assertEqual(factor('t1','join','GPU0',0),1)
        z1=(math.log(factor('t1','join','GPU0',.2))+.2**2/2)/.2
        z2=(math.log(factor('t1','join','GPU0',.4))+.4**2/2)/.4
        self.assertAlmostEqual(z1,z2)
        self.assertNotEqual(factor('t1','join','GPU0',.2),factor('t1','join','GPU1',.2))

    def test_initial_unreferenced_copy(self):
        c={'capacity_GiB':10, 'copies':[{'id':'unused','size_GiB':6,'readers':[]}],
           'tasks':[{'id':'a','query':'A','duration_s':1,'scratch_GiB':5}],
           'queries':{'A':{}},'incumbent':['a']}
        self.assertEqual(replay(c,['a'])['objective_s'],1)
        self.assertEqual(replay(c,['a'])['peak_GiB'],5)
        self.assertEqual(frontier_prefixes(c,'a'),[])

    def test_table_one_and_search(self):
        c = fixture()
        self.assertEqual([replay(c,list(o))['objective_s'] for o in ['arb','rba','rab']], [20,18,21])
        self.assertEqual(search(c,'b')['best']['order'], ['r','b','a'])
        with self.assertRaises(Infeasible): replay(c, list('bar'))

    def test_duration_exchange(self):
        for a,r,b in product([1,2,4,8], repeat=3):
            c=fixture()
            for t in c['tasks']: t['duration_s']={'a':a,'r':r,'b':b}[t['id']]
            c['queries']['R']['fixed_tail_s']=a+r+b+1
            self.assertEqual(replay(c,list('arb'))['objective_s']-replay(c,list('rba'))['objective_s'],a-r-b)

    def test_peak_gap(self):
        for length in [1,2,10,100]:
            c=fixture()
            for t in c['tasks']: t['duration_s']=length if t['id']=='r' else 1
            c['queries']['R']['fixed_tail_s']=length+3
            rows=[replay(c,list(o)) for o in ['arb','rab','rba']]
            lowpeak=min(x['peak_GiB'] for x in rows)
            self.assertEqual(min(x['objective_s'] for x in rows if x['peak_GiB']==lowpeak)-min(x['objective_s'] for x in rows),length)

    def test_all_readers_and_cap(self):
        c=fixture('two_readers')
        self.assertEqual(frontier_prefixes(c,'b',2),[])
        result=search(c,'b')
        self.assertEqual(result['best']['events'][0]['freed'],[])
        self.assertEqual(result['best']['events'][1]['freed'],['X'])
        self.assertLess(result['best']['objective_s'],result['incumbent']['objective_s'])

    def test_output_erases_release(self):
        c=fixture()
        c['tasks'][1]['outputs']=[{'id':'Y','size_GiB':4,'readers':['a']}]
        c['tasks'][2]['scratch_GiB']=7
        c['tasks'][0]['parents']=['r']
        c['incumbent']=list('rab')
        result=search(c,'b')
        self.assertEqual(result['best']['order'],list('rab'))
        self.assertTrue(any('infeasible' in row for row in result['candidates']))

    def test_reservations_and_pin_lifecycle(self):
        l=Ledger(10,[{'id':'X','size_GiB':6,'readers':['r','dma']}])
        l.reserve('Y',4)
        self.assertEqual(l.used,10)
        l.materialize('Y',['b'])
        self.assertEqual(l.used,10)
        with self.assertRaises(Infeasible): l.reserve('scratch',1)
        l.pin('X','r'); l.pin('X','dma','dma'); l.acknowledge('X','r')
        self.assertEqual(l.collect(),[])
        l.acknowledge('X','dma')
        self.assertEqual(l.collect(),['X'])

    def test_remap_and_protected_prefix(self):
        l=Ledger(12,[{'id':'X','size_GiB':6,'readers':['r']},{'id':'Y','size_GiB':6,'readers':[]}])
        l.remap('X','Y','r')
        self.assertEqual(l.copies['Y']['uses']['r'],'demand')
        self.assertEqual(l.collect(),['X'])
        c=fixture(); c['protected_prefix']=['a']
        self.assertEqual(search(c,'b')['best']['order'],list('arb'))
        with self.assertRaises(Infeasible): replay(c,list('rba'))

    def test_pending_ancestor_cap(self):
        c=fixture('two_readers')
        c['tasks'][1]['parents']=['other']
        self.assertEqual(frontier_prefixes(c,'b',3),[])
        self.assertTrue(frontier_prefixes(c,'b',4))

    def test_sampler_coverage_and_dag(self):
        for n,expected in [(12,71),(96,94)]:
            s=Diverse(n,[set() for _ in range(n)],20261011)
            rows=[s.next(i%3+1) for i in range(284)]
            self.assertEqual(summarize(rows)['3']['task_sets'],expected)
            self.assertEqual(summarize(old(n,284))['3']['task_sets'],2)
        parents=[set(),set(),{0},{0},{1},{2,3},{4},set(),{5,6},{7},{9},{8,10}]
        s=Diverse(12,parents,epoch_seed('dag',1))
        for i in range(284):
            seen=set()
            for v in s.next(i%3+1)[::2]:
                self.assertTrue(parents[v] <= seen)
                self.assertNotIn(v,seen)
                seen.add(v)

if __name__=='__main__': unittest.main()
