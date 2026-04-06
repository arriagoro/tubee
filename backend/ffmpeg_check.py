"""Check and set FFmpeg path at startup"""
import os
import subprocess
import shutil

def find_ffmpeg():
    """Find ffmpeg/ffprobe binaries and add to PATH"""
    # Common locations
    paths = [
        "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin",
        "/nix/store", "/app/.nixpacks/bin"
    ]
    
    for path in paths:
        if shutil.which("ffmpeg", path=path):
            os.environ["PATH"] = f"{path}:{os.environ.get('PATH', '')}"
            return True
    
    # Try installing via pip as last resort
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        os.environ["PATH"] = f"{ffmpeg_dir}:{os.environ.get('PATH', '')}"
        return True
    except Exception:
        pass
    
    return False

# Run at import
find_ffmpeg()
