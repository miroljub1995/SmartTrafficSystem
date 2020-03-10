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

stepSize = 0.05

def isYellow():
    return traci.trafficlight.getPhase("center") % 2 != 0

def run():
    seconds = 0
    current_phase = 0
    steps_in_phase = 0

    detectors = {}
    for det in traci.lanearea.getIDList():
        detectors[det] = {'cars': {}}
    num_passed_light = 0

    print(detectors)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        seconds += stepSize

        for det in detectors:
            cars = traci.lanearea.getLastStepVehicleIDs(det)
            for car in cars:
                if car not in detectors[det]['cars']:
                    detectors[det]['cars'][car] = car
                    print("New car {} in detector {}".format(car, det))

            for car in list(detectors[det]['cars']):
                if car not in cars:
                    del detectors[det]['cars'][car]
                    num_passed_light += 1
                    print("Car {} left detector {}".format(car, det))


        if isYellow() and steps_in_phase >= 3:
            current_phase = random.randrange(4) * 2
            print("Random: {}".format(current_phase))
            traci.trafficlight.setPhase("center", current_phase)
            steps_in_phase = 0
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
