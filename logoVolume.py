from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Load the image
image_path = r"C:\Users\yegor\Desktop\Atlas\Atlas.png"
logo_image = Image.open(image_path).convert('L')  # Convert to grayscale

# Convert image to numpy array
image_array = np.array(logo_image)

# Create x, y coordinates
x = np.arange(0, image_array.shape[1])
y = np.arange(0, image_array.shape[0])
x, y = np.meshgrid(x, y)

# Create a 3D plot
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Use the pixel values as heights for the 3D plot
ax.plot_surface(x, y, image_array, cmap='gray', rstride=1, cstride=1)

# Setting labels and title
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_zlabel('Intensity')
ax.set_title('3D Mesh of Logo')

# Display the plot
plt.show()
