import numpy as np
import traci

class Table:
    TABLE_SAVING_INTERVAL = 20
    NUM_CHUNKS_IN_LEARNING_PERIOD = 10

    def __init__(self, num_of_states, num_of_actions, out_path, detectors):
        self.q_matrix = np.zeros((num_of_states, num_of_actions))
        self.out_path = out_path
        self.detectors = detectors
        self.state = 0
        self.num_learned = 0
        self.__update_current()
        self.prev_state = None
        self.prev_action = None
        self.prev_eval = 0
        self.sum_of_cars_prev = self.detectors.num_cars + 0.5
        self.chunks = []

    def __save_previous(self):
        self.prev_state = self.state
        self.prev_action = self.predicted_action

    def __update_current(self):
        self.__update_current_state()
        self.predicted_action = self.__get_next_action()

    def next_step(self):
        self.__save_previous()
        self.__update_current()

        curr_eval = self.detectors.num_passed_light / self.sum_of_cars_prev
        reward = curr_eval - self.prev_eval
        self.chunks.append((self.prev_state, self.prev_action, reward, self.state))
        self.prev_eval = curr_eval
        if len(self.chunks) == self.NUM_CHUNKS_IN_LEARNING_PERIOD:
            self.learn(self.chunks)
            self.chunks = []

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
        n = 20
        gamma = 0.9
        num_chunks = len(chunks)
        loss = 0.0
        for chunk in reversed(chunks):
            s, a, r, s_prim = chunk
            old_val = self.q_matrix[s, a]
            old_max = np.argmax(self.q_matrix[s])
            self.q_matrix[s, a] += 1. / n * (r + gamma * np.amax(self.q_matrix[s_prim]) - self.q_matrix[s, a])
            loss += abs(old_val - self.q_matrix[s, a])
            new_max = np.argmax(self.q_matrix[s])
            if old_max != new_max:
                print("Max changed")
        print("Loss: {}".format(loss / num_chunks))
        self.save_if_needed()

    def get_predicted_phase(self):
        next_action = self.predicted_action
        current_phase = next_action * 2
        return current_phase

    def save_if_needed(self):
        self.num_learned += 1
        if self.num_learned >= self.TABLE_SAVING_INTERVAL:
            self.save(self.out_path)
            self.num_learned = 0

    def __update_current_state(self):
        det_pairs = [
            ('e2Detector_r_up_0', 'e2Detector_r_down_0'),
            ('e2Detector_r_up_1', 'e2Detector_r_down_1'),
            ('e2Detector_r_right_0', 'e2Detector_r_left_0'),
            ('e2Detector_r_right_1', 'e2Detector_r_left_1')]

        substates = np.array([self.__det_pair_to_substate(pair, 3) for pair in det_pairs])
        self.state = self.__substates_to_state(substates, 6)

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
        if n >= 4:
            return 2
        elif n > 0:
            return 1
        else:
            return 0