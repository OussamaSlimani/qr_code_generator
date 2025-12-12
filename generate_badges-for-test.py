import json
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from textwrap import wrap

# ==============================
# CONFIG
# ==============================
W, H = 600, 850
QR_SIZE = 380
BORDER = 22
QR_TOTAL = QR_SIZE + 2 * BORDER
DPI = (100, 100)

# ==============================
# FONT LOADER
# ==============================
def F(size, bold=True):
    fonts = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Helvetica-Bold.ttf" if bold else "Helvetica.ttf",
    ]
    for f in fonts:
        try:
            return ImageFont.truetype(f, size)
        except:
            pass
    return ImageFont.load_default()

# ==============================
# QR GENERATOR WITH ROUNDED WHITE OUTLINE
# ==============================
def make_qr_badge(data):
    qr = qrcode.QRCode(
        box_size=10,
        border=2,
        error_correction=qrcode.ERROR_CORRECT_H
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    img = img.resize((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)

    badge = Image.new("RGBA", (QR_TOTAL, QR_TOTAL), (255, 255, 255))

    # QR rounded mask
    mask = Image.new("L", (QR_SIZE, QR_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, QR_SIZE - 1, QR_SIZE - 1), radius=34, fill=255)

    rounded_qr = Image.new("RGBA", (QR_SIZE, QR_SIZE))
    rounded_qr.paste(img, (0, 0))
    rounded_qr.putalpha(mask)

    badge.paste(rounded_qr, (BORDER, BORDER), rounded_qr)

    # Full outline rounding
    full_mask = Image.new("L", (QR_TOTAL, QR_TOTAL), 0)
    draw = ImageDraw.Draw(full_mask)
    draw.rounded_rectangle((0, 0, QR_TOTAL - 1, QR_TOTAL - 1), radius=42, fill=255)
    badge.putalpha(full_mask)

    return badge

# ==============================
# CENTERED TEXT
# ==============================
def draw_centered(draw, text, y, size, color=(255, 255, 255), bold=True):
    font = F(size, bold)
    w = draw.textbbox((0, 0), text, font=font)[2]
    x = (W - w) // 2
    draw.text((x, y), text, fill=color, font=font)

# ==============================
# MAIN
# ==============================
try:
    people = json.load(open("participants-test.json", encoding="utf-8"))
except Exception as e:
    print("Error:", e)
    exit()

Path("badges-enis").mkdir(exist_ok=True)
print(f"Generating {len(people)} clean badges...\n")

for p in people:
    name = p.get("name", "No Name").strip().upper()
    pid = str(p.get("id", "000")).zfill(3)
    pbranch = str(p.get("studentBranch", "0000")).zfill(3)

    if not name or name == "NO NAME":
        continue

    bg = Image.new("RGB", (W, H), (15, 22, 50))
    draw = ImageDraw.Draw(bg)

    # -----------------------------
    # QR CENTER POSITION
    # -----------------------------
    qr_x = (W - QR_TOTAL) // 2
    qr_y = (H - QR_TOTAL) // 2 + 40

    qr_badge = make_qr_badge(pid)
    bg.paste(qr_badge, (qr_x, qr_y), qr_badge)

    # -----------------------------
    # NAME — centered at top
    # -----------------------------
    font_size = 40
    temp_font = F(font_size)

    if draw.textbbox((0, 0), name, font=temp_font)[2] > W - 100:
        wrapped = wrap(name, 22)

        if len(wrapped) >= 2:
            draw_centered(draw, wrapped[0], 60, 40)
            draw_centered(draw, " ".join(wrapped[1:3]), 100, 40, color=(220, 240, 255))
        else:
            draw_centered(draw, name, 70, 40)
    else:
        draw_centered(draw, name, 70, 40)

    # -----------------------------
    # BRANCH — TOP QR
    # -----------------------------
    draw_centered(draw, pbranch, qr_y - 90, 40, color=(255, 255, 255), bold=True)

    # -----------------------------
    # ID — elegant bottom small
    # -----------------------------
    draw_centered(draw, pid, qr_y + QR_TOTAL + 70, 38, color=(170, 210, 255), bold=False)

    # -----------------------------
    # SAVE
    # -----------------------------
    file = f"badges-enis/{pid}.jpg"
    bg.convert("RGB").save(file, "JPEG", quality=90, dpi=DPI)

    size_kb = os.path.getsize(file) // 1024
    print(f"{pid} → {name[:30]:30} → {size_kb} KB")

print("\nAll badges ready.\n")
