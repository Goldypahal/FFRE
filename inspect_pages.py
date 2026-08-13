import fitz

doc = fitz.open("FFIRE_SRS.pdf")
for i in range(10): # First 10 pages
    print(f"--- Page {i+1} ---")
    print(doc[i].get_text())
