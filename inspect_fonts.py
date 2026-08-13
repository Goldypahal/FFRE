import fitz # PyMuPDF

doc = fitz.open("FFIRE_SRS.pdf")
# Inspect page 5 (Introduction)
page = doc[4]
print("--- Page 5 Blocks ---")
blocks = page.get_text("dict")["blocks"]
for block in blocks[:10]: # Print first 10 blocks
    if "lines" in block:
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"Text: {span['text']!r}")
                print(f"  Font: {span['font']}, Size: {span['size']:.1f}, Color: {span['color']}")
                print(f"  Origin: {span['origin']}")
