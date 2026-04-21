
import whisper
import subprocess
from datetime import timedelta

# ─── CONFIG ───────────────────────────────────────────────
VIDEO_PATH = "C:\\Users\\abhishek.k\\Downloads\\Apr_08_0446_pm_21s_202604081703_x8ucj.mp4"
OUTPUT_PATH = "C:\\Users\\abhishek.k\\Downloads\\output_subtitled.mp4"
WORDS_PER_CHUNK = 3
FONT_SIZE = 22
# ──────────────────────────────────────────────────────────

def format_time_ass(seconds):
    t = timedelta(seconds=seconds)
    total_seconds = int(t.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    centiseconds = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02}:{secs:02}.{centiseconds:02}"

def transcribe(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path, word_timestamps=True)
    words = []
    for segment in result["segments"]:
        for word in segment.get("words", []):
            words.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"]
            })
    return words

def build_ass(words, output_ass="subtitles.ass"):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(fontsize=FONT_SIZE)

    events = []

    # Group into chunks of WORDS_PER_CHUNK
    chunks = []
    for i in range(0, len(words), WORDS_PER_CHUNK):
        chunk = words[i:i+WORDS_PER_CHUNK]
        chunks.append(chunk)

    for chunk in chunks:
        chunk_start = chunk[0]["start"]
        chunk_end = chunk[-1]["end"]

        # For each word in chunk, highlight it while others are white
        for active_idx, active_word in enumerate(chunk):
            w_start = active_word["start"]
            w_end = active_word["end"]

            line = ""
            for idx, w in enumerate(chunk):
                if idx == active_idx:
                    # Blue highlight box + white text
                    line += r"{\3c&H8B0000&\bord3\shad0\p0}{\c&H00FFFFFF&\3c&HFF6600&}" + \
                            r"{\blur0}{\bord3\shad1\3c&HCC4400&}" + \
                            f"{{\\c&H00FFFFFF&\\3c&H0066FF&}}{w['word']} "
                else:
                    line += f"{{\\c&H00FFFFFF&}}{w['word']} "

            line = line.strip()
            events.append(
                f"Dialogue: 0,{format_time_ass(w_start)},{format_time_ass(w_end)},Default,,0,0,0,,{line}"
            )

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(events))

    print(f"✅ ASS file written: {output_ass}")
    return output_ass

def burn_subtitles(video_path, ass_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass={ass_path}",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Output video: {output_path}")

if __name__ == "__main__":
    print("🎬 Transcribing...")
    words = transcribe(VIDEO_PATH)

    print("📝 Building subtitles...")
    ass_file = build_ass(words)

    print("🔥 Burning into video...")
    burn_subtitles(VIDEO_PATH, ass_file, OUTPUT_PATH)