# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset and returns matching items sorted by relevance. Filters listings by description keywords, size, and maximum price.

**Input parameters:**
- `description` (str): Search keywords to match against listing titles and descriptions (e.g., "vintage graphic tee")
- `size` (str or None): Target clothing size to filter by (e.g., "M", "L"). Pass None to ignore size filtering.
- `max_price` (float): Maximum price threshold in dollars. Returns only listings with price ≤ max_price.

**What it returns:**
A list of matching listing dictionaries. Each listing contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Results sorted by relevance to description. Returns an empty list [] if no matches found.

**What happens if it fails or returns nothing:**
If results are empty, the agent sets an error message in session["error"] stating "No listings match your search. Try different keywords, remove size filters, or increase your budget." and stops — does NOT call suggest_outfit. The user sees the error message instead of fit results.

---

### Tool 2: suggest_outfit

**What it does:**
Uses Groq's LLM (llama-3.3-70b-versatile) to intelligently match the new item with existing wardrobe pieces and generate a personalized styling suggestion. Produces practical outfit pairing advice and styling tips.

**Input parameters:**
- `new_item` (dict): The secondhand item to style. Contains: `title`, `description`, `category`, `style_tags`, `colors`, `brand`, `price`, `condition`, etc.
- `wardrobe` (dict): User's existing wardrobe structure. Contains `items` list where each item has: `category`, `color`, `style_tags`, `description`. Example structure from wardrobe_schema.json.

**What it returns:**
A string containing the styling suggestion. Format: "Pair this [new_item] with [wardrobe_item] for a [style] look. [Specific styling tips like tucking, rolling, accessory pairing]." Example: "Pair this with your wide-leg jeans and platform Docs for a classic 90s grunge look. Roll the sleeves once and tuck the front corner slightly for shape."

**What happens if it fails or returns nothing:**
If wardrobe is empty (wardrobe['items'] == []), the agent provides general standalone styling advice for the new item without referencing wardrobe pieces. If LLM returns empty string, return a fallback message: "[Item name] is a great find! Style it however feels authentic to you — there's no wrong way to wear it." The agent does NOT crash or skip the fit card.

---

### Tool 3: create_fit_card

**What it does:**
Uses Groq's LLM to generate a user-facing fit card — a short, enthusiastic post-like caption that combines the new item details with the styling suggestion. Creates shareable, social-media-style content that feels authentic and personal.

**Input parameters:**
- `outfit` (str): The styling suggestion returned by suggest_outfit (e.g., "Pair this with your wide-leg jeans..."). Can be a single suggestion or fallback message.
- `new_item` (dict): The secondhand item being styled. Contains: `title`, `price`, `brand`, `platform`, `condition`, `description`, `colors`, etc.

**What it returns:**
A string containing the fit card — a short, narrative caption (1–2 sentences) styled like a thrift haul post. Example: "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤 full look in my stories". Includes: item name, price, platform, styling sentiment, and optional emojis for personality.

**What happens if it fails or returns nothing:**
If outfit is empty or None, return a fallback card: "Added [item name] from [platform] to my wardrobe for $[price]. Great condition — ready to style!" If LLM response is empty, return the fallback. Guard against None values by checking outfit length before calling LLM. The agent does NOT crash or return None.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

1. **Receive user query** containing fashion intent (search keywords, size, price, wardrobe description).

2. **Call search_listings** with description, size, and max_price extracted from user query.

3. **Check if results are empty**:
   - If `results == []`: Set `session["error"]` to helpful message explaining search failure and what user can try differently. Return session immediately — **stop here, do NOT proceed**.
   - If `results != []`: Continue to step 4.

4. **Select top result**: Set `session["selected_item"] = results[0]` (the most relevant match).

5. **Call suggest_outfit** with `new_item=session["selected_item"]` and the user's wardrobe dict.
   - Store result: `session["outfit_suggestion"] = <returned string>`.

6. **Call create_fit_card** with `outfit=session["outfit_suggestion"]` and `new_item=session["selected_item"]`.
   - Store result: `session["fit_card"] = <returned string>`.

7. **Return session** containing all three outputs: `selected_item`, `outfit_suggestion`, `fit_card`, and any errors.

**Key decision points:**
- Empty search results halt the loop immediately — no outfit suggestion or fit card is generated.
- All three tool calls execute sequentially only when search succeeds.
- State flows forward: search result → suggest input → fit card input, no backtracking.

---

## State Management

**How does information from one tool get passed to the next?**

All state is stored in a `session` dictionary that persists throughout the agent's execution:

```python
session = {
    "query": "<original user query>",
    "wardrobe": {<loaded wardrobe dict>},
    "search_results": [],           # populated by search_listings
    "selected_item": None,          # set to results[0] after search
    "outfit_suggestion": "",        # populated by suggest_outfit
    "fit_card": "",                 # populated by create_fit_card
    "error": None                   # set if search fails or error occurs
}
```

**Data flow between tools:**
1. **search_listings** receives `description`, `size`, `max_price` from parsed query. Outputs list stored in `session["search_results"]`.
2. **After search**, the planning loop sets `session["selected_item"] = session["search_results"][0]`.
3. **suggest_outfit** receives `new_item=session["selected_item"]` and `wardrobe=session["wardrobe"]`. Outputs string stored in `session["outfit_suggestion"]`.
4. **create_fit_card** receives `outfit=session["outfit_suggestion"]` and `new_item=session["selected_item"]`. Outputs string stored in `session["fit_card"]`.
5. **At end**, return `session` containing all three outputs and any error messages.

**No state mutations between tool calls** — tools are pure functions that receive exactly what they need from session and return new data; the planning loop decides what to store next.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query (returns []) | Set session["error"] = "No listings match your search. Try different keywords, remove size filters, or increase your budget." Stop execution. Display error message to user — no fit card generated. |
| suggest_outfit | Wardrobe is empty (wardrobe['items'] == []) | Return general standalone styling advice: "[Item name] is a great find! Style it however feels authentic to you — there's no wrong way to wear it." Agent continues to create_fit_card without crashing. |
| create_fit_card | Outfit string is empty or None | Check outfit length before calling LLM. If empty, return fallback: "Added [item name] from [platform] to my wardrobe for $[price]. Great condition — ready to style!" Agent returns valid card string, not None or exception. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                           FitFindr Agent Architecture                         │
│                                                                               │
│  User Query (keywords, size, price, wardrobe description)                    │
│         │                                                                     │
│         ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │              Planning Loop (run_agent)                       │            │
│  │  - Parse query parameters                                    │            │
│  │  - Manage session state                                      │            │
│  │  - Orchestrate tool calls and error handling                 │            │
│  └─────────────────────────────────────────────────────────────┘            │
│         │                                                                     │
│         ▼                                                                     │
│  ┌──────────────────────────────┐                                            │
│  │  search_listings(            │                                            │
│  │    description,              │  ◄──── Receives: query parameters         │
│  │    size, max_price)          │                                            │
│  │                              │                                            │
│  │  Returns: list of items      │ ───►  session["search_results"]           │
│  └──────────────────────────────┘        session["selected_item"]           │
│         │                                                                     │
│         ├─ results == [] ──────────────► [ERROR PATH]                        │
│         │                                 session["error"] = message          │
│         │                                 Return session early ⚠️             │
│         │                                                                     │
│         └─ results != [] ───────────────► Continue to next tool              │
│         │                                                                     │
│         ▼                                                                     │
│  ┌──────────────────────────────┐                                            │
│  │  suggest_outfit(             │                                            │
│  │    new_item,                 │  ◄──── Receives: session["selected_item"] │
│  │    wardrobe)                 │        & session["wardrobe"]              │
│  │                              │                                            │
│  │  Returns: styled suggestion  │ ───►  session["outfit_suggestion"]        │
│  └──────────────────────────────┘                                            │
│         │                                                                     │
│         ├─ wardrobe empty ────────► Use fallback: general styling advice    │
│         │                                                                     │
│         └─ wardrobe populated ────► Use LLM to match items                   │
│         │                                                                     │
│         ▼                                                                     │
│  ┌──────────────────────────────┐                                            │
│  │  create_fit_card(            │                                            │
│  │    outfit,                   │  ◄──── Receives: session["outfit_suggestion"]
│  │    new_item)                 │        & session["selected_item"]         │
│  │                              │                                            │
│  │  Returns: fit card string    │ ───►  session["fit_card"]                 │
│  └──────────────────────────────┘                                            │
│         │                                                                     │
│         ├─ outfit empty ─────────► Use fallback: basic item card            │
│         │                                                                     │
│         └─ outfit populated ─────► Use LLM to create social post            │
│         │                                                                     │
│         ▼                                                                     │
│  Return session                                                               │
│  (selected_item, outfit_suggestion, fit_card, or error message)             │
│         │                                                                     │
│         ▼                                                                     │
│  Display to User                                                              │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │ Session State (persists across all tool calls)              │             │
│  │ - query: original user query                                │             │
│  │ - wardrobe: loaded wardrobe dict                            │             │
│  │ - search_results: list from search_listings                 │             │
│  │ - selected_item: results[0]                                 │             │
│  │ - outfit_suggestion: returned by suggest_outfit             │             │
│  │ - fit_card: returned by create_fit_card                     │             │
│  │ - error: set if search fails                                │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

**Tool 1 — search_listings:**
- Use Claude (via Claude Code) to implement search_listings in tools.py
- Give Claude: Tool 1 spec block (what it does, exact parameters, return value, failure mode) + a note that I must use load_listings() from utils/data_loader.py
- Expect: Function that filters listings by description (keyword match), size (exact), max_price (≤ check); returns matching list sorted by relevance or price
- Verify: 
  1. Check the generated code uses load_listings() and not hardcoded file loading
  2. Run `python -c "from tools import search_listings; print(search_listings('vintage tee', size='M', max_price=30))"` and confirm it returns a list with matching items
  3. Test edge cases: search with no matches returns [], search with None size ignores size filter, search respects price ceiling

**Tool 2 — suggest_outfit:**
- Use Claude to implement suggest_outfit in tools.py
- Give Claude: Tool 2 spec block + note about using Groq's llama-3.3-70b-versatile model with GROQ_API_KEY from .env
- Expect: Function that takes new_item dict and wardrobe dict, calls LLM with a prompt that pairs the new item with wardrobe pieces, returns string suggestion
- Verify:
  1. Confirm the code reads GROQ_API_KEY from .env and initializes Groq client
  2. Run with example wardrobe: `python -c "from tools import suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe; item=load_listings()[0]; print(suggest_outfit(item, get_example_wardrobe()))"` and check output is meaningful styling advice
  3. Run with empty wardrobe: `python -c "from tools import suggest_outfit; from utils.data_loader import load_listings, get_empty_wardrobe; item=load_listings()[0]; print(suggest_outfit(item, get_empty_wardrobe()))"` and confirm it doesn't crash, returns fallback or general advice
  4. Run the same input 3 times and confirm outputs vary (temperature is reasonable for creativity)

**Tool 3 — create_fit_card:**
- Use Claude to implement create_fit_card in tools.py
- Give Claude: Tool 3 spec block + note about using Groq LLM, signature is create_fit_card(outfit, new_item)
- Expect: Function that takes outfit suggestion string and new_item dict, calls LLM to generate a social-media-style fit card caption, returns string
- Verify:
  1. Check code guards against empty outfit string (checks length before LLM call)
  2. Run with full outfit: `python -c "from tools import create_fit_card, suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe; item=load_listings()[0]; outfit=suggest_outfit(item, get_example_wardrobe()); print(create_fit_card(outfit, item))"` and confirm output is a short, stylized caption
  3. Run with empty outfit: `python -c "from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[0]; print(create_fit_card('', item))"` and confirm it returns fallback string, not exception
  4. Run 2–3 times on same input and verify outputs differ slightly (personality/variation)

**Milestone 4 — Planning loop and state management:**

**run_agent() planning loop:**
- Use Claude to implement run_agent(query, wardrobe) in agent.py
- Give Claude: Planning Loop section + State Management section + Architecture diagram (the full ASCII box) + the tool specs (so it knows what each tool returns)
- Expect: Function that (1) parses user query for keywords/size/price, (2) calls search_listings, (3) checks if results empty — if yes set error and return, if no proceed, (4) calls suggest_outfit with results[0] and wardrobe, (5) calls create_fit_card with suggestion + item, (6) returns session dict with all outputs
- Verify:
  1. Read generated code: confirm it branches on `if results == []` before calling suggest_outfit (not calling all tools unconditionally)
  2. Confirm session dict is populated with selected_item, outfit_suggestion, fit_card keys
  3. Run the no-results test case from agent.py: `python agent.py` and trigger the "designer ballgown size XXS max_price 5" query — confirm agent returns early with error, no outfit/fit_card generated
  4. Run happy-path test: `python agent.py` with example query and trace that session["selected_item"] matches the first search result, session["outfit_suggestion"] is passed into create_fit_card, and final session has all three outputs

**handle_query() in app.py:**
- Use Claude to implement handle_query(query_text) that calls run_agent() and maps session to Gradio output panels
- Give Claude: The TODO steps in app.py + note that it should display session["error"] if error exists, else display selected_item info + outfit_suggestion + fit_card
- Expect: Function that parses query, loads wardrobe, calls run_agent(), returns three strings for Gradio output panels (item info, outfit suggestion, fit card)
- Verify:
  1. Run `python app.py` and test with example query in browser at http://localhost:7860
  2. Confirm all three output panels populate for a happy-path query
  3. Trigger error case and confirm only error message displays, other panels are empty or say "No results"

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1 — Parse and Search:**
- Agent parses query: description="vintage graphic tee", size=None (user didn't specify), max_price=30.0
- **Tool called:** search_listings("vintage graphic tee", size=None, max_price=30.0)
- **Why this tool:** Extract available inventory matching the user's intent and budget constraints
- **Output:** Returns list of 3 matching vintage band tees and graphic shirts all under $30:
  ```
  [
    {"id": 2, "title": "Faded Band Tee", "brand": "Vintage", "price": 22, "size": "M", "condition": "Good", "platform": "Depop", "category": "tops", "style_tags": ["vintage", "grunge"], ...},
    {"id": 5, "title": "Y2K Graphic Tee", "brand": "Lee", "price": 18, "size": "L", "condition": "Very Good", "platform": "Poshmark", ...},
    {"id": 8, "title": "Band Tee Print", "brand": "Thrifted", "price": 12, "size": "M", "condition": "Good", "platform": "ThredUP", ...}
  ]
  ```
- **Session after Step 1:** `session["search_results"] = [...]`, `session["selected_item"] = session["search_results"][0]` (the Faded Band Tee, $22)

**Step 2 — Suggest Outfit:**
- Planning loop checks: `results != []` ✓ Continue to suggestion.
- Agent loads user's wardrobe from session. Based on query, wardrobe likely contains: "baggy jeans", "chunky sneakers", other pieces.
- **Tool called:** suggest_outfit(new_item={Faded Band Tee dict}, wardrobe={user's wardrobe dict})
- **Why this tool:** Match the new item intelligently with existing wardrobe pieces to create a cohesive outfit
- **Output:** LLM generates:
  ```
  "Pair this with your baggy jeans and chunky sneakers for an effortless 90s grunge look. Roll the sleeves 
   once to show the worn texture and tuck the front corner slightly into your waistband for shape. 
   Top it off with a silver chain necklace or small hoop earrings to balance the oversized silhouette."
  ```
- **Session after Step 2:** `session["outfit_suggestion"] = "Pair this with your baggy..."`

**Step 3 — Create Fit Card:**
- Planning loop continues (no errors yet).
- **Tool called:** create_fit_card(outfit=session["outfit_suggestion"], new_item={Faded Band Tee})
- **Why this tool:** Generate a shareable, personal caption summarizing the find and styling for the user
- **Output:** LLM generates a social-media-style fit card:
  ```
  "thrifted this faded band tee off depop for $22 and honestly it was made for my baggy jeans 🖤 
   rolled the sleeves and tucked it slightly — vintage energy unlocked"
  ```
- **Session after Step 3:** `session["fit_card"] = "thrifted this faded band tee..."`

**Final output to user:**

The agent returns session to the Gradio interface, which displays:

```
=== ITEM FOUND ===
Faded Band Tee | Vintage Brand
Price: $22 | Condition: Good | Platform: Depop
Size: M | Category: Tops | Style: Vintage, Grunge

=== HOW TO STYLE IT ===
Pair this with your baggy jeans and chunky sneakers for an effortless 90s grunge look. 
Roll the sleeves once to show the worn texture and tuck the front corner slightly into your waistband 
for shape. Top it off with a silver chain necklace or small hoop earrings to balance the 
oversized silhouette.

=== FIT CARD ===
thrifted this faded band tee off depop for $22 and honestly it was made for my baggy jeans 🖤 
rolled the sleeves and tucked it slightly — vintage energy unlocked
```

User sees the complete three-step interaction result in a single view: what was found, how to wear it, and a ready-to-share post caption.
