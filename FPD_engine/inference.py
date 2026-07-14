import torch
import numpy as np
from transformers import DistilBertTokenizerFast
from dark_pattern_classifier import DarkPatternScorer, predict_score, clean_text

MODEL_NAME = "distilbert-base-uncased"
SAVE_PATH  = "dark_pattern_model.pt"
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)
model     = DarkPatternScorer().to(DEVICE)
model.load_state_dict(torch.load(SAVE_PATH, map_location=DEVICE))
model.eval()

def score(text: str) -> dict:
    results = predict_score([text], model, tokenizer)
    return results[0]

def score_many(texts: list) -> list:
    return predict_score(texts, model, tokenizer)

if __name__ == "__main__":
    text = input("Enter text to classify: ")
    result = score(text)
    print(f"\nScore  : {result['deceptive_score']}/10")
    print(f"Verdict: {result['verdict']}")