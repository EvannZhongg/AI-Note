import multiprocessing
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from Note import launch_sticky_note

def main():
    processes = []
    command_queue = multiprocessing.Queue()

    # 第一个便笺
    p = multiprocessing.Process(target=launch_sticky_note, args=(None, command_queue))
    p.start()
    processes.append(p)

    while processes:
        try:
            cmd = command_queue.get(timeout=0.5)
            if cmd == "new":
                # 默认新便笺(无位置)
                new_p = multiprocessing.Process(target=launch_sticky_note, args=(None, command_queue))
                new_p.start()
                processes.append(new_p)

            elif isinstance(cmd, tuple) and cmd[0] == "new_with_xy":
                # 指定位置的新便笺
                x = cmd[1]
                y = cmd[2]
                new_p = multiprocessing.Process(
                    target=launch_sticky_note,
                    args=(None, command_queue, x, y)
                )
                new_p.start()
                processes.append(new_p)

            # ============ 新增：open_with_xy 命令处理 ============
            elif isinstance(cmd, tuple) and cmd[0] == "open_with_xy":
                note_id = cmd[1]
                x = cmd[2]
                y = cmd[3]
                new_p = multiprocessing.Process(
                    target=launch_sticky_note,
                    args=(note_id, command_queue, x, y)
                )
                new_p.start()
                processes.append(new_p)

        except multiprocessing.queues.Empty:
            pass

        # 清理退出的进程
        processes = [p for p in processes if p.is_alive()]

    # 收尾
    for p in processes:
        if p.is_alive():
            p.terminate()
            p.join()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
