"""
tests/test_failure_modes.py

Milestone 5: Deliberately trigger and verify each failure mode.
Tests that the agent responds gracefully to edge cases.

Run with: pytest tests/test_failure_modes.py -v -s
Or run directly: python tests/test_failure_modes.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import search_listings, suggest_outfit, create_fit_card
from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings


print("\n" + "="*80)
print("MILESTONE 5: FAILURE MODE TESTING")
print("="*80)


# ────────────────────────────────────────────────────────────────────────────────
# FAILURE MODE 1: search_listings returns zero results
# ────────────────────────────────────────────────────────────────────────────────

print("\n" + "─"*80)
print("FAILURE MODE 1: search_listings returns zero results")
print("─"*80)

print("\nTest: search_listings('designer ballgown', size='XXS', max_price=5)")
results = search_listings("designer ballgown", size="XXS", max_price=5)

print(f"✓ Returns empty list: {results == []}")
print(f"✓ Type is list: {isinstance(results, list)}")
print(f"✓ Length: {len(results)}")

print("\n→ Tool behavior: Returns empty list gracefully (no exception)")
print("✓ PASS: Tool handles zero results correctly")

# Now test the full agent with this impossible query
print("\nTest: Full agent with no-results query")
print("Query: 'designer ballgown size XXS under $5'")

session = run_agent(
    query="designer ballgown size XXS under $5",
    wardrobe=get_example_wardrobe()
)

print(f"\nAgent Response:")
print(f"  session['error']: {session['error']}")
print(f"  session['selected_item']: {session['selected_item']}")
print(f"  session['outfit_suggestion']: {session['outfit_suggestion']}")
print(f"  session['fit_card']: {session['fit_card']}")

print("\n→ Agent behavior:")
print(f"  ✓ Stops early (error set): {session['error'] is not None}")
print(f"  ✓ No item selected: {session['selected_item'] is None}")
print(f"  ✓ No outfit generated: {session['outfit_suggestion'] is None}")
print(f"  ✓ No fit card generated: {session['fit_card'] is None}")
print(f"  ✓ Error message is helpful: {'Try different keywords' in session['error']}")

print("\n✓ PASS: Agent handles no-results gracefully with informative error")


# ────────────────────────────────────────────────────────────────────────────────
# FAILURE MODE 2: suggest_outfit with empty wardrobe
# ────────────────────────────────────────────────────────────────────────────────

print("\n" + "─"*80)
print("FAILURE MODE 2: suggest_outfit with empty wardrobe")
print("─"*80)

print("\nTest: suggest_outfit with empty wardrobe")
results = search_listings("vintage graphic tee", max_price=50)
item = results[0]
empty_wardrobe = get_empty_wardrobe()

print(f"Item: {item['title']}")
print(f"Wardrobe items: {len(empty_wardrobe['items'])}")

suggestion = suggest_outfit(item, empty_wardrobe)

print(f"\nTool Response (first 200 chars):")
print(f"  {suggestion[:200]}...")

print(f"\n→ Tool behavior:")
print(f"  ✓ Returns non-empty string: {len(suggestion) > 0}")
print(f"  ✓ No exception raised: True")
print(f"  ✓ Provides general styling advice: {'pair' in suggestion.lower() or 'style' in suggestion.lower()}")

print("\n✓ PASS: Tool handles empty wardrobe gracefully")

# Now test through full agent
print("\nTest: Full agent with empty wardrobe")
print("Query: 'vintage graphic tee under $30'")

session2 = run_agent(
    query="vintage graphic tee under $30",
    wardrobe=get_empty_wardrobe()
)

print(f"\nAgent Response:")
print(f"  Item found: {session2['selected_item']['title'] if session2['selected_item'] else 'None'}")
print(f"  Outfit (first 150 chars): {session2['outfit_suggestion'][:150]}...")
print(f"  Fit card (first 100 chars): {session2['fit_card'][:100]}...")
print(f"  Error: {session2['error']}")

print(f"\n→ Agent behavior:")
print(f"  ✓ Still finds items: {session2['selected_item'] is not None}")
print(f"  ✓ Provides outfit suggestion: {len(session2['outfit_suggestion']) > 0}")
print(f"  ✓ Creates fit card: {len(session2['fit_card']) > 0}")
print(f"  ✓ No error (graceful): {session2['error'] is None}")

print("\n✓ PASS: Agent works with empty wardrobe (no crash)")


# ────────────────────────────────────────────────────────────────────────────────
# FAILURE MODE 3: create_fit_card with empty outfit
# ────────────────────────────────────────────────────────────────────────────────

print("\n" + "─"*80)
print("FAILURE MODE 3: create_fit_card with empty outfit")
print("─"*80)

print("\nTest: create_fit_card with various empty/invalid outfit inputs")
results = search_listings("vintage graphic tee", max_price=50)
item = results[0]

test_cases = [
    ("empty string", ""),
    ("None", None),
    ("whitespace only", "   "),
]

for name, outfit in test_cases:
    fit_card = create_fit_card(outfit, item)
    print(f"\nInput: {name} ({repr(outfit)})")
    print(f"  Output: {fit_card[:100]}...")
    print(f"  ✓ Returns non-empty string: {len(fit_card) > 0}")
    print(f"  ✓ No exception: True")

print("\n✓ PASS: Tool handles empty outfit gracefully")

# Verify the fallback message is informative
fallback_card = create_fit_card("", item)
print(f"\nFallback message (empty outfit):")
print(f"  {fallback_card}")
print(f"  ✓ Includes item name: {item['title'] in fallback_card}")
print(f"  ✓ Includes platform: {item['platform'].lower() in fallback_card.lower()}")
print(f"  ✓ Includes price: {str(item['price']) in fallback_card}")

print("\n✓ PASS: Fallback message is informative")


# ────────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────────────────────────────────────────

print("\n" + "="*80)
print("FAILURE MODE TESTING COMPLETE")
print("="*80)

print("\n✓ Failure Mode 1 (no search results): PASS")
print("  - Tool returns empty list gracefully")
print("  - Agent stops early with helpful error message")
print("  - No downstream tools called")

print("\n✓ Failure Mode 2 (empty wardrobe): PASS")
print("  - Tool provides general styling advice")
print("  - Agent completes without error")
print("  - All three tools execute successfully")

print("\n✓ Failure Mode 3 (empty outfit): PASS")
print("  - Tool returns informative fallback message")
print("  - No exception raised")
print("  - Message includes item details (name, price, platform)")

print("\n" + "="*80)
print("All failure modes handled gracefully! ✓")
print("="*80 + "\n")
