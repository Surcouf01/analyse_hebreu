#!python
# pip install pillow
from PIL import Image, ImageDraw, ImageFont

W, H = 512, 512
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)

# Police hébraïque : Noto Sans Hebrew, Ezra SIL (SBL), David (Windows)...
# Téléchargez un .ttf et indiquez son chemin ici :
font = ImageFont.truetype("C:/Windows/Fonts/david.ttf", size=300)

# "את" — la bidi est gérée par Pillow (features="rtla" pour certains cas)
draw.text((W // 2, H // 2), "את", font=font, fill="black", anchor="mm")

img.save("icone.bmp")
print("icone.bmp créé")

src = Image.open("icone.bmp").convert("RGBA")  # votre PNG exporté (idéalement 512×512 ou 256×256)

sizes = [256, 64, 48, 32, 16]
imgs = [src.resize((s, s), Image.LANCZOS) for s in sizes]

imgs[0].save("icone.ico", format="ICO", append_images=imgs[1:], sizes=[(s, s) for s in sizes])
print("icone.ico créé")

