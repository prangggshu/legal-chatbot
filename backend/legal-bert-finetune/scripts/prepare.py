import argparse
import json
import random
import re
from pathlib import Path


def normalize_text(text: str) -> str:
	return re.sub(r"\s+", " ", (text or "")).strip()


def write_jsonl(path: Path, rows: list[dict]) -> None:
	with open(path, "w", encoding="utf-8") as file:
		for row in rows:
			file.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_rows(rows: list[dict], train_ratio: float, val_ratio: float, seed: int) -> tuple[list[dict], list[dict], list[dict]]:
	rng = random.Random(seed)
	shuffled = rows[:]
	rng.shuffle(shuffled)

	total = len(shuffled)
	train_end = int(total * train_ratio)
	val_end = train_end + int(total * val_ratio)

	train_rows = shuffled[:train_end]
	val_rows = shuffled[train_end:val_end]
	test_rows = shuffled[val_end:]
	return train_rows, val_rows, test_rows


def build_examples(records: list[dict], negatives_per_positive: int, seed: int) -> list[dict]:
	rng = random.Random(seed)
	by_law: dict[str, list[int]] = {}

	for index, record in enumerate(records):
		law = record["law"]
		by_law.setdefault(law, []).append(index)

	all_indices = list(range(len(records)))
	examples: list[dict] = []
	seen = set()

	for idx, record in enumerate(records):
		question = record["question"]
		positive_context = record["context"]
		law = record["law"]
		sample_id = record["id"]

		positive_key = (question, positive_context, 1)
		if positive_key not in seen:
			examples.append(
				{
					"id": f"{sample_id}_pos",
					"question": question,
					"context": positive_context,
					"text": f"{question} [SEP] {positive_context}",
					"label": 1,
					"law": law,
				}
			)
			seen.add(positive_key)

		candidate_indices = [candidate for candidate in all_indices if candidate != idx]
		same_law = [candidate for candidate in by_law.get(law, []) if candidate != idx]
		different_law = [candidate for candidate in candidate_indices if records[candidate]["law"] != law]

		negative_sources = []
		if same_law:
			negative_sources.append(("hard", same_law))
		if different_law:
			negative_sources.append(("cross_law", different_law))
		if not negative_sources:
			negative_sources.append(("random", candidate_indices))

		generated = 0
		source_cursor = 0
		while generated < negatives_per_positive and negative_sources:
			source_name, pool = negative_sources[source_cursor % len(negative_sources)]
			source_cursor += 1
			if not pool:
				continue

			candidate_idx = rng.choice(pool)
			negative_context = records[candidate_idx]["context"]
			negative_key = (question, negative_context, 0)
			if negative_key in seen:
				continue

			examples.append(
				{
					"id": f"{sample_id}_neg_{generated}",
					"question": question,
					"context": negative_context,
					"text": f"{question} [SEP] {negative_context}",
					"label": 0,
					"law": law,
					"negative_type": source_name,
				}
			)
			seen.add(negative_key)
			generated += 1

	rng.shuffle(examples)
	return examples


def main() -> None:
	parser = argparse.ArgumentParser(description="Prepare Legal-BERT relevance classification data.")
	parser.add_argument("--input", default="../data/legal_qa.json", help="Path to legal_qa.json")
	parser.add_argument("--output-dir", default="../data", help="Directory for train/val/test JSONL files")
	parser.add_argument("--negatives-per-positive", type=int, default=1, help="Number of negative pairs generated per positive sample")
	parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio")
	parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio")
	parser.add_argument("--seed", type=int, default=42, help="Random seed")
	parser.add_argument("--max-records", type=int, default=0, help="Optional cap for faster experiments (0 = all)")
	args = parser.parse_args()

	script_dir = Path(__file__).resolve().parent
	input_path = (script_dir / args.input).resolve()
	output_dir = (script_dir / args.output_dir).resolve()
	output_dir.mkdir(parents=True, exist_ok=True)

	with open(input_path, "r", encoding="utf-8") as file:
		raw_records = json.load(file)

	records: list[dict] = []
	for item in raw_records:
		question = normalize_text(item.get("question", ""))
		context = normalize_text(item.get("context", ""))
		law = normalize_text(item.get("law", "unknown")) or "unknown"
		sample_id = normalize_text(item.get("id", "")) or f"sample_{len(records)}"
		if question and context:
			records.append({"id": sample_id, "question": question, "context": context, "law": law})

	if args.max_records > 0:
		records = records[: args.max_records]

	if not records:
		raise ValueError("No valid records found in input file.")

	examples = build_examples(records, negatives_per_positive=args.negatives_per_positive, seed=args.seed)
	train_rows, val_rows, test_rows = split_rows(examples, train_ratio=args.train_ratio, val_ratio=args.val_ratio, seed=args.seed)

	train_path = output_dir / "train.jsonl"
	val_path = output_dir / "val.jsonl"
	test_path = output_dir / "test.jsonl"
	meta_path = output_dir / "dataset_meta.json"

	write_jsonl(train_path, train_rows)
	write_jsonl(val_path, val_rows)
	write_jsonl(test_path, test_rows)

	label_counts = {"train": {"0": 0, "1": 0}, "val": {"0": 0, "1": 0}, "test": {"0": 0, "1": 0}}
	for split_name, split_rows_data in [("train", train_rows), ("val", val_rows), ("test", test_rows)]:
		for row in split_rows_data:
			label_counts[split_name][str(row["label"])] += 1

	metadata = {
		"input": str(input_path),
		"records_used": len(records),
		"examples_total": len(examples),
		"splits": {
			"train": len(train_rows),
			"val": len(val_rows),
			"test": len(test_rows),
		},
		"label_counts": label_counts,
		"negatives_per_positive": args.negatives_per_positive,
		"seed": args.seed,
	}

	with open(meta_path, "w", encoding="utf-8") as file:
		json.dump(metadata, file, ensure_ascii=False, indent=2)

	print(f"Prepared dataset at: {output_dir}")
	print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
	main()
