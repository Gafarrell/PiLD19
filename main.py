import serial

port = serial.Serial('/dev/serial0', baudrate=230400, timeout=3.0, parity='N', stopbits=1)


class DataPoint:

    def __init__(self):
        self.distance = int.from_bytes(port.read(2), "little")
        self.intensity = int.from_bytes(port.read(), "big")

    def print(self):
        print('\tDistance: %d, Intensity: %d' % (self.distance, self.intensity))


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
        step = (self.end_angle - self.start_angle)/11.0

        for i in range(len(self.data_points)):
            angle = self.start_angle + (step*i)
            if start > end:
                if start >= angle >= end:
                    filtered_data.append([self.data_points[i], angle])
            else:
                if start <= angle <= end:
                    filtered_data.append([self.data_points[i], angle])
        return filtered_data


# Main program loop here.
while True:
    frame = LidarFrame()
    data_within_angle = frame.get_points_within_angles(0, 90)
    for point in data_within_angle:
        point[0].print()
        print('Detected at angle: %d' % point[1])
