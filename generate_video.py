#!/usr/bin/env python3
"""
Direct video generation script for AutoVideoCraft
"""
import os
import sys
from pathlib import Path

# Add src to path
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT / "src"))

# Initialize environment
from autovideocraft.init_env import initialize
initialize()

from autovideocraft.config import load_config
from autovideocraft.pipeline import VideoPipeline

def main():
    print("=" * 50)
    print("AutoVideoCraft - Direct Video Generation")
    print("=" * 50)
    
    # Load config
    config = load_config()
    
    # Create pipeline
    pipeline = VideoPipeline(config)
    
    # Generate video with Qingming Festival topic
    topic = "清明节的习俗和文化"
    
    print(f"\nGenerating video about: {topic}")
    print("-" * 50)
    
    result = pipeline.generate(
        topic=topic,
        duration=30,
        language="中文",
    )
    
    print("-" * 50)
    if result.success:
        print(f"✅ Video generated successfully!")
        print(f"   Title: {result.title}")
        print(f"   Video: {result.video_path}")
        print(f"   Time: {result.elapsed_seconds:.1f}s")
        print(f"\n📝 Script:\n{result.script}")
    else:
        print(f"❌ Failed: {result.error}")
    
    return result

if __name__ == "__main__":
    main()