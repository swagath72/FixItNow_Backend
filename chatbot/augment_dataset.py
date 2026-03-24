import json

def augment_dataset():
    with open("chatbot/dataset.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Key objects and their plural/variation forms
    plurals = {
        "fan": ["fans", "ceiling fan", "ceiling fans", "table fan", "table fans"],
        "light": ["lights", "bulb", "bulbs", "led", "leds", "tube light", "tube lights"],
        "switch": ["switches", "board", "boards", "plug", "plugs"],
        "pipe": ["pipes", "line", "lines"],
        "tap": ["taps", "faucet", "faucets"],
        "drain": ["drains", "drainage"],
        "sink": ["sinks", "basin", "basins"],
        "toilet": ["toilets", "commode", "commodes"],
        "ac": ["air conditioner", "air conditioners", "split ac", "window ac"],
    }

    # Intent target mapping
    mappings = {
        "electrical_issue": ["fan", "light", "switch"],
        "plumbing_issue": ["pipe", "tap", "drain", "sink", "toilet"],
        "ac_issue": ["ac"]
    }

    sentences = [
        "in my home {} are not working",
        "{} is broken",
        "{} are broken",
        "i have an issue with my {}",
        "can i book a service for {}",
        "what service should i book for {}",
        "my {} need repair",
        "need a technician for {}"
    ]

    for item in data:
        intent = item["intent"]
        if intent in mappings:
            new_patterns = []
            for base_word in mappings[intent]:
                words_to_use = [base_word] + plurals.get(base_word, [])
                for word in words_to_use:
                    for sentence in sentences:
                        new_patterns.append(sentence.format(word))
            
            # Add to existing patterns
            item["patterns"].extend(new_patterns)
            # Remove duplicates
            item["patterns"] = list(set(item["patterns"]))

    with open("chatbot/dataset.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Dataset augmented with plural forms and natural sentences!")

if __name__ == "__main__":
    augment_dataset()
