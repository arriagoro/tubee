"""Ensure FFmpeg is available - use imageio-ffmpeg as bundled fallback"""
import os
import shutil

def setup_ffmpeg():
    # Check if system ffmpeg exists
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    
    # Use imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        
        # Add to PATH
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = f"{ffmpeg_dir}:{current_path}"
        
        # Create ffprobe symlink if needed
        ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe")
        if not os.path.exists(ffprobe_path):
            # ffprobe is usually same binary as ffmpeg with different name
            import stat
            os.symlink(ffmpeg_exe, ffprobe_path)
        
        print(f"FFmpeg configured via imageio-ffmpeg: {ffmpeg_exe}")
        return True
    except Exception as e:
        print(f"FFmpeg setup warning: {e}")
        return False

setup_ffmpeg()
