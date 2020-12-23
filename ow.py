import cv2
from math import pow, sqrt
from mss import mss
import numpy as np
import time

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
autoshotOn = False
headshotOn = False

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
    
def is_activated_autoshot():
    return win32api.GetAsyncKeyState(0x61) != 0
    
def is_activated_autoshot():
    return win32api.GetAsyncKeyState(0x62) != 0    

def locate_target(targets):
    # compute the center of the contour
    global autoshotOn
    global headshotOn
    
    currentTarget = 1    
    optimalTarget = 1
    lastClosestTarget = 99999
    
    mid = SQUARE_SIZE / 2
    
    while currentTarget < 6:    
        if(len(targets) >= currentTarget + 1)
            moment = cv2.moments(targets[currentTarget])
                     
            cx = int(moment["m10"] / moment["m00"])
            cy = int(moment["m01"] / moment["m00"])
            
            x = -(mid - cx) if cx < mid else cx - mid
            y = -(mid - cy) if cy < mid else cy - mid
            target_size = cv2.contourArea(target)
            distance = sqrt(pow(x, 2) + pow(y, 2))
            
            if(distance < lastClosestTarget){
                lastClosestTarget = distance
                optimalTarget = currentTarget
            }
            currentTarget = currentTarget + 1
    
    # now get priority target
    target = targets[optimalTarget]
    moment = cv2.moments(target)
    
    if moment["m00"] == 0:
        return
            
    x = -(mid - cx) if cx < mid else cx - mid
    y = -(mid - cy) if cy < mid else cy - mid
    
    if autoshotOn:
        (autoshotX, autoshotY, autoshotW, autoshotH) = cv2.boundingRect(target)
        thirdWidth = autoshotW / 3
        thirdHeight = autoshotH / 3
        
        if x >= thirdWidth * -1 and x <= thirdWidth and y >= thirdHeight * -1 and y <= thirdHeight
            flags, hcursor, (currentX,currentY) = win32gui.GetCursorInfo()
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,currentX,currentY,0,0)
            
            randomSleep = float(decimal.Decimal(random.randrange(10, 25))/100)
            sleep(randomSleep)
            
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,currentX,currentY,0,0)
            
            randomSleep = float(decimal.Decimal(random.randrange(05, 12))/100)
            sleep(randomSleep)      
    
    if is_activated():
        if headshotOn:
            (headshotX, headshotY, headshotW, headshotH) = cv2.boundingRect(target)
            quarterHeight = headshotH/4 # get the quarter height to boost up Y        
            y = y-quarterHeight     
        
        target_size = cv2.contourArea(target)
        distance = sqrt(pow(x, 2) + pow(y, 2))
        slope = ((1.0 / 3.0) - 1.0) / (MAX_TARGET_DISTANCE / target_size)
        multiplier = ((MAX_TARGET_DISTANCE - distance) / target_size) * slope + 1
    
        mouse_move(int(x * multiplier), int(y * multiplier * -1))       

    # if __debug__:
        # # draw the contour of the chosen target in green
        # cv2.drawContours(frame, [target], -1, (0, 255, 0), 2)
        # # draw a small white circle at their center of mass
        # cv2.circle(frame, (cx, cy), 7, (255, 255, 255), -1)


# Main lifecycle
while True:
    frame = np.asarray(sct.grab(dimensions))
    contours = viz.process(frame)
    
    print("Autoshot: " + str(autoshotOn))
    print("Headshot: " + str(headshotOn))  
    
    currentTime = int(round(time.time() * 1000))
    if currentTime > startTime + 500:
        if is_activated_autoshot():
            startTime = currentTime
            autoshotOn = not autoshotOn
            print("Autoshot: " + str(autoshotOn))
        if is_activated_headshot():
            startTime = currentTime
            headshotOn = not headshotOn
            print("Headshot: " + str(headshotOn))            

    if len(contours) > 1:
        # contour[0] == bounding window frame
        # contour[1] == closest/largest character
        locate_target(contours)

    # if __debug__:
        # # Green contours are the "character" matches
        # cv2.drawContours(frame, contours, -1, (0, 255, 0), 1)
        # cv2.imshow('res', frame)


sct.close()
cv2.destroyAllWindows()
