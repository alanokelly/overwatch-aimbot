import cv2

import getopt
from math import pow, sqrt
from mss import mss
from time import time, sleep
import numpy as np
import threading
import datetime
from win32 import win32api
import win32con
import lib.viz as viz

toggleMode = False
debugMode = False

options = "dt"
long_options = ["debug", "toggleMode"]

# Parsing argument 
arguments, values = getopt.getopt(argumentList, options, long_options) 
    
# checking each argument 
for currentArgument, currentValue in arguments:            
    if currentArgument in ("-d", "--debug"): 
        debugMode = True          
    elif currentArgument in ("-t", "--toggle"): 
        toggleMode = True

if debugMode:
    cv2.namedWindow('res', cv2.WINDOW_NORMAL)

# The size of the window to scan for targets in, in pixels
# i.e. SQUARE_SIZE of 600 => 600 x 600px
SQUARE_SIZE = 600
viz.SQUARE_SIZE = SQUARE_SIZE

# The maximum possible pixel distance that a character's center
# can be before locking onto them
TARGET_SIZE = 100
MAX_TARGET_DISTANCE = sqrt(2 * pow(TARGET_SIZE, 2))
viz.TARGET_SIZE = TARGET_SIZE
viz.MAX_TARGET_DISTANCE = MAX_TARGET_DISTANCE

# Variables for tracking and updating state
lastKeypressTimeUpdate = time()
isActive = False
lastProcessingDate = datetime.datetime.now()

# Create an instance of mss to capture the selected window square
sct = mss()

# Use the first monitor, change to desired monitor number
dimensions = sct.monitors[1]

# Compute the center square of the screen to parse
dimensions['left'] = int((dimensions['width'] / 2) - (SQUARE_SIZE / 2))
dimensions['top'] = int((dimensions['height'] / 2) - (SQUARE_SIZE / 2))
dimensions['width'] = SQUARE_SIZE
dimensions['height'] = SQUARE_SIZE


# Calls the Windows API to simulate mouse movement events that are sent to OW
def mouse_move(x, y):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)


# Determines if the Caps Lock key is pressed in or not
def is_activated_activePressMode():
    return win32api.GetAsyncKeyState(0x14) != 0


def is_activated_toggleMode():
    return isActive and (win32api.GetAsyncKeyState(0x01) != 0 or win32api.GetAsyncKeyState(0x02) != 0)


# compute the center of the contour
def compute_x_and_y(target):
    moment = cv2.moments(target)
    if moment["m00"] == 0:
        return

    cx = int(moment["m10"] / moment["m00"])
    cy = int(moment["m01"] / moment["m00"])

    mid = SQUARE_SIZE / 2
    x = -(mid - cx) if cx < mid else cx - mid
    y = -(mid - cy) if cy < mid else cy - mid

    target_size = cv2.contourArea(target)
    distance = sqrt(pow(x, 2) + pow(y, 2))

    # There's definitely some sweet spot to be found here
    # for the sensitivity in regards to the target's size
    # and distance
    slope = ((1.0 / 3.0) - 1.0) / (MAX_TARGET_DISTANCE / target_size)
    multiplier = ((MAX_TARGET_DISTANCE - distance) / target_size) * slope + 1

    returnX = int(x * multiplier)
    returnY = int(y * multiplier) * -1 
    return returnX, returnY, cx, cy


# move the mouse towards the closest target in our list of targets
def locate_target(targets):  
    #some defaults to use before running our search.
    shortestDistance = 10000000
    targetMoveX = 0
    targetMoveY = 0
    targetCX = 0
    targetCY = 0
    targetId = 1

    #get array length, remove one for the first target (bounding box)
    arrayLength = len(targets) - 1
    if arrayLength > 10:
        arrayLength = 10

    for i in range(1, arrayLength):
        x, y, cx, cy = compute_x_and_y(targets[i])
        distance = math.sqrt(pow(x, 2) + pow(y, 2))
        if distance < shortestDistance:
            shortestDistance = distance
            targetId = i
            targetMoveX = x
            targetMoveY = y
            targetCenterX = cx
            targetCenterY = cy

    if (toggleMode and is_activated_toggleMode()) or (not(toggleMode) and is_activated_activePressMode()):
        mouse_move(targetMoveX, targetMoveY)

    if debugMode:
        # draw the contour of the chosen target in green
        cv2.drawContours(frame, [targets[targetId]], -1, (0, 255, 0), 2)
        # draw a small white circle at their center of mass
        cv2.circle(frame, (targetCenterX, targetCenterY), 5, (255, 255, 255), -1) 


# Main lifecycle
frame = np.asarray(sct.grab(dimensions))
contours = viz.process(frame)

while True:
    if toggleMode: 
        currentProcessingDate = datetime.datetime.now()
        if (currentProcessingDate - lastProcessingDate).microseconds >= 500:
            frame = np.asarray(sct.grab(dimensions))
            contours = viz.process(frame)
            lastProcessDate = currentProcessingDate

        if win32api.GetAsyncKeyState(0x10) != 0:
            currentKeypressTime = time()
            if (currentKeypressTime - lastKeypressTimeUpdate) >= 1:
                isActive = not(isActive)
                print(isActive)
                lastKeypressTimeUpdate = time()

    # For now, just attempt to lock on to the largest contour match
    if len(contours) > 1:
        # contour[0] == bounding window frame
        # contour[1] == closest/largest character
        locate_target(contours)

    if debugMode:
        # Green contours are the "character" matches
        cv2.drawContours(frame, contours, -1, (0, 255, 0), 1)
        cv2.imshow('res', frame)

    # Press `q` to stop the program
    if cv2.waitKey(25) & 0xFF == ord("q"):
            break

sct.close()
cv2.destroyAllWindows()
