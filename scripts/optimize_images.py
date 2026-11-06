from pathlib import Path
from PIL import Image
import re

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "img"
HTML = ROOT / "index.html"

# Keep source assets untouched. Build high-quality responsive WebP derivatives.
# Preserve alpha channels so transparent artwork never gets flattened to black.
def open_preserving_alpha(path: Path):
    im = Image.open(path)
    if "A" in im.getbands() or "transparency" in im.info:
        return im.convert("RGBA")
    return im.convert("RGB")

def save_variant(source: Path, target: Path, max_width: int, quality: int = 90):
    im = open_preserving_alpha(source)
    if im.width > max_width:
        height = round(im.height * max_width / im.width)
        im = im.resize((max_width, height), Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    im.save(target, "WEBP", quality=quality, method=6)

def variants(stem: str, source_name: str, widths: tuple[int, ...], quality: int = 90):
    source = IMG / source_name
    if not source.exists():
        print(f"Skip missing source: {source_name}")
        return
    for width in widths:
        target = IMG / f"{stem}-{width}.webp"
        save_variant(source, target, width, quality)

# Hero: three useful breakpoints, with a high-quality desktop candidate.
variants("hero-img", "hero-img.png", (480, 900, 1254), 92)

# Service and project previews: retain enough pixels for crisp retina displays.
for i in range(1, 6):
    variants(f"service{i}", f"service{i}.webp", (640, 1200), 91)
    variants(f"selected_work{i}", f"selected_work{i}.webp", (640, 1200), 91)

# Before/after comparison: larger candidates prevent enlarged mobile blur.
variants("before", "Before.png", (720, 1600), 92)
variants("after", "After.png", (720, 1600), 92)

# Testimonial previews render smaller, but remain high quality on high-density screens.
for i in range(1, 7):
    variants(f"testimonial_{i}", f"testimonial_{i}.webp", (480, 900), 91)

html = HTML.read_text(encoding="utf-8")

# Use the same responsive candidate set in both the preload and hero image.
hero_preload = (
    '<link rel="preload" as="image" href="img/hero-img-900.webp" '
    'imagesrcset="img/hero-img-480.webp 480w, img/hero-img-900.webp 900w, '
    'img/hero-img-1254.webp 1254w" imagesizes="(max-width: 767px) 100vw, 50vw" '
    'fetchpriority="high">'
)
preload_pattern = re.compile(r'<link\s+rel="preload"\s+as="image"[^>]*hero-img[^>]*>', re.I)
if preload_pattern.search(html):
    html = preload_pattern.sub(hero_preload, html, count=1)
else:
    html = html.replace("</head>", f"  {hero_preload}\n</head>", 1)

def update_img_tag(match, src, srcset, sizes):
    tag = match.group(0)
    tag = re.sub(r'\bsrc=(["\'])' + re.escape(src) + r'\1', f'src="{srcset.split(",")[0].split()[0]}"', tag, count=1)
    # Remove old responsive attributes before inserting the correct set.
    tag = re.sub(r'\s+srcset=(["\']).*?\1', '', tag, count=1)
    tag = re.sub(r'\s+sizes=(["\']).*?\1', '', tag, count=1)
    return tag[:-1] + f' srcset="{srcset}" sizes="{sizes}">'

def set_responsive_image(html_text, source, candidates, sizes):
    # Keep original alt text, loading, decoding and accessibility attributes.
    pattern = re.compile(r'<img\b[^>]*?\bsrc=(["\'])' + re.escape(source) + r'\1[^>]*>', re.I | re.S)
    srcset = ", ".join(f"img/{name} {width}w" for name, width in candidates)
    fallback = candidates[len(candidates)//2][0]
    def repl(m):
        tag = m.group(0)
        tag = re.sub(r'\bsrc=(["\'])' + re.escape(source) + r'\1', f'src="{fallback}"', tag, count=1)
        tag = re.sub(r'\s+srcset=(["\']).*?\1', '', tag, count=1)
        tag = re.sub(r'\s+sizes=(["\']).*?\1', '', tag, count=1)
        return tag[:-1] + f' srcset="{srcset}" sizes="{sizes}">'
    return pattern.sub(repl, html_text)

html = set_responsive_image(
    html, "img/hero-img.png",
    [("hero-img-480.webp", 480), ("hero-img-900.webp", 900), ("hero-img-1254.webp", 1254)],
    "(max-width: 767px) 100vw, 50vw"
)

for i in range(1, 6):
    for prefix in ("service", "selected_work"):
        source = f"img/{prefix}{i}.webp"
        html = set_responsive_image(
            html, source,
            [(f"{prefix}{i}-640.webp", 640), (f"{prefix}{i}-1200.webp", 1200)],
            "(max-width: 700px) 90vw, (max-width: 1100px) 45vw, 560px"
        )

for i in range(1, 7):
    source = f"img/testimonial_{i}.webp"
    html = set_responsive_image(
        html, source,
        [(f"testimonial_{i}-480.webp", 480), (f"testimonial_{i}-900.webp", 900)],
        "(max-width: 700px) 85vw, 520px"
    )

for name, stem in (("img/Before.png", "before"), ("img/After.png", "after")):
    html = set_responsive_image(
        html, name,
        [(f"{stem}-720.webp", 720), (f"{stem}-1600.webp", 1600)],
        "(max-width: 700px) 100vw, 720px"
    )

# CTA background is deliberately left byte-for-byte unchanged: it is already small,
# and preserving its original alpha/background avoids black matte artifacts.
# Create a clean, lossless CTA derivative without compositing or adding a background.
cta_source = IMG / "cta-phone-bg.webp"
if cta_source.exists():
    cta_image = open_preserving_alpha(cta_source)
    cta_target = IMG / "cta-phone-bg-clean.webp"
    save_kwargs = {"format": "WEBP", "lossless": True, "method": 6, "exact": True}
    icc_profile = Image.open(cta_source).info.get("icc_profile")
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile
    cta_image.save(cta_target, **save_kwargs)

html = html.replace("url('img/cta-phone-bg.webp')", "url('img/cta-phone-bg-clean.webp')")
HTML.write_text(html, encoding="utf-8")
print("Created high-quality responsive WebP variants; original assets and CTA background preserved.")
