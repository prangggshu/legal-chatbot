import argparse
import importlib.util
import json
import sys
import sysconfig
from pathlib import Path

import numpy as np


def ensure_stdlib_tokenize() -> None:
	stdlib_tokenize_path = Path(sysconfig.get_paths()["stdlib"]) / "tokenize.py"
	spec = importlib.util.spec_from_file_location("tokenize", stdlib_tokenize_path)
	if spec is None or spec.loader is None:
		raise RuntimeError("Unable to load stdlib tokenize module.")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	sys.modules["tokenize"] = module


ensure_stdlib_tokenize()

from datasets import load_from_disk
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments


def compute_metrics(eval_pred):
	logits, labels = eval_pred
	predictions = np.argmax(logits, axis=1)
	return {
		"accuracy": float(accuracy_score(labels, predictions)),
		"precision": float(precision_score(labels, predictions, zero_division=0)),
		"recall": float(recall_score(labels, predictions, zero_division=0)),
		"f1": float(f1_score(labels, predictions, zero_division=0)),
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Train Legal-BERT relevance classifier.")
	parser.add_argument("--tokenized-dir", default="../data/tokenized", help="Path to tokenized DatasetDict")
	parser.add_argument("--output-dir", default="../output/legal-bert-finetuned", help="Directory to save fine-tuned model")
	parser.add_argument("--model-name", default="nlpaueb/legal-bert-base-uncased", help="Base model")
	parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
	parser.add_argument("--train-batch-size", type=int, default=8, help="Train batch size per device")
	parser.add_argument("--eval-batch-size", type=int, default=16, help="Eval batch size per device")
	parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
	parser.add_argument("--weight-decay", type=float, default=0.01, help="Weight decay")
	parser.add_argument("--seed", type=int, default=42, help="Random seed")
	args = parser.parse_args()

	script_dir = Path(__file__).resolve().parent
	tokenized_dir = (script_dir / args.tokenized_dir).resolve()
	output_dir = (script_dir / args.output_dir).resolve()

	dataset = load_from_disk(str(tokenized_dir))

	model = AutoModelForSequenceClassification.from_pretrained(
		args.model_name,
		num_labels=2,
		id2label={0: "Not Relevant", 1: "Relevant"},
		label2id={"Not Relevant": 0, "Relevant": 1},
	)

	training_args = TrainingArguments(
		output_dir=str(output_dir),
		num_train_epochs=args.epochs,
		per_device_train_batch_size=args.train_batch_size,
		per_device_eval_batch_size=args.eval_batch_size,
		learning_rate=args.learning_rate,
		weight_decay=args.weight_decay,
		logging_steps=50,
		save_strategy="epoch",
		eval_strategy="epoch",
		load_best_model_at_end=True,
		metric_for_best_model="f1",
		greater_is_better=True,
		report_to="none",
		seed=args.seed,
	)

	trainer = Trainer(
		model=model,
		args=training_args,
		train_dataset=dataset["train"],
		eval_dataset=dataset["validation"],
		compute_metrics=compute_metrics,
	)

	trainer.train()

	eval_metrics = trainer.evaluate(dataset["test"])
	trainer.save_model(str(output_dir))

	metrics_path = output_dir / "test_metrics.json"
	with open(metrics_path, "w", encoding="utf-8") as file:
		json.dump(eval_metrics, file, indent=2)

	print("Training complete.")
	print(json.dumps(eval_metrics, indent=2))
	print(f"Model saved to: {output_dir}")
	print(f"Test metrics saved to: {metrics_path}")


if __name__ == "__main__":
	main()
