"""
Dark Pattern Classifier using DistilBERT
=========================================
Combines two datasets:
  - darkpattern.csv   : text + binary label + Pattern Category
  - dark_patterns.csv : Pattern String + Pattern Category + Pattern Type + Deceptive?

Output: Deceptive score from 1 (not deceptive) to 10 (highly deceptive)
"""

# ── Imports ───────────────────────────────────────────────────────────────────
import os
import re
import warnings
import numpy as np
import pandas as pd

import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader

from transformers import (
    DistilBertTokenizerFast,
    DistilBertModel,
    get_linear_schedule_with_warmup,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, mean_absolute_error

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_NAME     = "distilbert-base-uncased"
MAX_LEN        = 128
BATCH_SIZE     = 16          # lower to 8 on 4 GB RAM
EPOCHS         = 4
LR             = 2e-5
SEED           = 42
SAVE_PATH      = "dark_pattern_model.pt"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

torch.manual_seed(SEED)
np.random.seed(SEED)


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING & CLEANING
# ══════════════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Lowercase, strip URLs, normalise whitespace."""
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", "", text)          # remove URLs
    text = re.sub(r"[^a-z0-9\s'.,!?%-]", " ", text)       # keep useful punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text


def deceptive_score_from_category(category: str, is_dark: bool) -> float:
    """
    Map Pattern Category → raw severity weight (1-10).
    Non-dark patterns always score 1.
    """
    if not is_dark:
        return 1.0
    severity = {
        "Forced Action":   9.5,
        "Sneaking":        9.0,
        "Obstruction":     8.5,
        "Misdirection":    8.0,
        "Urgency":         7.0,
        "Scarcity":        6.5,
        "Social Proof":    5.5,
    }
    return severity.get(category, 5.0)


def load_and_merge() -> pd.DataFrame:
    # ── Dataset 1: darkpattern.csv ────────────────────────────────────────────
    dp1 = pd.read_csv("darkpattern.csv")
    dp1 = dp1.rename(columns={"text": "text", "label": "is_dark",
                               "Pattern Category": "category"})
    dp1 = dp1[["text", "is_dark", "category"]].copy()
    dp1["is_dark"] = dp1["is_dark"].astype(int)

    # ── Dataset 2: dark_patterns.csv ─────────────────────────────────────────
    dp2 = pd.read_csv("dark_patterns.csv")
    dp2 = dp2.rename(columns={
        "Pattern String": "text",
        "Pattern Category": "category",
        "Deceptive?": "deceptive_raw",
    })
    # Map Deceptive? → binary label  (Yes=1, No=0, Depends=1 conservatively)
    deceptive_map = {"Yes": 1, "No": 0, "Depends": 1}
    dp2["is_dark"] = dp2["deceptive_raw"].map(deceptive_map).fillna(0).astype(int)
    dp2 = dp2[["text", "is_dark", "category"]].copy()

    # ── Merge ─────────────────────────────────────────────────────────────────
    df = pd.concat([dp1, dp2], ignore_index=True)

    # ── Clean ─────────────────────────────────────────────────────────────────
    df["text"] = df["text"].apply(clean_text)
    df["category"] = df["category"].fillna("Unknown").str.strip()

    # Drop duplicates and empty texts
    df = df.drop_duplicates(subset=["text"])
    df = df[df["text"].str.len() > 5].reset_index(drop=True)

    # ── Compute deceptive score (1-10, float) ─────────────────────────────────
    df["score"] = df.apply(
        lambda r: deceptive_score_from_category(r["category"], bool(r["is_dark"])),
        axis=1,
    )

    # Normalise score to [1, 10]
    lo, hi = df["score"].min(), df["score"].max()
    df["score"] = 1 + (df["score"] - lo) / (hi - lo + 1e-8) * 9

    print(f"\nDataset ready: {len(df)} samples")
    print(df["category"].value_counts())
    print(f"\nScore distribution:\n{df['score'].describe()}\n")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 2. DATASET CLASS
# ══════════════════════════════════════════════════════════════════════════════

class DarkPatternDataset(Dataset):
    def __init__(self, texts, scores, tokenizer, max_len=MAX_LEN):
        self.texts     = texts
        self.scores    = scores
        self.tokenizer = tokenizer
        self.max_len   = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids":      enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "score":          torch.tensor(self.scores[idx], dtype=torch.float),
        }


# ══════════════════════════════════════════════════════════════════════════════
# 3. MODEL  (DistilBERT + regression head → score 1-10)
# ══════════════════════════════════════════════════════════════════════════════

class DarkPatternScorer(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert   = DistilBertModel.from_pretrained(MODEL_NAME)
        self.drop   = nn.Dropout(0.2)
        self.fc     = nn.Linear(self.bert.config.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        out    = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = out.last_hidden_state[:, 0, :]   # [CLS] token
        pooled = self.drop(pooled)
        raw    = self.fc(pooled).squeeze(-1)
        # Scale sigmoid output to [1, 10]
        score  = 1 + self.sigmoid(raw) * 9
        return score


# ══════════════════════════════════════════════════════════════════════════════
# 4. TRAINING
# ══════════════════════════════════════════════════════════════════════════════

def train_epoch(model, loader, optimizer, scheduler, criterion):
    model.train()
    total_loss = 0
    for batch in loader:
        optimizer.zero_grad()
        ids   = batch["input_ids"].to(DEVICE)
        mask  = batch["attention_mask"].to(DEVICE)
        score = batch["score"].to(DEVICE)

        pred = model(ids, mask)
        loss = criterion(pred, score)
        loss.backward()

        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        total_loss += loss.item()
    return total_loss / len(loader)


def eval_epoch(model, loader, criterion):
    model.eval()
    total_loss, preds_all, true_all = 0, [], []
    with torch.no_grad():
        for batch in loader:
            ids   = batch["input_ids"].to(DEVICE)
            mask  = batch["attention_mask"].to(DEVICE)
            score = batch["score"].to(DEVICE)

            pred = model(ids, mask)
            loss = criterion(pred, score)
            total_loss += loss.item()

            preds_all.extend(pred.cpu().numpy())
            true_all.extend(score.cpu().numpy())

    mae = mean_absolute_error(true_all, preds_all)
    return total_loss / len(loader), mae


# ══════════════════════════════════════════════════════════════════════════════
# 5. INFERENCE FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def predict_score(texts, model, tokenizer, batch_size=8) -> list[dict]:
    """
    Given a list of raw text strings, return a list of dicts:
      { "text": ..., "deceptive_score": float(1-10), "verdict": str }
    """
    model.eval()
    results = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        cleaned = [clean_text(t) for t in chunk]
        enc = tokenizer(
            cleaned,
            max_length=MAX_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        ids  = enc["input_ids"].to(DEVICE)
        mask = enc["attention_mask"].to(DEVICE)
        with torch.no_grad():
            scores = model(ids, mask).cpu().numpy()

        for orig, score in zip(chunk, scores):
            s = float(np.clip(score, 1, 10))
            if s <= 3:
                verdict = "Not deceptive"
            elif s <= 5:
                verdict = "Mildly deceptive"
            elif s <= 7.5:
                verdict = "Moderately deceptive"
            else:
                verdict = "Highly deceptive"
            results.append({"text": orig, "deceptive_score": round(s, 2), "verdict": verdict})
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Load data ────────────────────────────────────────────────────────────
    df = load_and_merge()

    X = df["text"].tolist()
    y = df["score"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=SEED
    )

    # ── Tokenizer ────────────────────────────────────────────────────────────
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

    train_ds = DarkPatternDataset(X_train, y_train, tokenizer)
    test_ds  = DarkPatternDataset(X_test,  y_test,  tokenizer)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # ── Model ────────────────────────────────────────────────────────────────
    model     = DarkPatternScorer().to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)

    total_steps = len(train_loader) * EPOCHS
    scheduler   = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=total_steps // 10,
        num_training_steps=total_steps,
    )

    # ── Training loop ────────────────────────────────────────────────────────
    print("=" * 55)
    print("Training DistilBERT Dark Pattern Scorer")
    print("=" * 55)

    best_mae = float("inf")
    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, criterion)
        val_loss, mae = eval_epoch(model, test_loader, criterion)
        print(f"Epoch {epoch}/{EPOCHS} | train_loss={train_loss:.4f} | "
              f"val_loss={val_loss:.4f} | MAE={mae:.4f}")

        if mae < best_mae:
            best_mae = mae
            torch.save(model.state_dict(), SAVE_PATH)
            print(f"  ✓ Best model saved (MAE={mae:.4f})")

    # ── Load best model & run demo inference ────────────────────────────────
    model.load_state_dict(torch.load(SAVE_PATH, map_location=DEVICE))

    demo_texts = [
        "Only 2 left in stock! Order now before it's too late!",
        "Free shipping on all orders over $50.",
        "13,472 people are viewing this item right now.",
        "Limited offer: expires in 00:04:23 — don't miss out!",
        "By clicking 'No thanks', I agree to miss out on 50% savings.",
        "Standard return policy: 30 days, no questions asked.",
        "Subscribe and save — cancel anytime.",
    ]

    print("\n" + "=" * 55)
    print("Demo Inference Results")
    print("=" * 55)
    results = predict_score(demo_texts, model, tokenizer)
    for r in results:
        bar = "█" * int(r["deceptive_score"])
        print(f"\nText   : {r['text'][:70]}")
        print(f"Score  : {r['deceptive_score']:.1f}/10  {bar}")
        print(f"Verdict: {r['verdict']}")

    print(f"\n✓ Training complete. Best MAE: {best_mae:.4f}")
    print(f"✓ Model saved to '{SAVE_PATH}'")


if __name__ == "__main__":
    main()
