import json
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- Config ---
W, H = 600, 850
QR_SIZE = 280
BORDER = 15
QR_TOTAL = QR_SIZE + 2 * BORDER
DPI = (100, 100)

# Background files
BACKGROUND_PAGE1 = "background.png"  # First page background
BACKGROUND_PAGE2 = "background.png"  # Second page background

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

    badge = Image.new("RGBA", (QR_TOTAL, QR_TOTAL), (255, 255, 255, 0))

    # Rounded QR
    mask = Image.new("L", (QR_SIZE, QR_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, QR_SIZE-1, QR_SIZE-1], radius=30, fill=255)
    rounded_qr = Image.new("RGBA", (QR_SIZE, QR_SIZE))
    rounded_qr.paste(img, (0, 0))
    rounded_qr.putalpha(mask)
    badge.paste(rounded_qr, (BORDER, BORDER), rounded_qr)

    # Outer rounded white border
    full_mask = Image.new("L", (QR_TOTAL, QR_TOTAL), 0)
    draw = ImageDraw.Draw(full_mask)
    draw.rounded_rectangle([0, 0, QR_TOTAL-1, QR_TOTAL-1], radius=30, fill=255)
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
if not os.path.exists(BACKGROUND_PAGE1):
    print(f"Error: {BACKGROUND_PAGE1} not found!")
    exit()
if not os.path.exists(BACKGROUND_PAGE2):
    print(f"Error: {BACKGROUND_PAGE2} not found!")
    exit()

try:
    people = json.load(open("participants-test.json", encoding="utf-8"))
except Exception as e:
    print("Error loading JSON:", e)
    exit()

# Load both backgrounds
template_page1 = Image.open(BACKGROUND_PAGE1).convert("RGBA")
template_page2 = Image.open(BACKGROUND_PAGE2).convert("RGBA")

if template_page1.size != (W, H):
    print(f"Warning: {BACKGROUND_PAGE1} size is {template_page1.size}, resizing to {W}x{H}")
    template_page1 = template_page1.resize((W, H), Image.Resampling.LANCZOS)
    
if template_page2.size != (W, H):
    print(f"Warning: {BACKGROUND_PAGE2} size is {template_page2.size}, resizing to {W}x{H}")
    template_page2 = template_page2.resize((W, H), Image.Resampling.LANCZOS)

Path("badges").mkdir(exist_ok=True)
print(f"Generating {len(people)} badges as 2-page PDFs...\n")

for p in people:
    name = p.get("Full Name", "No Name").strip().upper()
    branch = p.get("Branch", "").strip().upper()
    pid = str(p.get("ID", "000")).zfill(3)

    if not name or name in ("NO NAME", " "):
        continue

    # === PAGE 1: Background + Name + Branch + "Participant" ===
    page1 = template_page1.copy()
    draw1 = ImageDraw.Draw(page1)
    
    # Name
    draw_centered(draw1, name, 250, 40)
    
    # Branch
    draw_centered(draw1, branch, 350, 32)
    
    # "Participant" text
    draw_centered(draw1, "PARTICIPANT", 450, 36, color=(200, 200, 200))

    # === PAGE 2: Background + Name + QR + ID ===
    page2 = template_page2.copy()
    draw2 = ImageDraw.Draw(page2)

    # Name
    draw_centered(draw2, name, 150, 40)

    # QR centered
    qr_badge = make_qr_badge(pid)
    qr_x = (W - QR_TOTAL) // 2
    qr_y = (H - QR_TOTAL) // 2 - 30
    page2.paste(qr_badge, (qr_x, qr_y), qr_badge)

    # ID number at bottom
    draw_centered(draw2, pid, 600, 30, color=(210, 210, 255), bold=False)

    # Convert to RGB for saving
    rgb_page1 = Image.new("RGB", (W, H), (255, 255, 255))
    rgb_page1.paste(page1, (0, 0), page1) if page1.mode == "RGBA" else rgb_page1.paste(page1)
    
    rgb_page2 = Image.new("RGB", (W, H), (255, 255, 255))
    rgb_page2.paste(page2, (0, 0), page2) if page2.mode == "RGBA" else rgb_page2.paste(page2)

    # Save as 2-page PDF
    pdf_file = f"badges/{pid}.pdf"
    pdf = canvas.Canvas(pdf_file, pagesize=(W, H))
    
    # Page 1
    pdf.drawImage(ImageReader(rgb_page1), 0, 0, width=W, height=H)
    pdf.showPage()
    
    # Page 2
    pdf.drawImage(ImageReader(rgb_page2), 0, 0, width=W, height=H)
    pdf.showPage()
    
    pdf.save()

    kb = os.path.getsize(pdf_file) // 1024
    print(f"{pid} → {name[:40]:40} → {kb} KB (PDF)")

print("\nAll 2-page PDF badges generated!")