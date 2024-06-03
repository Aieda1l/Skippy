import cv2
import numpy as np
import mss
import ctypes
import time
import math

# Screen grabber module
from lib.grab import grab_screen

# Initialize the screen capture object
sct = mss.mss()
Wd, Hd = sct.monitors[1]["width"], sct.monitors[1]["height"]
PUL = ctypes.POINTER(ctypes.c_ulong)

# Size of screen capture
ACTIVATION_RANGE = 600

# Size (in pixels) of what to scale the screen capture up to
target_width = int(ACTIVATION_RANGE)

# Define the player's field of view (FOV)
fov_degrees = 220

# Define the angle which the player is facing
player_degrees = 0

# Define screen capture area (top-left corner)
print("[INFO] Loading screen capture device...")
W, H = None, None
origbox = (0, 0, ACTIVATION_RANGE, ACTIVATION_RANGE)

# Define the maximum raycast length
max_ray_length = 400  # You can change this value as needed

# Define the number of rays to emit
num_rays = math.floor(fov_degrees / 8) # Edit this value as needed

# Initial minimap center values
a, b, radius = 0, 0, 0

# Initialize variables for calculating FPS
frame_count = 0
start_time = time.time()

# Initialize the FPS display text
fps_text = ""

# Define the kernel for morphological closing
val = 5  # Change this value as needed
kernel = np.ones((val, val), np.uint8)

# Get minimap center
def get_minimap_center():
    image = np.array(grab_screen(region=origbox))

    # Resize the frame to target width while preserving the aspect ratio
    scale_factor = target_width / ACTIVATION_RANGE
    target_height = int(image.shape[0] * scale_factor)
    image = cv2.resize(image, (target_width, target_height))

    # Apply Canny edge detection
    monoimage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(monoimage, 10, 100)

    # Find circles in the edge-detected image
    detected_circles = cv2.HoughCircles(
        edges,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=1,
        param2=15,
        minRadius=100,
        maxRadius=300
    )

    # Apply Hough transform on the blurred image.
    """detected_circles = cv2.HoughCircles(edges, 
                       cv2.HOUGH_GRADIENT, 1, 20, param1 = 1,
                   param2 = 15, minRadius = 100, maxRadius = 300)"""

    if detected_circles is not None:
      
        # Convert the circle parameters a, b and r to integers.
        detected_circles = np.uint16(np.around(detected_circles))

        pt = detected_circles[0, :][0]  # Get the parameters of the first circle
        return pt[0], pt[1], pt[2]
    
    return 0, 0, 0

while True:
    image = np.array(grab_screen(region=origbox))

    # If the frame dimensions are empty, grab them
    if W is None or H is None:
        (H, W) = image.shape[:2]

    # Resize the frame to target width while preserving the aspect ratio
    scale_factor = target_width / ACTIVATION_RANGE
    target_height = int(image.shape[0] * scale_factor)
    image = cv2.resize(image, (target_width, target_height))

    monoimage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY, (5, 5), 0)

    # Apply edge detection
    edges = cv2.Canny(monoimage, 100, 200)

    # Perform morphological closing to connect gaps in the edges
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Get the center of the image (the player's position)    
    center = (edges.shape[1] // 2, edges.shape[0] // 2)

    # Get center of minimap
    if a == 0 or b == 0:
        a, b, radius = get_minimap_center()
    
    if not a == 0 and not b == 0:
        center = (a, b - 20)

    # Create an empty image to visualize the FOV
    fov_image = np.zeros_like(edges)

    # Initialize an empty list to store ray endpoints
    ray_endpoints = []

    # Cast rays within the FOV
    for angle in np.linspace(-fov_degrees / 2, fov_degrees / 2, num_rays):  # Using num_rays here
        # Convert the angle to radians
        angle_rad = np.radians(angle + player_degrees - 90)

        # Starting point of the ray
        start_point = center

        for r in range(max_ray_length):  # Use the variable for max ray length
            # Calculate the end point of the ray
            end_point = (int(start_point[0] + r * np.cos(angle_rad)), int(start_point[1] + r * np.sin(angle_rad)))

            # Check if the end_point is within the bounds of the edges array
            if 0 <= end_point[0] < edges.shape[1] and 0 <= end_point[1] < edges.shape[0]:
                # If the ray hits an edge, stop
                if edges[end_point[1], end_point[0]] != 0:
                    break
            else:
                # If the end_point is out of bounds, break the loop
                break
            
        # Add the endpoint to the list
        ray_endpoints.append(end_point)

    ray_endpoints = np.array(ray_endpoints)

    height, width, _ = image.shape
    #image = np.zeros((height, width, 3), dtype=np.uint8)

    alpha = 0.5

    overlay = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2RGB)
    output = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2RGB)

    cv2.fillPoly(overlay, pts=[ray_endpoints], color=(251, 153, 87))
    cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)

    cv2.polylines(output, pts=[ray_endpoints], isClosed=True, color=(251, 153, 87), thickness=2, lineType=cv2.LINE_AA)
    cv2.circle(output, (a, b), radius, (251, 153, 87), 2)
    cv2.circle(output, center, 5, (0, 0, 255), -1)

    # Scale up final image
    scale_factor = ACTIVATION_RANGE / target_width
    target_height = int(output.shape[0] * scale_factor)
    image = cv2.resize(output, (ACTIVATION_RANGE, target_height))

    # Calculate FPS
    frame_count += 1
    elapsed_time = time.time() - start_time
    if elapsed_time >= 1.0:
        fps = frame_count / elapsed_time
        fps_text = f"FPS: {int(fps)}"
        frame_count = 0
        start_time = time.time()

    # Display the FPS text on the final image
    cv2.putText(image, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Display the final image
    cv2.imshow("Neural Net Vision (Skippy)", image)

    if cv2.waitKey(1) & 0xFF == ord('0'):
        break

# Release resources
cv2.destroyAllWindows()
