import numpy as np
import traci

def map_lambda(arr, func):
    return np.array([func(x) for x in arr])

class Table:
    def __init__(self, num_of_states, num_of_actions):
        self.q_matrix = np.random.random_sample((num_of_states, num_of_actions))
        self.current_state = 0

    def update(self):
        self.current_state = self.__calculate_current_state()

    def get_next_action(self):
        k = 2
        row = self.q_matrix[self.current_state]
        mapped_row = map_lambda(row, lambda x: k ** x)
        sum_of_elements = np.sum(mapped_row)
        probs = map_lambda(mapped_row, lambda x: x / sum_of_elements)
        selected = np.random.choice(self.q_matrix.shape[1], p=probs)
        return selected

    def __calculate_current_state(self):
        det_pairs = [
            ('e2Detector_r_up_0', 'e2Detector_r_down_0'),
            ('e2Detector_r_up_1', 'e2Detector_r_down_1'),
            ('e2Detector_r_right_0', 'e2Detector_r_left_0'),
            ('e2Detector_r_right_1', 'e2Detector_r_left_1')]

        substates = np.array([self.__det_pair_to_substate(pair, 3) for pair in det_pairs])
        return self.__substates_to_state(substates, 6)

    def __substates_to_state(self, substates, num_substates):
        result = 0
        k = 1
        for ss in reversed(substates):
            result += k * ss
            k *= num_substates
        return result

    def __det_pair_to_substate(self, det_pair, num_intervals):
        d1, d2 = det_pair
        num_cars_d1 = len(traci.lanearea.getLastStepVehicleIDs(d1))
        num_cars_d2 = len(traci.lanearea.getLastStepVehicleIDs(d2))

        interval1 = self.__num_cars_to_intervals(num_cars_d1)
        interval2 = self.__num_cars_to_intervals(num_cars_d2)

        return self.__intervals_to_substate(interval1, interval2, num_intervals)

    def __intervals_to_substate(self, i1, i2, n):
        i, j = i1, i2
        if i > j:
            i, j = j, i
        return int((-(i ** 2) + i * (2 * n - 1) + 2 * j) / 2)

    def __num_cars_to_intervals(self, n):
        if n > 4:
            return 2
        elif n > 0:
            return 1
        else:
            return 0