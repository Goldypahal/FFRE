import fitz

doc = fitz.open("FFIRE_SRS.pdf")
for i, page in enumerate(doc):
    text = page.get_text()
    for line in text.split("\n"):
        if "figure" in line.lower() or "diagram" in line.lower():
            print(f"Page {i+1}: {line.strip()}")
