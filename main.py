from lib import skippy
import os

# Clear terminal
os.system('cls' if os.name == 'nt' else 'clear')

print('''
====================================
 Skippy: Neural-Network Aimbot (v0.1)
====================================

[INFO] press 'q' to quit or ctrl+C in console...''')

skippy = skippy.Skippy()
skippy.start()
