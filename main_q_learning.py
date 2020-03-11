#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import sys
import random
import time

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa
import numpy as np
from detectors import Detectors

STEP_SIZE = 0.05
SIMULATION_DURATION = 400000
CHUNK_DURATION = 180

def isYellow():
    return traci.trafficlight.getPhase("center") % 2 != 0

def intervals_to_substate(i1, i2, n):
    i, j = i1, i2
    if i > j:
        i, j = j, i
    return int((-(i ** 2) + i * (2 * n - 1) + 2 * j) / 2)

def num_cars_to_intervals(n):
    if n > 4:
        return 2
    elif n > 0:
        return 1
    else:
        return 0

def map_lambda(arr, func):
    return np.array([func(x) for x in arr])

def get_next_action(q, s):
    k = 2
    row = q[s]
    mapped_row = map_lambda(row, lambda x: k ** x)
    sum_of_elements = np.sum(mapped_row)
    probs = map_lambda(mapped_row, lambda x: x / sum_of_elements)
    selected = np.random.choice(q.shape[1], p=probs)
    return selected

def det_pair_to_substate(det_pair, num_intervals):
    d1, d2 = det_pair
    num_cars_d1 = len(traci.lanearea.getLastStepVehicleIDs(d1))
    num_cars_d2 = len(traci.lanearea.getLastStepVehicleIDs(d2))

    interval1 = num_cars_to_intervals(num_cars_d1)
    interval2 = num_cars_to_intervals(num_cars_d2)

    return intervals_to_substate(interval1, interval2, num_intervals)

def substates_to_state(substates, num_substates):
    result = 0
    k = 1
    for ss in reversed(substates):
        result += k * ss
        k *= num_substates
    return result

def get_current_state():
    det_pairs = [
        ('e2Detector_r_up_0', 'e2Detector_r_down_0'),
        ('e2Detector_r_up_1', 'e2Detector_r_down_1'),
        ('e2Detector_r_right_0', 'e2Detector_r_left_0'),
        ('e2Detector_r_right_1', 'e2Detector_r_left_1')]

    substates = np.array([det_pair_to_substate(pair, 3) for pair in det_pairs])
    return substates_to_state(substates, 6)

def run():
    seconds = 0
    current_phase = 0
    steps_in_phase = 0
    #         v0  v1  v2
    # stanja: 0, 1-4, 5+  (v0 x v0), (v0 x v1), (v0 x v2), (v1 x v1), (v1 x v2), (v2 x v2)
    #                         s0         s1         s2         s3         s4         s5
    states_per_det = 6
    num_of_states = states_per_det ** 4

    num_of_actions = 4
    q = np.random.random_sample((num_of_states, num_of_actions))
    print("Matrix: shape: {}, \n{}".format(q.shape, q))
    get_next_action(q, 0)

    detectors = Detectors()
    
    prev_eval = sys.float_info.max

    flow = 0
    seconds_in_chunk = 0

    while seconds < SIMULATION_DURATION:
        traci.simulationStep()
        detectors.update()
        seconds += STEP_SIZE

        current_state = get_current_state()
        print("State: {}".format(current_state))

        if isYellow() and steps_in_phase >= 3:
            # current_phase = random.randrange(4) * 2
            current_phase = get_next_action(q, current_state) * 2
            print("Random: {}".format(current_phase))
            traci.trafficlight.setPhase("center", current_phase)
            steps_in_phase = 0
            
            sum_of_cars = detectors.num_cars
            num_passed_light = detectors.num_passed

            curr_eval = 0
            if sum_of_cars != 0:
                curr_eval = num_passed_light / sum_of_cars
                print("Ratio: {} / {} = {}".format(num_passed_light, sum_of_cars, curr_eval))
            else:
                curr_eval = sys.float_info.max
                print("Ratio: {}".format(curr_eval))
            reward = curr_eval - prev_eval
            print("Reward: {} - {} = {}".format(curr_eval, prev_eval, reward))
            prev_eval = curr_eval
            num_passed_light = 0
            if seconds_in_chunk >= CHUNK_DURATION:
                # save chunk
                pass

        elif steps_in_phase >= 15:
            current_phase += 1
            traci.trafficlight.setPhase("center", current_phase)
            steps_in_phase = 0
        else:
            steps_in_phase += STEP_SIZE

        

        if seconds_in_chunk >= CHUNK_DURATION:
            seconds_in_chunk = 0
        else:
            seconds_in_chunk += STEP_SIZE

    num_passed_light = detectors.num_passed
    print("Num of cars: {}".format(num_passed_light))
    print("Time: {}".format(traci.simulation.getTime()))
    print(num_passed_light * 60 / traci.simulation.getTime())
    traci.close()
    sys.stdout.flush()

# this is the main entry point of this script
if __name__ == "__main__":
    out = 'out'
    if not os.path.exists(out):
        os.mkdir(out)

    sumoBinary = checkBinary('sumo-gui')
    traci.start([sumoBinary, "-c", "cross.sumocfg",
                             "--tripinfo-output", os.path.join(out, "tripinfo.xml"),
                             "--step-length", "{}".format(STEP_SIZE)])

    run()
