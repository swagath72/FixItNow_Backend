import json

intents_data = [
    {
        "intent": "greeting",
        "patterns": ["hi", "hello", "hey", "good morning", "good evening"],
        "responses": ["Hello! Welcome to FIXITNOW. How can I help you?"]
    },
    {
        "intent": "booking_process",
        "patterns": ["book service", "schedule service", "i want to book"],
        "responses": ["Go to Home → Select Service → Choose Technician → Confirm booking."]
    },
    {
        "intent": "plumbing_issue",
        "patterns": ["pipe leak", "water leak", "plumber needed"],
        "responses": ["Turn off water valve and book a plumber."]
    },
    {
        "intent": "electrical_issue",
        "patterns": ["fan not working", "power issue", "switch problem"],
        "responses": ["Turn off MCB and book an electrician."]
    }
]

services = ["plumbing", "electrical", "ac", "cleaning", "carpentry", "painting"]

prefixes = [
    "i want to", "please", "can you", "help me",
    "i need to", "is it possible to", "let me"
]

suffixes = [
    "please", "now", "urgent", "immediately",
    "asap", "help", "fix it"
]

extra_words = [
    "quick", "fast", "today", "tomorrow",
    "right now"
]

# 🔥 Expand patterns
for intent in intents_data:
    new_patterns = list(intent["patterns"])

    for p in intent["patterns"]:
        for pre in prefixes:
            for suf in suffixes:
                for extra in extra_words:
                    new_patterns.append(f"{pre} {p}")
                    new_patterns.append(f"{p} {suf}")
                    new_patterns.append(f"{pre} {extra} {p}")
                    new_patterns.append(f"{extra} {p}")

    intent["patterns"] = list(set(new_patterns))

# 🔥 Add booking + service combinations (VERY IMPORTANT)
booking_patterns = []
for s in services:
    booking_patterns.extend([
        f"book {s}",
        f"book {s} service",
        f"i want to book {s}",
        f"schedule {s}",
        f"need {s} service",
        f"hire {s}",
        f"{s} booking"
    ])

intents_data.append({
    "intent": "book_service_specific",
    "patterns": booking_patterns,
    "responses": ["Sure! Go to Home → Select Service → Choose Technician → Confirm booking."]
})

# Save dataset
with open("chatbot/dataset.json", "w") as f:
    json.dump(intents_data, f, indent=2)

print("✅ Dataset generated with large patterns!")