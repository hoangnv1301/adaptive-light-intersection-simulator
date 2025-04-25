# LAG
# NO. OF VEHICLES IN SIGNAL CLASS
# stops not used
# DISTRIBUTION
# BUS TOUCHING ON TURNS
# Distribution using python class

# *** IMAGE XY COOD IS TOP LEFT
import random
import math
import time
import threading
# from vehicle_detection import detection
import pygame
import sys
import os
import json
import multiprocessing
from multiprocessing.connection import Connection
from http.server import HTTPServer, BaseHTTPRequestHandler
import datetime

# Thêm biến để kiểm tra xem có đang chạy ở chế độ đồng bộ không
SYNC_VEHICLES = 'SYNC_VEHICLES' in os.environ and os.environ['SYNC_VEHICLES'] == '1'
adaptive_pipe = None

# Khởi tạo pipe nếu đang chạy ở chế độ đồng bộ
if SYNC_VEHICLES:
    try:
        pipe_fd = int(os.environ['ADAPTIVE_PIPE_FD'])
        adaptive_pipe = Connection(pipe_fd)
        print("Adaptive simulator: Connected to vehicle generator pipe")
    except (KeyError, ValueError) as e:
        print(f"Error setting up pipe: {e}")
        SYNC_VEHICLES = False

# options={
#    'model':'./cfg/yolo.cfg',     #specifying the path of model
#    'load':'./bin/yolov2.weights',   #weights
#    'threshold':0.3     #minimum confidence factor to create a box, greater than 0.3 good
# }

# tfnet=TFNet(options)    #READ ABOUT TFNET

# Default values of signal times
defaultRed = 150
defaultYellow = 5
defaultGreen = 20
defaultMinimum = 10
defaultMaximum = 60

# Add accident simulation variables
accidentOccurred = False
accidentDirection = -1  # -1 means no accident
accidentTime = 0
accidentDuration = 60  # Accident lasts for 60 seconds
accidentBlinkTimer = 0
accidentBlinkInterval = 0.5  # Blink every half second

signals = []
noOfSignals = 4
simTime = 300       # change this to change time of simulation
timeElapsed = 0

currentGreen = 0   # Indicates which signal is green
nextGreen = (currentGreen+1)%noOfSignals
currentYellow = 0   # Indicates whether yellow signal is on or off 

# Average times for vehicles to pass the intersection
carTime = 2
bikeTime = 1
rickshawTime = 2.25 
busTime = 2.5
truckTime = 2.5

# Count of cars at a traffic signal
noOfCars = 0
noOfBikes = 0
noOfBuses =0
noOfTrucks = 0
noOfRickshaws = 0
noOfLanes = 2

# Red signal time at which cars will be detected at a signal
detectionTime = 5

speeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'rickshaw':2, 'bike':2.5}  # average speeds of vehicles

# Coordinates of start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'rickshaw', 4:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]

# Move vehicle count coordinates even further to the left/right to avoid any overlap
vehicleCountCoods = [(300,210),(1430,210),(1430,550),(300,550)]
vehicleCountTexts = ["0", "0", "0", "0"]

# Move waiting vehicle counts to positions that don't overlap with timers
waitingVehicleCoods = [(300,240),(1430,240),(1430,580),(300,580)]
waitingVehicleTexts = ["0", "0", "0", "0"]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stops = {'right': [580,580,580], 'down': [320,320,320], 'left': [810,810,810], 'up': [545,545,545]}

mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
rotationAngle = 3

# Gap between vehicles
gap = 15    # stopping gap
gap2 = 15   # moving gap

pygame.init()
simulation = pygame.sprite.Group()

# Add variables for tracking additional metrics
maxWaitingTime = {0: 0, 1: 0, 2: 0, 3: 0}  # Max waiting time for each direction
currentWaitingTime = {0: 0, 1: 0, 2: 0, 3: 0}  # Current waiting time for each direction
maxQueueLength = {0: 0, 1: 0, 2: 0, 3: 0}  # Max queue length for each direction
totalWaitingTime = {0: 0, 1: 0, 2: 0, 3: 0}  # Total waiting time for each direction
vehiclesProcessed = {0: 0, 1: 0, 2: 0, 3: 0}  # Vehicles processed in each direction
trafficEfficiency = {0: 0, 1: 0, 2: 0, 3: 0}  # Traffic processing efficiency per direction
lastUpdateTime = time.time()  # Last time metrics were updated
metricsUpdateInterval = 1.0  # Update metrics every second

# Performance stats history for graphing
performanceHistory = {
    'timestamps': [],
    'totalVehicles': [],
    'waitingTimes': {0: [], 1: [], 2: [], 3: []},
    'queueLengths': {0: [], 1: [], 2: [], 3: []},
    'throughput': []
}

# Add direction display names
directionDisplay = {
    'right': 'LEFT',     # Bên phải của màn hình thực tế là LEFT
    'left': 'RIGHT',     # Bên trái của màn hình thực tế là RIGHT
    'up': 'BOTTOM',      # Phía trên của màn hình thực tế là BOTTOM
    'down': 'TOP'        # Phía dưới của màn hình thực tế là TOP
}

# Add function to update metrics
def updateMetrics():
    global maxWaitingTime, currentWaitingTime, maxQueueLength, trafficEfficiency, lastUpdateTime, performanceHistory
    
    current_time = time.time()
    if current_time - lastUpdateTime < metricsUpdateInterval:
        return
    
    lastUpdateTime = current_time
    
    # Add current timestamp to history
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    performanceHistory['timestamps'].append(timestamp)
    
    # Calculate total vehicles
    totalVehiclesPassed = 0
    for i in range(noOfSignals):
        totalVehiclesPassed += vehicles[directionNumbers[i]]['crossed']
    
    performanceHistory['totalVehicles'].append(totalVehiclesPassed)
    
    # Update per-direction metrics
    for i in range(noOfSignals):
        direction = directionNumbers[i]
        direction_idx = i
        
        # Calculate current queue length
        currentQueueLength = 0
        for lane in range(3):
            for vehicle in vehicles[direction][lane]:
                if vehicle.crossed == 0:
                    currentQueueLength += 1
        
        # Update max queue length if needed
        if currentQueueLength > maxQueueLength[direction_idx]:
            maxQueueLength[direction_idx] = currentQueueLength
        
        # Record queue length history
        performanceHistory['queueLengths'][direction_idx].append(currentQueueLength)
        
        # Calculate current waiting time for vehicles at this signal
        longestWait = 0
        totalWaitingVehicles = 0
        for lane in range(3):
            for vehicle in vehicles[direction][lane]:
                if vehicle.waiting and vehicle.waitStartTime is not None:
                    waitTime = time.time() - vehicle.waitStartTime + vehicle.totalWaitTime
                    if waitTime > longestWait:
                        longestWait = waitTime
                    totalWaitingVehicles += 1
        
        currentWaitingTime[direction_idx] = longestWait
        
        # Update max waiting time if needed
        if longestWait > maxWaitingTime[direction_idx]:
            maxWaitingTime[direction_idx] = longestWait
        
        # Record waiting time history
        performanceHistory['waitingTimes'][direction_idx].append(longestWait)
        
        # Calculate traffic efficiency (vehicles processed per second of green time)
        if signals[i].totalGreenTime > 0:
            trafficEfficiency[direction_idx] = vehicles[direction]['crossed'] / signals[i].totalGreenTime
        
    # Calculate overall throughput (vehicles per second)
    if timeElapsed > 0:
        throughput = totalVehiclesPassed / timeElapsed
        performanceHistory['throughput'].append(throughput)
    
    # Keep only the last 60 data points for graphs (1 minute of data)
    max_history = 60
    if len(performanceHistory['timestamps']) > max_history:
        performanceHistory['timestamps'] = performanceHistory['timestamps'][-max_history:]
        performanceHistory['totalVehicles'] = performanceHistory['totalVehicles'][-max_history:]
        performanceHistory['throughput'] = performanceHistory['throughput'][-max_history:]
        
        for i in range(noOfSignals):
            performanceHistory['waitingTimes'][i] = performanceHistory['waitingTimes'][i][-max_history:]
            performanceHistory['queueLengths'][i] = performanceHistory['queueLengths'][i][-max_history:]

# Add function to draw advanced metrics
def drawAdvancedMetrics(screen, font):
    # Define panel dimensions and position
    panel_width = 600  # Final width increase
    panel_height = 200 # Keep height
    panel_x = 820      # Adjusted position slightly left again
    panel_y = 80       # Keep y position

    # Background for metrics panel
    metrics_bg = pygame.Surface((panel_width, panel_height))
    metrics_bg.fill((0, 0, 0))
    metrics_bg.set_alpha(200)  # Semi-transparent
    screen.blit(metrics_bg, (panel_x, panel_y))

    # Define column x-coordinates relative to panel_x with more spacing
    col_direction = panel_x + 15
    col_max_wait = panel_x + 90  # Adjusted spacing
    col_queue = panel_x + 230     # Adjusted spacing
    col_efficiency = panel_x + 330  # Adjusted spacing
    col_avg_wait = panel_x + 450    # Pushed further right
    # Estimate column widths for centering
    col_max_wait_width = col_queue - col_max_wait
    col_queue_width = col_efficiency - col_queue
    col_efficiency_width = col_avg_wait - col_efficiency
    col_avg_wait_width = (panel_x + panel_width) - col_avg_wait

    # Define row y-coordinates relative to panel_y
    row_title = panel_y + 10
    row_header = panel_y + 40
    row_data_start = panel_y + 70
    row_spacing = 30
    row_totals = panel_y + 180 # Position for total vehicles/throughput - Moved down 10px

    # Title
    title_text = "ADVANCED METRICS (ADAPTIVE)" # Assuming this file is adaptive, adjust if needed
    title_render = font.render(title_text, True, (255, 255, 0))
    title_rect = title_render.get_rect(center=(panel_x + panel_width // 2, row_title + 10))
    screen.blit(title_render, title_rect)

    # Headers
    headers = ["Dir", "Max Wait (s)", "Queue", "Efficiency", "Avg Wait (s)"]
    header_coords = [col_direction, col_max_wait, col_queue, col_efficiency, col_avg_wait]
    for i, header in enumerate(headers):
        header_render = font.render(header, True, (255, 255, 255))
        screen.blit(header_render, (header_coords[i], row_header))

    # Direction labels and Data
    directions_display = ["LEFT", "TOP", "RIGHT", "BOTTOM"] # Use display names
    for i in range(4):
        row_y = row_data_start + i * row_spacing

        # Direction (Left-aligned)
        dir_text = font.render(directions_display[i], True, (255, 255, 255))
        screen.blit(dir_text, (col_direction, row_y))

        # Max waiting time (Center-aligned)
        max_wait_val = maxWaitingTime[i]
        color = (0, 255, 0) if max_wait_val < 30 else ((255, 255, 0) if max_wait_val < 60 else (255, 0, 0))
        max_wait_render = font.render(f"{max_wait_val:.1f}", True, color)
        max_wait_rect = max_wait_render.get_rect(centerx=col_max_wait + col_max_wait_width // 2, y=row_y)
        screen.blit(max_wait_render, max_wait_rect)

        # Current queue length (Center-aligned)
        queue_length = 0
        direction = directionNumbers[i]
        for lane in range(3):
            for vehicle in vehicles[direction][lane]:
                if vehicle.crossed == 0:
                    queue_length += 1
        color = (0, 255, 0) if queue_length < 10 else ((255, 255, 0) if queue_length < 20 else (255, 0, 0))
        queue_render = font.render(f"{queue_length}", True, color)
        queue_rect = queue_render.get_rect(centerx=col_queue + col_queue_width // 2, y=row_y)
        screen.blit(queue_render, queue_rect)

        # Efficiency (Center-aligned)
        eff_val = trafficEfficiency[i]
        eff_text = f"{eff_val:.2f}" if eff_val > 0 else "0.00"
        eff_render = font.render(eff_text, True, (0, 255, 255))
        eff_rect = eff_render.get_rect(centerx=col_efficiency + col_efficiency_width // 2, y=row_y)
        screen.blit(eff_render, eff_rect)

        # Avg waiting time (Center-aligned)
        avg_wait_val = 0.0
        if vehiclesProcessed[i] > 0:
            avg_wait_val = totalWaitingTime[i] / vehiclesProcessed[i]
            color = (0, 255, 0) if avg_wait_val < 15 else ((255, 255, 0) if avg_wait_val < 30 else (255, 0, 0))
            avg_text = f"{avg_wait_val:.1f}"
        else:
            color = (0, 255, 0)
            avg_text = "0.0"
        avg_render = font.render(avg_text, True, color)
        avg_rect = avg_render.get_rect(centerx=col_avg_wait + col_avg_wait_width // 2, y=row_y)
        screen.blit(avg_render, avg_rect)

    # Draw overall efficiency metrics at the bottom of the panel
    total_vehicles_passed = 0
    for i in range(noOfSignals):
        total_vehicles_passed += vehicles[directionNumbers[i]]['crossed']

    total_vehicles_render = font.render(f"Total passed: {total_vehicles_passed}", True, (255, 255, 255))
    # Position Total passed near the left
    screen.blit(total_vehicles_render, (col_direction, row_totals))

    if timeElapsed > 0:
        throughput_val = total_vehicles_passed / timeElapsed
        throughput_text = f"Throughput: {throughput_val:.2f} veh/s"
    else:
        throughput_text = "Throughput: 0.00 veh/s"
    throughput_render = font.render(throughput_text, True, (255, 255, 255))
    # Position throughput aligned with the Efficiency column
    screen.blit(throughput_render, (col_efficiency, row_totals))

class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "30"
        self.totalGreenTime = 0
        
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        self.waiting = False  # Whether vehicle is waiting at signal
        self.waitStartTime = None  # When the vehicle started waiting
        self.totalWaitTime = 0  # Total time spent waiting
        vehicles[direction][lane].append(self)
        # self.stop = stops[direction][lane]
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

    
        if(direction=='right'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):    # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().width - gap         # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap
            else:
                self.stop = defaultStop[direction]
            # Set new starting and stopping coordinate
            temp = self.currentImage.get_rect().width + gap    
            x[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='left'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] += temp
            stops[direction][lane] += temp
        elif(direction=='down'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='up'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] += temp
            stops[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.currentImage, (self.x, self.y))

    def move(self):
        # Check if vehicle starts waiting
        isWaiting = False
        direction_index = self.direction_number # Get the index (0-3) for metrics

        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.currentImage.get_rect().width>stopLines[self.direction]):   # if the image has crossed stop line now
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                # Update Avg Wait metrics if the vehicle waited at all
                if self.totalWaitTime > 0:
                    vehiclesProcessed[direction_index] += 1
                    totalWaitingTime[direction_index] += self.totalWaitTime
                self.waiting = False # Ensure waiting is false after crossing
                self.waitStartTime = None
            if(self.willTurn==1):
                if(self.crossed==0 or self.x+self.currentImage.get_rect().width<mid[self.direction]['x']):
                    if((self.x+self.currentImage.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x += self.speed
                    else:
                        isWaiting = True
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if(self.rotateAngle==90):
                            self.turned = 1
                            # path = "images/" + directionNumbers[((self.direction_number+1)%noOfSignals)] + "/" + self.vehicleClass + ".png"
                            # self.x = mid[self.direction]['x']
                            # self.y = mid[self.direction]['y']
                            # self.image = pygame.image.load(path)
                    else:
                        if(self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2)):
                            self.y += self.speed
                        else:
                            isWaiting = True
            else: 
                if((self.x+self.currentImage.get_rect().width<=self.stop or self.crossed == 1 or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x += self.speed  # move the vehicle
                else:
                    isWaiting = True

        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.currentImage.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                # Update Avg Wait metrics if the vehicle waited at all
                if self.totalWaitTime > 0:
                    vehiclesProcessed[direction_index] += 1
                    totalWaitingTime[direction_index] += self.totalWaitTime
                self.waiting = False # Ensure waiting is false after crossing
                self.waitStartTime = None
            if(self.willTurn==1):
                if(self.crossed==0 or self.y+self.currentImage.get_rect().height<mid[self.direction]['y']):
                    if((self.y+self.currentImage.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.y += self.speed
                    else:
                        isWaiting = True
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or self.y<(vehicles[self.direction][self.lane][self.index-1].y - gap2)):
                            self.x -= self.speed
            else: 
                if((self.y+self.currentImage.get_rect().height<=self.stop or self.crossed == 1 or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y += self.speed
                else:
                    isWaiting = True
            
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                # Update Avg Wait metrics if the vehicle waited at all
                if self.totalWaitTime > 0:
                    vehiclesProcessed[direction_index] += 1
                    totalWaitingTime[direction_index] += self.totalWaitTime
                self.waiting = False # Ensure waiting is false after crossing
                self.waitStartTime = None
            if(self.willTurn==1):
                if(self.crossed==0 or self.x>mid[self.direction]['x']):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x -= self.speed
                    else:
                        isWaiting = True
                else: 
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if(self.rotateAngle==90):
                            self.turned = 1
                            # path = "images/" + directionNumbers[((self.direction_number+1)%noOfSignals)] + "/" + self.vehicleClass + ".png"
                            # self.x = mid[self.direction]['x']
                            # self.y = mid[self.direction]['y']
                            # self.currentImage = pygame.image.load(path)
                    else:
                        if(self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or self.x>(vehicles[self.direction][self.lane][self.index-1].x + gap2)):
                            self.y -= self.speed
                        else:
                            isWaiting = True
            else: 
                if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x -= self.speed  # move the vehicle    
                else:
                    isWaiting = True
            
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                # Update Avg Wait metrics if the vehicle waited at all
                if self.totalWaitTime > 0:
                    vehiclesProcessed[direction_index] += 1
                    totalWaitingTime[direction_index] += self.totalWaitTime
                self.waiting = False # Ensure waiting is false after crossing
                self.waitStartTime = None
            if(self.willTurn==1):
                if(self.crossed==0 or self.y>mid[self.direction]['y']):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.y -= self.speed
                    else:
                        isWaiting = True
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x<(vehicles[self.direction][self.lane][self.index-1].x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width - gap2) or self.y>(vehicles[self.direction][self.lane][self.index-1].y + gap2)):
                            self.x += self.speed
                        else:
                            isWaiting = True
            else: 
                if((self.y>=self.stop or self.crossed == 1 or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y -= self.speed
                else:
                    isWaiting = True

        # Update waiting status (This part accumulates self.totalWaitTime correctly)
        if isWaiting and not self.waiting and self.crossed == 0:
            self.waiting = True
            self.waitStartTime = time.time()
        elif not isWaiting and self.waiting:
            self.waiting = False
            if self.waitStartTime is not None:
                self.totalWaitTime += time.time() - self.waitStartTime
                self.waitStartTime = None

# Initialization of signals with default values
def initialize():
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts4)
    repeat()

# Set time according to formula
def setTime():
    global noOfCars, noOfBikes, noOfBuses, noOfTrucks, noOfRickshaws, noOfLanes
    global carTime, busTime, truckTime, rickshawTime, bikeTime
    os.system("say detecting vehicles, "+directionNumbers[(currentGreen+1)%noOfSignals])
#    detection_result=detection(currentGreen,tfnet)
#    greenTime = math.ceil(((noOfCars*carTime) + (noOfRickshaws*rickshawTime) + (noOfBuses*busTime) + (noOfBikes*bikeTime))/(noOfLanes+1))
#    if(greenTime<defaultMinimum):
#       greenTime = defaultMinimum
#    elif(greenTime>defaultMaximum):
#       greenTime = defaultMaximum
    # greenTime = len(vehicles[currentGreen][0])+len(vehicles[currentGreen][1])+len(vehicles[currentGreen][2])
    # noOfVehicles = len(vehicles[directionNumbers[nextGreen]][1])+len(vehicles[directionNumbers[nextGreen]][2])-vehicles[directionNumbers[nextGreen]]['crossed']
    # print("no. of vehicles = ",noOfVehicles)
    noOfCars, noOfBuses, noOfTrucks, noOfRickshaws, noOfBikes = 0,0,0,0,0
    for j in range(len(vehicles[directionNumbers[nextGreen]][0])):
        vehicle = vehicles[directionNumbers[nextGreen]][0][j]
        if(vehicle.crossed==0):
            vclass = vehicle.vehicleClass
            # print(vclass)
            noOfBikes += 1
    for i in range(1,3):
        for j in range(len(vehicles[directionNumbers[nextGreen]][i])):
            vehicle = vehicles[directionNumbers[nextGreen]][i][j]
            if(vehicle.crossed==0):
                vclass = vehicle.vehicleClass
                # print(vclass)
                if(vclass=='car'):
                    noOfCars += 1
                elif(vclass=='bus'):
                    noOfBuses += 1
                elif(vclass=='truck'):
                    noOfTrucks += 1
                elif(vclass=='rickshaw'):
                    noOfRickshaws += 1
    # print(noOfCars)
    greenTime = math.ceil(((noOfCars*carTime) + (noOfRickshaws*rickshawTime) + (noOfBuses*busTime) + (noOfTrucks*truckTime)+ (noOfBikes*bikeTime))/(noOfLanes+1))
    # greenTime = math.ceil((noOfVehicles)/noOfLanes) 
    print('Green Time: ',greenTime)
    if(greenTime<defaultMinimum):
        greenTime = defaultMinimum
    elif(greenTime>defaultMaximum):
        greenTime = defaultMaximum
    # greenTime = random.randint(15,50)
    signals[(currentGreen+1)%(noOfSignals)].green = greenTime
   
def simulateAccident():
    # Re-enabling accident simulation
    global accidentOccurred, accidentDirection, accidentTime, accidentDuration
    
    # Higher chance of accidents (5% chance every time this function is called)
    if not accidentOccurred and random.random() < 0.05:
        accidentDirection = random.randint(0, noOfSignals-1)
        accidentOccurred = True
        accidentTime = timeElapsed
        # Random accident duration between 10-30 seconds
        accidentDuration = random.randint(10, 30)
        print(f"ACCIDENT at {directionNumbers[accidentDirection]} direction! Duration: {accidentDuration}s")
    
    # If accident has been active for its duration, clear it
    if accidentOccurred and (timeElapsed - accidentTime) >= accidentDuration:
        accidentOccurred = False
        accidentDirection = -1
        print("Accident cleared")

def repeat():
    global currentGreen, currentYellow, nextGreen, accidentOccurred, accidentDirection, accidentTime, accidentDuration
    
    # Check for accident - đã vô hiệu hóa
    # simulateAccident()
    
    # If accident has been active for its duration, clear it - đã vô hiệu hóa
    # if accidentOccurred and (timeElapsed - accidentTime) >= accidentDuration:
    #     accidentOccurred = False
    #     accidentDirection = -1
    #     print("Accident cleared")
    
    # If next signal is where accident occurred, skip to the next one - đã vô hiệu hóa
    # if accidentOccurred and nextGreen == accidentDirection:
    #     nextGreen = (nextGreen + 1) % noOfSignals
    #     # Reset red time for the skipped signal
    #     signals[accidentDirection].red = defaultRed
    #     print(f"Skipping signal at accident location, new nextGreen: {directionNumbers[nextGreen]}")
    
    while(signals[currentGreen].green>0):
        printStatus()
        updateValues()
        
        # simulateAccident()  # Enable accident simulation
        
        # If accident occurs at current green signal, immediately end green phase - đã vô hiệu hóa
        # if accidentOccurred and currentGreen == accidentDirection:
        #     signals[currentGreen].green = 0
        #     # Reset red time for the accident direction
        #     signals[accidentDirection].red = defaultRed
        #     print("Ending green phase due to accident")
        
        # If accident has been active for its duration, clear it - đã vô hiệu hóa
        # if accidentOccurred and (timeElapsed - accidentTime) >= accidentDuration:
        #     accidentOccurred = False
        #     accidentDirection = -1
        #     print("Accident cleared")
            
        if(signals[(currentGreen+1)%(noOfSignals)].red==detectionTime):
            thread = threading.Thread(name="detection",target=setTime, args=())
            thread.daemon = True
            thread.start()
        
        time.sleep(1)
    
    currentYellow = 1
    vehicleCountTexts[currentGreen] = "0"
    for i in range(0,3):
        stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while(signals[currentGreen].yellow>0):
        printStatus()
        updateValues()
        
        # simulateAccident()  # Enable accident simulation
        
        time.sleep(1)
    currentYellow = 0
    
    signals[currentGreen].green = defaultGreen
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
       
    currentGreen = nextGreen
    
    # If next signal is where accident occurred, skip to the next one - đã vô hiệu hóa
    # if accidentOccurred and currentGreen == accidentDirection:
    #     currentGreen = (currentGreen + 1) % noOfSignals
    #     # Reset red time for the skipped signal
    #     signals[accidentDirection].red = defaultRed
    #     print(f"Skipping to next signal due to accident, new currentGreen: {directionNumbers[currentGreen]}")
    
    nextGreen = (currentGreen+1)%noOfSignals
    
    # If next signal is where accident occurred, skip to the next one - đã vô hiệu hóa
    # if accidentOccurred and nextGreen == accidentDirection:
    #     nextGreen = (nextGreen + 1) % noOfSignals
    #     # Reset red time for the skipped signal
    #     signals[accidentDirection].red = defaultRed
    #     print(f"Skipping next signal due to accident, new nextGreen: {directionNumbers[nextGreen]}")
    
    # Calculate red time for next signal based on current signal's timing
    # if not (accidentOccurred and nextGreen == accidentDirection):
    signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green
    
    repeat()

# Print the signal timers on cmd
def printStatus():                                                                                           
	for i in range(0, noOfSignals):
		if(i==currentGreen):
			if(currentYellow==0):
				print(" GREEN TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
			else:
				print("YELLOW TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
		else:
			print("   RED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
	print()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
                signals[i].totalGreenTime+=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1
    
    # Update metrics
    updateMetrics()

# Generating vehicles in the simulation
def generateVehicles():
    if SYNC_VEHICLES and adaptive_pipe:
        # Nhận dữ liệu phương tiện từ pipe
        while True:
            try:
                # Nhận dữ liệu phương tiện từ pipe
                vehicle_data = adaptive_pipe.recv()
                
                # Tạo phương tiện từ dữ liệu nhận được
                lane_number = vehicle_data['lane_number']
                vehicleClass = vehicle_data['vehicle_class']
                direction_number = vehicle_data['direction_number']
                direction = vehicle_data['direction']
                will_turn = vehicle_data['will_turn']
                
                # Tạo phương tiện với dữ liệu đã đồng bộ
                Vehicle(lane_number, vehicleClass, direction_number, direction, will_turn)
            except (EOFError, BrokenPipeError) as e:
                print(f"Adaptive simulator: Pipe closed or error: {e}")
                break
    else:
        # Phương thức tạo phương tiện cũ khi không chạy ở chế độ đồng bộ
        while(True):
            # Tạo nhiều phương tiện cùng lúc để mô phỏng tình trạng ùn tắc cực kỳ cao
            num_vehicles_per_batch = 4  # Tạo 4 xe cùng lúc - tăng từ 2 lên 4
            
            for _ in range(num_vehicles_per_batch):
                # Tăng tỉ lệ phương tiện lớn (xe buýt, xe tải) để tạo tắc nghẽn nghiêm trọng hơn
                vehicle_probs = [10, 45, 40, 2, 3]  # car, bus, truck, rickshaw, bike - tăng tỉ lệ xe lớn
                vehicle_type_rand = random.randint(0, 99)
                
                vehicle_type = 0
                prob_sum = 0
                for i, prob in enumerate(vehicle_probs):
                    prob_sum += prob
                    if vehicle_type_rand < prob_sum:
                        vehicle_type = i
                        break
                
                if(vehicle_type==4):
                    lane_number = 0
                else:
                    lane_number = random.randint(0,1) + 1
                
                # Tăng tỉ lệ xe rẽ để tạo nhiều tình huống phức tạp hơn nữa
                will_turn = 0
                if(lane_number==2):
                    will_turn = 1 if random.random() < 0.85 else 0  # 85% xe sẽ rẽ - tăng từ 70%
                
                # Tạo kẹt xe cực lớn ở nhiều hướng - thay đổi mô hình kẹt xe thường xuyên
                # Sử dụng hàm sin để tạo ra các đợt sóng giao thông theo thời gian
                time_factor = timeElapsed % 60  # Chu kỳ 60 giây
                
                # Phase shift để các đợt sóng giao thông từ các hướng khác nhau
                right_wave = abs(math.sin(time_factor/10)) * 100  # Đợt sóng hướng right
                down_wave = abs(math.sin((time_factor/10) + 1.5)) * 100  # Đợt sóng hướng down
                left_wave = abs(math.sin((time_factor/10) + 3)) * 100  # Đợt sóng hướng left
                up_wave = abs(math.sin((time_factor/10) + 4.5)) * 100  # Đợt sóng hướng up
                
                # Xác định hướng dựa trên các đợt sóng
                direction_probs = [
                    max(15, int(right_wave)),  # right
                    max(15, int(down_wave)),   # down
                    max(15, int(left_wave)),   # left
                    max(15, int(up_wave))      # up
                ]
                
                # Đảm bảo tổng xác suất là 100%
                total_prob = sum(direction_probs)
                direction_probs = [int(p * 100 / total_prob) for p in direction_probs]
                
                # Đảm bảo tổng xác suất là 100 bằng cách điều chỉnh giá trị cuối cùng
                direction_probs[3] = 100 - sum(direction_probs[:3])
                
                # Đôi khi tạo ra sự cố cực kỳ nghiêm trọng ở một hướng ngẫu nhiên
                if random.random() < 0.1:  # 10% cơ hội
                    chaotic_dir = random.randint(0, 3)
                    direction_probs = [10, 10, 10, 10]
                    direction_probs[chaotic_dir] = 70
                
                dir_rand = random.randint(0, 99)
                
                direction_number = 0
                prob_sum = 0
                for i, prob in enumerate(direction_probs):
                    prob_sum += prob
                    if dir_rand < prob_sum:
                        direction_number = i
                        break
                
                Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
            
            # Gần như không có thời gian chờ giữa các đợt tạo xe
            time.sleep(0.02)  # Giảm từ 0.05 xuống 0.02 giây - tăng tốc độ tạo xe

def simulationTime():
    global timeElapsed, simTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simTime):
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')
            for i in range(noOfSignals):
                print('Lane',i+1,':',vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']
            print('Total vehicles passed: ',totalVehicles)
            print('Total time passed: ',timeElapsed)
            print('No. of vehicles passed per unit time: ',(float(totalVehicles)/float(timeElapsed)))
            os._exit(1)
    

# Add these global variables
HOST = "0.0.0.0"
PORT = 8000

# Add this class for handling HTTP requests
class TrafficSignalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/traffic-signals':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Create JSON response
            response = {
                "signals": {
                    "signal1": {
                        "red": 1 if currentGreen != 0 else 0,
                        "yellow": 1 if currentGreen == 0 and currentYellow == 1 else 0,
                        "green": 1 if currentGreen == 0 and currentYellow == 0 else 0,
                        "timer": signals[0].red if currentGreen != 0 else 
                                (signals[0].yellow if currentYellow == 1 else signals[0].green),
                        "direction": "LEFT",
                        "maxWaitTime": round(maxWaitingTime[0], 1),
                        "currentWaitTime": round(currentWaitingTime[0], 1),
                        "queueLength": maxQueueLength[0],
                        "efficiency": round(trafficEfficiency[0], 2) if trafficEfficiency[0] > 0 else 0
                    },
                    "signal2": {
                        "red": 1 if currentGreen != 1 else 0,
                        "yellow": 1 if currentGreen == 1 and currentYellow == 1 else 0,
                        "green": 1 if currentGreen == 1 and currentYellow == 0 else 0,
                        "timer": signals[1].red if currentGreen != 1 else 
                                (signals[1].yellow if currentYellow == 1 else signals[1].green),
                        "direction": "TOP",
                        "maxWaitTime": round(maxWaitingTime[1], 1),
                        "currentWaitTime": round(currentWaitingTime[1], 1),
                        "queueLength": maxQueueLength[1],
                        "efficiency": round(trafficEfficiency[1], 2) if trafficEfficiency[1] > 0 else 0
                    },
                    "signal3": {
                        "red": 1 if currentGreen != 2 else 0,
                        "yellow": 1 if currentGreen == 2 and currentYellow == 1 else 0,
                        "green": 1 if currentGreen == 2 and currentYellow == 0 else 0,
                        "timer": signals[2].red if currentGreen != 2 else 
                                (signals[2].yellow if currentYellow == 1 else signals[2].green),
                        "direction": "RIGHT",
                        "maxWaitTime": round(maxWaitingTime[2], 1),
                        "currentWaitTime": round(currentWaitingTime[2], 1),
                        "queueLength": maxQueueLength[2],
                        "efficiency": round(trafficEfficiency[2], 2) if trafficEfficiency[2] > 0 else 0
                    },
                    "signal4": {
                        "red": 1 if currentGreen != 3 else 0,
                        "yellow": 1 if currentGreen == 3 and currentYellow == 1 else 0,
                        "green": 1 if currentGreen == 3 and currentYellow == 0 else 0,
                        "timer": signals[3].red if currentGreen != 3 else 
                                (signals[3].yellow if currentYellow == 1 else signals[3].green),
                        "direction": "BOTTOM",
                        "maxWaitTime": round(maxWaitingTime[3], 1),
                        "currentWaitTime": round(currentWaitingTime[3], 1),
                        "queueLength": maxQueueLength[3],
                        "efficiency": round(trafficEfficiency[3], 2) if trafficEfficiency[3] > 0 else 0
                    }
                },
                "currentGreen": currentGreen,
                "currentYellow": currentYellow,
                "timeElapsed": timeElapsed,
                "delay": 1000,  # 1 second in milliseconds
                "metrics": {
                    "maxWaitingTimes": [round(maxWaitingTime[i], 1) for i in range(4)],
                    "currentWaitingTimes": [round(currentWaitingTime[i], 1) for i in range(4)],
                    "maxQueueLengths": [maxQueueLength[i] for i in range(4)],
                    "trafficEfficiency": [round(trafficEfficiency[i], 2) for i in range(4)]
                }
            }
            
            # Add accident information if there's an accident
            if accidentOccurred:
                response["accident"] = {
                    "direction": directionDisplay[directionNumbers[accidentDirection]],
                    "timeRemaining": accidentDuration - (timeElapsed - accidentTime)
                }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

# Add function to start HTTP server
def start_server():
    server = HTTPServer((HOST, PORT), TrafficSignalHandler)
    print(f"Server started at http://{HOST}:{PORT}")
    server.serve_forever()

# Modify the Main class to start the HTTP server
class Main:
    thread4 = threading.Thread(name="simulationTime",target=simulationTime, args=()) 
    thread4.daemon = True
    thread4.start()

    thread2 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread2.daemon = True
    thread2.start()

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize 
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/mod_int.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("ADAPTIVE TIMING SIMULATION")

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread3.daemon = True
    thread3.start()

    # Add this line after other thread starts
    thread5 = threading.Thread(name="httpServer", target=start_server)
    thread5.daemon = True
    thread5.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))   # display background in simulation
        for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
            if(i==currentGreen):
                if(currentYellow==1):
                    if(signals[i].yellow==0):
                        signals[i].signalText = "STOP"
                    else:
                        signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    if(signals[i].green==0):
                        signals[i].signalText = "SLOW"
                    else:
                        signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if(signals[i].red<=10):
                    if(signals[i].red==0):
                        signals[i].signalText = "GO"
                    else:
                        signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]

        # display signal timer and vehicle count
        for i in range(0,noOfSignals):  
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i]) 
            
            # Display crossed vehicles count
            displayText = vehicles[directionNumbers[i]]['crossed']
            vehicleCountTexts[i] = font.render("Crossed: " + str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i],vehicleCountCoods[i])
            
            # Count and display waiting vehicles
            waitingCount = 0
            for lane in range(3):
                for vehicle in vehicles[directionNumbers[i]][lane]:
                    if vehicle.crossed == 0:
                        waitingCount += 1
            
            waitingVehicleTexts[i] = font.render("On Lane: " + str(waitingCount), True, black, white)
            screen.blit(waitingVehicleTexts[i],waitingVehicleCoods[i])
            
            # Display adaptive timing indicator
            if i == currentGreen and currentYellow == 0:
                green_time_text = font.render(f"Green: {signals[i].green}s (Adaptive)", True, (0, 255, 0), (0, 0, 0))
                screen.blit(green_time_text, (signalCoods[i][0] - 100, signalCoods[i][1] - 30))

        # Display title
        title = font.render("ADAPTIVE TIMING SIMULATION", True, (255, 255, 255), (0, 0, 0))
        screen.blit(title, (screenWidth//2 - 150, 20))

        timeElapsedText = font.render(("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText,(1100,50))
        
        # Display performance metrics
        totalVehicles = 0
        for i in range(noOfSignals):
            totalVehicles += vehicles[directionNumbers[i]]['crossed']
        
        if timeElapsed > 0:
            throughput = totalVehicles / timeElapsed
            performance_text = font.render(f"Vehicles/second: {throughput:.2f}", True, (255, 255, 255), (0, 0, 0))
            screen.blit(performance_text, (20, 50))
            
            # Hiển thị tổng số xe đã qua ngã tư
            total_vehicles_text = font.render(f"Total vehicles passed: {totalVehicles}", True, (255, 255, 255), (0, 0, 0))
            screen.blit(total_vehicles_text, (20, 80))

        # Update performance metrics
        drawAdvancedMetrics(screen, font)
        
        # display the vehicles
        for vehicle in simulation:  
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            # vehicle.render(screen)
            vehicle.move()

        pygame.display.update()

Main()