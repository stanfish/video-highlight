"""
Test script for memory monitoring utilities.
Run this to verify memory estimation is working correctly.
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.memory_monitor import (
    get_available_memory,
    get_total_memory,
    format_memory_size,
    estimate_total_memory,
    check_memory_safety,
    calculate_optimal_batch_size
)


def test_memory_info():
    """Test basic memory information retrieval."""
    print("=== System Memory Information ===")
    total = get_total_memory()
    available = get_available_memory()
    
    print(f"Total Memory: {format_memory_size(total)}")
    print(f"Available Memory: {format_memory_size(available)}")
    print(f"Used Memory: {format_memory_size(total - available)}")
    print(f"Memory Usage: {((total - available) / total * 100):.1f}%")
    print()


def test_memory_estimation(test_folder):
    """Test memory estimation for a folder of videos."""
    from src.utils.file_manager import get_media_files
    
    print(f"=== Memory Estimation Test ===")
    print(f"Test folder: {test_folder}")
    
    if not os.path.exists(test_folder):
        print(f"Error: Folder does not exist: {test_folder}")
        return
    
    videos, images = get_media_files(test_folder)
    all_media = videos + images
    
    print(f"Found {len(videos)} videos and {len(images)} images")
    
    if not all_media:
        print("No media files found.")
        return
    
    # Estimate memory
    clip_duration = 5.0  # Average clip duration
    memory_estimate = estimate_total_memory(all_media, target_width=1920, 
                                           clip_duration=clip_duration)
    
    print(f"\nEstimated total memory: {format_memory_size(memory_estimate['total_estimated'])}")
    print(f"Estimated peak memory: {format_memory_size(memory_estimate['peak_memory'])}")
    
    # Check safety
    is_safe, warning_level, message = check_memory_safety(memory_estimate['peak_memory'])
    print(f"\nSafety check: {warning_level.upper()}")
    print(message)
    
    # Calculate optimal batch size
    batch_size = calculate_optimal_batch_size(all_media, target_width=1920, 
                                             clip_duration=clip_duration)
    print(f"\nRecommended batch size: {batch_size}")
    
    # Show per-file breakdown (first 5 files)
    print(f"\nPer-file estimates (first 5):")
    for filename, estimated in memory_estimate['per_file'][:5]:
        print(f"  {filename}: {format_memory_size(estimated)}")
    
    if len(memory_estimate['per_file']) > 5:
        print(f"  ... and {len(memory_estimate['per_file']) - 5} more files")
    
    print()


def main():
    """Run all tests."""
    print("Memory Monitor Test Suite\n")
    
    # Test 1: System memory info
    test_memory_info()
    
    # Test 2: Memory estimation (if test folder provided)
    if len(sys.argv) > 1:
        test_folder = sys.argv[1]
        test_memory_estimation(test_folder)
    else:
        print("=== Memory Estimation Test ===")
        print("To test memory estimation, run:")
        print(f"  python {os.path.basename(__file__)} <path_to_video_folder>")
        print()
    
    print("✅ Tests complete!")


if __name__ == "__main__":
    main()
