import sys
import pygame
import threading
import time
import random
import math
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from simulation_dual_mode_for_comparison import Vehicle, TrafficSignal, directionNumbers, vehicleTypes, signals, defaultStop, defaultYellow, defaultRed, currentGreen, currentYellow, vehicles, x, y, speeds, mid, stops, noOfSignals, timeElapsed, accidentOccurred, accidentDirection, accidentTime, accidentDuration, accidentBlinkInterval, accidentBlinkTimer, directionDisplay, stopLines, gap, gap2, rotationAngle, simTime, simulationTime, generateVehicles, simulation, signalCoods, signalTimerCoods, vehicleCountCoods, waitingVehicleCoods

# Create copies of all variables and classes for the fixed timing simulation
fixed_signals = []
fixed_currentGreen = 0
fixed_currentYellow = 0
fixed_nextGreen = 1
fixed_vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
fixed_x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}
fixed_y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}
fixed_stops = {'right': [580,580,580], 'down': [320,320,320], 'left': [810,810,810], 'up': [545,545,545]}
fixed_simulation = pygame.sprite.Group()

# Create performance comparison variables
adaptive_total_vehicles = 0
fixed_total_vehicles = 0

class FixedVehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = fixed_x[direction][lane]
        self.y = fixed_y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        fixed_vehicles[direction][lane].append(self)
        self.index = len(fixed_vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        if(direction=='right'):
            if(len(fixed_vehicles[direction][lane])>1 and fixed_vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = fixed_vehicles[direction][lane][self.index-1].stop - fixed_vehicles[direction][lane][self.index-1].currentImage.get_rect().width - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap    
            fixed_x[direction][lane] -= temp
            fixed_stops[direction][lane] -= temp
        elif(direction=='left'):
            if(len(fixed_vehicles[direction][lane])>1 and fixed_vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = fixed_vehicles[direction][lane][self.index-1].stop + fixed_vehicles[direction][lane][self.index-1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            fixed_x[direction][lane] += temp
            fixed_stops[direction][lane] += temp
        elif(direction=='down'):
            if(len(fixed_vehicles[direction][lane])>1 and fixed_vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = fixed_vehicles[direction][lane][self.index-1].stop - fixed_vehicles[direction][lane][self.index-1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            fixed_y[direction][lane] -= temp
            fixed_stops[direction][lane] -= temp
        elif(direction=='up'):
            if(len(fixed_vehicles[direction][lane])>1 and fixed_vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = fixed_vehicles[direction][lane][self.index-1].stop + fixed_vehicles[direction][lane][self.index-1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            fixed_y[direction][lane] += temp
            fixed_stops[direction][lane] += temp
        fixed_simulation.add(self)

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.currentImage.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                fixed_vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x+self.currentImage.get_rect().width<mid[self.direction]['x']):
                    if((self.x+self.currentImage.get_rect().width<=self.stop or (fixed_currentGreen==0 and fixed_currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.currentImage.get_rect().width<(fixed_vehicles[self.direction][self.lane][self.index-1].x - gap2) or fixed_vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x += self.speed
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.y+self.currentImage.get_rect().height<(fixed_vehicles[self.direction][self.lane][self.index-1].y - gap2) or self.x+self.currentImage.get_rect().width<(fixed_vehicles[self.direction][self.lane][self.index-1].x - gap2)):
                            self.y += self.speed
            else: 
                if((self.x+self.currentImage.get_rect().width<=self.stop or self.crossed == 1 or (fixed_currentGreen==0 and fixed_currentYellow==0)) and (self.index==0 or self.x+self.currentImage.get_rect().width<(fixed_vehicles[self.direction][self.lane][self.index-1].x - gap2) or (fixed_vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.x += self.speed
        
        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.currentImage.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                fixed_vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y+self.currentImage.get_rect().height<mid[self.direction]['y']):
                    if((self.y+self.currentImage.get_rect().height<=self.stop or (fixed_currentGreen==1 and fixed_currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.currentImage.get_rect().height<(fixed_vehicles[self.direction][self.lane][self.index-1].y - gap2) or fixed_vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.y += self.speed
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x>(fixed_vehicles[self.direction][self.lane][self.index-1].x + fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or self.y<(fixed_vehicles[self.direction][self.lane][self.index-1].y - gap2)):
                            self.x -= self.speed
            else: 
                if((self.y+self.currentImage.get_rect().height<=self.stop or self.crossed == 1 or (fixed_currentGreen==1 and fixed_currentYellow==0)) and (self.index==0 or self.y+self.currentImage.get_rect().height<(fixed_vehicles[self.direction][self.lane][self.index-1].y - gap2) or (fixed_vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y += self.speed
        
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                fixed_vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x>mid[self.direction]['x']):
                    if((self.x>=self.stop or (fixed_currentGreen==2 and fixed_currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(fixed_vehicles[self.direction][self.lane][self.index-1].x + fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or fixed_vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                        self.x -= self.speed
                else: 
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.y>(fixed_vehicles[self.direction][self.lane][self.index-1].y + fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or self.x>(fixed_vehicles[self.direction][self.lane][self.index-1].x + gap2)):
                            self.y -= self.speed
            else: 
                if((self.x>=self.stop or self.crossed == 1 or (fixed_currentGreen==2 and fixed_currentYellow==0)) and (self.index==0 or self.x>(fixed_vehicles[self.direction][self.lane][self.index-1].x + fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or (fixed_vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.x -= self.speed
        
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                fixed_vehicles[self.direction]['crossed'] += 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y>mid[self.direction]['y']):
                    if((self.y>=self.stop or (fixed_currentGreen==3 and fixed_currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(fixed_vehicles[self.direction][self.lane][self.index-1].y + fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or fixed_vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.y -= self.speed
                else:   
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x<(fixed_vehicles[self.direction][self.lane][self.index-1].x - fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width - gap2) or self.y>(fixed_vehicles[self.direction][self.lane][self.index-1].y + gap2)):
                            self.x += self.speed
            else: 
                if((self.y>=self.stop or self.crossed == 1 or (fixed_currentGreen==3 and fixed_currentYellow==0)) and (self.index==0 or self.y>(fixed_vehicles[self.direction][self.lane][self.index-1].y + fixed_vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height + gap2) or (fixed_vehicles[self.direction][self.lane][self.index-1].turned==1))):                
                    self.y -= self.speed

# Initialize fixed signals with 30-second green time
def initialize_fixed():
    global fixed_signals, fixed_currentGreen, fixed_nextGreen
    
    # Create signals with fixed 30-second green time
    ts1 = TrafficSignal(0, defaultYellow, 30, 30, 30)
    fixed_signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, 30, 30, 30)
    fixed_signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, 30, 30, 30)
    fixed_signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, 30, 30, 30)
    fixed_signals.append(ts4)
    
    repeat_fixed()

# Update fixed signal timers
def updateValues_fixed():
    for i in range(0, noOfSignals):
        if(i==fixed_currentGreen):
            if(fixed_currentYellow==0):
                fixed_signals[i].green-=1
                fixed_signals[i].totalGreenTime+=1
            else:
                fixed_signals[i].yellow-=1
        else:
            fixed_signals[i].red-=1

# Print status of fixed signals
def printStatus_fixed():                                                                                           
    for i in range(0, noOfSignals):
        if(i==fixed_currentGreen):
            if(fixed_currentYellow==0):
                print(" GREEN FIXED TS",i+1,"-> r:",fixed_signals[i].red," y:",fixed_signals[i].yellow," g:",fixed_signals[i].green)
            else:
                print("YELLOW FIXED TS",i+1,"-> r:",fixed_signals[i].red," y:",fixed_signals[i].yellow," g:",fixed_signals[i].green)
        else:
            print("   RED FIXED TS",i+1,"-> r:",fixed_signals[i].red," y:",fixed_signals[i].yellow," g:",fixed_signals[i].green)
    print()

# Repeat cycle for fixed signal timing
def repeat_fixed():
    global fixed_currentGreen, fixed_currentYellow, fixed_nextGreen
    
    while(fixed_signals[fixed_currentGreen].green>0):
        printStatus_fixed()
        updateValues_fixed()
        time.sleep(1)
    
    fixed_currentYellow = 1
    for i in range(0,3):
        fixed_stops[directionNumbers[fixed_currentGreen]][i] = defaultStop[directionNumbers[fixed_currentGreen]]
        for vehicle in fixed_vehicles[directionNumbers[fixed_currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[fixed_currentGreen]]
    
    while(fixed_signals[fixed_currentGreen].yellow>0):
        printStatus_fixed()
        updateValues_fixed()
        time.sleep(1)
    
    fixed_currentYellow = 0
    
    fixed_signals[fixed_currentGreen].green = 30  # Reset to fixed 30 seconds
    fixed_signals[fixed_currentGreen].yellow = defaultYellow
    fixed_signals[fixed_currentGreen].red = defaultRed
       
    fixed_currentGreen = (fixed_currentGreen + 1) % noOfSignals
    fixed_nextGreen = (fixed_currentGreen + 1) % noOfSignals
    
    # Set red time for next signal
    fixed_signals[fixed_nextGreen].red = fixed_signals[fixed_currentGreen].yellow + fixed_signals[fixed_currentGreen].green
    
    repeat_fixed()

# Generate vehicles for fixed timing simulation
def generateVehicles_fixed():
    while(True):
        vehicle_type = random.randint(0,4)
        if(vehicle_type==4):
            lane_number = 0
        else:
            lane_number = random.randint(0,1) + 1
        will_turn = 0
        if(lane_number==2):
            temp = random.randint(0,4)
            if(temp<=2):
                will_turn = 1
            elif(temp>2):
                will_turn = 0
        temp = random.randint(0,999)
        direction_number = 0
        a = [400,800,900,1000]
        if(temp<a[0]):
            direction_number = 0
        elif(temp<a[1]):
            direction_number = 1
        elif(temp<a[2]):
            direction_number = 2
        elif(temp<a[3]):
            direction_number = 3
        FixedVehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(0.75)

# Main class to run both simulations
class DualSimulation:
    def __init__(self):
        # Initialize both simulations
        pygame.init()
        
        # Create a single window with double width
        combined_screen = pygame.display.set_mode((2800, 800))
        pygame.display.set_caption("Traffic Signal Comparison: Adaptive vs Fixed")
        
        # Create surfaces for each simulation
        self.adaptive_screen = pygame.Surface((1400, 800))
        self.fixed_screen = pygame.Surface((1400, 800))
        
        # Load images
        self.background = pygame.image.load('images/mod_int.png')
        self.redSignal = pygame.image.load('images/signals/red.png')
        self.yellowSignal = pygame.image.load('images/signals/yellow.png')
        self.greenSignal = pygame.image.load('images/signals/green.png')
        self.font = pygame.font.Font(None, 30)
        
        # Start threads for adaptive simulation
        self.thread1 = threading.Thread(target=simulationTime)
        self.thread1.daemon = True
        self.thread1.start()
        
        # Start threads for fixed simulation
        self.thread_fixed1 = threading.Thread(target=initialize_fixed)
        self.thread_fixed1.daemon = True
        self.thread_fixed1.start()
        
        self.thread_fixed2 = threading.Thread(target=generateVehicles_fixed)
        self.thread_fixed2.daemon = True
        self.thread_fixed2.start()
        
        # Generate vehicles for adaptive simulation
        self.thread3 = threading.Thread(target=generateVehicles)
        self.thread3.daemon = True
        self.thread3.start()
        
        # Start HTTP server
        self.thread5 = threading.Thread(target=start_server)
        self.thread5.daemon = True
        self.thread5.start()
        
        self.run()
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            
            # Update performance comparison variables
            adaptive_total_vehicles = 0
            fixed_total_vehicles = 0
            for direction in directionNumbers:
                adaptive_total_vehicles += vehicles[direction]['crossed']
                fixed_total_vehicles += fixed_vehicles[direction]['crossed']
            
            # Render adaptive simulation
            self.render_adaptive()
            
            # Render fixed simulation
            self.render_fixed()
            
            # Combine both screens side by side
            combined_screen = pygame.display.get_surface()
            combined_screen.blit(self.adaptive_screen, (0, 0))
            combined_screen.blit(self.fixed_screen, (1400, 0))
            
            # Add labels to identify each simulation
            adaptive_label = self.font.render("ADAPTIVE TIMING", True, (255, 255, 255), (0, 0, 0))
            fixed_label = self.font.render("FIXED TIMING (30s)", True, (255, 255, 255), (0, 0, 0))
            combined_screen.blit(adaptive_label, (600, 20))
            combined_screen.blit(fixed_label, (2000, 20))
            
            # Add dividing line between the two simulations
            pygame.draw.line(combined_screen, (255, 255, 255), (1400, 0), (1400, 800), 2)
            
            # Add performance comparison stats at the bottom
            if timeElapsed > 0:
                # Calculate throughput (vehicles per second)
                adaptive_throughput = adaptive_total_vehicles / timeElapsed
                fixed_throughput = fixed_total_vehicles / timeElapsed
                
                # Display comparison metrics
                comparison_bg = pygame.Rect(0, 740, 2800, 60)
                pygame.draw.rect(combined_screen, (0, 0, 0), comparison_bg)
                
                # Total vehicles
                total_vehicles_text = self.font.render(f"Total Vehicles - Adaptive: {adaptive_total_vehicles} | Fixed: {fixed_total_vehicles} | Difference: {adaptive_total_vehicles - fixed_total_vehicles}", True, (255, 255, 255))
                combined_screen.blit(total_vehicles_text, (20, 750))
                
                # Throughput
                throughput_text = self.font.render(f"Vehicles/second - Adaptive: {adaptive_throughput:.2f} | Fixed: {fixed_throughput:.2f} | Ratio: {(adaptive_throughput/fixed_throughput):.2f}x", True, (255, 255, 255))
                combined_screen.blit(throughput_text, (20, 780))
            
            pygame.display.update()
    
    def render_adaptive(self):
        self.adaptive_screen.blit(self.background, (0, 0))
        
        # Display signals
        for i in range(0, noOfSignals):
            if(i==currentGreen):
                if(currentYellow==1):
                    if(signals[i].yellow==0):
                        signals[i].signalText = "STOP"
                    else:
                        signals[i].signalText = signals[i].yellow
                    self.adaptive_screen.blit(self.yellowSignal, signalCoods[i])
                else:
                    if(signals[i].green==0):
                        signals[i].signalText = "SLOW"
                    else:
                        signals[i].signalText = signals[i].green
                    self.adaptive_screen.blit(self.greenSignal, signalCoods[i])
            else:
                if(signals[i].red<=10):
                    if(signals[i].red==0):
                        signals[i].signalText = "GO"
                    else:
                        signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                self.adaptive_screen.blit(self.redSignal, signalCoods[i])
        
        # Display signal timers and vehicle counts
        for i in range(0, noOfSignals):
            signal_text = self.font.render(str(signals[i].signalText), True, (255, 255, 255), (0, 0, 0))
            self.adaptive_screen.blit(signal_text, signalTimerCoods[i])
            
            # Display crossed vehicles
            crossed_text = self.font.render("Crossed: " + str(vehicles[directionNumbers[i]]['crossed']), True, (0, 0, 0), (255, 255, 255))
            self.adaptive_screen.blit(crossed_text, vehicleCountCoods[i])
            
            # Count and display waiting vehicles
            waiting_count = 0
            for lane in range(3):
                for vehicle in vehicles[directionNumbers[i]][lane]:
                    if vehicle.crossed == 0:
                        waiting_count += 1
            
            waiting_text = self.font.render("On Lane: " + str(waiting_count), True, (0, 0, 0), (255, 255, 255))
            self.adaptive_screen.blit(waiting_text, waitingVehicleCoods[i])
            
            # Display green time setting (adaptive)
            if i == currentGreen and currentYellow == 0:
                green_time_text = self.font.render(f"Green: {signals[i].green}s (Adaptive)", True, (0, 255, 0), (0, 0, 0))
                self.adaptive_screen.blit(green_time_text, (signalCoods[i][0] - 100, signalCoods[i][1] - 30))
        
        # Display time elapsed
        time_text = self.font.render("Time Elapsed: " + str(timeElapsed), True, (0, 0, 0), (255, 255, 255))
        self.adaptive_screen.blit(time_text, (1100, 50))
        
        # Display vehicles
        for vehicle in simulation:
            self.adaptive_screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()
        
        # Display accident warning if needed
        if accidentOccurred:
            # Update blink timer
            global accidentBlinkTimer
            accidentBlinkTimer += 1
            if accidentBlinkTimer >= 30:
                accidentBlinkTimer = 0
            
            if accidentBlinkTimer < 15:
                direction = directionNumbers[accidentDirection]
                displayDirection = directionDisplay[direction]
                
                accident_text = self.font.render(f"ACCIDENT ON {displayDirection} LANE!", True, (255, 0, 0), (255, 255, 255))
                accident_rect = accident_text.get_rect(center=(700, 50))
                self.adaptive_screen.blit(accident_text, accident_rect)
                
                accidentX = signalCoods[accidentDirection][0] + 15
                accidentY = signalCoods[accidentDirection][1] + 15
                pygame.draw.line(self.adaptive_screen, (255, 0, 0), (accidentX-10, accidentY-10), (accidentX+10, accidentY+10), 4)
                pygame.draw.line(self.adaptive_screen, (255, 0, 0), (accidentX-10, accidentY+10), (accidentX+10, accidentY-10), 4)
    
    def render_fixed(self):
        self.fixed_screen.blit(self.background, (0, 0))
        
        # Display signals for fixed timing
        for i in range(0, noOfSignals):
            if(i==fixed_currentGreen):
                if(fixed_currentYellow==1):
                    if(fixed_signals[i].yellow==0):
                        fixed_signals[i].signalText = "STOP"
                    else:
                        fixed_signals[i].signalText = fixed_signals[i].yellow
                    self.fixed_screen.blit(self.yellowSignal, signalCoods[i])
                else:
                    if(fixed_signals[i].green==0):
                        fixed_signals[i].signalText = "SLOW"
                    else:
                        fixed_signals[i].signalText = fixed_signals[i].green
                    self.fixed_screen.blit(self.greenSignal, signalCoods[i])
            else:
                if(fixed_signals[i].red<=10):
                    if(fixed_signals[i].red==0):
                        fixed_signals[i].signalText = "GO"
                    else:
                        fixed_signals[i].signalText = fixed_signals[i].red
                else:
                    fixed_signals[i].signalText = "---"
                self.fixed_screen.blit(self.redSignal, signalCoods[i])
        
        # Display signal timers and vehicle counts for fixed timing
        for i in range(0, noOfSignals):
            signal_text = self.font.render(str(fixed_signals[i].signalText), True, (255, 255, 255), (0, 0, 0))
            self.fixed_screen.blit(signal_text, signalTimerCoods[i])
            
            # Display crossed vehicles
            crossed_text = self.font.render("Crossed: " + str(fixed_vehicles[directionNumbers[i]]['crossed']), True, (0, 0, 0), (255, 255, 255))
            self.fixed_screen.blit(crossed_text, vehicleCountCoods[i])
            
            # Count and display waiting vehicles
            waiting_count = 0
            for lane in range(3):
                for vehicle in fixed_vehicles[directionNumbers[i]][lane]:
                    if vehicle.crossed == 0:
                        waiting_count += 1
            
            waiting_text = self.font.render("On Lane: " + str(waiting_count), True, (0, 0, 0), (255, 255, 255))
            self.fixed_screen.blit(waiting_text, waitingVehicleCoods[i])
            
            # Display green time setting (fixed)
            if i == fixed_currentGreen and fixed_currentYellow == 0:
                green_time_text = self.font.render(f"Green: {fixed_signals[i].green}s (Fixed 30s)", True, (0, 255, 0), (0, 0, 0))
                self.fixed_screen.blit(green_time_text, (signalCoods[i][0] - 100, signalCoods[i][1] - 30))
        
        # Display time elapsed (same as adaptive)
        time_text = self.font.render("Time Elapsed: " + str(timeElapsed), True, (0, 0, 0), (255, 255, 255))
        self.fixed_screen.blit(time_text, (1100, 50))
        
        # Display vehicles for fixed timing
        for vehicle in fixed_simulation:
            self.fixed_screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()
        
        # Mirror accident display if needed
        if accidentOccurred and accidentBlinkTimer < 15:
            direction = directionNumbers[accidentDirection]
            displayDirection = directionDisplay[direction]
            
            accident_text = self.font.render(f"ACCIDENT ON {displayDirection} LANE!", True, (255, 0, 0), (255, 255, 255))
            accident_rect = accident_text.get_rect(center=(700, 50))
            self.fixed_screen.blit(accident_text, accident_rect)
            
            accidentX = signalCoods[accidentDirection][0] + 15
            accidentY = signalCoods[accidentDirection][1] + 15
            pygame.draw.line(self.fixed_screen, (255, 0, 0), (accidentX-10, accidentY-10), (accidentX+10, accidentY+10), 4)
            pygame.draw.line(self.fixed_screen, (255, 0, 0), (accidentX-10, accidentY+10), (accidentX+10, accidentY-10), 4)

# Start the HTTP server (same as in original)
def start_server():
    server = HTTPServer(("0.0.0.0", 8000), TrafficSignalHandler)
    print(f"Server started at http://0.0.0.0:8000")
    server.serve_forever()

# Entry point
if __name__ == "__main__":
    DualSimulation() 