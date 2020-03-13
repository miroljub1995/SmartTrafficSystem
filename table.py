import numpy as np
import traci

class Table:
    def __init__(self, num_of_states, num_of_actions):
        self.q_matrix = np.zeros((num_of_states, num_of_actions))
        self.next_step()

    def next_step(self):
        self.state = self.__calculate_current_state()
        self.predicted_action = self.__get_next_action()

    def save(self, path):
        np.savetxt(path, self.q_matrix, fmt="%+5.15f")
        print("Table saved")

    def load(self, path):
        self.q_matrix = np.loadtxt(path)
        self.next_step()

    def __get_next_action(self):
        random_rate = 0.9
        probs = np.full(self.q_matrix.shape[1], (1 - random_rate) / (self.q_matrix.shape[1] - 1.))
        row = self.q_matrix[self.state]
        max_index = np.argmax(row)
        probs[max_index] = random_rate

        # k = 1.06
        # mapped_row = k ** row
        # sum_of_elements = np.sum(mapped_row)
        # probs = mapped_row / sum_of_elements
        selected = np.random.choice(self.q_matrix.shape[1], p=probs)
        return selected

    def learn(self, chunks):
        n = 4
        gama = 0.5
        num_chunks = len(chunks)
        loss = 0.0
        for chunk in reversed(chunks):
            s, a, r, s_prim = chunk
            old_val = self.q_matrix[s, a]
            self.q_matrix[s, a] += 1. / n * (r + gama * np.amax(self.q_matrix[s_prim]) - self.q_matrix[s, a])
            loss += abs(old_val - self.q_matrix[s, a])
        print("Loss: {}".format(loss / num_chunks))


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