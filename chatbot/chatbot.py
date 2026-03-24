import pickle
import json
import random

# Load model
model = pickle.load(open("chatbot/model.pkl", "rb"))
vectorizer = pickle.load(open("chatbot/vectorizer.pkl", "rb"))

# Load dataset
with open("chatbot/dataset.json") as f:
    data = json.load(f)

intent_responses = {item["intent"]: item["responses"] for item in data}

def get_response(user_input):
    user_input_low = user_input.lower().strip()
    
    # 🔑 Hybrid Link: Keywords override ML for specific common queries
    if any(word in user_input_low for word in ["price", "cost", "charge", "fees", "how much", "rate"]):
        if "plumb" in user_input_low: return random.choice(intent_responses["cost_plumbing"])
        if "elect" in user_input_low: return random.choice(intent_responses["cost_electrical"])
        if "ac" in user_input_low: return random.choice(intent_responses["cost_ac"])
        if "clean" in user_input_low: return random.choice(intent_responses["cost_cleaning"])
        if "carpent" in user_input_low: return random.choice(intent_responses["cost_carpentry"])
        if "paint" in user_input_low: return random.choice(intent_responses["cost_painting"])
        return random.choice(intent_responses["pricing"])

    if any(word in user_input_low for word in ["contact", "call", "phone", "number", "reach", "talk to"]) and \
       any(word in user_input_low for word in ["technician", "worker", "pro", "expert", "plumber", "electrician"]):
        return "Once your booking is confirmed and the technician is assigned, you can view their contact number in the 'My Bookings' or 'Live Tracking' section of the app. You can call them directly from there."

    if any(word in user_input_low for word in ["track", "where is", "arrival", "location"]):
        return random.choice(intent_responses["tracking"])

    # ℹ️ Information Inquiry Link: Detecting questions about service availability/types
    if any(word in user_input_low for word in ["available", "type", "offer", "provide", "list", "what kind", "what can you"]):
        if "plumb" in user_input_low: 
            return "Our plumbing services include: Tap/Faucet Repair, Pipe Leak fixing, Toilet/Flush repair, Drainage cleaning, and Sink installation. You can book any of these from the Home screen."
        if "elect" in user_input_low:
            return "For electrical needs, we offer: Fan repair, Light/LED installation, Switch & Socket fixing, MCB/Breaker repair, and General wiring. Check the Electrical category in the app."
        if "ac" in user_input_low:
            return "We provide comprehensive AC services: General servicing, Gas refilling, Cooling repairs, and Uninstallation/Installation of AC units."
        if "clean" in user_input_low:
            return "We offer: Full home deep cleaning, Sofa/Carpet cleaning, Kitchen deep cleaning, and Bathroom cleaning services."
        if "carpent" in user_input_low:
            return "Our carpentry services cover: Furniture repair, Door/Window fixes, Wardrobe repairs, and new Furniture assembly."
        if "paint" in user_input_low:
            return "We offer: Interior/Exterior house painting, Waterproofing, Wall textures, and Wood/Metal painting."
        return random.choice(intent_responses["services_list"])

    # 🛠️ Service Recommendation Link: Detecting specific problem keywords
    if any(word in user_input_low for word in ["fan", "light", "bulb", "switch", "mcb", "shock", "wire", "power", "electricity", "short circuit", "socket"]):
        return random.choice(intent_responses["electrical_issue"])
    
    if any(word in user_input_low for word in ["leak", "pipe", "tap", "drain", "sink", "toilet", "flush", "plumb", "blockage", "faucet"]):
        return random.choice(intent_responses["plumbing_issue"])
    
    if any(word in user_input_low for word in ["ac", "air condition", "cooling", "refill", "ac repair"]):
        return random.choice(intent_responses["ac_issue"])
    
    if any(word in user_input_low for word in ["clean", "sofa", "mopping", "sweeping", "housekeep"]):
        return random.choice(intent_responses.get("cleaning", intent_responses["services_list"]))
    
    if any(word in user_input_low for word in ["furniture", "wood", "door", "table", "chair", "cabinet", "carpenter"]):
        return random.choice(intent_responses.get("carpentry", intent_responses["services_list"]))

    if any(word in user_input_low for word in ["paint", "wall", "color", "whitewash", "painter"]):
        return random.choice(intent_responses.get("painting", intent_responses["services_list"]))

    # 🤖 AI Core: Weighted Vectorization (TF-IDF) + Probability Classification
    X = vectorizer.transform([user_input_low])
    intent = model.predict(X)[0]
    proba = model.predict_proba(X)
    confidence = max(proba[0])

    if confidence > 0.15:
        return random.choice(intent_responses[intent])

    # 💬 Conversational fallbacks
    if user_input_low in ["yes", "ok", "okay", "yeah", "sure"]:
        return "Great! Do you have any specific service in mind, or should I tell you more about what we offer?"
    if user_input_low in ["no", "nothing", "nope"]:
        return "Alright! I'm here if you change your mind. Have a wonderful day!"

    # ❌ Fallback
    return "I'm here to help! Could you please tell me a bit more? For example, are you looking for a plumber, electrician, or AC repair?"