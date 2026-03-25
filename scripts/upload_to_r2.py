#!/usr/bin/env python3
"""
Download assets from current sources and upload to Cloudflare R2
"""

import subprocess
import os
import urllib.parse
import time

R2_BUCKET = "mood42-assets"
R2_PUBLIC_URL = "https://pub-c60e3a4de388402ba5e40acbc497a6d6.r2.dev"
TEMP_DIR = "/tmp/mood42-assets"

# All tracks from tools.py CHANNEL_TRACKS
TRACKS = {
    # CH01
    "ch01_hanging_lanterns.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kalaido%20-%20Hanging%20Lanterns.mp3",
    "ch01_first_snow.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kerusu%20-%20First%20Snow.mp3",
    "ch01_lofi_experimentin.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kronicle%20-%20Lofi%20Experimentin%20%28No%20Copyright%20Hip%20Hop%20Music%29.mp3",
    # CH02
    "ch02_lofi_rain_beat.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28FREE%29%20Lo-fi%20Type%20Beat%20-%20Rain.mp3",
    "ch02_chill_jazzy_lofi.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/%5BNo%20Copyright%20Music%5D%20Chill%20Jazzy%20Lofi%20Hip-Hop%20Beat%20%28Copyright%20Free%29%20Music%20By%20KaizanBlu.mp3",
    "ch02_herbal_tea_jazz.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/%5BNon%20Copyrighted%20Music%5D%20Artificial.Music%20-%20Herbal%20Tea%20%5BLo-fi%5D.mp3",
    # CH03
    "ch03_swing_jazz_grooves.mp3": "https://archive.org/download/lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm/LOFI%20Music%E3%80%80Swing%20Jazz%20Grooves%20to%20Elevate%20Your%20Mood%20%EF%BD%9C%20Feel%20the%20Rhythm%20.mp3",
    "ch03_jazz_type_beat.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28no%20copyright%20music%29%20jazz%20type%20beat%20bread%20royalty%20free%20youtube%20music%20prod.%20by%20lukrembo.mp3",
    "ch03_deep_space_jazz.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/deep%20space%20-%20Ambient%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3",
    # CH04
    "ch04_synthwave_dreams.mp3": "https://archive.org/download/synthwave/synthwave.mp3",
    "ch04_cyberpunk_night.mp3": "https://archive.org/download/synthwave/cyberpunk.mp3",
    "ch04_defective_beats.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/defective%20-%20LofiTrap%20Style%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3",
    # CH05
    "ch05_cosmic_drift.mp3": "https://archive.org/download/dx_ambient/05_ambient.mp3",
    "ch05_deep_ambient.mp3": "https://archive.org/download/dx_ambient/02_ambient.mp3",
    "ch05_night_meditation.mp3": "https://archive.org/download/dx_ambient/06_ambient.mp3",
    # CH06
    "ch06_finite_dreams.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/finite%20-%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3",
    "ch06_onion_lukrembo.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Onion%20%28Prod.%20by%20Lukrembo%29.mp3",
    "ch06_tranquillity.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Tranquillity%20-%20Chill%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3",
    # CH07
    "ch07_dancing_on_my_own.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Outgoing%20Hikikomori%20-%20Dancing%20On%20My%20Own%20%28No%20copyright%20lo%20fi%20beat%29.mp3",
    "ch07_take_care_surf.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/%E3%81%91%EF%BD%8D%20SURF%20-%20Take%20Care.mp3",
    "ch07_waves.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/Matt%20Quentin%20-%20Waves.mp3",
    # CH08
    "ch08_focus_ambient.mp3": "https://archive.org/download/dx_ambient/03_ambient.mp3",
    "ch08_floating_ambient.mp3": "https://archive.org/download/dx_ambient/04_ambient.mp3",
    "ch08_ambient_space.mp3": "https://archive.org/download/dx_ambient/01_ambient.mp3",
    # CH09
    "ch09_sunset_drive.mp3": "https://archive.org/download/kalaido-hanging-lanterns_202101/flovry%20-%20car%20radio.mp3",
    "ch09_deep_electronic.mp3": "https://archive.org/download/dx_ambient/07_ambient.mp3",
    "ch09_electronic_dreams.mp3": "https://archive.org/download/dx_ambient/08_ambient.mp3",
    # CH10
    "ch10_soft_piano_dreams.mp3": "https://archive.org/download/dx_ambient/01_ambient.mp3",
    "ch10_rainy_window_piano.mp3": "https://archive.org/download/dx_ambient/02_ambient.mp3",
    "ch10_evening_reflection.mp3": "https://archive.org/download/dx_ambient/04_ambient.mp3",
}

# Videos - using Pexels which works reliably
VIDEOS = {
    # CH01 - Late Night coding
    "ch01_rain_window.mp4": "https://videos.pexels.com/video-files/2491284/2491284-hd_1920_1080_24fps.mp4",
    "ch01_city_timelapse.mp4": "https://videos.pexels.com/video-files/2795391/2795391-hd_1920_1080_25fps.mp4",
    "ch01_liquid_motion.mp4": "https://videos.pexels.com/video-files/3129671/3129671-hd_1920_1080_30fps.mp4",
    # CH02 - Rain Cafe
    "ch02_rainy_street.mp4": "https://videos.pexels.com/video-files/2491284/2491284-hd_1920_1080_24fps.mp4",
    "ch02_rain_drops.mp4": "https://videos.pexels.com/video-files/1448735/1448735-hd_1920_1080_24fps.mp4",
    "ch02_forest_sunlight.mp4": "https://videos.pexels.com/video-files/857251/857251-hd_1920_1080_25fps.mp4",
    # CH03 - Jazz Noir
    "ch03_city_lights.mp4": "https://videos.pexels.com/video-files/3129957/3129957-hd_1920_1080_24fps.mp4",
    "ch03_rain_puddles.mp4": "https://videos.pexels.com/video-files/2491284/2491284-hd_1920_1080_24fps.mp4",
    "ch03_downtown_traffic.mp4": "https://videos.pexels.com/video-files/1560089/1560089-hd_1920_1080_24fps.mp4",
    # CH04 - Synthwave
    "ch04_neon_grid.mp4": "https://videos.pexels.com/video-files/3129671/3129671-hd_1920_1080_30fps.mp4",
    "ch04_galaxy_travel.mp4": "https://videos.pexels.com/video-files/1409899/1409899-hd_1920_1080_25fps.mp4",
    "ch04_color_gradient.mp4": "https://videos.pexels.com/video-files/2098989/2098989-hd_1920_1080_30fps.mp4",
    # CH05 - Deep Space
    "ch05_stars.mp4": "https://videos.pexels.com/video-files/1409899/1409899-hd_1920_1080_25fps.mp4",
    "ch05_nebula.mp4": "https://videos.pexels.com/video-files/1851190/1851190-hd_1920_1080_30fps.mp4",
    "ch05_cosmic.mp4": "https://videos.pexels.com/video-files/3129671/3129671-hd_1920_1080_30fps.mp4",
    # CH06 - Tokyo Drift
    "ch06_neon_city.mp4": "https://videos.pexels.com/video-files/3129957/3129957-hd_1920_1080_24fps.mp4",
    "ch06_night_drive.mp4": "https://videos.pexels.com/video-files/1560089/1560089-hd_1920_1080_24fps.mp4",
    "ch06_rain_taxi.mp4": "https://videos.pexels.com/video-files/2491284/2491284-hd_1920_1080_24fps.mp4",
    # CH07 - Sunday Morning
    "ch07_sunrise.mp4": "https://videos.pexels.com/video-files/857251/857251-hd_1920_1080_25fps.mp4",
    "ch07_flowers.mp4": "https://videos.pexels.com/video-files/2098989/2098989-hd_1920_1080_30fps.mp4",
    "ch07_garden.mp4": "https://videos.pexels.com/video-files/857195/857195-hd_1920_1080_25fps.mp4",
    # CH08 - Focus
    "ch08_minimal.mp4": "https://videos.pexels.com/video-files/3129671/3129671-hd_1920_1080_30fps.mp4",
    "ch08_abstract.mp4": "https://videos.pexels.com/video-files/2098989/2098989-hd_1920_1080_30fps.mp4",
    "ch08_clouds.mp4": "https://videos.pexels.com/video-files/1851190/1851190-hd_1920_1080_30fps.mp4",
    # CH09 - Melancholy
    "ch09_rain_window.mp4": "https://videos.pexels.com/video-files/2491284/2491284-hd_1920_1080_24fps.mp4",
    "ch09_foggy_city.mp4": "https://videos.pexels.com/video-files/3129957/3129957-hd_1920_1080_24fps.mp4",
    "ch09_lonely_street.mp4": "https://videos.pexels.com/video-files/1560089/1560089-hd_1920_1080_24fps.mp4",
    # CH10 - Golden Hour
    "ch10_sunset.mp4": "https://videos.pexels.com/video-files/857251/857251-hd_1920_1080_25fps.mp4",
    "ch10_golden_light.mp4": "https://videos.pexels.com/video-files/2098989/2098989-hd_1920_1080_30fps.mp4",
    "ch10_ocean_sunset.mp4": "https://videos.pexels.com/video-files/1409899/1409899-hd_1920_1080_25fps.mp4",
}


def download_file(url, dest_path):
    """Download a file using curl with redirect following."""
    print(f"  Downloading: {os.path.basename(dest_path)}")
    result = subprocess.run(
        ["curl", "-sL", "-o", dest_path, url],
        capture_output=True,
        timeout=120
    )
    if result.returncode != 0:
        print(f"    ERROR: {result.stderr.decode()}")
        return False

    # Check file size
    if os.path.exists(dest_path):
        size = os.path.getsize(dest_path)
        if size < 1000:  # Less than 1KB is probably an error
            print(f"    ERROR: File too small ({size} bytes)")
            return False
        print(f"    OK ({size // 1024} KB)")
        return True
    return False


def upload_to_r2(local_path, r2_key):
    """Upload file to R2 using wrangler."""
    print(f"  Uploading: {r2_key}")
    result = subprocess.run(
        ["wrangler", "r2", "object", "put", f"{R2_BUCKET}/{r2_key}", "--file", local_path, "--remote"],
        capture_output=True,
        timeout=300
    )
    if result.returncode != 0:
        print(f"    ERROR: {result.stderr.decode()}")
        return False
    print(f"    OK")
    return True


def main():
    os.makedirs(f"{TEMP_DIR}/audio", exist_ok=True)
    os.makedirs(f"{TEMP_DIR}/video", exist_ok=True)

    print("=" * 50)
    print("DOWNLOADING & UPLOADING AUDIO TRACKS")
    print("=" * 50)

    audio_success = 0
    for filename, url in TRACKS.items():
        local_path = f"{TEMP_DIR}/audio/{filename}"
        if not os.path.exists(local_path):
            if download_file(url, local_path):
                if upload_to_r2(local_path, f"audio/{filename}"):
                    audio_success += 1
        else:
            print(f"  Skipping (exists): {filename}")
            if upload_to_r2(local_path, f"audio/{filename}"):
                audio_success += 1
        time.sleep(0.5)  # Rate limiting

    print(f"\nAudio: {audio_success}/{len(TRACKS)} uploaded")

    print("\n" + "=" * 50)
    print("DOWNLOADING & UPLOADING VIDEOS")
    print("=" * 50)

    video_success = 0
    for filename, url in VIDEOS.items():
        local_path = f"{TEMP_DIR}/video/{filename}"
        if not os.path.exists(local_path):
            if download_file(url, local_path):
                if upload_to_r2(local_path, f"video/{filename}"):
                    video_success += 1
        else:
            print(f"  Skipping (exists): {filename}")
            if upload_to_r2(local_path, f"video/{filename}"):
                video_success += 1
        time.sleep(0.5)

    print(f"\nVideo: {video_success}/{len(VIDEOS)} uploaded")

    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Public URL: {R2_PUBLIC_URL}")
    print("=" * 50)


if __name__ == "__main__":
    main()
