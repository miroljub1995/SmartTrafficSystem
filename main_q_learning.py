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
from phase_decision import Q_learning_decision
from phase_controller import Phase_controller
from output_generators import Average_waiting_time

STEP_SIZE = 0.2
SIMULATION_DURATION = 4000000
NUM_CHUNKS_IN_LEARNING_PERIOD = 10
GREEN_LIGHT_DUR = 15
YELLOW_LIGHT_DUR = 3
TABLE_OUT_PATH = "out/table.txt"
OUT_DIR = "out/q_learning/"

TRAINING_DURATION = 36000
TABLE_SAVING_INTERVAL = 20

def isYellow():
    return traci.trafficlight.getPhase("center") % 2 != 0

def run():
    seconds = 0
    #           v0   v1  v2
    # intervali: 0, 1-4, 5+  (v0 x v0), (v0 x v1), (v0 x v2), (v1 x v1), (v1 x v2), (v2 x v2)
    # podstanja                  s0         s1         s2         s3         s4         s5
    states_per_det = 6
    num_of_states = states_per_det ** 4
    num_of_actions = 4

    phase_controller = Phase_controller(STEP_SIZE, GREEN_LIGHT_DUR, YELLOW_LIGHT_DUR)
    detectors = Detectors(phase_controller)

    table = Table(num_of_states, num_of_actions, TABLE_OUT_PATH, detectors)
    if os.path.exists(TABLE_OUT_PATH):
        table.load(TABLE_OUT_PATH)
    phase_decision = Q_learning_decision(table)

    #generators
    average_waiting_time = Average_waiting_time("out/q_learning/")
    
    # while seconds < SIMULATION_DURATION:
    start = time.time()
    while time.time() - start < TRAINING_DURATION:
        traci.simulationStep()
        phase_controller.simulation_step()
        seconds += STEP_SIZE
        detectors.update()

        # print("Passed: {}".format(detectors.num_passed_light))
        
        if phase_controller.is_yellow() and phase_controller.is_end_of_yellow():# transition from yellow to green
            average_waiting_time.update(seconds)
            
            #drawing stats
            # plt.plot(average_waiting_time.samples[1], average_waiting_time.samples[0])
            # plt.pause(0.05)

            table.next_step()
            
            current_phase = phase_decision.next_phase()
            phase_controller.set_phase(current_phase)

            detectors.num_passed_light = 0
        elif phase_controller.is_end_of_green():
            current_phase = phase_controller.get_phase()
            current_phase += 1
            phase_controller.set_phase(current_phase)

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
