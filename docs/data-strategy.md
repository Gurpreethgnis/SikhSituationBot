# SikhSituationBot Data Schema

To ensure the Frontend and Backend teams remain synced, use this exact JSON structure for the initial PoC dataset in `/data/shabads.json`.

```json
[
  {
    "shabad_id": "G1",
    "gurmukhi": "ਤਪਤਿ ਮਾਹਿ ਠਾਢਿ ਵਰਤਾਈ ॥",
    "romanization": "tapat maahi thaadh varataaee ||",
    "english_translation": "In the midst of the burning heat, a cooling breeze has begun to blow.",
    "context_tags": ["anxiety", "peace", "calm", "stress"],
    "source": "SGGS Page 1",
    "recommended_persona": "any"
  }
]
```

## Implementation Strategy: "The Graduated Search"
To avoid scope creep, students should implement search in this order:
1. **v1 (Day 1)**: Simple String Matching. If `query` is in `context_tags`, return.
2. **v2 (Week 2)**: Fuzzy Matching (using a library like `fuzzywuzzy` or `Fuse.js`).
3. **v3 (Week 3)**: Semantic Search (using Python's `sentence-transformers` to compare query embeddings to `english_translation`).

**Do not attempt v3 until v1 and v2 are working perfectly.**
