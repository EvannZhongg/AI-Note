import multiprocessing
import time
from StickyNote import launch_sticky_note

def main():
    processes = []
    # 创建用于通信的命令队列（所有便笺窗口共享同一个队列）
    command_queue = multiprocessing.Queue()

    # 启动第一个便笺窗口
    p = multiprocessing.Process(target=launch_sticky_note, args=(None, command_queue))
    p.start()
    processes.append(p)

    # 主进程循环：不断检查命令队列，并清理已退出的进程
    while True:
        # 处理命令队列中的请求
        while not command_queue.empty():
            cmd = command_queue.get()
            if cmd == "new":
                # 收到新建便笺的请求，启动一个新的便笺进程
                new_p = multiprocessing.Process(target=launch_sticky_note, args=(None, command_queue))
                new_p.start()
                processes.append(new_p)
        # 清理已退出的进程
        processes = [p for p in processes if p.is_alive()]
        # 当没有任何便笺窗口进程存活时，退出主循环（程序结束）
        if not processes:
            break
        time.sleep(0.5)

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows 平台需要此行
    main()
