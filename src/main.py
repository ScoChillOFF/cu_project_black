import os

from multiprocessing import Process


def run_script(script_name):
    os.system(f"python {script_name}")


if __name__ == '__main__':
    process1 = Process(target=run_script, args=('app/app.py',))
    process2 = Process(target=run_script, args=('bot/bot.py',))

    process1.start()
    process2.start()

    process1.join()
    process2.join()