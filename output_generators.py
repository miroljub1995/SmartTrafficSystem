import traci
import numpy as np
import os

class Average_waiting_time:
    def __init__(self, out_folder):
        self.out_folder = out_folder
        self.samples = []
        self.num_unsaved = 0

    def record(self, seconds):
        all_cars_on_scene = traci.vehicle.getIDList()
        avg = 0
        if len(all_cars_on_scene) > 0:
            avg = np.average(list(map(traci.vehicle.getAccumulatedWaitingTime, all_cars_on_scene)))
        sample = [[avg], [seconds]]
        self.samples = np.hstack((np.reshape(self.samples, (2, -1)), sample))
        self.num_unsaved += 1
        self.__save_if_need()

    def __save_if_need(self):
        if self.num_unsaved == 10:
            self.save()
            self.num_unsaved = 0

    def save(self):
        if not os.path.exists(self.out_folder):
            os.mkdir(self.out_folder)
        np.savetxt(os.path.join(self.out_folder, "awt.txt"), self.samples)
        print("Average waiting time saved to awt.txt")