import random

class Random_decision:
    def __init__(self):
        self.next_phase = 0

    def next_step(self):
        self.next_phase = random.randrange(0, 7, 2)

    def get_predicted_phase(self):
        return self.next_phase
