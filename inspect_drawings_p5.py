import fitz

doc = fitz.open("FFIRE_SRS.pdf")
page = doc[4]
for i, d in enumerate(page.get_drawings()):
    print(f"Drawing {i}: rect={d['rect']}, type={d['type']}, fill={d.get('fill')}, fill_opacity={d.get('fill_opacity')}")
