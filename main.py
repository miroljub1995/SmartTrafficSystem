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
    currentPhase = 0
    stepsInPhase = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        seconds += stepSize

        cars = traci.vehicle.getIDList()
        for car in cars:
            print("Vehicle: {}, lane: {}".format(car, traci.vehicle.getLaneID(car)))

        # print("currentPhase: {}, stepsInPhase: {}".format(currentPhase, stepsInPhase))
        # print("Is yellow: {}".format(isYellow()))
        if isYellow() and stepsInPhase >= 3:
            currentPhase = random.randrange(4) * 2
            print("Random: {}".format(currentPhase))
            traci.trafficlight.setPhase("center", currentPhase)
            stepsInPhase = 0
        elif stepsInPhase >= 15:
            currentPhase += 1
            traci.trafficlight.setPhase("center", currentPhase)
            stepsInPhase = 0
        else:
            stepsInPhase += stepSize
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