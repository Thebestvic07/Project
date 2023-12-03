from threading import Timer
from communication import *
from data import *
from tdmclient import ClientAsync, aw

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

def DataMes(data, thymio):
    thymio.read_variables()
    data += "\n{:4d} , {:4d}".format(thymio.motors.left, thymio.motors.right)

Ts = 0.1
data = '"Motor Left", "Motor Right",'
thymio = Thymio()

rt = RepeatedTimer(Ts, thymio.read_variables(), data, thymio)

try : 
    aw(thymio.client.sleep(5))
    thymio.set_variable(Motors(0,0))
    aw(thymio.client.sleep(10))

finally:
        rt.stop() # better in a try/finally block to make sure the program ends!
        thymio.set_variable(Motors(0,0))
        with open("data.txt", "w+") as file:
            file.write(data)