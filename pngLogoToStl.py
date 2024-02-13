import numpy as np
from stl import mesh
from PIL import Image, ImageFilter

def create_3d_mesh_with_enhanced_detail(image_path, output_path, resolution=(200, 200), backplate_thickness=2):
    # Load the image and convert to grayscale
    logo_image = Image.open(image_path).convert('L')

    # Apply a filter to enhance edges (attempt to interpret features)
    logo_image = logo_image.filter(ImageFilter.FIND_EDGES)

    # Resize for higher resolution
    logo_image = logo_image.resize(resolution, Image.LANCZOS)

    # Convert image to numpy array and normalize
    image_array = np.array(logo_image)
    normalized_array = image_array / 255.0

    # Creating the x, y coordinates and z as the normalized pixel values
    x_len, y_len = normalized_array.shape
    x = np.arange(0, x_len, 1)
    y = np.arange(0, y_len, 1)
    x, y = np.meshgrid(x, y)
    z = normalized_array * 10  # Scale the heights to improve printability

    # Add backplate vertices
    backplate_z = -np.ones((x_len, y_len)) * backplate_thickness
    backplate_vertices = np.stack([x.ravel(), y.ravel(), backplate_z.ravel()], axis=1)

    # Combine the logo and backplate vertices
    vertices = np.vstack([np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1), backplate_vertices])

    # Creating the faces for the STL
    faces = []
    for i in range(x_len - 1):
        for j in range(y_len - 1):
            # Each square in the mesh consists of two triangles (for the logo)
            v1 = i * y_len + j
            v2 = v1 + y_len
            v3 = v1 + 1
            v4 = v2 + 1
            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])

            # Backplate faces (bottom of the model)
            b_v1 = v1 + x_len * y_len
            b_v2 = v2 + x_len * y_len
            b_v3 = v3 + x_len * y_len
            b_v4 = v4 + x_len * y_len
            faces.append([b_v1, b_v2, b_v3])
            faces.append([b_v2, b_v4, b_v3])

    # Creating the mesh
    logo_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            logo_mesh.vectors[i][j] = vertices[f[j], :]

    # Save to STL
    logo_mesh.save(output_path)


# Path to files
image_path = r"C:\Users\yegor\Desktop\Atlas\Atlas.png"
output_stl_path = r"C:\Users\yegor\Desktop\ss.stl"

# Create and save the 3D mesh with enhanced detail and backplate
create_3d_mesh_with_enhanced_detail(image_path, output_stl_path)

output_stl_path
