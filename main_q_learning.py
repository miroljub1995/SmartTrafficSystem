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
from table import Table

STEP_SIZE = 0.05
SIMULATION_DURATION = 400000
CHUNK_DURATION = 180

def isYellow():
    return traci.trafficlight.getPhase("center") % 2 != 0

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

    table = Table(num_of_states, num_of_actions)
    detectors = Detectors()
    
    prev_eval = sys.float_info.max

    flow = 0
    seconds_in_chunk = 0

    while seconds < SIMULATION_DURATION:
        traci.simulationStep()
        detectors.update()
        table.update()
        seconds += STEP_SIZE

        print("State: {}".format(table.current_state))

        if isYellow() and steps_in_phase >= 3:
            current_phase = table.get_next_action() * 2
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
