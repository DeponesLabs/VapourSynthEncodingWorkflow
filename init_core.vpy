import os
import vapoursynth as vs

import os
from typing import Dict

def read_environ() -> Dict[str, str]:
    
    environ: Dict[str, str] = {}
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    environ[key] = value
    return environ

ENVIRON = read_environ()
INPUT_FILE = ENVIRON["INPUT_FILE"]

# Initialize the Core Engine
core = vs.core
print(str(core))
# Load L-SMASH Plugin Manually and Isolated
# core.std.LoadPlugin(path=r"E:\HOME\Documents\Encoding\libs\L-SMASH-Works-r1310.0.0.0\x64\LSMASHSource.dll")

# Load Source Video into Memory (using LWLibavSource)
clip = core.lsmas.LWLibavSource(source=ENVIRON["INPUT_FILE"])

print(f"Genişlik: {clip.width}px")
print(f"Yükseklik: {clip.height}px")
print(f"Toplam Kare Sayısı: {clip.num_frames}")
print(f"Kare Hızı (FPS): {clip.fps.numerator / clip.fps.denominator}")
print(f"Renk Formatı: {clip.format.name}")

# Crop the source
clip = core.std.Crop(clip, left=150, top=74, right=160, bottom=70)

# Preparation for Piping
# Deliver the processed video to the command line (terminal/vspipe)
clip.set_output()

# Pipeline Command: 
# $ vspipe -c y4m init_core.py - | x264.exe --demuxer y4m --crf 18 --preset slow --profile high --tune stillimage -o "raw_video.264" -

# Crop Preview Command:
# vspipe -c y4m init_core.py - | ffplay -i -