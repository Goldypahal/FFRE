import sys
try:
    import pypdf
except ImportError:
    try:
        import PyPDF2 as pypdf
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pypdf'])
        import pypdf

reader = pypdf.PdfReader(r'g:\Desktop\FFRE\FFIRE_SRS.pdf')
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"
with open(r'g:\Desktop\FFRE\FFIRE_SRS.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")
