import fitz

doc = fitz.open("FFIRE_SRS.pdf")
page = doc[2] # page 3
print("--- Page 3 text details ---")
for word in page.get_text("words"):
    # word is a tuple: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
    if word[0] > 450: # text on the right side of the TOC
        print(f"X={word[0]:.1f}, Y={word[1]:.1f}, Text={word[4]!r}, CodePoints={[ord(c) for c in word[4]]}")
