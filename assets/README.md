# Assets

`shift-zero-hero.gif` (README) and `shift-zero-hero.mp4` (X/social) are
rendered from `render_hero.py`. Storyboard by Fable.

```bash
python3 assets/render_hero.py                 # 360 frames -> assets/build/
python3 assets/render_hero.py 12.8            # one still at t=12.8s, for review

cd assets
ffmpeg -framerate 20 -i build/f%04d.png -vf "palettegen=max_colors=64:stats_mode=full" build/pal.png
ffmpeg -framerate 20 -i build/f%04d.png -i build/pal.png \
  -lavfi "paletteuse=dither=none:diff_mode=rectangle" -loop 0 shift-zero-hero.gif
ffmpeg -framerate 20 -i build/f%04d.png -vf "scale=1280:720:flags=lanczos" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -r 30 -movflags +faststart shift-zero-hero.mp4
```

Needs Pillow, the Inter and DejaVu fonts, and ffmpeg.
