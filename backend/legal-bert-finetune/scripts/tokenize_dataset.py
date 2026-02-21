import argparse
from pathlib import Path

from datasets import load_dataset
from transformers import AutoTokenizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Tokenize legal relevance dataset for Legal-BERT training.")
    parser.add_argument("--data-dir", default="../data", help="Directory containing train.jsonl, val.jsonl, test.jsonl")
    parser.add_argument("--output-dir", default="../data/tokenized", help="Output directory for tokenized DatasetDict")
    parser.add_argument("--model-name", default="nlpaueb/legal-bert-base-uncased", help="Tokenizer model name")
    parser.add_argument("--max-length", type=int, default=256, help="Max token length")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    data_dir = (script_dir / args.data_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()

    data_files = {
        "train": str((data_dir / "train.jsonl").resolve()),
        "validation": str((data_dir / "val.jsonl").resolve()),
        "test": str((data_dir / "test.jsonl").resolve()),
    }

    dataset = load_dataset("json", data_files=data_files)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize_batch(examples):
        return tokenizer(
            examples["question"],
            examples["context"],
            truncation=True,
            padding="max_length",
            max_length=args.max_length,
        )

    tokenized = dataset.map(tokenize_batch, batched=True)
    tokenized = tokenized.rename_column("label", "labels")

    columns_to_keep = ["input_ids", "attention_mask", "token_type_ids", "labels"]

    for split in tokenized.keys():
        existing_columns = tokenized[split].column_names
        removable_columns = [column for column in existing_columns if column not in columns_to_keep]
        tokenized[split] = tokenized[split].remove_columns(removable_columns)

    output_dir.mkdir(parents=True, exist_ok=True)
    tokenized.save_to_disk(str(output_dir))
    print(f"Tokenized dataset saved to: {output_dir}")


if __name__ == "__main__":
    main()
