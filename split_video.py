#!/usr/bin/env python3
"""视频分割脚本 - 将大视频分割成小段"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from moviepy.editor import VideoFileClip

def split_video(input_path, output_dir, num_parts=2):
    """将视频分割成指定数量的小段"""
    video = VideoFileClip(input_path)
    duration = video.duration
    
    part_duration = duration / num_parts
    
    print(f"视频总时长: {duration:.1f}秒")
    print(f"分割成 {num_parts} 部分，每部分约 {part_duration:.1f}秒")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    for i in range(num_parts):
        start_time = i * part_duration
        end_time = min((i + 1) * part_duration, duration)
        
        output_path = os.path.join(output_dir, f"{base_name}_part{i+1}.mp4")
        
        print(f"\n正在截取第 {i+1} 部分 ({start_time:.1f}s - {end_time:.1f}s)...")
        part = video.subclip(start_time, end_time)
        part.write_videofile(output_path, codec='libx264', audio_codec='aac', 
                            verbose=False, logger=None)
        
        file_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"✅ 第 {i+1} 部分已保存: {output_path} ({file_size:.1f}MB)")
    
    video.close()
    print("\n分割完成！")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python split_video.py <视频文件路径>")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_directory = os.path.dirname(input_video)
    
    split_video(input_video, output_directory, num_parts=2)