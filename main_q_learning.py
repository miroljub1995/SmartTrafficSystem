#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import sys
import random
import time
import multiprocessing

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
import numpy as np
import matplotlib.pyplot as plt

from detectors import Detectors
from table import Table

STEP_SIZE = 0.2
SIMULATION_DURATION = 4000000
NUM_CHUNKS_IN_PERIOD = 10
GREEN_LIGHT_DUR = 15
YELLOW_LIGHT_DUR = 3
TABLE_OUT_PATH = "out/table.txt"

TRAINING_DURATION = 36000
TABLE_SAVING_INTERVAL = 20

def isYellow():
    return traci.trafficlight.getPhase("center") % 2 != 0

def run():
    seconds = 0
    current_phase = 0
    steps_in_phase = 0
    #           v0   v1  v2
    # intervali: 0, 1-4, 5+  (v0 x v0), (v0 x v1), (v0 x v2), (v1 x v1), (v1 x v2), (v2 x v2)
    # podstanja                  s0         s1         s2         s3         s4         s5
    states_per_det = 6
    num_of_states = states_per_det ** 4
    num_of_actions = 4

    table = Table(num_of_states, num_of_actions)
    if os.path.exists(TABLE_OUT_PATH):
        table.load(TABLE_OUT_PATH)
    detectors = Detectors()
    
    prev_eval = 0

    chunks = []
    num_passed_light = 0
    sum_of_cars_prev = 0.5
    num_learned = 0
    
    car_passed = []
    samples = []

    # while seconds < SIMULATION_DURATION:
    start = time.time()
    while time.time() - start < TRAINING_DURATION:
        traci.simulationStep()
        # continue
        seconds += STEP_SIZE

        detectors.update()
        num_passed_light += detectors.num_passed
        car_passed.extend([traci.vehicle.getAccumulatedWaitingTime(car) for car in detectors.passed])
        # if len(car_passed) > 100:
        #     to_remove = len(car_passed) - 100
        #     car_passed = car_passed[to_remove:]
        
        if isYellow() and steps_in_phase >= 3:# transition from yellow to green

            #drawing stats
            all_cars_on_scene = traci.vehicle.getIDList()
            avg = 0
            if len(all_cars_on_scene) > 0:
                avg = np.average([traci.vehicle.getAccumulatedWaitingTime(car) for car in all_cars_on_scene])
            sample = [[avg], [seconds]]
            samples = np.hstack((np.reshape(samples, (2, -1)), sample))

            
            # car_passed_average_wait = 0
            # if len(car_passed):
            #     car_passed_average_wait = np.average(car_passed)
            # print("Average: {} {}".format(car_passed, car_passed_average_wait))

            # x = [[car_passed_average_wait], [seconds]]
            # samples = np.hstack((np.reshape(samples, (2, -1)), x))

            print("Samples: {}".format(samples))
            plt.plot(samples[1], samples[0])
            # plt.pause(0.05)
            car_passed = []


            prev_state = table.state
            prev_action = table.predicted_action
            table.next_step()
            # print("State: {}".format(table.state))
            
            # print("Number passed: {}".format(num_passed_light))
            # flow = num_passed_light * 60 / GREEN_LIGHT_DUR + YELLOW_LIGHT_DUR
            # print("Flow: {}".format(flow))

            sum_of_cars = detectors.num_cars + 0.5
            curr_eval = 0
            curr_eval = num_passed_light / sum_of_cars_prev

            reward = curr_eval - prev_eval
            chunks.append((prev_state, prev_action, reward, table.state))
            sum_of_cars_prev = sum_of_cars

            if len(chunks) == NUM_CHUNKS_IN_PERIOD:
                table.learn(chunks)
                num_learned += 1
                if num_learned >= TABLE_SAVING_INTERVAL:
                    table.save(TABLE_OUT_PATH)
                    num_learned = 0
                chunks = []
            
            steps_in_phase = 0
            next_action = table.predicted_action
            current_phase = next_action * 2
            # print("Next phase: {}".format(current_phase))
            traci.trafficlight.setPhase("center", current_phase)

            prev_eval = curr_eval
            num_passed_light = 0
            num_passed_light = 0

        elif steps_in_phase >= GREEN_LIGHT_DUR:
            current_phase += 1
            traci.trafficlight.setPhase("center", current_phase)
            steps_in_phase = 0
        else:
            steps_in_phase += STEP_SIZE

    table.save(TABLE_OUT_PATH)
    traci.close()
    sys.stdout.flush()

# this is the main entry point of this script
if __name__ == "__main__":
    out = 'out'
    cpus = multiprocessing.cpu_count()
    if not os.path.exists(out):
        os.mkdir(out)

    sumoBinary = checkBinary('sumo-gui')
    # sumoBinary = checkBinary('sumo')
    traci.start([sumoBinary, "-c", "cross.sumocfg",
                             "--tripinfo-output", os.path.join(out, "tripinfo.xml"),
                             "--step-length", "{}".format(STEP_SIZE),
                             "--threads", "{}".format(cpus),
                             '--no-step-log'])

    run()
