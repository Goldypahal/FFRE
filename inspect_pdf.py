import fitz # PyMuPDF

doc = fitz.open("FFIRE_SRS.pdf")
print(f"Total pages: {len(doc)}")
for i, page in enumerate(doc):
    text = page.get_text()
    images = page.get_images()
    rects = page.get_drawings()
    print(f"Page {i+1}: text_len={len(text)}, images_count={len(images)}, vector_shapes={len(rects)}")
