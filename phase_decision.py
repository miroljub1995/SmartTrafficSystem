


class Q_learning_decision:
        def __init__(self, table):
            self.table = table

        def next_phase(self):
            next_action = self.table.predicted_action
            current_phase = next_action * 2
            return current_phase