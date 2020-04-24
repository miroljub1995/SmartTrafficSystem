import sys
s = int(sys.argv[1])



def get_substates(state, num_diff_substates, substates_count):
    res = []
    for i in reversed(range(substates_count)):
        d = state // num_diff_substates ** i
        state = state % num_diff_substates ** i
        res.append(d)
    return res

print(get_substates(s, 6, 4))