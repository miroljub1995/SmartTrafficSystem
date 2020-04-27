#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import sys
import time
import multiprocessing
import argparse

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
from phase_controller import Phase_controller
from output_generators import Average_waiting_time
from factories import q_factory, r_factory, rr_factory
from traffic_generator import Traffic_generator

STEP_SIZE = 0.2
SIMULATION_DURATION = 50000
TRAINING_DURATION = 36000
GREEN_LIGHT_DUR = 15
YELLOW_LIGHT_DUR = 3

def run(config):
    seconds = 0
    phase_controller = Phase_controller(STEP_SIZE, GREEN_LIGHT_DUR, YELLOW_LIGHT_DUR)
    detectors = Detectors(phase_controller)
    traffic = Traffic_generator(STEP_SIZE)

    light_decision_system = config.factory(config.out_dir, detectors)

    #generators
    average_waiting_time = Average_waiting_time(config.out_dir)

    while seconds < SIMULATION_DURATION:
    # start = time.time()
    # while time.time() - start < TRAINING_DURATION:
        traci.simulationStep()
        traffic.next_step()
        phase_controller.simulation_step()
        seconds += STEP_SIZE
        detectors.update()

        if phase_controller.is_yellow() and phase_controller.is_end_of_yellow():# transition from yellow to green
            average_waiting_time.update(seconds)
            #drawing stats
            # plt.plot(average_waiting_time.samples[1], average_waiting_time.samples[0])
            # plt.pause(0.05)

            light_decision_system.next_step()
            current_phase = light_decision_system.get_predicted_phase()
            phase_controller.set_phase(current_phase)

            detectors.num_passed_light = 0
        elif phase_controller.is_end_of_green():
            current_phase = phase_controller.get_phase()
            current_phase += 1
            phase_controller.set_phase(current_phase)

    traci.close()
    sys.stdout.flush()

class Config:
    def __init__(self, factory, out_dir, sumo_binary):
        self.factory = factory
        self.out_dir = out_dir
        self.sumo_binary = sumo_binary

def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", help="Define type, can be q (for q learning), rand (for random) or rr (for robin round)", type=str, choices=["q", "r", "rr"], required=True)
    parser.add_argument("--no-gui", dest="sumo_binary", action="store_const", const="sumo", default="sumo-gui", help="run without gui (default: with gui)")
    args = parser.parse_args()
    if args.t == "q":
        return Config(q_factory, "out/q/", args.sumo_binary)
    elif args.t == 'r':
        return Config(r_factory, "out/r/", args.sumo_binary)
    elif args.t == 'rr':
        return Config(rr_factory, "out/rr/", args.sumo_binary)
    else:
        raise Exception("Should not be reached")

def main():
    config = get_config()
    print("Args: {}".format(config))
    out = 'out'
    det_out = os.path.join(out, "det")
    if not os.path.exists(out):
        os.mkdir(out)
    if not os.path.exists(det_out):
        os.mkdir(det_out)

    cpus = multiprocessing.cpu_count()
    sumo_binary = checkBinary(config.sumo_binary)
    traci.start([sumo_binary,
                 "-c", "cross.sumocfg",
                 "--tripinfo-output", os.path.join(det_out, "tripinfo.xml"),
                 "--step-length", "{}".format(STEP_SIZE),
                 "--threads", "{}".format(cpus),
                 '--no-step-log'])

    run(config)

main()
