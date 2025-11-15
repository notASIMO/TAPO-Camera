# play_rtsp_audio.py
import subprocess
import sys
import pyaudio
import struct

# ---- CONFIG ----
USER = "Depasa"
PASSWORD = "tapo1234"
HOST = "10.239.197.233"
RTSP = f"rtsp://{USER}:{PASSWORD}@{HOST}:554/stream1"  # try /h264 if stream1 doesn't include audio

# audio params (match ffmpeg output)
SAMPLE_RATE = 16000   # common value; if audio is 44100 change accordingly
CHANNELS = 1
SAMPLE_WIDTH = 2      # bytes per sample for pcm_s16le

# ffmpeg command: decode audio to signed 16-bit little-endian PCM on stdout
ffmpeg_cmd = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-i", RTSP,
    "-vn",                     # no video
    "-acodec", "pcm_s16le",
    "-ac", str(CHANNELS),
    "-ar", str(SAMPLE_RATE),
    "-f", "s16le",
    "-"                        # output to stdout
]

def main():
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(SAMPLE_WIDTH),
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True,
                    frames_per_buffer=1024)

    # start ffmpeg subprocess
    proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**6)

    try:
        while True:
            data = proc.stdout.read(1024 * SAMPLE_WIDTH)  # read bytes
            if not data:
                print("No audio data (stream ended).")
                break
            stream.write(data)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        proc.kill()
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()