import os
import time

print(os.path.realpath(os.environ['APPDATA']))
time.sleep(1)
print(os.listdir(os.environ['APPDATA']))
time.sleep(10)
