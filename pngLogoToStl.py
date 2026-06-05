import os
import cv2
import numpy as np
from stl import mesh

def generate_perfect_logo_stl(
    image_path, 
    output_stl_path, 
    target_width_mm=150.0, 
    backplate_thickness_mm=3.0, 
    logo_height_mm=1.5, 
    nozzle_diameter_mm=0.4, 
    inverse=False,
    resolution_limit=450, 
    threshold=127, 
    invert_logo=True, 
    edge_smoothing=1.2
):
    """
    Generates a single, perfectly scaled STL file.
    
    Parameters:
        image_path (str): Path to your PNG logo.
        output_stl_path (str): Path to save the output STL.
        target_width_mm (float): Exact width the model will have in OrcaSlicer.
        backplate_thickness_mm (float): Total thickness of the base plate.
        logo_height_mm (float): Extrusion height (or depth of the etch).
        nozzle_diameter_mm (float): Your printer nozzle size (filters out thin details).
        inverse (bool): 
            False -> Logo is ETCHED (carved) into the plate, leaving a solid floor.
            True -> Logo is RAISED (placed on top) of the plate.
        resolution_limit (int): Controls mesh density (450 gives sharp lines at ~20MB).
        threshold (int): Binary threshold (0 to 255).
        invert_logo (bool): True if your logo is dark on a light background.
        edge_smoothing (float): Smooths vertical walls to prevent printer vibrations.
    """
    print("Loading and preparing image...")
    # 1. Load image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Could not load image at {image_path}")
        return

    if invert_logo:
        img = cv2.bitwise_not(img)

    # Convert to clean black and white
    _, img_thresh = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)

    # 2. Filter out features smaller than the printer nozzle
    orig_h, orig_w = img.shape
    pixel_nozzle_width = int(round(nozzle_diameter_mm * (orig_w / target_width_mm)))
    
    if pixel_nozzle_width > 1:
        print(f"Filtering lines smaller than {nozzle_diameter_mm}mm (Nozzle limit)...")
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (pixel_nozzle_width, pixel_nozzle_width))
        img_filtered = cv2.morphologyEx(img_thresh, cv2.MORPH_OPEN, kernel)
    else:
        img_filtered = img_thresh

    # 3. Downsample to an optimized grid to keep file size lightweight
    aspect_ratio = orig_h / orig_w
    if orig_w >= orig_h:
        grid_w = resolution_limit
        grid_h = int(resolution_limit * aspect_ratio)
    else:
        grid_h = resolution_limit
        grid_w = int(resolution_limit / aspect_ratio)

    print(f"Optimizing mesh grid: {grid_w} x {grid_h}...")
    img_resized = cv2.resize(img_filtered, (grid_w, grid_h), interpolation=cv2.INTER_LANCZOS4)

    if edge_smoothing > 0:
        blur_size = int(edge_smoothing * 2) | 1
        img_resized = cv2.GaussianBlur(img_resized, (blur_size, blur_size), 0)

    # Normalize image values between 0.0 (background) and 1.0 (logo)
    img_normalized = img_resized / 255.0

    # 4. Generate the 3D grid with baked-in heights
    R, C = img_normalized.shape
    N = R * C
    scale_factor = target_width_mm / (C - 1)
    
    x_coords, y_coords = np.mgrid[0:R, 0:C]
    x_scaled = y_coords * scale_factor
    y_scaled = (R - 1 - x_coords) * scale_factor

    # Height logic based on Inverse setting
    if not inverse:
        # ETCHED MODE (Logo is carved down into the backplate)
        # Background is at full backplate thickness.
        # Logo is carved down, leaving a solid floor underneath.
        z_top = backplate_thickness_mm - (img_normalized * logo_height_mm)
    else:
        # RAISED MODE (Logo is placed on top of the backplate)
        # Background is at backplate thickness.
        # Logo rises above the backplate.
        z_top = backplate_thickness_mm + (img_normalized * logo_height_mm)

    # Base is flat at 0mm for perfect print bed adhesion
    z_bottom = np.zeros(N)

    # Combine top and bottom coordinates
    vertices_top = np.column_stack([x_scaled.ravel(), y_scaled.ravel(), z_top.ravel()])
    vertices_bottom = np.column_stack([x_scaled.ravel(), y_scaled.ravel(), z_bottom])
    vertices = np.vstack([vertices_top, vertices_bottom])

    print("Assembling watertight STL triangles...")
    # 5. Build STL faces using fast vectorized indexing
    idx = np.arange(N).reshape(R, C)
    
    v00 = idx[:-1, :-1].ravel()
    v01 = idx[:-1, 1:].ravel()
    v10 = idx[1:, :-1].ravel()
    v11 = idx[1:, 1:].ravel()
    
    # Top face triangles
    top_tri1 = np.column_stack([v00, v10, v01])
    top_tri2 = np.column_stack([v10, v11, v01])
    
    # Bottom plate triangles (flipped winding for downward facing normals)
    bottom_tri1 = np.column_stack([v00 + N, v01 + N, v10 + N])
    bottom_tri2 = np.column_stack([v10 + N, v01 + N, v11 + N])
    
    # Side walls
    tc_left = idx[:-1, 0]
    tn_left = idx[1:, 0]
    bc_left = tc_left + N
    bn_left = tn_left + N
    left_tri1 = np.column_stack([tc_left, bc_left, tn_left])
    left_tri2 = np.column_stack([tn_left, bc_left, bn_left])
    
    tc_right = idx[:-1, -1]
    tn_right = idx[1:, -1]
    bc_right = tc_right + N
    bn_right = tn_right + N
    right_tri1 = np.column_stack([tc_right, tn_right, bc_right])
    right_tri2 = np.column_stack([tn_right, bn_right, bc_right])
    
    tc_top = idx[0, :-1]
    tn_top = idx[0, 1:]
    bc_top = tc_top + N
    bn_top = tn_top + N
    top_tri1_wall = np.column_stack([tc_top, tn_top, bc_top])
    top_tri2_wall = np.column_stack([tn_top, bn_top, bc_top])
    
    tc_bottom = idx[-1, :-1]
    tn_bottom = idx[-1, 1:]
    bc_bottom = tc_bottom + N
    bn_bottom = tn_bottom + N
    bottom_tri1_wall = np.column_stack([tc_bottom, bc_bottom, tn_bottom])
    bottom_tri2_wall = np.column_stack([tn_bottom, bc_bottom, bn_bottom])
    
    all_faces = np.vstack([
        top_tri1, top_tri2,
        bottom_tri1, bottom_tri2,
        left_tri1, left_tri2,
        right_tri1, right_tri2,
        top_tri1_wall, top_tri2_wall,
        bottom_tri1_wall, bottom_tri2_wall
    ])
    
    # Build mesh object
    logo_mesh = mesh.Mesh(np.zeros(all_faces.shape[0], dtype=mesh.Mesh.dtype))
    logo_mesh.vectors[:, 0, :] = vertices[all_faces[:, 0]]
    logo_mesh.vectors[:, 1, :] = vertices[all_faces[:, 1]]
    logo_mesh.vectors[:, 2, :] = vertices[all_faces[:, 2]]
    
    # Save file
    output_dir = os.path.dirname(output_stl_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    logo_mesh.save(output_stl_path)
    print(f"Success! Saved perfect STL to: {output_stl_path}")


# --- RUN CONFIGURATION ---
if __name__ == "__main__":
    image_input = r"Atlas.png"
    stl_output = r"logo.stl"
    
    if os.path.exists(image_input):
        generate_perfect_logo_stl(
            image_path=image_input,
            output_stl_path=stl_output,
            target_width_mm=220.0,         # Exact physical width in OrcaSlicer
            backplate_thickness_mm=3.0,    # Overall plate thickness
            logo_height_mm=1.5,            # Extrusion height or etch depth
            nozzle_diameter_mm=0.4,        # Lines smaller than this will be deleted
            inverse=True,                 # False = Etched (carved in), True = Raised (on top)
            resolution_limit=450,          # High detail, lightweight (~18MB file)
            threshold=127,
            invert_logo=True,
            edge_smoothing=1.2
        )
    else:
        print(f"File not found: {image_input}")
