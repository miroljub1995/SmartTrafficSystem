import traci


class Detectors:
    def __init__(self):
        self.detectors = []
        for det in traci.lanearea.getIDList():
            self.detectors.append(Detector(det))

        self.num_passed = 0
        self.num_cars = 0

    def update(self):
        self.num_passed = 0
        self.num_cars = 0
        for det in self.detectors:
            det.update()
            self.num_passed += det.num_passed
            self.num_cars += det.num_cars()

class Detector:
    def __init__(self, id_string):
        self.id = id_string
        self.num_arrived = 0
        self.num_passed = 0

        self.cars = []

    def update(self):
        self.num_passed = 0
        self.num_arrived = 0
        cars = traci.lanearea.getLastStepVehicleIDs(self.id)
        for car in cars:
            if car not in self.cars:
                self.num_arrived += 1
                self.cars.append(car)
        for car in list(self.cars):
            if car not in cars:
                self.cars.remove(car)
                self.num_passed += 1

    def num_cars(self):
        return len(self.cars)
