import random
import traci

CHANGE_PROBABILITIES_INTERVAL = 600
MAX_PROBABILIY = 0.09

class Route_generator:
    def __init__(self, route_name):
        self.route_name = route_name
        self.car_count = 0
        self.regenerate_prob()

    def generate(self):
        if random.random() < self.probability:
            self.__add_car()

    def regenerate_prob(self):
        self.probability = random.uniform(0, MAX_PROBABILIY)

    def __add_car(self):
        car_id = "car_{}_{}".format(self.route_name, self.car_count)
        traci.vehicle.add(car_id, self.route_name, typeID="car1", departSpeed="max", departLane='best')
        traci.vehicle.setColor(car_id, (255, 255, 0))
        self.car_count += 1

class Traffic_generator:
    def __init__(self, step_size):
        self.step_size = step_size
        self.seconds = 0
        self.route_generators = [Route_generator('route_up_left'),
                                 Route_generator('route_up_down'),
                                 Route_generator('route_up_right'),
                                 Route_generator('route_right_up'),
                                 Route_generator('route_right_left'),
                                 Route_generator('route_right_down'),
                                 Route_generator('route_down_right'),
                                 Route_generator('route_down_up'),
                                 Route_generator('route_down_left'),
                                 Route_generator('route_left_down'),
                                 Route_generator('route_left_right'),
                                 Route_generator('route_left_up')]

    def next_step(self):
        prev_time = self.seconds
        self.seconds += self.step_size
        if int(prev_time) < int(self.seconds):
            self.__on_every_second()

    def __on_every_second(self):
        for gen in self.route_generators:
            gen.generate()
            if int(self.seconds) % CHANGE_PROBABILITIES_INTERVAL == 0:
                gen.regenerate_prob()
