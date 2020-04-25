import os

from q_decision import Table
from r_decision import Random_decision

def q_factory(out_dir, detectors):
    #           v0   v1  v2
    # intervals: 0, 1-4, 5+  (v0 x v0), (v0 x v1), (v0 x v2), (v1 x v1), (v1 x v2), (v2 x v2)
    # substates                 s0         s1         s2         s3         s4         s5
    states_per_det = 6
    num_of_states = states_per_det ** 4
    num_of_actions = 4
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    table_out_path = os.path.join(out_dir, "table.txt")
    table = Table(num_of_states, num_of_actions, table_out_path, detectors)
    if os.path.exists(table_out_path):
        table.load(table_out_path)
    return table

def r_factory(_, __):
    return Random_decision()

def rr_factory(_, __):
    raise NotImplementedError