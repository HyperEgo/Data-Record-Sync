import os
import time
import random

def generate_log(begin, end, dir_path="raw_logs/"):
    
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
        
    with open(dir_path + "Mateo_" + time.asctime(begin) + ".txt", "w") as file:
        current_time = begin
        file_contents = ""
        categories = ("General", "Emergency", "High", "Low", "Medium")
        counter = 1
        while time.mktime(current_time) <= time.mktime(end):
            file_contents += time.strftime("%d %B %Y %H:%M:%S", current_time) + " - "
            file_contents += categories[random.randint(0, 4)] + " - "
            file_contents += "Hello, this is message number " + str(counter) + ".\n"
            counter += 1
            current_time = time.localtime(time.mktime(current_time) + 3)
        file.write(file_contents)