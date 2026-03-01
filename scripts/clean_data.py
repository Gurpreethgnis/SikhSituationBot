import json
import os

def clean_data():
    input_file = os.path.join('data', 'shabad.json')
    output_file = os.path.join('data', 'shabads_cleaned.json')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Example of normalization logic
    # This script will ensure all entries follow the schema in docs/data-strategy.md
    cleaned = []
    for entry in data:
        shabad = {
            "shabad_id": entry.get("id", "unknown"),
            "gurmukhi": entry.get("gurmukhi", ""), # This would be filled by a scraper or manual entry
            "romanization": entry.get("romanization", ""),
            "english_translation": entry.get("english_translation", ""),
            "context_tags": entry.get("context_tags", []),
            "source": entry.get("source", "Unknown"),
            "recommended_persona": entry.get("recommended_persona", "any")
        }
        
        # If the input was the situational format, we map it as best as we can
        # or leave placeholders for manual completion
        if "situation" in entry:
            shabad["context_tags"].extend(entry.get("intended_feelings", []))
            shabad["context_tags"].append(entry["situation"].lower())
            
        cleaned.append(shabad)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=4, ensure_ascii=False)
    
    print(f"Cleaned data saved to {output_file}")

if __name__ == "__main__":
    clean_data()
