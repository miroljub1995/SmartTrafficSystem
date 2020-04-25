
class Round_robin_decision:
    def __init__(self):
        self.next_phase = 0

    def next_step(self):
        self.next_phase = (self.next_phase + 2) % 8

    def get_predicted_phase(self):
        return self.next_phase
