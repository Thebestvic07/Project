## Lib import
from timeit import default_timer as timer
from tdmclient import ClientAsync, aw
import time
import cv2 as cv
import keyboard
import threading

from Codes.utils.data import *
from Codes.utils.communication import *
from Codes.kalman_filter import *
from Codes.motion_control import *
from Codes.obstacle_avoidance import *
from Codes.camera import *
from Codes.map import *
 

## Constants
GRID_RES = 25
TIMESTEP = 0.1
SIZE_THYM = 2.0  #size of thymio in number of grid
LOST_TRESH = 10 #treshold to be considered lost
REACH_TRESH = 3 #treshhold to reach current checkpoint
GLOBAL_PLANNING = True


## Functions

def run_camera(mes_pos : Robot, mes_goal: Point):
    '''
    Function that updates the global Mes_Robot variable with camera data every 0.1 seconds

    '''
    cap = cv2.VideoCapture(0)

    while True:
        if cap.isOpened() == False:
            print("Error : video stream closed")
        else:
            frame = cap.read()[1]
    
            frame, arucos, robot_pos, angle = show_robot(frame, grid_resolution)
            goal_pos = get_goal_pos(arucos, grid_resolution)

            if goal_pos != (0, 0):
                mes_goal = Point(goal_pos[0], goal_pos[1])

            mes_pos.update(Robot(Point(robot_pos[0], robot_pos[1]), angle))
            mes_goal.update(Point(goal_pos[0], goal_pos[1]))

            cv2.imshow("Video Stream", frame)

            print(f'Robot position: {robot_pos} and angle: {angle}')
            print(f'Goal position: {goal_pos}')
            
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        time.sleep(0.1)


def update_thymio(thymio : Thymio):
    '''
    Function that updates the variables of the thymio object (sensor data) every 0.1 seconds

    '''
    while True:
        thymio.read_variables()

        time.sleep(0.1)


## Main

if __name__ == "__main__":
    # Init Thymio
    thymio = Thymio()
    thymio.start()

    # Init map
    map = Map([], [], None)
    fram, builtmap = apply_grid_to_camera(GRID_RES)
    map.update(builtmap, frame)

    # Init variables
    car = Robot(Point(0,0), 0)
    goal = Point(0,0)
    env = Environment(car, map, goal)

    # Launch Threads
    camera_thread = threading.Thread(target=run_camera, args=(car, goal,), daemon=True)
    camera_thread.start()

    thymio_thread = threading.Thread(target=update_thymio, args=(thymio,), daemon=True)
    thymio_thread.start()

    # Init Kalman filter
    kalman = Kalman(car)

    # Init timer
    start = time.time()
    current = start

    # Init loop
    while True:
        # Update motion every 0.1 seconds
        if current - start < TIMESTEP:
            time.sleep(0.01)
            current = time.time()
            continue

        # Update env with Kalman

        # Compute path if needed
        if GLOBAL_PLANNING:
            path = calculate_path(env, SIZE_THYM, False)
            GLOBAL_PLANNING = False
        
        dist_to_checkpoint = car.position.dist(path[0])

        if dist_to_checkpoint >= LOST_TRESH:
            GLOBAL_PLANNING = True

        if dist_to_checkpoint <= REACH_TRESH:
            path.pop(0)       

        # Update mes_env
        env.update(Environment(car, map, goal))

        # Update kalman
        kalman.kalman_filter(thymio.input, thymio.speed, env.robot.position)

        # Update motion
        motion.update(env, kalman.robot)

        # Update avoid
        avoid.update(env, kalman.robot)

        # Update thymio
        thymio.set_variable(motion.output)

        # Check if goal reached
        if env.robot.position.dist(env.goal) < 0.1:
            print("Goal reached !")
            break

        # Check if escape key pressed
        if keyboard.is_pressed('esc'):
            break

    # Stop Thymio
    thymio.stop()
