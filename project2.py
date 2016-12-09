# Operating Systems Project 2
# Sean Maltby, Solomon Mori, Thomas Wagner

import sys
from collections import deque

t = 0  # Elapsed time (ms)
n = 0  # Number of processes
t_memmove = 1  # Time to move one frame of memory
total_mem = 256  # Maximum amount of memory
mem_per_line = 32  # Memory displayed per line of output

NEXT_FIT = 'Contiguous -- Next-Fit'
BEST_FIT = 'Contiguous -- Best-Fit'
WORST_FIT = 'Contiguous -- Worst-Fit'
NON_CONTIGUOUS = 'Non-contiguous'

class Process:
    def __init__(self, id, size, arrival_times):
        self.id = id
        self.size = size
        self.arrival_times = arrival_times


def main():
    global n
    if len(sys.argv) != 2:
        print >> sys.stderr, 'ERROR: Invalid arguments\nUSAGE: ./a.out <input-file>'
        exit()

    # Open input and output files
    input_name = sys.argv[1]
    input_f = open(input_name, 'r')
    processes = []

    first_line = True
    for line in input_f:
        if not line.startswith("#") and not line.isspace() and len(line) > 0:
            if first_line:
                n = int(line)
                first_line = False
            else:
                args = line.split(" ")
                id = args[0]
                size = int(args[1])
                arrival_times = {}
                for i in range(2, len(args)):
                    args2 = args[i].split('/')
                    arr_time = int(args2[0])
                    run_time = int(args2[1])
                    arrival_times[arr_time] = run_time

                processes.append(Process(id, size, arrival_times))

    simulate(processes, NEXT_FIT)
    print
    simulate(processes, BEST_FIT)
    print
    simulate(processes, WORST_FIT)
    # print
    # simulate(processes, NON_CONTIGUOUS)


def simulate(processes, algorithm):
    global t

    memory = [None] * total_mem
    empty_partitions = deque()
    empty_partitions.append((0, total_mem))

    process_partitions = {}
    process_end_times = {}

    defragment_time = 0
    t = 0
    print "time %dms: Simulator started (%s)" % (t, algorithm)
    while 1:
        # Check arrivals and ends
        for process in processes:
            # Process is done, take it out of memory
            if process.id in process_end_times and process_end_times[process.id] == t:
                # Add the used partition back as an empty partition and delete it's memory
                start, end = process_partitions[process.id]
                for i in range(start, end):
                    memory[i] = None

                # Reverse loop over empty partitions so that if any are deleted, they don't disrupt the loop
                for i in reversed(range(len(empty_partitions))):
                    partition = empty_partitions[i]
                    # Check for adjacencies, and merge with the newly empty partition
                    if start == partition[1]:
                        start = partition[0]
                        del empty_partitions[i]
                    elif end == partition[0]:
                        end = partition[1]
                        del empty_partitions[i]
                del process_partitions[process.id]
                empty_partitions.appendleft((start, end))

                print "time %dms: Process %s removed:" % (t + defragment_time, process.id)
                print_memory(memory)

            # Process has arrived, attempt to add it to memory
            if t in process.arrival_times:
                print "time %dms: Process %s arrived (requires %d frames)" % (
                t + defragment_time, process.id, process.size)
                chosen_partition = choose_partition(algorithm, process, empty_partitions)

                # Could not find an empty partition of sufficient size
                if chosen_partition is None:
                    free = free_memory(empty_partitions)
                    # If there is enough free memory to fit the process, defragment, otherwise, skip the process
                    if free >= process.size:
                        print "time %dms: Cannot place process %s -- starting defragmentation!" % \
                              (t + defragment_time, process.id)
                        frames_moved = defragment(memory, free, process_partitions, empty_partitions)
                        defragment_time += frames_moved * t_memmove
                        print "time %dms: Defragmentation complete (moved %d frames: X, Y, Z)" % \
                              (t + defragment_time, frames_moved)
                        print_memory(memory)

                        # Choose the partition again now that memory has been defragmented
                        chosen_partition = choose_partition(algorithm, process, empty_partitions)
                    else:
                        print "time %dms: Cannot place process %s -- skipped!" % (t + defragment_time, process.id)
                        print_memory(memory)
                        continue

                for i in range(chosen_partition[0], chosen_partition[1]):
                    memory[i] = process.id
                process_partitions[process.id] = chosen_partition
                print "time %dms: Placed process %s:" % (t + defragment_time, process.id)
                print_memory(memory)

                process_end_times[process.id] = t + process.arrival_times[t]

        if len(empty_partitions) > 0 and empty_partitions[0] == (0, total_mem):
            arriving = False
            for process in processes:
                for arrival_time in process.arrival_times:
                    if arrival_time > t:
                        arriving = True
            if not arriving:
                break
        t += 1
    print "time %dms: Simulator ended (%s)" % (t + defragment_time, algorithm)


def choose_partition(algorithm, process, empty_partitions):
    chosen_partition = None
    if algorithm == NEXT_FIT:
        for i in range(len(empty_partitions)):
            start, end = empty_partitions[i]
            partition_size = end - start
            if partition_size > process.size:
                empty_partitions[i] = (start + process.size, end)
                chosen_partition = (start, start + process.size)
                break
            elif partition_size == process.size:
                del empty_partitions[i]
                chosen_partition = (start, end)
                break
    elif algorithm == BEST_FIT or algorithm == WORST_FIT:
        chosen_i = None
        for i in range(len(empty_partitions)):
            start, end = empty_partitions[i]
            partition_size = end - start
            if partition_size >= process.size:
                if chosen_partition is not None:
                    if algorithm == BEST_FIT and chosen_partition[1] - chosen_partition[0] <= partition_size:
                        continue
                    elif algorithm == WORST_FIT and chosen_partition[1] - chosen_partition[0] >= partition_size:
                        continue

                chosen_partition = (start, start + process.size)
                chosen_i = i

        if chosen_partition is not None:
            start, end = empty_partitions[chosen_i]
            partition_size = end - start
            if partition_size > process.size:
                empty_partitions[chosen_i] = (start + process.size, end)
            else:
                del empty_partitions[chosen_i]
    return chosen_partition


def print_memory(memory):
    print '=' * mem_per_line
    for i in range(0, total_mem, mem_per_line):
        for j in range(i, i + mem_per_line):
            if memory[j] is None:
                sys.stdout.write('.')
            else:
                sys.stdout.write(memory[j])
        print
    print '=' * mem_per_line


def free_memory(empty_partitions):
    free = 0
    for start, end in empty_partitions:
        free += end - start
    return free


def defragment(memory, free, process_partitions, empty_partitions):
    # Move frames to the lowest index empty slot in memory, keeping track of how many frames get moved
    frames_moved = 0
    empty = None
    for i in range(total_mem):
        frame = memory[i]
        if frame is not None and empty is not None:
            memory[empty] = frame
            memory[i] = None
            empty += 1
            frames_moved += 1
        elif frame is None and empty is None:
            empty = i

    # Rebuild the process partitions tracker
    process_partitions.clear()
    start = None
    current_frame = None
    for i in range(total_mem):
        frame = memory[i]
        if frame != current_frame:
            if current_frame is not None:
                process_partitions[current_frame] = (start, i)
            start = i
            current_frame = frame

    # Rebuild the empty partitions tracker
    empty_partitions.clear()
    empty_partitions.append((total_mem - free, total_mem))

    return frames_moved


if __name__ == "__main__":
    main()