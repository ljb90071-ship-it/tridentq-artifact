"""Validate archived aggregate data and calculate paper comparisons.

This performs table analysis; it does not execute database workloads.
"""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def rows(name):
    with (ROOT/'data'/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

main={(r['policy'],r['workload']):r for r in rows('main.csv')}
assert len(main)==24
gains={}
for workload in ['H-Mix','DS-Mix','Branch-Mix']:
    cover=main['Cover-64',workload]; tri=main['TridentQ',workload]
    gains[workload]={key:100*(float(cover[key])-float(tri[key]))/float(cover[key])
                     for key in ['mean_s','mean_trace_p95_s']}
for r in rows('main.csv'):
    assert 0 < float(r['mean_s']) <= float(r['mean_trace_p95_s'])
for r in rows('memory.csv'):
    gain=100*(1-float(r['TridentQ_mean_s'])/float(r['Cover-64_mean_s']))
    assert abs(gain-float(r['gain_percent'])) < .051
for r in rows('oracle.csv'):
    assert int(r['all_hits'])==int(r['improvable_hits'])+int(r['noop_optimal_states'])
    assert int(r['all_states'])==int(r['improvable_states'])+int(r['noop_optimal_states'])
for r in rows('paired_summary.csv'):
    delta=float(main['Cover-64',r['workload']]['mean_s'])-float(main['TridentQ',r['workload']]['mean_s'])
    assert abs(delta-float(r['mean_difference_s'])) < 1e-10
    assert float(r['min_difference_s'])<=delta<=float(r['max_difference_s'])
for r in rows('fanout.csv'):
    assert 0<=float(r['closure_fits_k3_percent'])<=100
    assert 0<=float(r['response_reduction_percent'])<=100
actions=json.loads((ROOT/'data/accepted_actions.json').read_text())
for key in ['device_change_percent','release_group_percent']:
    assert sum(actions[key].values())==100
for key in ['device_change_counts','release_group_counts']:
    assert sum(actions[key].values())==actions['count']
paired=rows('paired_trace_means.csv')
for summary in rows('paired_summary.csv'):
    sample=[r for r in paired if r['family']==summary['workload']]
    assert len(sample)==10
    delta=[float(r['difference_s']) for r in sample]
    assert abs(sum(delta)/10-float(summary['mean_difference_s']))<1e-10
    assert abs(min(delta)-float(summary['min_difference_s']))<1e-10
    assert abs(max(delta)-float(summary['max_difference_s']))<1e-10
    assert sum(x>0 for x in delta)==int(summary['positive_pairs'])
    for r in sample:
        assert abs(float(r['Cover-64_mean_s'])-float(r['TridentQ_mean_s'])-float(r['difference_s']))<1e-10
    for policy in ['Cover-64','TridentQ']:
        assert abs(sum(float(r[policy+'_mean_s']) for r in sample)/10-float(main[policy,summary['workload']]['mean_s']))<1e-10
print(json.dumps({'analysis':'archived aggregate comparisons','gain_percent':gains,
 'generic_fraction_of_Cartesian_to_TridentQ_gap':(4.5-4.08)/(4.5-3.82),
 'consistency_checks':'passed'},indent=2))
