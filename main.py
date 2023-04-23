import serial
from time import *
import RPi.GPIO as GPIO

port = serial.Serial('/dev/serial0', baudrate=230400, timeout=3.0, parity='N', stopbits=1)

class VibrationMotorRangeLink:
    def __init__(self, port, threshold, name, start, end):
        #GPIO.setup(port, GPIO.OUT)
        self._active = False
        self._threshold = threshold
        self._name = name
        self.points = dict.fromkeys(range(start, end))

    def update_data(self, data_points):
        for point in data_points:
            if point[1] in self.points:
                self.points[point[1]] = point[0]
        
        object_detected = False
        for point in self.points.values():
            if point == None:
                continue
            if point.distance <= self._threshold:
                object_detected = True
                break
            object_detected = False
        
        if object_detected == self._active:
            return
        
        self._active = object_detected
        print('%s vibration motor %s' % ("Activating" if self._active else "Deactivating", self._name))

    def __str__(self) -> str:
        string = ""
        for key in self.points.keys():
            string += "{key}: {point}\n".format(key=key, point=self.points[key])

class DataPoint:

    def __init__(self):
        self.distance = int.from_bytes(port.read(2), "little")
        self.intensity = int.from_bytes(port.read(), "big")

    def print(self):
        print('\tDistance: %d, Intensity: %d' % (self.distance, self.intensity))

    def __str__(self) -> str:
        return "(%f, %f)" % self.distance, self.intensity

class LidarFrame:

    def __init__(self):
        self.header = port.read().hex()
        while self.header != b'\x54'.hex():
            self.header = port.read().hex()
        
        port.read()  # Skip over the data size since it's just a fixed number of 12.
        self.spd = int.from_bytes(port.read(2), "little")
        self.start_angle = int.from_bytes(port.read(2), "little")/100.0
        self.data_points = []
        for i in range(12):
            self.data_points.append(DataPoint())
        self.end_angle = int.from_bytes(port.read(2), "little")/100.0
        self.timestamp = int.from_bytes(port.read(2), "little")
        self.crc8 = int.from_bytes(port.read(), "big")
    
    def print(self):
        print('Speed: %d' % self.spd)
        print('Start Angle: %d' % self.start_angle)
        print('Data Points:')
        for i in range(12):
            print(self.data_points[i])
        print('End angle: %d' % self.end_angle)
        print('Timestamp: %d' % self.timestamp)
        print('Crc8: %d' % self.crc8)

    def get_points_within_angles(self, start, end):
        filtered_data = []
        
        # Linearly interpolate the angle to get the angle per data point
        step = self.get_step()
        
        for i in range(len(self.data_points)):
            angle = (self.start_angle + (step*i)) % 360
            
            if start <= angle <= end:
                filtered_data.append([self.data_points[i], angle])
        return filtered_data
    
    
    def get_step(self):
        step = 0
        if self.end_angle > self.start_angle:
            step = (self.end_angle - self.start_angle)/11.0
        else:
            end_angle = self.end_angle + 360.0
            step = (end_angle - self.start_angle)/11.0
        
        return step
    
    
    def get_points_and_angles(self):
        tuples = []
        
        step = self.get_step()
        
        for i in range(len(self.data_points)):
            angle = (self.start_angle + (step*i)) % 360
            tuples.append([self.data_points[i], int(angle)])
        
        return tuples


# Starts GPIO pin #4 with constant output.
GPIO.setmode(GPIO.BCM)
# Do the same setup for all other GPIO pins that are supposed to be used.

try:


    # CHANGE THESE TO THE CORRECT PINS WHEN THEY ARE ACTUALLY CONNECTED.
    motor_left = VibrationMotorRangeLink(4, 50, "Left", 210, 250)
    motor_middle = VibrationMotorRangeLink(5, 50, "Middle", 250, 290)
    motor_right = VibrationMotorRangeLink(6, 50, "Right", 290, 330)
    
    
    # Main program loop here.
    while True:
        frame = LidarFrame()

        #The overall angle coverage is between 210 and 330 degrees
        left_points = frame.get_points_within_angles(210, 250)
        center_points  = frame.get_points_within_angles(251, 290)
        right_points  = frame.get_points_within_angles(291, 330)

        motor_left.update_data(left_points)
        motor_middle.update_data(center_points)
        motor_right.update_data(right_points)

        print(motor_left)

except KeyboardInterrupt:
    GPIO.cleanup()

