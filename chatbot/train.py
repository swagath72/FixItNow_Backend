import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def train_model():
    with open("chatbot/dataset.json") as f:
        data = json.load(f)

    texts = []
    labels = []

    for item in data:
        for pattern in item["patterns"]:
            texts.append(pattern.lower())
            labels.append(item["intent"])

    # 🔥 Improved vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=5000,
        stop_words="english"
    )

    X = vectorizer.fit_transform(texts)

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    )

    model.fit(X, labels)

    pickle.dump(model, open("chatbot/model.pkl", "wb"))
    pickle.dump(vectorizer, open("chatbot/vectorizer.pkl", "wb"))

    print(f"✅ Trained with {len(texts)} patterns")

if __name__ == "__main__":
    train_model()