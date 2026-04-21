# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 21:03:14 2026

@author: abhishek.k
"""

import os
import subprocess
import shutil
import whisper
from datetime import timedelta

FFMPEG_PATH = r"C:\Users\abhishek.k\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
os.environ["PATH"] += os.pathsep + FFMPEG_PATH

VIDEO_PATH = r"C:\Users\abhishek.k\Downloads\output_subtitled.mp4"
OUTPUT_PATH = r"C:\Users\abhishek.k\Downloads\output_cut.mp4"
WORD_TO_CUT = "wait"

def transcribe_words(video_path):
    print("🎬 Transcribing...")
    model = whisper.load_model("base")
    result = model.transcribe(video_path, word_timestamps=True)
    words = []
    for segment in result["segments"]:
        for word in segment.get("words", []):
            words.append({
                "word": word["word"].strip().lower(),
                "start": word["start"],
                "end": word["end"]
            })
    return words

def cut_word_from_video(video_path, output_path, word_to_cut):
    words = transcribe_words(video_path)

    # Find all occurrences of the word
    cuts = [(w["start"], w["end"]) for w in words if w["word"] == word_to_cut.lower()]
    
    if not cuts:
        print(f"❌ Word '{word_to_cut}' not found in video.")
        return

    print(f"✅ Found '{word_to_cut}' at: {cuts}")

    # Build keep segments (everything except the cut words)
    duration_cmd = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    total_duration = float(duration_cmd.stdout.strip())

    keep_segments = []
    prev_end = 0.0
    for start, end in sorted(cuts):
        if prev_end < start:
            keep_segments.append((prev_end, start))
        prev_end = end
    if prev_end < total_duration:
        keep_segments.append((prev_end, total_duration))

    print(f"📋 Keeping segments: {keep_segments}")

    # Write each segment to temp file
    temp_files = []
    for i, (start, end) in enumerate(keep_segments):
        temp = f"D:\\temp_seg_{i}.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(start),
            "-to", str(end),
            "-c", "copy",
            temp
        ], capture_output=True)
        temp_files.append(temp)

    # Write concat list
    concat_list = r"D:\concat_list.txt"
    with open(concat_list, "w") as f:
        for t in temp_files:
            f.write(f"file '{t}'\n")

    # Concat all segments
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        output_path
    ], capture_output=True)

    # Cleanup
    for t in temp_files:
        os.remove(t)
    os.remove(concat_list)

    print(f"✅ Done! Output: {output_path}")

if __name__ == "__main__":
    cut_word_from_video(VIDEO_PATH, OUTPUT_PATH, WORD_TO_CUT)