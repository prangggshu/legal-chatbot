import re

with open("../data/min_wages_raw.txt", encoding="utf-8") as f:
    text = f.read()

# Remove STATE AMENDMENTS blocks
text = re.sub(r"STATE AMENDMENTS.*?(Section|\Z)", r"\1", text, flags=re.S)

# Remove extra newlines
text = re.sub(r"\n{2,}", "\n", text)

# Remove bracketed references [12], [***]
text = re.sub(r"\[.*?\]", "", text)

with open("../data/min_wages_clean.txt", "w", encoding="utf-8") as f:
    f.write(text.strip())

print("Cleaned text saved")
