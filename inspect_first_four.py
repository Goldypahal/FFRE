import fitz

doc = fitz.open("FFIRE_SRS.pdf")
for i in range(4): # Pages 1-4
    print(f"--- Page {i+1} ---")
    page = doc[i]
    print(page.get_text())
