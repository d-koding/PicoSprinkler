import time
from machine import RTC

"""
A schedule class that takes task functions
and sets them to run at specific times. This will turn off and on
specific relays based off a set schedule.

author: Dylan O'Connor
"""

class Schedule:
    def __init__(self):
        self.schedule = {}

    def add_task(self, day_of_week, hour, minute, task_function, *args):
        if day_of_week not in self.schedule:
            self.schedule[day_of_week] = []
        self.schedule[day_of_week].append((hour, minute, task_function, args))
    
    def remove_task(self, day_of_week, hour, minute, task_function, *args):
        if day_of_week not in self.schedule:
            self.schedule[day_of_week] = []
        # unfinished code

    def run(self):
        rtc = RTC()
        while True:
            current_time = rtc.datetime()
            day_of_week = current_time[3]  
            hour = current_time[4]     
            minute = current_time[5]  

            if day_of_week in self.schedule:
                tasks = self.schedule[day_of_week]
                for task in tasks:
                    task_hour, task_minute, task_function, args = task
                    if task_hour == hour and task_minute == minute:
                        print(f"Executing task for day {day_of_week} at {hour}:{minute}")
                        task_function(*args)
                        time.sleep(60)

            time.sleep(10)

