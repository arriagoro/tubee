"""
Setup FFmpeg using imageio-ffmpeg bundled binary.
This runs at startup and configures ffmpeg/ffprobe paths.
"""
import os
import sys
import shutil

def setup():
    # Already available system-wide?
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    
    try:
        import imageio_ffmpeg as iio
        ffmpeg_path = iio.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        
        # Add to PATH
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        
        # Create ffprobe symlink/copy if missing
        ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe")
        if not os.path.exists(ffprobe_path):
            try:
                os.symlink(ffmpeg_path, ffprobe_path)
            except Exception:
                import shutil as sh
                sh.copy2(ffmpeg_path, ffprobe_path)
        
        print(f"[setup_ffmpeg] Using bundled FFmpeg: {ffmpeg_path}", file=sys.stderr)
    except Exception as e:
        print(f"[setup_ffmpeg] Warning: {e}", file=sys.stderr)

setup()
