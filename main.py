#!/usr/bin/env python
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2020 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    runner.py
# @author  Lena Kalleske
# @author  Daniel Krajzewicz
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2009-03-26

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import sys
import optparse
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

        # cars = traci.vehicle.getIDList()
        # for car in cars:
        #     print("Vehicle: {}, lane: {}".format(car, traci.vehicle.getLaneID(car)))

        # print("currentPhase: {}, stepsInPhase: {}".format(currentPhase, stepsInPhase))
        # print("Is yellow: {}".format(isYellow()))
        # print(traci.lanearea.getLastStepVehicleNumber('e2Detector_r_left_0'))
        traci.lanearea.getLastStepVehicleIDs('e2Detector_r_left_0')

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
