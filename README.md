# FitFindr — Fashion Discovery Agent

An AI agent that helps users find and style secondhand clothing items using intelligent search, wardrobe matching, and personalized styling suggestions powered by Groq's LLM.

## Overview

FitFindr processes user queries through a three-step planning loop:
1. **Search** for secondhand listings matching user preferences
2. **Suggest** outfit combinations using the user's existing wardrobe
3. **Create** a shareable fit card caption for social media

The agent gracefully handles edge cases (empty wardrobes, no search results) and provides informative fallback responses.

---

## Tool Inventory

### Tool 1: `search_listings`

**Purpose:** Search the mock listings dataset for secondhand items matching user query with optional size and price filters.

**Function Signature:**
```python
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]
```

**Inputs:**
- `description` (str): Keywords describing what the user is looking for (e.g., "vintage graphic tee")
- `size` (str or None): Target clothing size to filter by, case-insensitive (e.g., "M", "L"). None skips size filtering.
- `max_price` (float or None): Maximum price threshold in dollars. Only returns items with price ≤ max_price. None skips price filtering.

**Output:**
A list of matching listing dictionaries sorted by relevance (highest keyword match first). Returns empty list `[]` if no matches. Each listing contains:
- `id` (int): Unique listing identifier
- `title` (str): Item name
- `description` (str): Detailed item description
- `category` (str): Item category (tops, bottoms, outerwear, shoes, accessories)
- `style_tags` (list): Style descriptors (vintage, y2k, grunge, cottagecore, streetwear, etc.)
- `size` (str): Clothing size
- `condition` (str): Item condition (Good, Very Good, Like New, Fair)
- `price` (float): Price in dollars
- `colors` (list): Item colors
- `brand` (str): Brand name
- `platform` (str): Where item is sold (Depop, Poshmark, ThredUP, etc.)

---

### Tool 2: `suggest_outfit`

**Purpose:** Use Groq LLM to intelligently match a new item with existing wardrobe pieces and generate personalized styling suggestions.

**Function Signature:**
```python
def suggest_outfit(new_item: dict, wardrobe: dict) -> str
```

**Inputs:**
- `new_item` (dict): A listing dict from search_listings containing item details (title, description, category, style_tags, colors, brand, price, condition, etc.)
- `wardrobe` (dict): User's wardrobe structure with keys:
  - `items` (list): List of wardrobe item dicts, each containing: `id`, `name`, `category`, `colors`, `style_tags`, `notes`
  - May be empty (empty `items` list) — handles gracefully with general styling advice

**Output:**
A non-empty string (250–500 chars) containing styling suggestions. Format: "Pair this [new_item] with [wardrobe_item] for a [style] look. [Specific styling tips: tucking, rolling, layering, accessories]."

Example: "Pair this with your baggy jeans and chunky sneakers for an effortless 90s grunge look. Roll the sleeves once to show the worn texture and tuck the front corner slightly into your waistband for shape."

**Behavior:**
- If wardrobe is empty: Returns general styling advice (what pieces pair well, vibe it suits, styling tips, accessories)
- If wardrobe is populated: References specific wardrobe items by name
- If LLM returns empty: Returns fallback: "[Item name] is a great find! Style it however feels authentic to you — there's no wrong way to wear it."

---

### Tool 3: `create_fit_card`

**Purpose:** Use Groq LLM to generate a casual, shareable social-media-style outfit caption combining item details with styling suggestion.

**Function Signature:**
```python
def create_fit_card(outfit: str, new_item: dict) -> str
```

**Inputs:**
- `outfit` (str): The styling suggestion returned by suggest_outfit (250–500 char string). Can be fallback message or general advice.
- `new_item` (dict): The listing dict for the thrifted item containing: `title`, `price`, `brand`, `platform`, `condition`, `description`, `colors`, etc.

**Output:**
A string (1–2 sentences, ~100–150 chars) styled like an Instagram/TikTok OOTD post. Format: "[Item name] from [platform] for $[price] is [adjective]... [styling sentiment]. [Optional emoji]"

Example: "Just scored this Graphic Tee for $24 on Depop 🤩, perfect for a grunge revival vibe!"

**Behavior:**
- If outfit is empty, None, or whitespace-only: Returns fallback: "Added [item name] from [platform] to my wardrobe for $[price]. Great condition — ready to style!"
- Uses temperature=0.9 for creativity/variation — same input can produce different captions
- If LLM returns empty: Returns fallback message
- Never raises exceptions or returns None

---

## How the Planning Loop Works

The agent orchestrates the three tools through conditional logic:

```
1. Receive user query
   ↓
2. Call search_listings(description, size, max_price)
   ↓
3. Check: results == [] ?
   ├─ YES → Set session["error"] with helpful message
   │        Return session with error and stop execution
   │        (do NOT call suggest_outfit or create_fit_card)
   │
   └─ NO → Continue
      ↓
4. Set session["selected_item"] = results[0] (top match)
   ↓
5. Call suggest_outfit(selected_item, wardrobe)
   Store: session["outfit_suggestion"] = returned string
   ↓
6. Call create_fit_card(outfit_suggestion, selected_item)
   Store: session["fit_card"] = returned string
   ↓
7. Return session with all three outputs
```

**Decision Points:**
- Empty search results halt the loop immediately — no outfit suggestion or fit card generated
- All three tool calls execute sequentially only when search succeeds
- State flows unidirectionally: search result → outfit input → card input

---

## State Management Approach

**Session Dictionary Structure:**
```python
session = {
    "query": str,                    # Original user query
    "wardrobe": dict,                # Loaded wardrobe from user (has 'items' key)
    "search_results": list[dict],    # List of matching listings from search_listings
    "selected_item": dict | None,    # Top search result (results[0])
    "outfit_suggestion": str,        # Styling suggestion from suggest_outfit
    "fit_card": str,                 # Final caption from create_fit_card
    "error": str | None              # Error message if search fails
}
```

**Data Flow Between Tools:**

1. **Planning loop** extracts `query` parameters and loads `wardrobe`
2. **search_listings** receives description, size, max_price from parsed query
   - Returns `search_results` list
3. **Planning loop** sets `selected_item = search_results[0]`
4. **suggest_outfit** receives `selected_item` and `wardrobe`
   - Returns string stored in `outfit_suggestion`
5. **create_fit_card** receives `outfit_suggestion` and `selected_item`
   - Returns string stored in `fit_card`
6. **Planning loop** returns complete session dict

**No state mutations between tool calls** — tools are pure functions receiving exactly what they need from session; planning loop controls what gets stored next.

---

## Error Handling Strategy

| Tool | Failure Mode | Agent Response |
|------|-------------|----------------|
| **search_listings** | No listings match the query (e.g., "designer ballgown size XXS max_price 5") | Returns empty list `[]`. Planning loop detects this, sets `session["error"] = "No listings match your search. Try different keywords, remove size filters, or increase your budget."` and stops. User sees error message instead of results. |
| **suggest_outfit** | Wardrobe is empty (`wardrobe['items'] == []`) | LLM receives prompt asking for general styling advice (what pieces pair well, what vibe suits, styling tips, accessories). Returns non-empty string with general guidance. No crash, no exception. |
| **create_fit_card** | Outfit string is empty, None, or whitespace-only | Function checks outfit length before calling LLM. If empty, returns fallback: "Added [item name] from [platform] to my wardrobe for $[price]. Great condition — ready to style!" Never returns None or raises exception. |

**Concrete Example from Testing:**
```
Test: search_listings("designer ballgown", size="XXS", max_price=5)
Expected: []
Actual: []
Agent Response: "No listings match your search. Try different keywords, remove size filters, or increase your budget."
Result: ✓ Graceful failure with actionable feedback
```

---

## Spec Reflection

**One way planning.md helped during implementation:**

Planning.md forced me to write exact function signatures and clarify input/output contracts *before* coding. This prevented ambiguity during implementation — I knew search_listings needed to score by keyword relevance and return items sorted by relevance, not just return any matching items. The detailed error-handling section in planning.md also caught edge cases early (empty wardrobe, no search results) that I might have glossed over otherwise. When Claude generated the tool code, I could immediately verify it matched the spec by comparing signatures and return types.

**One divergence from your spec, and why:**

I used `temperature=0.9` in create_fit_card for LLM creativity, whereas the initial spec didn't explicitly mention temperature tuning. I added this because testing showed that without temperature variation, the same input always produced identical captions, which felt repetitive for a social-media-style tool. Increasing temperature makes the tool produce varied, authentic-sounding posts. This was a trade-off between deterministic predictability (which the spec didn't require) and user experience (which benefits from variation).

---

## AI Usage Section

### Instance 1: Implementing search_listings

**What I directed the AI to do:**
I gave Claude the Tool 1 specification from planning.md (exact inputs, return value, failure mode) and asked it to implement the function using `load_listings()` from utils/data_loader.py. I specified that filtering should be by keyword match (score-based), size substring match (case-insensitive), and price threshold, with results sorted by relevance.

**What I revised/overrode:**
Claude's implementation was solid, but I manually tested it against four specific test cases (search with keywords, search with size filter, search with price filter, search with no matches) before trusting it. All tests passed without revision.

**Outcome:**
Tool passed all 9 unit tests including edge cases (empty results, combined filters, case-insensitivity).

### Instance 2: Implementing suggest_outfit (LLM Integration)

**What I directed the AI to do:**
I gave Claude the Tool 2 specification and emphasized that this tool calls the Groq LLM. I specified two prompt branches: one for empty wardrobe (ask for general styling advice) and one for populated wardrobe (ask to match items by name). I included the Groq model name and max_tokens.

**What I revised/overrode:**
Claude initially used `client.messages.create()` (Anthropic API syntax), but this was Groq, which uses `client.chat.completions.create()`. I caught this during the first test, fixed it to the correct Groq API call, and re-tested. After the fix, it passed all tests including the empty-wardrobe fallback case.

**Outcome:**
Tool correctly branches logic (empty vs. populated wardrobe) and returns non-empty suggestions in both cases. Tested with both example and empty wardrobes.

### Instance 3: Test Suite Creation

**What I directed the AI to do (implicitly):**
I created a comprehensive pytest test suite covering 24 test cases across three tool classes: TestSearchListings (9 tests), TestSuggestOutfit (5 tests), TestCreateFitCard (7 tests), and TestToolsIntegration (3 tests). Tests cover happy paths, edge cases, and failure modes.

**What I revised/overrode:**
The test import paths initially failed because tests/ wasn't in the Python path. I manually fixed the sys.path insertion to allow tests to import tools.py from the parent directory.

**Outcome:**
All 24 tests pass. This provides confidence that each tool works independently and the full pipeline (search → suggest → card) works end-to-end.

---

## Complete Interaction Walkthrough

**User query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1 — search_listings**
- **Tool called:** `search_listings("vintage graphic tee", size=None, max_price=30.0)`
- **Input:** 
  - description: "vintage graphic tee"
  - size: None (user didn't specify)
  - max_price: 30.0
- **Why this tool:** Extract available inventory matching user's intent and budget constraints. Score by keyword relevance to find best matches.
- **Output:** 
  ```python
  [
    {
      "id": 2, "title": "Faded Band Tee", "brand": "Vintage", 
      "price": 22.0, "size": "M", "condition": "Good", "platform": "Depop",
      "category": "tops", "style_tags": ["vintage", "grunge"],
      "description": "Authentic vintage band tee from the 90s, faded graphics...",
      "colors": ["grey", "black"]
    },
    # ... 2 more items ...
  ]
  ```
  Planning loop sets: `session["selected_item"] = results[0]` (the Faded Band Tee, $22)

**Step 2 — suggest_outfit**
- **Tool called:** `suggest_outfit(new_item={Faded Band Tee}, wardrobe={user's wardrobe})`
- **Input:**
  - new_item: Dict with title, brand, price, colors, style_tags, description, etc.
  - wardrobe: Dict containing 10 wardrobe items (loaded from session["wardrobe"])
- **Why this tool:** Intelligently match the new item with existing wardrobe pieces to create a cohesive outfit
- **Output:** 
  ```
  "Pair this with your baggy jeans and chunky sneakers for an effortless 90s 
  grunge look. Roll the sleeves once to show the worn texture and tuck the 
  front corner slightly into your waistband for shape. Top it off with a silver 
  chain necklace to balance the oversized silhouette."
  ```
  Planning loop stores: `session["outfit_suggestion"] = returned string`

**Step 3 — create_fit_card**
- **Tool called:** `create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`
- **Input:**
  - outfit: The 200+ char suggestion from step 2
  - new_item: The Faded Band Tee dict
- **Why this tool:** Generate a shareable, personal caption summarizing the find and styling for social media
- **Output:**
  ```
  "Just thrifted this faded band tee off Depop for $22 and honestly it was 
  made for my baggy jeans 🖤 rolled the sleeves and tucked it slightly — 
  vintage energy unlocked"
  ```
  Planning loop stores: `session["fit_card"] = returned string`

**Final output to user:**

The agent returns the complete session to the Gradio interface (Milestone 4/5), which displays three panels:

```
═══════════════════════════════════════════════════════════════
                    ITEM FOUND ✓
═══════════════════════════════════════════════════════════════
Faded Band Tee | Vintage Brand
Price: $22.00 | Condition: Good | Platform: Depop
Size: M | Category: Tops | Style: Vintage, Grunge

═══════════════════════════════════════════════════════════════
                   HOW TO STYLE IT
═══════════════════════════════════════════════════════════════
Pair this with your baggy jeans and chunky sneakers for an 
effortless 90s grunge look. Roll the sleeves once to show the 
worn texture and tuck the front corner slightly into your 
waistband for shape. Top it off with a silver chain necklace 
to balance the oversized silhouette.

═══════════════════════════════════════════════════════════════
                      FIT CARD
═══════════════════════════════════════════════════════════════
Just thrifted this faded band tee off Depop for $22 and 
honestly it was made for my baggy jeans 🖤 rolled the sleeves 
and tucked it slightly — vintage energy unlocked
═══════════════════════════════════════════════════════════════
```

User sees the complete three-step result in one view: what was found, how to wear it, and a ready-to-share caption.

---

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

---

## Running the Project

**Test individual tools:**
```bash
pytest tests/test_tools.py -v
```

**Run the agent (Milestone 4+):**
```bash
python app.py
```

Then open the URL shown in your terminal (typically http://localhost:7860).

---

## Project Structure

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading data
├── tests/
│   └── test_tools.py          # 24 pytest tests for all three tools
├── tools.py                   # The three required tools (implemented)
├── agent.py                   # Planning loop (Milestone 4)
├── app.py                     # Gradio interface (Milestone 4)
├── planning.md                # Completed spec with tool designs
├── action.md                  # Milestone checklist
├── origin.md                  # Project guidance
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .env                       # (Create this) Add GROQ_API_KEY
└── .gitignore
```
