from transformers import AutoTokenizer, AutoModel

model_name = "nlpaueb/legal-bert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

print("Legal-BERT loaded successfully!")
