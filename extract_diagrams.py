import fitz
import os

doc = fitz.open("FFIRE_SRS.pdf")

diagram_pages = {
    11: "figure_5_1_architecture.png",       # Page 12
    14: "figure_6_1_langgraph_pipeline.png", # Page 15
    18: "figure_8_1_dfd_lvl0.png",           # Page 19
    19: "figure_8_2_dfd_lvl1.png",           # Page 20
    20: "figure_9_1_erd.png",                 # Page 21
    23: "figure_11_1_sequence.png",          # Page 24
    24: "figure_12_1_usecase.png",           # Page 25
    27: "figure_13_1_statemachine.png",      # Page 28
    29: "figure_14_1_activity.png",          # Page 30
    31: "figure_15_1_components.png",        # Page 32
    32: "figure_16_1_deployment.png",        # Page 33
    34: "figure_18_1_reasoning.png"          # Page 35
}

os.makedirs("diagrams", exist_ok=True)

for p_idx, filename in diagram_pages.items():
    page = doc[p_idx]
    drawings = page.get_drawings()
    
    # Calculate union bounding box of drawings in the content area (between y=80 and y=760)
    bbox = fitz.Rect()
    for d in drawings:
        r = d["rect"]
        # Skip background blocks
        if r.width > page.rect.width - 20 and r.height > page.rect.height - 20:
            continue
        # Skip header and footer decorations
        if r.y1 < 80 or r.y0 > 760:
            continue
        # Include rect
        bbox.include_rect(r)
    
    # Add padding
    padding = 15
    if bbox.is_empty or bbox.width < 50 or bbox.height < 50:
        # Fallback to content area
        bbox = fitz.Rect(40, 80, page.rect.width - 40, page.rect.height - 80)
    else:
        bbox.x0 = max(0, bbox.x0 - padding)
        bbox.y0 = max(80, bbox.y0 - padding)
        bbox.x1 = min(page.rect.width, bbox.x1 + padding)
        bbox.y1 = min(760, bbox.y1 + padding)
        
    zoom = 3
    mat = fitz.Matrix(zoom, zoom)
    
    page.set_cropbox(bbox)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    output_path = os.path.join("diagrams", filename)
    pix.save(output_path)
    page.set_cropbox(page.rect)
    print(f"Extracted Page {p_idx+1} diagram to {output_path} | Bounding Box: {bbox}")

print("All diagrams extracted.")
