import json
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_output_folder(folder_name="badges"):
    """Create output folder if it doesn't exist"""
    Path(folder_name).mkdir(exist_ok=True)
    return folder_name

def load_participants(filename="participants.json"):
    """Load participants from JSON file with error handling"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            participants = json.load(f)
        if not participants:
            raise ValueError("No participants found in JSON file")
        return participants
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []
    except json.JSONDecodeError:
        print(f"Error: {filename} is not valid JSON!")
        return []

def get_font(size, bold=False):
    """Load font with multiple fallback options"""
    font_options = [
        ("Arial", ["arialbd.ttf" if bold else "arial.ttf", "Arial.ttf"]),
        ("Helvetica", ["HelveticaBd.ttf" if bold else "Helvetica.ttf"]),
        ("DejaVu", ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]),
    ]
    
    for name, paths in font_options:
        for path in paths:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    
    # Final fallback
    print(f"Warning: Using default font (size {size})")
    return ImageFont.load_default()

# Constants
class BadgeConfig:
    # Dimensions: A5 Portrait at 300 DPI
    WIDTH, HEIGHT = 1120, 1580
    MARGIN = 80
    
    # Colors
    BG = (255, 255, 255)
    TEXT = (30, 30, 30)
    HEADER_BG = (0, 102, 204)
    ROLE_CHALLENGER = (220, 20, 60)
    ROLE_VISITOR = (0, 120, 215)
    BORDER = (40, 40, 40)
    QR_LABEL = (80, 80, 80)
    
    # Font sizes
    TITLE_SIZE = 85
    NAME_SIZE = 80
    ROLE_SIZE = 65
    ID_SIZE = 50
    
    # QR Code settings
    QR_SIZE = 700
    QR_Y_POSITION = 720

def generate_qr_code(data, size=700):
    """Generate a QR code with proper error correction"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=15,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
    return qr_img

def draw_centered_text(draw, text, y_position, font, color, width):
    """Draw text centered horizontally"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) / 2
    draw.text((x, y_position), text, fill=color, font=font)

def sanitize_filename(name, max_length=50):
    """Create safe filename from participant name"""
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    return safe.strip("_")[:max_length]

def create_badge(person, config, fonts, output_folder):
    """Generate a single badge"""
    # Extract participant data with defaults
    full_name = person.get("Full Name", "Unknown").strip()
    role = person.get("Role", "Participant").strip()
    participant_id = person.get("ID", "NO-ID")
    
    if not full_name or full_name == "Unknown":
        print(f"Warning: Skipping participant with missing name (ID: {participant_id})")
        return False
    
    # Create blank badge
    badge = Image.new("RGB", (config.WIDTH, config.HEIGHT), config.BG)
    draw = ImageDraw.Draw(badge)
    
    # Header background
    draw.rectangle([0, 0, config.WIDTH, 300], fill=config.HEADER_BG)
    
    # Event title (centered)
    title = "Fit-Tech Hackathon"
    draw_centered_text(draw, title, 100, fonts['title'], "white", config.WIDTH)
    
    # Participant name (centered)
    draw_centered_text(draw, full_name, 400, fonts['name'], config.TEXT, config.WIDTH)
    
    # Role (centered, colored)
    role_text = role.upper()
    role_color = config.ROLE_CHALLENGER if "challenger" in role.lower() else config.ROLE_VISITOR
    draw_centered_text(draw, role_text, 540, fonts['role'], role_color, config.WIDTH)
    
    # Generate and paste QR code
    try:
        qr_img = generate_qr_code(participant_id, config.QR_SIZE)
        qr_x = (config.WIDTH - config.QR_SIZE) // 2
        badge.paste(qr_img, (qr_x, config.QR_Y_POSITION), qr_img)
    except Exception as e:
        print(f"Warning: Failed to generate QR code for {full_name}: {e}")
    
    # QR label (centered below QR)
    qr_label = f"ID: {participant_id}"
    draw_centered_text(draw, qr_label, 1450, fonts['id'], config.QR_LABEL, config.WIDTH)
    
    # Decorative border
    border_margin = config.MARGIN // 2
    draw.rectangle(
        [border_margin, border_margin, 
         config.WIDTH - border_margin, config.HEIGHT - border_margin],
        outline=config.BORDER, 
        width=12
    )
    
    # Save badge
    filename = f"{output_folder}/{participant_id}.png"
    
    try:
        badge.save(filename, "PNG", dpi=(300, 300))
        print(f"✓ Generated: {filename}")
        return True
    except Exception as e:
        print(f"✗ Error saving badge for {full_name}: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 60)
    print("Fit-Tech Hackathon Badge Generator")
    print("=" * 60)
    
    # Setup
    config = BadgeConfig()
    output_folder = create_output_folder()
    participants = load_participants()
    
    if not participants:
        print("\n✗ No participants to process. Exiting.")
        return
    
    # Load fonts
    fonts = {
        'title': get_font(config.TITLE_SIZE, bold=True),
        'name': get_font(config.NAME_SIZE, bold=True),
        'role': get_font(config.ROLE_SIZE, bold=True),
        'id': get_font(config.ID_SIZE, bold=False)
    }
    
    print(f"\nProcessing {len(participants)} participant(s)...\n")
    
    # Generate badges
    success_count = 0
    for i, person in enumerate(participants, 1):
        print(f"[{i}/{len(participants)}] ", end="")
        if create_badge(person, config, fonts, output_folder):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✓ Successfully generated {success_count}/{len(participants)} badges")
    print(f"✓ Saved to '{output_folder}/' folder")
    print(f"✓ Format: A5 Portrait (300 DPI)")
    print(f"✓ Print tip: 2 badges per A4 sheet")
    print("=" * 60)

if __name__ == "__main__":
    main()