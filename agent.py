"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import logging
from tools import search_listings, suggest_outfit, create_fit_card

# ── logging setup ─────────────────────────────────────────────────────────────

# Configure logging to show detailed execution flow
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    import re

    # ─── STEP 1: Initialize session ───────────────────────────────────────────
    logger.info("╔════════════════════════════════════════════════════════════════════╗")
    logger.info("║                    FITFINDR PLANNING LOOP START                     ║")
    logger.info("╚════════════════════════════════════════════════════════════════════╝")
    logger.info(f"User Query: '{query}'")
    logger.info(f"Wardrobe Items: {len(wardrobe.get('items', []))} pieces")

    session = _new_session(query, wardrobe)
    logger.info("✓ Session initialized")

    # ─── STEP 2: Parse query parameters ──────────────────────────────────────
    logger.info("\n[STEP 1/5] Parsing user query...")
    description = query
    size = None
    max_price = None

    # Extract size (look for "size X" pattern or just isolated letters like "M", "L")
    size_match = re.search(r'size\s+([A-Z0-9/]+)', query, re.IGNORECASE)
    if size_match:
        size = size_match.group(1)
        description = re.sub(r'size\s+[A-Z0-9/]+', '', description, flags=re.IGNORECASE)

    # Extract max_price (look for "under $X" or "$X" or "max $X" or just numbers with $)
    price_match = re.search(r'(?:under|max|up to)?\s*\$(\d+(?:\.\d{2})?)', query, re.IGNORECASE)
    if price_match:
        max_price = float(price_match.group(1))
        description = re.sub(r'(?:under|max|up to)?\s*\$\d+(?:\.\d{2})?', '', description, flags=re.IGNORECASE)

    # Clean up description: remove extra whitespace and commas
    description = re.sub(r'\s+', ' ', description).strip()
    description = description.rstrip(',').strip()

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    logger.info(f"  └─ Description: '{description}'")
    logger.info(f"  └─ Size: {size if size else 'Any'}")
    logger.info(f"  └─ Max Price: ${max_price if max_price else 'Any'}")
    logger.info("✓ Query parsing complete\n")

    # ─── STEP 3: Call search_listings tool ─────────────────────────────────
    logger.info("[STEP 2/5] Calling Tool 1: search_listings()")
    logger.info(f"  └─ INITIATED: search_listings")
    logger.info(f"  └─ Input: description='{description}', size={size}, max_price={max_price}")
    logger.info(f"  └─ RUNNING...")

    session["search_results"] = search_listings(
        description=session["parsed"]["description"],
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )

    logger.info(f"  └─ COMPLETED: Found {len(session['search_results'])} matching listings")
    logger.info(f"  └─ Results stored in session['search_results']")

    # ─── CRITICAL: Check if results are empty ────────────────────────────────
    if len(session["search_results"]) == 0:
        logger.warning("\n✗ ERROR: No listings match the search criteria!")
        session["error"] = "No listings match your search. Try different keywords, remove size filters, or increase your budget."
        logger.info(f"  └─ Error Message: {session['error']}")
        logger.info("\n╔════════════════════════════════════════════════════════════════════╗")
        logger.info("║                    PLANNING LOOP TERMINATED (NO RESULTS)            ║")
        logger.info("╚════════════════════════════════════════════════════════════════════╝\n")
        return session

    logger.info("✓ Search successful, proceeding to next step\n")

    # ─── STEP 4: Select top result ───────────────────────────────────────────
    logger.info("[STEP 3/5] Selecting top result")
    session["selected_item"] = session["search_results"][0]
    logger.info(f"  └─ Selected: {session['selected_item']['title']} (${session['selected_item']['price']})")
    logger.info(f"  └─ Stored in session['selected_item']")
    logger.info("✓ Item selection complete\n")

    # ─── STEP 5: Call suggest_outfit tool ─────────────────────────────────
    logger.info("[STEP 4/5] Calling Tool 2: suggest_outfit()")
    logger.info(f"  └─ INITIATED: suggest_outfit")
    logger.info(f"  └─ Input: new_item='{session['selected_item']['title']}', wardrobe={len(session['wardrobe'].get('items', []))} pieces")
    logger.info(f"  └─ RUNNING...")

    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )

    logger.info(f"  └─ COMPLETED: Generated outfit suggestion ({len(session['outfit_suggestion'])} chars)")
    logger.info(f"  └─ Suggestion: {session['outfit_suggestion'][:100]}...")
    logger.info(f"  └─ Stored in session['outfit_suggestion']")
    logger.info("✓ Outfit suggestion complete\n")

    # ─── STEP 6: Call create_fit_card tool ───────────────────────────────
    logger.info("[STEP 5/5] Calling Tool 3: create_fit_card()")
    logger.info(f"  └─ INITIATED: create_fit_card")
    logger.info(f"  └─ Input: outfit='{session['outfit_suggestion'][:50]}...', new_item='{session['selected_item']['title']}'")
    logger.info(f"  └─ RUNNING...")

    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )

    logger.info(f"  └─ COMPLETED: Generated fit card ({len(session['fit_card'])} chars)")
    logger.info(f"  └─ Fit Card: {session['fit_card'][:80]}...")
    logger.info(f"  └─ Stored in session['fit_card']")
    logger.info("✓ Fit card generation complete\n")

    # ─── STEP 7: Return session ────────────────────────────────────────────
    logger.info("╔════════════════════════════════════════════════════════════════════╗")
    logger.info("║                    PLANNING LOOP COMPLETE ✓                        ║")
    logger.info("╚════════════════════════════════════════════════════════════════════╝")
    logger.info(f"STATE SUMMARY:")
    logger.info(f"  └─ selected_item: {session['selected_item']['title']}")
    logger.info(f"  └─ outfit_suggestion: {len(session['outfit_suggestion'])} chars")
    logger.info(f"  └─ fit_card: {len(session['fit_card'])} chars")
    logger.info(f"  └─ error: {session['error']}")
    logger.info("")

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
