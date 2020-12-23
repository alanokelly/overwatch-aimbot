import cv2
import pyautogui
from math import pow, sqrt
from mss import mss
import numpy as np
import time
import random

from win32 import win32api
import win32con

import lib.viz as viz

# if __debug__:
    # cv2.namedWindow('res', cv2.WINDOW_NORMAL)

# The size of the window to scan for targets in, in pixels
# i.e. SQUARE_SIZE of 600 => 600 x 600px
SQUARE_SIZE = 600
viz.SQUARE_SIZE = SQUARE_SIZE
startTime = int(round(time.time() * 1000))
startTimeMouseMove = int(round(time.time() * 1000))
autoshotOn = False
headshotOn = False
singleUseHeadshot = False
lastXMove = 0
lastYMove = 0

# The maximum possible pixel distance that a character's center
# can be before locking onto them
TARGET_SIZE = 100
MAX_TARGET_DISTANCE = sqrt(2 * pow(TARGET_SIZE, 2))
viz.TARGET_SIZE = TARGET_SIZE
viz.MAX_TARGET_DISTANCE = MAX_TARGET_DISTANCE

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
def is_activated():
    return win32api.GetAsyncKeyState(0x10) != 0

def locate_target(targets):
    # compute the center of the contour
    global autoshotOn
    global singleUseHeadshot
    global startTimeMouseMove
    global lastXMove
    global lastYMove
    closestDistance = 10000
    closestX = 10000
    closestY = 10000
    closestSplitWidth = 0
    closestSplitHeight = 0    
    
    i = 0
    for target in targets:   
        if target is targets[0]:
            continue
        if i >= 4:
            break
        i = i + 1    
        
        moment = cv2.moments(target)   
        x,y,w,h = cv2.boundingRect(target)    
        if moment["m00"] == 0:
            return
            
        width = w * 1/2
        height = h * 1/3
        
        if headshotOn or singleUseHeadshot:
            adjustY = int(height/4)
        
        cx = int(moment["m10"] / moment["m00"])
        cy = int(moment["m01"] / moment["m00"])

        mid = SQUARE_SIZE / 2
        x = -(mid - cx) if cx < mid else cx - mid
        y = -(mid - cy) if cy < mid else cy - mid

        if headshotOn: 
            y = y - int(h/4)

        target_size = cv2.contourArea(target)
        distance = sqrt(pow(x, 2) + pow(y, 2))
        
        if distance <= closestDistance:
            closestDistance = distance
            closestSplitWidth = width/2
            closestSplitHeight = height/2

            # There's definitely some sweet spot to be found here
            # for the sensitivity in regards to the target's size
            # and distance
            slope = ((1.0 / 3.0) - 1.0) / (MAX_TARGET_DISTANCE / target_size)
            multiplier = ((MAX_TARGET_DISTANCE - distance) / target_size) * slope + 1
            targetX = int(x * multiplier)     
            targetY = int(y * multiplier * -1)
                
    currentTime = int(round(time.time() * 1000))
    
    if is_activated():
        mouse_move(targetX, targetY)
        if autoshotOn and x <= closestSplitWidth and x >= closestSplitWidth*-1 and y <= closestSplitHeight and y >= closestSplitHeight*-1:
            pyautogui.mouseDown()
            pyautogui.mouseUp()
            singleUseHeadshot = False

    # if __debug__:
        # # draw the contour of the chosen target in green
        # cv2.drawContours(frame, [target], -1, (0, 255, 0), 2)
        # # draw a small white circle at their center of mass
        # cv2.circle(frame, (cx, cy), 7, (255, 255, 255), -1)
        
    

# Main lifecycle
while True:
    frame = np.asarray(sct.grab(dimensions))
    contours = viz.process(frame)
    
    currentTime = int(round(time.time() * 1000))
    if currentTime > startTime + 500 and ( win32api.GetAsyncKeyState(0x64) != 0 or win32api.GetAsyncKeyState(0x61) != 0 or win32api.GetAsyncKeyState(0x66) != 0 or win32api.GetAsyncKeyState(0x63) != 0 or win32api.GetAsyncKeyState(0x62) != 0 ) :
        startTime = currentTime
        if(win32api.GetAsyncKeyState(0x64) != 0):
            autoshotOn = True
            print("Autoshot: On")
        if(win32api.GetAsyncKeyState(0x61) != 0):
            autoshotOn = False
            print("Autoshot: Off")
        if(win32api.GetAsyncKeyState(0x66) != 0):
            headshotOn = True
            print("Headshot: On")
        if(win32api.GetAsyncKeyState(0x63) != 0):
            headshotOn = False
            print("Headshot: Off")
        if(win32api.GetAsyncKeyState(0x62) != 0):
            singleUseHeadshot = True 
            headshotOn = False           
            print("Singe Use Headshot (requires Autoshot): On")            
                    
    # if currentTime > startTime + 500 and win32api.GetAsyncKeyState(0x52):
        # startTime = currentTime
        # randomY = random.randint(-8, 8)
        # win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 600, randomY, 0, 0)
        
    # For now, just attempt to lock on to the largest contour match
    if len(contours) > 1:
        # contour[0] == bounding window frame
        # contour[1] == closest/largest character
        locate_target(contours)
        time.sleep(0.001)

    # if __debug__:
        # # Green contours are the "character" matches
        # cv2.drawContours(frame, contours, -1, (0, 255, 0), 1)
        # cv2.imshow('res', frame)


sct.close()
cv2.destroyAllWindows()
