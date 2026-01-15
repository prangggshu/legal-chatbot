from pypdf import PdfReader

reader = PdfReader("MinimumWagesact.pdf")

text = ""
for page in reader.pages:
    if page.extract_text():
        text += page.extract_text() + "\n"
        
with open("../data/min_wages_raw.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Text extracted successfully")
