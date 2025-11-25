import os
import numpy as np
import cv2
from scipy import ndimage

def inpaint_nans(mat):
    # Create a mask for NaN values
    mask = np.isnan(mat)
    
    # If no NaNs, return original
    if not np.any(mask):
        return mat
    
    # use OpenCV's inpainting
    mat_copy = mat.copy()
    # Convert NaN to 0
    mat_copy[mask] = 0
    # Convert mask to CV_8U type (required by OpenCV)
    mask_cv = mask.astype(np.uint8) * 255
    
    result = cv2.inpaint(
        src=mat_copy.astype(np.float32), 
        inpaintMask=mask_cv, 
        inpaintRadius=3, 
        flags=cv2.INPAINT_NS
    )
    
    return result

def create_inpainted_layer(filename):
    
    in_path = os.path.join('_extrapolated_layer', filename, filename)
    out_path = os.path.join('_inpainted_layer', filename)
    
    # Create output directory
    os.makedirs(out_path, exist_ok=True)
    
    # Read input images
    rgb_tex = cv2.imread(f"{in_path}_BG.png")
    rgb_tex = rgb_tex.astype(np.float32) / 255.0  # Convert to [0,1] range
    
    d_encoded = cv2.imread(f"{in_path}_BG_depth.png")
    d_encoded = d_encoded.astype(np.float32) / 255.0
    
    alpha = cv2.imread(f"{in_path}_BGA.png")
    if alpha is None:
        raise ValueError(f"Could not read alpha image: {in_path}_BGA.png")
    
    # Check dimensions and resize if necessary
    rgb_height, rgb_width = rgb_tex.shape[:2]
    depth_height, depth_width = d_encoded.shape[:2]
    alpha_height, alpha_width = alpha.shape[:2]
    
    print(f"RGB dimensions: {rgb_width}x{rgb_height}")
    print(f"Depth dimensions: {depth_width}x{depth_height}")
    print(f"Alpha dimensions: {alpha_width}x{alpha_height}")
    
    # Ensure depth matches RGB dimensions
    if rgb_width != depth_width or rgb_height != depth_height:
        print(f"Resizing depth to match RGB dimensions: {rgb_width}x{rgb_height}")
        d_encoded = cv2.resize(d_encoded, (rgb_width, rgb_height))
    
    # Always resize alpha to match RGB dimensions (fix for the IndexError)
    if rgb_width != alpha_width or rgb_height != alpha_height:
        print(f"Resizing alpha to match RGB dimensions: {rgb_width}x{rgb_height}")
        alpha = cv2.resize(alpha, (rgb_width, rgb_height))
    
    alpha = alpha.astype(np.float32) / 255.0
    alpha = alpha[:,:,0]  # Use first channel
    
    # Process color channels
    inpainted = np.zeros_like(rgb_tex)
    
    for i in range(3):
        bg_channel = rgb_tex[:,:,i].copy()
        bg_channel[alpha < 0.5] = np.nan
        inpainted[:,:,i] = inpaint_nans(bg_channel)
    
    # Save inpainted color image
    cv2.imwrite(os.path.join(out_path, f"{filename}_BG_inp.png"), 
                (inpainted * 255).astype(np.uint8))
    
    # Process depth
    bg_d = d_encoded[:,:,0].copy()
    bg_d[alpha < 0.5] = np.nan
    
    d_d = inpaint_nans(bg_d)
    
    depth_inpainted = np.zeros_like(d_encoded)
    for i in range(3):
        depth_inpainted[:,:,i] = d_d
    
    cv2.imwrite(os.path.join(out_path, f"{filename}_BGD_inp.png"), 
                (depth_inpainted * 255).astype(np.uint8))