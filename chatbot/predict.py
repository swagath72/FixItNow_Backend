import pickle
import json

# Load model
model = pickle.load(open("chatbot/model.pkl", "rb"))
vectorizer = pickle.load(open("chatbot/vectorizer.pkl", "rb"))

with open("chatbot/dataset.json") as f:
    dataset = json.load(f)

# Map intent → response
intent_responses = {item["intent"]: item["responses"] for item in dataset}


def predict_intent(user_input):
    text = user_input.lower()

    # 🔥 PRIORITY FIX (VERY IMPORTANT)
    if "book" in text or "schedule" in text:
        return "booking_process"

    X = vectorizer.transform([text])
    return model.predict(X)[0]


def get_response(user_input):
    intent = predict_intent(user_input)
    return intent_responses.get(intent, ["Sorry, I didn't understand"])[0]


# Test
if __name__ == "__main__":
    while True:
        msg = input("You: ")
        print("Bot:", get_response(msg))