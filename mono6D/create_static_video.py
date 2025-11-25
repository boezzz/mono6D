import cv2
import argparse
import os
from tqdm import tqdm

def create_static_video(input_video_path, image_path, output_video_path=None):
    """
    Create a video with the same duration and fps as the input video,
    but containing only the provided static image for all frames.
    
    Args:
        input_video_path: Path to the reference video file
        image_path: Path to the static image to use for all frames
        output_video_path: Path to save the output video (if None, auto-generated)
        
    Returns:
        Path to the output video
    """
    # Set output path if not provided
    if output_video_path is None:
        input_filename, ext = os.path.splitext(input_video_path)
        image_basename = os.path.splitext(os.path.basename(image_path))[0]
        output_video_path = f"{input_filename}_{image_basename}_static.mp4"
    
    # Open the input video to get properties
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {input_video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Input video info: {width}x{height}, {fps} fps, {frame_count} frames")
    
    # Read the static image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not open image file: {image_path}")
    
    # Resize the image to match the video dimensions
    image = cv2.resize(image, (width, height))
    
    # Check if the image is grayscale or color
    is_grayscale = len(image.shape) == 2 or image.shape[2] == 1
    if is_grayscale:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # Initialize video writer with H.264 codec
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Fallback to other codecs if avc1 isn't available
    if not os.path.exists(output_video_path) or os.path.getsize(output_video_path) == 0:
        print("H.264 codec not available, trying MJPG...")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Write the static image for each frame
    print(f"Creating static video with {frame_count} frames...")
    for _ in tqdm(range(frame_count)):
        video_writer.write(image)
    
    # Release resources
    cap.release()
    video_writer.release()
    
    print(f"Static video saved to: {output_video_path}")
    return output_video_path

def main():
    parser = argparse.ArgumentParser(description="Create a video with static image matching input video format")
    parser.add_argument("input_video", help="Path to the input reference video file")
    parser.add_argument("image", help="Path to the static image to use for all frames")
    parser.add_argument("--output", "-o", help="Path for the output video (default: auto-generated)")
    
    args = parser.parse_args()
    
    create_static_video(args.input_video, args.image, args.output)

if __name__ == "__main__":
    main() 