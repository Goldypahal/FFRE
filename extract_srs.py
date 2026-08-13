import pypdf

reader = pypdf.PdfReader("FFIRE_SRS.pdf")
text = ""
for idx, page in enumerate(reader.pages):
    text += f"--- Page {idx + 1} ---\n"
    text += page.extract_text() + "\n"

with open("FFIRE_SRS_extracted.txt", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Extracted {len(reader.pages)} pages to FFIRE_SRS_extracted.txt")
