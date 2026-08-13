import fitz

doc = fitz.open("FFIRE_SRS.pdf")
page = doc[4] # page 5
print(f"Page size: {page.rect}")
blocks = page.get_text("dict")["blocks"]
for block in blocks:
    if "lines" in block:
        for line in block["lines"]:
            for span in line["spans"]:
                # Print only spans that are near the top or bottom of the page
                y = span["origin"][1]
                if y < 100 or y > 750:
                    print(f"Header/Footer - Text: {span['text']!r}, Origin: {span['origin']}, Font: {span['font']}, Size: {span['size']:.1f}, Color: {span['color']}")
                else:
                    # Just print heading text
                    if span["size"] > 11:
                        print(f"Heading - Text: {span['text']!r}, Origin: {span['origin']}, Font: {span['font']}, Size: {span['size']:.1f}, Color: {span['color']}")
