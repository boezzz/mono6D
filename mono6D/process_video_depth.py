import cv2
import os
import numpy as np
import argparse
from tqdm import tqdm
from gradio_client import Client, handle_file
import tempfile
import shutil

def process_video_depth(input_video_path, output_video_path=None, hf_token=None):
    """
    Process a video file to generate depth maps for each frame and create a depth video.
    
    Args:
        input_video_path: Path to the input video file
        output_video_path: Path to save the output depth video (if None, uses input name + "_depth.mp4")
        hf_token: HuggingFace token for accessing the API (if None, uses HF_TOKEN environment variable)
    
    Returns:
        Path to the output depth video
    """
    # Set output path if not provided
    if output_video_path is None:
        filename, ext = os.path.splitext(input_video_path)
        output_video_path = f"{filename}_depth.mp4"
    
    # Get HuggingFace token from environment variable if not provided
    if hf_token is None:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("Warning: No HuggingFace token provided. Some models may require authentication.")
            print("You can set it using the --token parameter or the HF_TOKEN environment variable.")
    
    # Create a temporary directory to store frames
    temp_dir = tempfile.mkdtemp()
    frames_dir = os.path.join(temp_dir, "frames")
    depth_dir = os.path.join(temp_dir, "depth")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(depth_dir, exist_ok=True)
    
    # Initialize the Gradio client for depth estimation
    print("Initializing Depth-Anywhere model...")
    client = Client("Albert-NHWang/Depth-Anywhere-App", hf_token=hf_token)
    
    try:
        # Open the video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video info: {width}x{height}, {fps} fps, {frame_count} frames")
        
        # Extract frames and process depth
        frame_idx = 0
        
        # Setup progress bar
        with tqdm(total=frame_count, desc="Processing frames") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Save the frame to the temporary directory
                frame_path = os.path.join(frames_dir, f"frame_{frame_idx:04d}.png")
                cv2.imwrite(frame_path, frame)
                
                # Process the frame for depth estimation
                try:
                    depth_result = client.predict(
                        path=frame_path,
                        api_name="/depth"
                    )
                    # Copy the depth result to our depth directory
                    depth_path = os.path.join(depth_dir, f"depth_{frame_idx:04d}.png")
                    shutil.copy(depth_result, depth_path)
                except Exception as e:
                    print(f"Error processing frame {frame_idx}: {e}")
                    # Create a blank depth map in case of error
                    blank_depth = np.zeros((height, width), dtype=np.uint8)
                    depth_path = os.path.join(depth_dir, f"depth_{frame_idx:04d}.png")
                    cv2.imwrite(depth_path, blank_depth)
                
                frame_idx += 1
                pbar.update(1)
        
        # Release the video capture
        cap.release()
        
        # Create video from depth frames
        print("Creating depth video...")
        
        # Initialize video writer with H.264 codec
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        depth_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height), False)
        
        # Fallback to other codecs if avc1 isn't available
        if not os.path.exists(output_video_path) or os.path.getsize(output_video_path) == 0:
            print("H.264 codec not available, trying MJPG...")
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            depth_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height), False)
        
        # Write depth frames to video
        for i in range(frame_idx):
            depth_path = os.path.join(depth_dir, f"depth_{i:04d}.png")
            if os.path.exists(depth_path):
                depth_frame = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
                depth_video.write(depth_frame)
            else:
                print(f"Warning: Depth frame {i} not found")
        
        # Release the video writer
        depth_video.release()
        
        print(f"Depth video saved to: {output_video_path}")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
    
    return output_video_path