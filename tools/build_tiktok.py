#!/usr/bin/env python3
"""Build TikTok assets from verified Osoul Al-Diafa source photography."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "03-محتوى-المنصات" / "tiktok"
VIDEOS = OUT / "videos"
COVERS = OUT / "covers"
OVERLAYS = OUT / ".overlays"
W, H = 1080, 1920
GOLD = "#C5A059"
PEARL = "#F4EFE6"
AMIRI = "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf"
AMIRI_BOLD = "/usr/share/fonts/truetype/amiri/Amiri-Bold.ttf"

CITIES = [
    ("jeddah", "جدة"),
    ("yanbu", "ينبع"),
    ("badr", "بدر"),
    ("madinah", "المدينة المنورة"),
    ("makkah", "مكة المكرمة"),
]
SERVICES = [
    ("coffee-servers", "صبابين قهوة", "01-الصور-القديمة/team/team-7.webp"),
    ("gahwaji-mubashir", "قهوجيين ومباشرين", "01-الصور-القديمة/team/team-3.webp"),
    ("gahwajiyat", "قهوجيات", "01-الصور-القديمة/team/team-11.webp"),
    ("arabic-coffee-corner", "ركن قهوة عربية", "01-الصور-القديمة/drinks/drink-1.webp"),
    ("wedding-hospitality", "ضيافة أعراس", "01-الصور-القديمة/setups/setup-4.webp"),
    ("conference-hospitality", "ضيافة مؤتمرات", "01-الصور-القديمة/setups/setup-1.webp"),
    ("event-hospitality", "تجهيز ضيافة حفلات", "01-الصور-القديمة/setups/setup-3.webp"),
]


def cover_crop(src: Image.Image) -> Image.Image:
    src = src.convert("RGB")
    scale = max(W / src.width, H / src.height)
    resized = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - W) // 2)
    top = max(0, (resized.height - H) // 2)
    return resized.crop((left, top, left + W, top + H))


def fit_text(draw, text, max_width, start_size=92, min_size=54):
    for size in range(start_size, min_size - 1, -2):
        font = ImageFont.truetype(AMIRI_BOLD, size)
        box = draw.textbbox((0, 0), text, font=font, direction="rtl")
        if box[2] - box[0] <= max_width:
            return font
    return ImageFont.truetype(AMIRI_BOLD, min_size)


def make_overlay(service_ar, city_ar, icon):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    # Quiet cinematic gradients for mobile readability.
    for y in range(0, 700):
        alpha = int(190 * (1 - y / 700) ** 1.8)
        draw.line((0, y, W, y), fill=(0, 0, 0, alpha))
    for y in range(1260, H):
        alpha = int(175 * ((y - 1260) / (H - 1260)) ** 1.5)
        draw.line((0, y, W, y), fill=(0, 0, 0, alpha))

    title = f"{service_ar} {city_ar}"
    font = fit_text(draw, title, 900)
    draw.text((W - 90, 150), title, font=font, fill=PEARL, anchor="ra", direction="rtl",
              stroke_width=1, stroke_fill=(0, 0, 0, 120))
    draw.rounded_rectangle((W - 300, 285, W - 90, 291), radius=3, fill=GOLD)
    sub = ImageFont.truetype(AMIRI, 49)
    draw.text((W - 90, 330), "فخامة هادئة تليق بمناسبتك", font=sub, fill=PEARL,
              anchor="ra", direction="rtl")
    cta = ImageFont.truetype(AMIRI_BOLD, 48)
    draw.text((90, H - 155), "نجهّز مناسبتك بذوق سعودي", font=cta, fill=PEARL,
              anchor="la", direction="rtl")

    # 10% of width, 4% margin, 70% opacity; fixed lower-right throughout video.
    logo = icon.copy().convert("RGBA").resize((108, 108), Image.Resampling.LANCZOS)
    alpha = logo.getchannel("A").point(lambda p: int(p * 0.70))
    logo.putalpha(alpha)
    layer.alpha_composite(logo, (W - 43 - 108, H - 43 - 108))
    return layer


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    for p in (VIDEOS, COVERS, OVERLAYS):
        p.mkdir(parents=True, exist_ok=True)

    icon_png = OVERLAYS / "icon-gold.png"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ROOT / "01-الصور-القديمة/icon-gold.svg"),
         "-vf", "scale=512:512", str(icon_png)])
    icon = Image.open(icon_png)

    captions = ["# كابشنات تيك توك — أصول الضيافة", "", "كل فيديو مستقل لخدمة × مدينة. الهاشتاقات محلية ومحدودة.", ""]
    manifest = []
    for service_slug, service_ar, src_rel in SERVICES:
        src_path = ROOT / src_rel
        source = Image.open(src_path)
        base = cover_crop(source)
        for city_slug, city_ar in CITIES:
            stem = f"{service_slug}-{city_slug}"
            overlay = make_overlay(service_ar, city_ar, icon)
            overlay_path = OVERLAYS / f"{stem}.png"
            overlay.save(overlay_path, optimize=True)

            cover = base.convert("RGBA")
            cover.alpha_composite(overlay)
            cover_path = COVERS / f"{stem}.webp"
            cover.convert("RGB").save(cover_path, "WEBP", quality=82, method=6)

            video_path = VIDEOS / f"{stem}.mp4"
            # Subtle push-in on source photo; text and brand remain fixed.
            filt = (
                "[0:v]scale=1200:2134:force_original_aspect_ratio=increase,"
                "crop=1200:2134,zoompan=z='min(zoom+0.0008,1.08)':"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=120:s=1080x1920:fps=24[bg];"
                "[1:v]format=rgba[ov];[bg][ov]overlay=0:0:format=auto,format=yuv420p[v]"
            )
            run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(src_path),
                 "-loop", "1", "-i", str(overlay_path), "-filter_complex", filt,
                 "-map", "[v]", "-t", "5", "-r", "24", "-an", "-c:v", "libx264",
                 "-preset", "medium", "-crf", "25", "-movflags", "+faststart", str(video_path)])

            title = f"{service_ar} {city_ar}"
            captions += [f"## {title}", "", f"{title} — نجهّز مناسبتك بذوق سعودي وفخامة هادئة. تواصل مع أصول الضيافة للحجز.", "",
                         f"#أصول_الضيافة #{city_ar.replace(' ', '_')} #ضيافة_سعودية", ""]
            manifest.append({"file": str(video_path.relative_to(ROOT)), "cover": str(cover_path.relative_to(ROOT)),
                             "source": src_rel, "service": service_ar, "city": city_ar})

    (OUT / "captions.md").write_text("\n".join(captions), encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # Intermediate overlays are reproducible and not deliverables.
    for p in OVERLAYS.iterdir():
        p.unlink()
    OVERLAYS.rmdir()


if __name__ == "__main__":
    main()
