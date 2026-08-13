import fitz

doc = fitz.open("FFIRE_SRS.pdf")
page = doc[2]
print("--- Page 3 (index 2) Spans ---")
spans = []
for b in page.get_text("dict")["blocks"]:
    if "lines" in b:
        for l in b["lines"]:
            for span in l["spans"]:
                spans.append(span)

for span in spans[:40]:
    print(f"Text: {span['text']!r:40s} Box: ({span['bbox'][0]:.1f}, {span['bbox'][1]:.1f}, {span['bbox'][2]:.1f}, {span['bbox'][3]:.1f}) Font: {span['font']} Size: {span['size']:.1f}")

