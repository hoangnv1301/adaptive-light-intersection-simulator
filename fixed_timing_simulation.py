# Fixed timing simulation (30 seconds per signal)
import pygame
import threading
import time
import random
import math
import os
import sys
import multiprocessing
from multiprocessing.connection import Connection
import datetime

# Thêm biến để kiểm tra xem có đang chạy ở chế độ đồng bộ không
SYNC_VEHICLES = 'SYNC_VEHICLES' in os.environ and os.environ['SYNC_VEHICLES'] == '1'
fixed_pipe = None

# Khởi tạo pipe nếu đang chạy ở chế độ đồng bộ
if SYNC_VEHICLES:
    try:
        pipe_fd = int(os.environ['FIXED_PIPE_FD'])
        fixed_pipe = Connection(pipe_fd)
        print("Fixed simulator: Connected to vehicle generator pipe")
    except (KeyError, ValueError) as e:
        print(f"Error setting up pipe: {e}")
        SYNC_VEHICLES = False

# Default values of signal times
defaultRed = 150
defaultYellow = 5
defaultGreen = 30  # Fixed at 30 seconds
defaultMinimum = 30
defaultMaximum = 30

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
vehicleCountCoods = [(380,210),(960,210),(960,550),(380,550)]
vehicleCountTexts = ["0", "0", "0", "0"]

# Move waiting vehicle counts to positions that don't overlap with timers
waitingVehicleCoods = [(380,240),(960,240),(960,580),(380,580)]
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

# Add direction display names
directionDisplay = {
    'right': 'LEFT',     # Bên phải của màn hình thực tế là LEFT
    'left': 'RIGHT',     # Bên trái của màn hình thực tế là RIGHT
    'up': 'BOTTOM',      # Phía trên của màn hình thực tế là BOTTOM
    'down': 'TOP'        # Phía dưới của màn hình thực tế là TOP
}

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
    # Background for metrics panel
    metrics_bg = pygame.Surface((500, 180))
    metrics_bg.fill((0, 0, 0))
    metrics_bg.set_alpha(200)  # Semi-transparent
    screen.blit(metrics_bg, (880, 100))
    
    # Title
    title = font.render("ADVANCED METRICS (FIXED TIMING)", True, (255, 255, 0))
    screen.blit(title, (900, 110))
    
    # Direction labels
    directions = ["LEFT", "TOP", "RIGHT", "BOTTOM"]
    for i, direction in enumerate(directions):
        dir_text = font.render(direction, True, (255, 255, 255))
        screen.blit(dir_text, (900, 140 + i * 30))
    
    # Max waiting time
    max_wait_title = font.render("Max Wait (s)", True, (255, 255, 255))
    screen.blit(max_wait_title, (1000, 140))
    
    for i in range(4):
        # Color code based on waiting time
        if maxWaitingTime[i] < 30:
            color = (0, 255, 0)  # Green for good
        elif maxWaitingTime[i] < 60:
            color = (255, 255, 0)  # Yellow for moderate
        else:
            color = (255, 0, 0)  # Red for bad
            
        max_wait = font.render(f"{maxWaitingTime[i]:.1f}", True, color)
        screen.blit(max_wait, (1000, 170 + i * 30))
    
    # Current queue length
    queue_title = font.render("Queue", True, (255, 255, 255))
    screen.blit(queue_title, (1080, 140))
    
    for i in range(4):
        # Color code based on queue length
        queue_length = 0
        direction = directionNumbers[i]
        for lane in range(3):
            for vehicle in vehicles[direction][lane]:
                if vehicle.crossed == 0:
                    queue_length += 1
        
        if queue_length < 10:
            color = (0, 255, 0)  # Green for good
        elif queue_length < 20:
            color = (255, 255, 0)  # Yellow for moderate
        else:
            color = (255, 0, 0)  # Red for bad
            
        queue_text = font.render(f"{queue_length}", True, color)
        screen.blit(queue_text, (1080, 170 + i * 30))
    
    # Efficiency
    eff_title = font.render("Efficiency", True, (255, 255, 255))
    screen.blit(eff_title, (1150, 140))
    
    for i in range(4):
        if trafficEfficiency[i] > 0:
            eff_text = font.render(f"{trafficEfficiency[i]:.2f}", True, (0, 255, 255))
            screen.blit(eff_text, (1150, 170 + i * 30))
        else:
            eff_text = font.render("0.00", True, (0, 255, 255))
            screen.blit(eff_text, (1150, 170 + i * 30))
    
    # Avg waiting time
    avg_title = font.render("Avg Wait (s)", True, (255, 255, 255))
    screen.blit(avg_title, (1250, 140))
    
    for i in range(4):
        if vehiclesProcessed[i] > 0:
            avg_wait = totalWaitingTime[i] / vehiclesProcessed[i]
            color = (0, 255, 0) if avg_wait < 15 else ((255, 255, 0) if avg_wait < 30 else (255, 0, 0))
            avg_text = font.render(f"{avg_wait:.1f}", True, color)
        else:
            avg_text = font.render("0.0", True, (0, 255, 0))
        screen.blit(avg_text, (1250, 170 + i * 30))
    
    # Draw overall efficiency metrics at the bottom
    total_vehicles = 0
    for i in range(noOfSignals):
        total_vehicles += vehicles[directionNumbers[i]]['crossed']
    
    total_vehicles_text = font.render(f"Total vehicles: {total_vehicles}", True, (255, 255, 255))
    screen.blit(total_vehicles_text, (900, 260))
    
    if timeElapsed > 0:
        throughput = total_vehicles / timeElapsed
        throughput_text = font.render(f"Throughput: {throughput:.2f} veh/s", True, (255, 255, 255))
        screen.blit(throughput_text, (1100, 260))

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
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        if(direction=='right'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().width - gap
            else:
                self.stop = defaultStop[direction]
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
        
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.currentImage.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.waitStartTime is not None:
                    self.totalWaitTime += time.time() - self.waitStartTime
                    vehiclesProcessed[0] += 1
                    totalWaitingTime[0] += self.totalWaitTime
                self.waiting = False
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
                    else:
                        if(self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2)):
                            self.y += self.speed
            else: 
                if((self.x+self.currentImage.get_rect().width<=self.stop or self.crossed == 1 or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.x += self.speed
                else:
                    isWaiting = True

        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.currentImage.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.waitStartTime is not None:
                    self.totalWaitTime += time.time() - self.waitStartTime
                    vehiclesProcessed[1] += 1
                    totalWaitingTime[1] += self.totalWaitTime
                self.waiting = False
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
                if self.waitStartTime is not None:
                    self.totalWaitTime += time.time() - self.waitStartTime
                    vehiclesProcessed[2] += 1
                    totalWaitingTime[2] += self.totalWaitTime
                self.waiting = False
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
                    else:
                        if(self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or self.x>(vehicles[self.direction][self.lane][self.index-1].x + gap2)):
                            self.y -= self.speed
            else: 
                if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.x -= self.speed
                else:
                    isWaiting = True
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.waitStartTime is not None:
                    self.totalWaitTime += time.time() - self.waitStartTime
                    vehiclesProcessed[3] += 1
                    totalWaitingTime[3] += self.totalWaitTime
                self.waiting = False
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
                if((self.y>=self.stop or self.crossed == 1 or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y -= self.speed
                else:
                    isWaiting = True

        # Update waiting status
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

def simulateAccident():
    # Đã tắt chế độ accident
    global accidentOccurred, accidentDirection, accidentTime
    # Không làm gì cả - đã vô hiệu hóa accident
    pass

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
        
        # Check for accident during green phase - đã vô hiệu hóa
        # simulateAccident()
        
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
        
        # Check for accident during yellow phase - đã vô hiệu hóa
        # simulateAccident()
        
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
                print(" GREEN FIXED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
            else:
                print("YELLOW FIXED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
        else:
            print("   RED FIXED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
    print()

# Update values of the signal timers after every second
def updateValues():
    global timeElapsed
    timeElapsed += 1
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
    if SYNC_VEHICLES and fixed_pipe:
        # Nhận dữ liệu phương tiện từ pipe
        while True:
            try:
                # Nhận dữ liệu phương tiện từ pipe
                vehicle_data = fixed_pipe.recv()
                
                # Tạo phương tiện từ dữ liệu nhận được
                lane_number = vehicle_data['lane_number']
                vehicleClass = vehicle_data['vehicle_class']
                direction_number = vehicle_data['direction_number']
                direction = vehicle_data['direction']
                will_turn = vehicle_data['will_turn']
                
                # Tạo phương tiện với dữ liệu đã đồng bộ
                Vehicle(lane_number, vehicleClass, direction_number, direction, will_turn)
            except (EOFError, BrokenPipeError) as e:
                print(f"Fixed simulator: Pipe closed or error: {e}")
                break
    else:
        # Phương thức tạo phương tiện cũ khi không chạy ở chế độ đồng bộ
        while(True):
            # Tạo nhiều phương tiện cùng lúc để mô phỏng tình trạng ùn tắc cực kỳ cao
            num_vehicles_per_batch = 2  # Tạo 2 xe cùng lúc
            
            for _ in range(num_vehicles_per_batch):
                # Tăng tỉ lệ phương tiện lớn (xe buýt, xe tải) để tạo tắc nghẽn nghiêm trọng hơn
                vehicle_probs = [20, 35, 35, 5, 5]  # car, bus, truck, rickshaw, bike
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
                    will_turn = 1 if random.random() < 0.7 else 0  # 70% xe sẽ rẽ
                
                # Tạo kẹt xe cực lớn ở một số hướng nhất định (mô phỏng tắc nghẽn đường)
                # Tập trung phần lớn xe ở hướng right (LEFT) - mô phỏng tắc nghẽn nghiêm trọng
                direction_probs = [70, 20, 5, 5]  # right, down, left, up
                
                # Thỉnh thoảng tạo đợt xe đông đúc từ hướng khác (mô phỏng xe từ đường phụ đổ ra)
                if random.random() < 0.2:  # 20% cơ hội tạo đợt xe từ hướng khác
                    traffic_surge_dir = random.randint(1, 3)  # random direction (không phải right)
                    new_probs = [25, 25, 25, 25]
                    new_probs[traffic_surge_dir] = 70
                    new_probs[0] = 100 - new_probs[1] - new_probs[2] - new_probs[3]
                    direction_probs = new_probs
                
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
            time.sleep(0.05)  # Giảm từ 0.1 xuống 0.05 giây

def showStats():
    while(True):
        totalVehicles = 0
        print('Lane-wise Vehicle Counts (Fixed Timing)')
        for i in range(noOfSignals):
            print('Lane',i+1,':',vehicles[directionNumbers[i]]['crossed'])
            totalVehicles += vehicles[directionNumbers[i]]['crossed']
        print('Total vehicles passed: ',totalVehicles)
        print('Total time passed: ',timeElapsed)
        print('No. of vehicles passed per unit time: ',(float(totalVehicles)/float(timeElapsed)))
        time.sleep(5)
        if(timeElapsed==simTime):
            print("Simulation finished for Fixed Timing. ")
            os._exit(1)

class Main:
    thread1 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread2.daemon = True
    thread2.start()
    
    thread3 = threading.Thread(name="showStats",target=showStats, args=())    # show statistics
    thread3.daemon = True
    thread3.start()

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
    pygame.display.set_caption("FIXED TIMING SIMULATION (30s)")

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

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
            
            # Display fixed timing indicator
            if i == currentGreen and currentYellow == 0:
                green_time_text = font.render(f"Green: {signals[i].green}s (Fixed 30s)", True, (0, 255, 0), (0, 0, 0))
                screen.blit(green_time_text, (signalCoods[i][0] - 100, signalCoods[i][1] - 30))

        # Display title
        title = font.render("FIXED TIMING SIMULATION (30s)", True, (255, 255, 255), (0, 0, 0))
        screen.blit(title, (screenWidth//2 - 150, 20))
        
        timeElapsedText = font.render(("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText,(1100,50))

        # Display performance metrics
        throughput = 0
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
        
        # Update and display advanced metrics
        drawAdvancedMetrics(screen, font)

        # display the vehicles
        for vehicle in simulation:  
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()

        pygame.display.update()

if __name__ == "__main__":
    Main() 