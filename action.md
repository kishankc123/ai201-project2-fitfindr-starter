# FitFindr — Action Plan

## Project Overview
Build an AI agent that helps users find and style secondhand clothing items using a planning loop with three core tools: `search_listings`, `suggest_outfit`, and `create_fit_card`.

---

## Milestone 1: Planning & Specification ✓ (COMPLETE THIS FIRST)

**Goal:** Define the complete agent architecture and tool specifications before writing code.

### Tasks:
- [ ] **Fill out Tool Specifications** in `planning.md`:
  - `search_listings`: Define input parameters (keywords, size, max_price, etc.), return structure (list of matching items), and failure handling (no matches)
  - `suggest_outfit`: Define how to combine a new item with existing wardrobe, return structure, and handling for empty wardrobes
  - `create_fit_card`: Define output format (styled description, item details, wear scenarios), and error handling for incomplete data

- [ ] **Define Planning Loop Logic** in `planning.md`:
  - Document the decision tree: how does the agent know which tool to call?
  - When does it search? When does it suggest? When does it create the final card?

- [ ] **Design State Management** in `planning.md`:
  - How is wardrobe data loaded and stored?
  - How does data flow from search → suggestion → card?

- [ ] **Create Architecture Diagram** in `planning.md`:
  - ASCII or Mermaid showing user input → agent loop → tool chain → output
  - Include error branches and state flow

- [ ] **Write Complete Interaction Walkthrough** in `planning.md`:
  - Step-by-step trace of the example query: "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

---

## Milestone 2: Setup & Data Validation

**Goal:** Verify all dependencies and test data loading before implementing tools.

### Tasks:
- [ ] **Environment Setup**:
  - Create and activate Python venv
  - Install requirements from `requirements.txt`
  - Create `.env` file with `GROQ_API_KEY`

- [ ] **Test Data Loading**:
  - Run `python utils/data_loader.py` to verify listings load
  - Load example wardrobe and inspect structure
  - Confirm all required fields exist in mock data

- [ ] **Verify Groq API Access**:
  - Test API key connectivity
  - Confirm model availability (likely using Groq's LLM models)

---

## Milestone 3: Individual Tool Implementation

**Goal:** Build and test each tool independently before connecting them.

### Task 3a: `search_listings()` Tool
- [ ] Implement function signature matching `planning.md` spec
- [ ] Parse search query (keywords, size, price filters)
- [ ] Filter `listings.json` against search criteria
- [ ] Return results in consistent format
- [ ] Handle zero-match case gracefully
- [ ] Unit test with 3–5 realistic queries (different styles, sizes, prices)

### Task 3b: `suggest_outfit()` Tool
- [ ] Implement function to match new item with wardrobe
- [ ] Use Groq API to suggest complementary pieces from wardrobe
- [ ] Return outfit description with styling rationale
- [ ] Handle empty wardrobe case (suggest standalone styling)
- [ ] Unit test: new item + populated wardrobe, new item + empty wardrobe

### Task 3c: `create_fit_card()` Tool
- [ ] Implement function to produce user-facing fit card
- [ ] Format: item details, suggested outfit, wear scenarios/occasions
- [ ] Include price, condition, platform info
- [ ] Handle incomplete input gracefully
- [ ] Unit test: full card generation for 2–3 test items

---

## Milestone 4: Planning Loop & Integration

**Goal:** Connect tools into a working agent loop that orchestrates tool calls.

### Tasks:
- [ ] **Implement Agent Planning Loop**:
  - Create main agent function that accepts user query + wardrobe
  - Define decision logic: when to call search vs. suggest vs. create
  - Implement state tracking (current search results, selected item, suggested outfit)

- [ ] **Implement State Management**:
  - Store intermediate results across tool calls
  - Pass data cleanly from search → suggest → card

- [ ] **Error Handling & Fallbacks**:
  - If search returns nothing: inform user, offer alternative query hints
  - If suggest fails: provide standalone item styling
  - If card creation fails: return raw item + wardrobe match instead

- [ ] **End-to-End Testing**:
  - Test complete flow with example query from `planning.md`
  - Verify tool calls happen in correct order
  - Check state flows correctly between steps
  - Manual testing: 3–5 realistic user scenarios

---

## Milestone 5: Documentation & Submission

**Goal:** Prepare final README submission with tool inventory and interaction walkthrough.

### Tasks:
- [ ] **Update README.md**:
  - Fill **Tool Inventory** section with exact function signatures from `tools.py`
  - Document each tool's name, input parameters (type), return value, failure modes
  - Ensure parameter counts/types match actual implementation exactly

- [ ] **Fill Interaction Walkthrough**:
  - Document the example query step-by-step
  - For each step: tool name, inputs, why it was called, actual output
  - Explain final card output to user

- [ ] **Complete Error Handling Table**:
  - For each tool, list the specific failure mode and agent's response

- [ ] **Spec Reflection**:
  - Answer: "One way planning.md helped during implementation" (2–3 sentences)
  - Answer: "One divergence from your spec, and why" (2–3 sentences)

---

## Stretch Features (Optional)

- [ ] Multi-turn conversation: refine search or outfit based on user feedback
- [ ] Wardrobe persistence: save user wardrobes between sessions
- [ ] Style recommendations: suggest items matching user's existing style tags
- [ ] Price tracking: identify trends in secondhand pricing

---

## Checklist for Submission

- [ ] `planning.md` fully completed with all sections filled
- [ ] `tools.py` (or equivalent) with all three tools implemented and tested
- [ ] Agent planning loop working end-to-end
- [ ] `README.md` updated with tool inventory and interaction walkthrough
- [ ] All tools documented with exact signatures matching code
- [ ] Error handling implemented for each failure mode
- [ ] Git history clean; code ready to push

