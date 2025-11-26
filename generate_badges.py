import json
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from textwrap import wrap

# --- Config ---
W, H = 600, 850
QR_SIZE = 380
BORDER = 22
QR_TOTAL = QR_SIZE + 2 * BORDER
DPI = (100, 100)

# --- Font loader ---
def F(size, bold=True):
    for name in [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Helvetica-Bold.ttf" if bold else "Helvetica.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except:
            pass
    return ImageFont.load_default()

# --- QR with white rounded border ---
def make_qr_badge(data):
    qr = qrcode.QRCode(box_size=10, border=2, error_correction=qrcode.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    img = img.resize((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)

    badge = Image.new("RGBA", (QR_TOTAL, QR_TOTAL), (255, 255, 255))

    mask = Image.new("L", (QR_SIZE, QR_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, QR_SIZE-1, QR_SIZE-1], radius=34, fill=255)

    rounded_qr = Image.new("RGBA", (QR_SIZE, QR_SIZE))
    rounded_qr.paste(img, (0, 0))
    rounded_qr.putalpha(mask)

    badge.paste(rounded_qr, (BORDER, BORDER), rounded_qr)

    # Full badge rounded corners
    full_mask = Image.new("L", (QR_TOTAL, QR_TOTAL), 0)
    draw = ImageDraw.Draw(full_mask)
    draw.rounded_rectangle([0, 0, QR_TOTAL-1, QR_TOTAL-1], radius=42, fill=255)
    badge.putalpha(full_mask)

    return badge

# --- Draw centered text ---
def draw_centered(draw, text, y, size, color=(255,255,255), bold=True):
    font = F(size, bold)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    draw.text((x, y), text, fill=color, font=font)

# --- Main ---
try:
    people = json.load(open("participants.json", encoding="utf-8"))
except Exception as e:
    print("Error:", e)
    exit()

Path("badges").mkdir(exist_ok=True)
print(f"Generating {len(people)} clean & balanced badges...\n")

for p in people:
    name = p.get("Full Name", "No Name").strip().upper()
    pid = str(p.get("ID", "000")).zfill(3)

    if not name or name == "NO NAME":
        continue

    bg = Image.new("RGB", (W, H), (15, 22, 50))
    draw = ImageDraw.Draw(bg)

    # === NAME (max 72pt, auto-split if too long) ===
    name_to_draw = name
    font_size = 40

    # Check if single line fits
    temp_font = F(font_size)
    if draw.textbbox((0,0), name, font=temp_font)[2] > W - 100:
        wrapped = wrap(name, width=22)
        if len(wrapped) >= 2:
            line1 = wrapped[0]
            line2 = " ".join(wrapped[1:3]) if len(wrapped) > 2 else wrapped[1]
            draw_centered(draw, line1, 60, 40, color=(255, 255, 255))
            draw_centered(draw, line2, 100, 40, color=(220, 240, 255))
        else:
            font_size = 40  # fallback
            draw_centered(draw, name, 70, font_size)
    else:
        draw_centered(draw, name, 70, font_size)

    # === QR — EXACT CENTER ===
    qr_badge = make_qr_badge(pid)
    qr_x = (W - QR_TOTAL) // 2
    qr_y = (H - QR_TOTAL) // 2
    bg.paste(qr_badge, (qr_x, qr_y), qr_badge)

    # === ID — small & elegant at bottom ===
    draw_centered(draw, pid, qr_y + QR_TOTAL + 50, 42, color=(170, 210, 255), bold=False)

    # Save
    file = f"badges/{pid}.jpg"
    bg.convert("RGB").save(file, "JPEG", quality=90, dpi=DPI)
    kb = os.path.getsize(f"badges/{pid}.jpg") // 1024
    print(f"{pid} → {name[:40]:40} → {kb} KB")

print("\nAll done! Clean, centered, professional badges with smaller text ready.")