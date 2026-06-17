"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Load all listings
    listings = load_listings()

    # Normalize description keywords to lowercase for matching
    description_lower = description.lower()
    keywords = description_lower.split()

    # Filter and score listings
    filtered_and_scored = []

    for listing in listings:
        # Filter by max_price if provided
        if max_price is not None and listing["price"] > max_price:
            continue

        # Filter by size if provided (case-insensitive substring match)
        if size is not None:
            size_lower = size.lower()
            listing_size_lower = listing["size"].lower()
            # Check if the target size is contained in the listing size
            # e.g., "M" matches "S/M", "M/L", or "M"
            if size_lower not in listing_size_lower:
                continue

        # Score by keyword relevance (count matching keywords in title and description)
        listing_text = (listing["title"] + " " + listing["description"]).lower()
        score = sum(1 for keyword in keywords if keyword in listing_text)

        # Only keep listings with at least one keyword match
        if score > 0:
            filtered_and_scored.append((listing, score))

    # Sort by score (highest first) and extract just the listing dicts
    filtered_and_scored.sort(key=lambda x: x[1], reverse=True)
    results = [listing for listing, _ in filtered_and_scored]

    return results


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    # Build item description for the LLM
    new_item_description = f"""
Title: {new_item.get('title', 'Unknown item')}
Brand: {new_item.get('brand', 'Unknown')}
Category: {new_item.get('category', 'Unknown')}
Colors: {', '.join(new_item.get('colors', []))}
Style tags: {', '.join(new_item.get('style_tags', []))}
Description: {new_item.get('description', 'No description')}
Condition: {new_item.get('condition', 'Unknown')}
"""

    # Check if wardrobe is empty
    if not wardrobe.get('items') or len(wardrobe['items']) == 0:
        # Empty wardrobe: ask for general styling advice
        prompt = f"""
You are a personal stylist. A customer just found this secondhand item and wants styling advice.
They don't have their existing wardrobe listed yet, so provide general styling suggestions.

New item:
{new_item_description}

Please suggest:
1. What types of pieces pair well with this item
2. What vibe or aesthetic this item suits
3. Specific styling tips (tucking, rolling sleeves, layering, etc.)
4. Accessory pairing ideas

Keep the response practical, friendly, and inspirational. Make it feel like authentic personal styling advice.
"""
    else:
        # Non-empty wardrobe: create specific outfit combinations
        wardrobe_items_text = "\n".join([
            f"- {item.get('name', 'Item')}: {item.get('category', 'unknown')} | "
            f"Colors: {', '.join(item.get('colors', []))} | "
            f"Style: {', '.join(item.get('style_tags', []))}"
            for item in wardrobe['items']
        ])

        prompt = f"""
You are a personal stylist. A customer found this secondhand item and wants outfit suggestions
using pieces from their existing wardrobe.

New item:
{new_item_description}

Their wardrobe includes:
{wardrobe_items_text}

Please suggest 1–2 complete outfit combinations:
1. Pair the new item with specific pieces from their wardrobe
2. Mention the exact wardrobe piece names
3. Describe the overall vibe/aesthetic of each outfit
4. Include specific styling tips (tucking, rolling, layering, etc.)
5. Suggest accessories or styling details

Keep the response practical, friendly, and feeling like authentic personal styling advice.
Make sure to reference actual pieces from their wardrobe by name.
"""

    # Call the Groq LLM
    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    response = message.choices[0].message.content if message.choices else ""

    # Return fallback if LLM returns empty string
    if not response or response.strip() == "":
        return f"{new_item.get('title', 'This item')} is a great find! Style it however feels authentic to you — there's no wrong way to wear it."

    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against empty or None outfit string
    if not outfit or outfit.strip() == "":
        fallback = f"Added {new_item.get('title', 'this item')} from {new_item.get('platform', 'thrift')} to my wardrobe for ${new_item.get('price', 'free')}. Great condition — ready to style!"
        return fallback

    # Build item description for the LLM
    item_title = new_item.get('title', 'this item')
    item_price = new_item.get('price', 'free')
    item_platform = new_item.get('platform', 'thrift')
    item_brand = new_item.get('brand', 'Unknown')
    item_condition = new_item.get('condition', 'Good')
    item_colors = ', '.join(new_item.get('colors', []))

    prompt = f"""
You are a fashion-savvy social media influencer writing a casual thrift haul post caption.

New item found:
- Title: {item_title}
- Brand: {item_brand}
- Price: ${item_price}
- Platform: {item_platform}
- Condition: {item_condition}
- Colors: {item_colors}

Styling suggestion:
{outfit}

Please generate a SHORT, CASUAL, AUTHENTIC Instagram/TikTok caption (1–2 sentences) for this thrift haul that:
1. Mentions the item name, price, and platform naturally (once each)
2. Captures the outfit vibe from the styling suggestion
3. Feels like a real OOTD post, not a product description
4. Includes optional emojis for personality
5. Sounds excited and authentic, like sharing a great find with friends

Keep it under 150 characters if possible. Make it feel personal and casual.
"""

    client = _get_groq_client()

    # Call the Groq LLM with higher temperature for variation
    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=256,
        temperature=0.9,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    response = message.choices[0].message.content if message.choices else ""

    # Return fallback if LLM returns empty string
    if not response or response.strip() == "":
        return f"Added {new_item.get('title', 'this item')} from {new_item.get('platform', 'thrift')} to my wardrobe for ${new_item.get('price', 'free')}. Great condition — ready to style!"

    return response
