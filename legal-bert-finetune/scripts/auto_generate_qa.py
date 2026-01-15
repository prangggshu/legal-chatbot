import json
import random
import os

# ================================
# PATH SETUP (ROBUST & SAFE)
# ================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLAUSE_FILE = os.path.join(BASE_DIR, "data", "min_wages_clauses.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "legal_qa.jsonl")

# ================================
# CLAUSE CLASSIFIER (RULE BASED)
# ================================
def classify_clause(clause: str) -> str:
    c = clause.lower()
    if "overtime" in c:
        return "overtime"
    if "minimum rate" in c or "minimum wages" in c:
        return "minimum_wages"
    if "working day" in c or "hours of work" in c:
        return "working_hours"
    if "payment" in c or "paid" in c or "wages shall be paid" in c:
        return "payment"
    if "appropriate government" in c:
        return "authority"
    if "penalty" in c or "punishable" in c:
        return "penalty"
    return "other"

# ================================
# QUESTION & ANSWER TEMPLATES
# ================================
QUESTION_TEMPLATES = {
    "overtime": "Is overtime work required to be paid at a higher rate?",
    "minimum_wages": "Who is responsible for fixing minimum wages?",
    "working_hours": "Does the law fix normal working hours?",
    "payment": "Is the employer required to pay wages as prescribed?",
    "authority": "Who has the authority to act under this law?",
    "penalty": "Is there a penalty for violating wage provisions?",
    "other": "What does the law state regarding this matter?"
}

ANSWER_TEMPLATES = {
    "overtime": "Yes, overtime work must be paid at the overtime rate as stated.",
    "minimum_wages": "The appropriate Government is responsible for fixing minimum wages.",
    "working_hours": "Yes, the law provides for fixing normal working hours.",
    "payment": "Yes, the employer must pay wages as prescribed by law.",
    "authority": "The appropriate Government has authority under this law.",
    "penalty": "Yes, penalties are prescribed for violations under the law.",
    "other": "The context explains the legal position on this matter."
}

# ================================
# LOAD CLAUSES
# ================================
with open(CLAUSE_FILE, encoding="utf-8") as f:
    raw_clauses = [c.strip() for c in f.read().split("\n\n") if len(c.split()) > 30]

print(f"Loaded {len(raw_clauses)} clauses")

records = []

# ================================
# POSITIVE SAMPLES
# ================================
for clause in raw_clauses:
    topic = classify_clause(clause)
    records.append({
        "question": QUESTION_TEMPLATES[topic],
        "context": clause,
        "answer": ANSWER_TEMPLATES[topic]
    })

# ================================
# NEGATIVE SAMPLES
# ================================
negatives = []
for rec in records:
    wrong_context = random.choice(raw_clauses)
    if wrong_context != rec["context"]:
        negatives.append({
            "question": rec["question"],
            "context": wrong_context,
            "answer": "The context does not address this question."
        })

records.extend(negatives)

# ================================
# WRITE OUTPUT
# ================================
print("Writing file to:", OUTPUT_FILE)

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for r in records:
        out.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"✅ Generated {len(records)} QA pairs successfully")
