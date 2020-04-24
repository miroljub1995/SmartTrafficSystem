import traci

class Phase_controller:
    def __init__(self, step_size, green_light_dur, yellow_light_dur):
        self.__step_size = step_size
        self.green_light_dur = green_light_dur
        self.yellow_light_dur = yellow_light_dur
        self.seconds_in_phase = 0

    def simulation_step(self):
        self.seconds_in_phase += self.__step_size

    def set_phase(self, phase):
        traci.trafficlight.setPhase("center", phase)
        self.seconds_in_phase = 0

    def get_phase(self):
        return traci.trafficlight.getPhase("center")


    def is_yellow(self):
        return traci.trafficlight.getPhase("center") % 2 != 0

    def is_end_of_yellow(self):
        return self.seconds_in_phase >= self.yellow_light_dur

    # def is_begining_of_green(self):
    #     return self.seconds_in_phase == 0

    def is_end_of_green(self):
        return self.seconds_in_phase >= self.green_light_dur