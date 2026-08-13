import fitz

doc = fitz.open("FFIRE_SRS.pdf")
page = doc[2] # page 3
print("--- Page 3 Blocks ---")
blocks = page.get_text("dict")["blocks"]
for block in blocks:
    if "lines" in block:
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"Text: {span['text']!r}, Origin: {span['origin']}, Font: {span['font']}, Size: {span['size']:.1f}, Color: {span['color']}")
