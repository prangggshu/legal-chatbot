import argparse
import importlib.util
import json
import sys
import sysconfig
from pathlib import Path

import torch


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
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def evaluate_model(model, dataset_split, device):
	labels = []
	predictions = []

	model.eval()
	with torch.no_grad():
		for row in dataset_split:
			input_ids = torch.tensor([row["input_ids"]], device=device)
			attention_mask = torch.tensor([row["attention_mask"]], device=device)

			model_inputs = {
				"input_ids": input_ids,
				"attention_mask": attention_mask,
			}

			if "token_type_ids" in row:
				model_inputs["token_type_ids"] = torch.tensor([row["token_type_ids"]], device=device)

			outputs = model(**model_inputs)
			prediction = int(torch.argmax(outputs.logits, dim=1).item())

			predictions.append(prediction)
			labels.append(int(row["labels"]))

	return {
		"accuracy": float(accuracy_score(labels, predictions)),
		"precision": float(precision_score(labels, predictions, zero_division=0)),
		"recall": float(recall_score(labels, predictions, zero_division=0)),
		"f1": float(f1_score(labels, predictions, zero_division=0)),
		"samples": len(labels),
	}


def predict_relevance(model, tokenizer, question: str, context: str, max_length: int, device):
	encoded = tokenizer(
		question,
		context,
		truncation=True,
		padding="max_length",
		max_length=max_length,
		return_tensors="pt",
	)
	encoded = {key: value.to(device) for key, value in encoded.items()}

	model.eval()
	with torch.no_grad():
		logits = model(**encoded).logits
		probabilities = torch.softmax(logits, dim=1)
		predicted_class = int(torch.argmax(probabilities, dim=1).item())
		confidence = float(probabilities[0][predicted_class].item())

	return {
		"label": "Relevant" if predicted_class == 1 else "Not Relevant",
		"class_id": predicted_class,
		"confidence": confidence,
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Evaluate and test Legal-BERT relevance classifier.")
	parser.add_argument("--model-dir", default="../output/legal-bert-finetuned", help="Directory containing fine-tuned model")
	parser.add_argument("--tokenized-dir", default="../data/tokenized", help="Tokenized dataset directory")
	parser.add_argument("--question", default="Can a wife claim alimony during divorce?", help="Question for single-sample inference")
	parser.add_argument(
		"--context",
		default="The wife may present a petition for expenses of the proceedings and alimony pending the suit.",
		help="Context for single-sample inference",
	)
	parser.add_argument("--max-length", type=int, default=256, help="Max token length for inference")
	args = parser.parse_args()

	script_dir = Path(__file__).resolve().parent
	model_dir = (script_dir / args.model_dir).resolve()
	tokenized_dir = (script_dir / args.tokenized_dir).resolve()

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
	model = AutoModelForSequenceClassification.from_pretrained(str(model_dir)).to(device)

	dataset = load_from_disk(str(tokenized_dir))
	metrics = evaluate_model(model, dataset["test"], device)
	prediction = predict_relevance(model, tokenizer, args.question, args.context, args.max_length, device)

	print("Test Metrics:")
	print(json.dumps(metrics, indent=2))
	print("\nSingle Prediction:")
	print(json.dumps({"question": args.question, "prediction": prediction}, indent=2))


if __name__ == "__main__":
	main()
