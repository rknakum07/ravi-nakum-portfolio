from pathlib import Path
from PIL import Image
import re

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "img"
HTML = ROOT / "index.html"

def webp(source: Path, target: Path, width: int, quality: int):
    image = Image.open(source).convert("RGB")
    if image.width > width:
        height = round(image.height * width / image.width)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    image.save(target, "WEBP", quality=quality, method=6)

# Hero: responsive mobile/tablet/desktop candidates.
hero = IMG / "hero-img.png"
webp(hero, IMG / "hero-img-480.webp", 480, 78)
webp(hero, IMG / "hero-img-900.webp", 900, 80)
webp(hero, IMG / "hero-img.webp", 1254, 82)

# Convert the before/after comparison screenshots to WebP.
for stem in ("Before", "After"):
    source = IMG / f"{stem}.png"
    webp(source, IMG / f"{stem.lower()}.webp", 720, 76)
    webp(source, IMG / f"{stem.lower()}-1600.webp", 1600, 80)

# Resize large project/service screenshots and create smaller responsive candidates.
for pattern in ("selected_work*.webp", "service*.webp"):
    for source in IMG.glob(pattern):
        if re.search(r"-\d+\.webp$", source.name):
            continue
        webp(source, source.with_name(source.stem + "-640.webp"), 640, 74)
        webp(source, source, 1200, 78)

# Testimonial screenshots are displayed smaller than full-width project previews.
for source in IMG.glob("testimonial_*.webp"):
    if re.search(r"-\d+\.webp$", source.name):
        continue
    webp(source, source.with_name(source.stem + "-600.webp"), 600, 74)
    webp(source, source, 1000, 76)

# Re-encode supporting photos without changing their filenames or layout.
for name in ("about-photo-1.webp", "about-photo-2.webp", "cta-phone-bg.webp"):
    source = IMG / name
    webp(source, source, 1086, 80)

html = HTML.read_text(encoding="utf-8")
html = html.replace(
    '<link rel="preload" as="image" href="img/hero-img.png" fetchpriority="high">',
    '<link rel="preload" as="image" href="img/hero-img-480.webp" imagesrcset="img/hero-img-480.webp 480w, img/hero-img-900.webp 900w, img/hero-img.webp 1254w" imagesizes="(max-width: 767px) 100vw, 50vw" fetchpriority="high">'
)
html = html.replace(
    '<img src="img/hero-img.png" alt="Ravi Nakum" draggable="false" fetchpriority="high" loading="eager" decoding="async">',
    '<img src="img/hero-img-900.webp" srcset="img/hero-img-480.webp 480w, img/hero-img-900.webp 900w, img/hero-img.webp 1254w" sizes="(max-width: 767px) 100vw, 50vw" width="1254" height="1254" alt="Ravi Nakum" draggable="false" fetchpriority="high" loading="eager" decoding="async">'
)

# Responsive srcsets for service and project cards.
for stem in [f"service{i}" for i in range(1, 6)] + [f"selected_work{i}" for i in range(1, 6)]:
    html = re.sub(
        rf'(<img\\b[^>]*?)src="img/{stem}\\.webp"([^>]*>)',
        rf'\\1src="img/{stem}.webp" srcset="img/{stem}-640.webp 640w, img/{stem}.webp 1200w" sizes="(max-width: 700px) 90vw, (max-width: 1100px) 45vw, 560px"\\2',
        html
    )

for i in range(1, 7):
    stem=f"testimonial_{i}"
    html = re.sub(
        rf'(<img\\b[^>]*?)src="img/{stem}\\.webp"([^>]*>)',
        rf'\\1src="img/{stem}.webp" srcset="img/{stem}-600.webp 600w, img/{stem}.webp 1000w" sizes="(max-width: 700px) 85vw, 520px"\\2',
        html
    )

html = html.replace('src="img/Before.png"', 'src="img/before.webp" srcset="img/before.webp 720w, img/before-1600.webp 1600w" sizes="(max-width: 700px) 100vw, 720px"')
html = html.replace('src="img/After.png"', 'src="img/after.webp" srcset="img/after.webp 720w, img/after-1600.webp 1600w" sizes="(max-width: 700px) 100vw, 720px"')
HTML.write_text(html, encoding="utf-8")
print("Optimized image assets and updated responsive image markup.")
