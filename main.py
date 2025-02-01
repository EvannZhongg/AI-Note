import multiprocessing
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Note import launch_sticky_note

def main():
    processes = []
    command_queue = multiprocessing.Queue()

    p = multiprocessing.Process(target=launch_sticky_note, args=(None, command_queue))
    p.start()
    processes.append(p)

    while processes:
        try:
            cmd = command_queue.get(timeout=0.5)
            if cmd == "new":
                new_p = multiprocessing.Process(target=launch_sticky_note, args=(None, command_queue))
                new_p.start()
                processes.append(new_p)
        except multiprocessing.queues.Empty:
            pass  # 队列为空，无新指令

        processes = [p for p in processes if p.is_alive()]

    for p in processes:
        if p.is_alive():
            p.terminate()
            p.join()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
