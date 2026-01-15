with open("../data/min_wages_clean.txt", encoding="utf-8") as f:
    text = f.read()

clauses = []
current = []

for line in text.split("\n"):
    if line.strip().startswith("Section"):
        if current:
            clauses.append(" ".join(current))
            current = []
    current.append(line.strip())

if current:
    clauses.append(" ".join(current))

with open("../data/min_wages_clauses.txt", "w", encoding="utf-8") as f:
    for c in clauses:
        if len(c.split()) > 40:  # ignore tiny clauses
            f.write(c.strip() + "\n\n")

print(f"Extracted {len(clauses)} clauses")
