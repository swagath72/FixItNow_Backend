import json

def add_info_intents():
    with open("chatbot/dataset.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    new_intents = [
        {
            "intent": "about_plumbing",
            "patterns": [
                "what plumbing services are available",
                "list of plumbing services",
                "plumbing service types",
                "what do you offer in plumbing",
                "available plumbing work",
                "plumber services list"
            ],
            "responses": ["Our plumbing services include: Tap/Faucet Repair, Pipe Leak fixing, Toilet/Flush repair, Drainage cleaning, and Sink installation."]
        },
        {
            "intent": "about_electrical",
            "patterns": [
                "what electrical services are available",
                "list of electrical services",
                "electrical service types",
                "what do you offer in electrical",
                "available electrical work",
                "electrician services list"
            ],
            "responses": ["For electrical needs, we offer: Fan repair, Light/LED installation, Switch & Socket fixing, MCB/Breaker repair, and General wiring."]
        },
        {
            "intent": "about_ac",
            "patterns": [
                "what ac services are available",
                "list of ac repair services",
                "ac service types",
                "what do you offer for ac",
                "available ac work"
            ],
            "responses": ["We provide comprehensive AC services: General servicing, Gas refilling, Cooling repairs, and Uninstallation/Installation of AC units."]
        }
    ]

    # Check if intent already exists
    existing_intents = [item["intent"] for item in data]
    for ni in new_intents:
        if ni["intent"] not in existing_intents:
            data.append(ni)
        else:
            # Update existing if needed
            index = next(i for i, item in enumerate(data) if item["intent"] == ni["intent"])
            data[index]["patterns"].extend(ni["patterns"])
            data[index]["patterns"] = list(set(data[index]["patterns"]))

    with open("chatbot/dataset.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Dataset updated with info intents!")

if __name__ == "__main__":
    add_info_intents()
