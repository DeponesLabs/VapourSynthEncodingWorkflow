import argparse
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def extract_audio(input_file: Path, output_file: Path, track_id: int) -> None:

    ext = input_file.suffix
    match ext:
        case "mp4":
            # mp4box syntax: 
            # $ mp4box -raw <track_id>:output=<output_file> <input_file>
            cmd = ["mp4box", "-raw", f"{track_id}:output={str(output_file)}", str(input_file)]
            decoder = "mp4box"
        case "mkv":
            # eac3to syntax: 
            # $ eac3to <input_file> <track_id>: <output_file>
            cmd = ["eac3to", str(input_file), f"{track_id}:", str(output_file)]
            decoder = "eac3to"
        case _:
            raise ValueError(f"Unsupported container format: {ext}")
    
    logger.info(f"[*] Executing demux: Extracting track {input_file} with {decoder}...")
    logger.info(f"[*] Executing: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        logger.info("[+] Audio extraction completed.")
    except subprocess.CalledProcessError as e:
        logger.info(f"[-] An error occured during demuxing audio: {e}")

def generate_vapoursynth(input_file: Path, vpy_file: Path):
    
    vpy_content = f"""import vapoursynth as vs
    core = vs.core
    clip = core.bs.VideoSource(source=r"{input_file.resolve()}")
    clip.set_output()
    """
    with open(vpy_file, "w", encoding="utf-8") as f:
        f.write(vpy_content)

def run_demux(args):
    
    input_file = Path(args.input)
    track_id = args.track
    
    if args.audio:
        audio_out = Path(args.audio)
    else:
        audio_out = input_file
        
    original_suffix = audio_out.suffix.lower()
    if original_suffix != '.wav':
        audio_out = audio_out.with_suffix('.wav')
    
    if args.output and original_suffix != '.wav':
        logger.warning(f"Audio extraction output can strictly be WAV. The extension was automatically changed from '{original_suffix}' to '.wav'.")
            
    extract_audio(input_file, audio_out, track_id)
    logger.info("[+] Demux completed!")

def run_encode_pipeline(args):
    """Executes the pipeline -> vpy -> pipe -> x264 workflow."""
    input_file = Path(args.input)
    audio_out = input_file.with_suffix('.aac')
    vpy_file = input_file.with_suffix('.vpy')

    # Demux
    logger.info(f"[*] Extracting track {args.audio} with eac3to...")
    subprocess.run(["eac3to", str(input_file), f"{args.audio}:", str(audio_out)], check=True)

    # Dynamic VapourSynth Project Generation
    logger.info(f"[*] Generating {vpy_file.name} project...")
    vpy_content = f"""import vapoursynth as vs
core = vs.core
clip = core.bs.VideoSource(source=r"{input_file.resolve()}")
clip.set_output()
"""
    with open(vpy_file, "w", encoding="utf-8") as f:
        f.write(vpy_content)

    # OS-Level Piping
    logger.info(f"[*] Initiating pipe: vspipe -> x264 (CRF {args.crf}, Preset: {args.preset})...")
    
    vspipe_cmd = ["vspipe", "-c", "y4m", str(vpy_file), "-"]
    
    x264_cmd = ["x264", "--demuxer", "y4m", "--crf", args.crf, "--preset", args.preset, "--profile", 
                args.profile, "--level", args.level, "--output", args.output, "-"]

    p_vspipe = subprocess.Popen(vspipe_cmd, stdout=subprocess.PIPE)
    p_x264 = subprocess.Popen(x264_cmd, stdin=p_vspipe.stdout)
    
    p_x264.wait()
    logger.info("[+] Full encode pipeline completed!")
