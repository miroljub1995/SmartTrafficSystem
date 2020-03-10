#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import sys
import random

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa
import numpy as np

stepSize = 0.05

def isYellow():
    return traci.trafficlight.getPhase("center") % 2 != 0

def combine_substates(s1, s2, n):
    i, j = s1, s2
    if i > j:
        i, j = j, i
    return int((-(i ** 2) + i * (2 * n - 1) + 2 * j) / 2)

def num_cars_to_substate(n):
    if n > 4:
        return 2
    elif n > 0:
        return 1
    else:
        return 0

def run():
    seconds = 0
    current_phase = 0
    steps_in_phase = 0
    #         v0  v1  v2
    # stanja: 0, 1-4, 5+  (v0 x v0), (v0 x v1), (v0 x v2), (v1 x v1), (v1 x v2), (v2 x v2)
    #                         s0         s1         s2         s3         s4         s5
    states_per_det = 3
    num_of_states = states_per_det ** 4

    num_of_actions = 4
    matrix = np.random.random_sample((num_of_states, num_of_actions))
    print("Matrix: shape: {}, \n{}".format(matrix.shape, matrix))

    detectors = {}
    for det in traci.lanearea.getIDList():
        detectors[det] = {'cars': {}}
    det_pairs = [
        ('e2Detector_r_up_0', 'e2Detector_r_down_0'),
        ('e2Detector_r_up_1', 'e2Detector_r_down_1'),
        ('e2Detector_r_right_0', 'e2Detector_r_left_0'),
        ('e2Detector_r_right_1', 'e2Detector_r_left_1')]

    
    num_passed_light = 0
    print(detectors)

    prev_eval = sys.float_info.max

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        seconds += stepSize

        for det in detectors:
            cars = traci.lanearea.getLastStepVehicleIDs(det)
            for car in cars:
                if car not in detectors[det]['cars']:
                    detectors[det]['cars'][car] = car
                    # print("New car {} in detector {}".format(car, det))

            for car in list(detectors[det]['cars']):
                if car not in cars:
                    del detectors[det]['cars'][car]
                    num_passed_light += 1
                    # print("Car {} left detector {}".format(car, det))

        if isYellow() and steps_in_phase >= 3:
            current_phase = random.randrange(4) * 2
            print("Random: {}".format(current_phase))
            traci.trafficlight.setPhase("center", current_phase)
            steps_in_phase = 0
            
            sum_of_cars = 0
            for det in detectors:
                sum_of_cars += len(traci.lanearea.getLastStepVehicleIDs(det))

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
        elif steps_in_phase >= 15:
            current_phase += 1
            traci.trafficlight.setPhase("center", current_phase)
            steps_in_phase = 0
        else:
            steps_in_phase += stepSize
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
                             "--step-length", "{}".format(stepSize)])

    run()
