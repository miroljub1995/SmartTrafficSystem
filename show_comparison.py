
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

def check_folders():
    if not os.path.exists('out'):
        print('out folder does not exist')
        sys.exit(1)
    if not os.path.exists('out/q'):
        print('out/q folder does not exist')
        sys.exit(1)
    if not os.path.exists('out/r'):
        print('out/r folder does not exist')
        sys.exit(1)
    if not os.path.exists('out/rr'):
        print('out/rr folder does not exist')
        sys.exit(1)

def average_in_partitions(arr):
    arr_reshaped = np.reshape(arr, (2, -1, 137))
    arr_reshaped = np.average(arr_reshaped, axis=2)
    return arr_reshaped

def show_awt():
    check_folders()
    awt_q = np.loadtxt('out/q/awt.txt')
    awt_r = np.loadtxt('out/r/awt.txt')
    awt_rr = np.loadtxt('out/rr/awt.txt')

    plt.plot(awt_r[1], awt_r[0], color='r', label='random')
    plt.plot(awt_rr[1], awt_rr[0], color='g', label='robin round')
    plt.plot(awt_q[1], awt_q[0], color='b', label='q-learning')

    plt.xlabel('time(s)')
    plt.ylabel('Awerage waiting time(s)')
    plt.legend()

    plt.figure()
    awt_q_reduced = average_in_partitions(awt_q)
    awt_r_reduced = average_in_partitions(awt_r)
    awt_rr_reduced = average_in_partitions(awt_rr)

    plt.plot(awt_r_reduced[1], awt_r_reduced[0], color='r', label='random')
    plt.plot(awt_rr_reduced[1], awt_rr_reduced[0], color='g', label='robin round')
    plt.plot(awt_q_reduced[1], awt_q_reduced[0], color='b', label='q-learning')

    plt.xlabel('time(s)')
    plt.ylabel('Awerage waiting time(s)')
    plt.legend()

    plt.show()

def main():
    show_awt()

main()
