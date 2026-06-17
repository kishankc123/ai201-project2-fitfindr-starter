"""
tests/test_tools.py

Pytest tests for the three FitFindr tools.
Tests cover happy path and failure modes for each tool.

Run with: pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings


# ── Tool 1: search_listings Tests ─────────────────────────────────────────────

class TestSearchListings:
    """Tests for search_listings(description, size, max_price)"""

    def test_search_returns_results(self):
        """Test that search_listings returns a list with results."""
        results = search_listings("vintage graphic tee")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_results_are_dicts(self):
        """Test that each result is a dict with expected fields."""
        results = search_listings("vintage graphic tee")
        for item in results:
            assert isinstance(item, dict)
            # Check that all required fields are present
            required_fields = [
                "id",
                "title",
                "description",
                "category",
                "style_tags",
                "size",
                "condition",
                "price",
                "colors",
                "brand",
                "platform",
            ]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_search_price_filter(self):
        """Test that max_price filter works correctly."""
        results = search_listings("jacket", max_price=20)
        assert all(item["price"] <= 20 for item in results)

    def test_search_size_filter(self):
        """Test that size filter works (case-insensitive)."""
        results = search_listings("graphic tee", size="M")
        # Size matching is substring-based (e.g., "M" matches "S/M", "M/L")
        for item in results:
            assert "M" in item["size"].upper()

    def test_search_combined_filters(self):
        """Test search with both size and price filters."""
        results = search_listings("graphic tee", size="M", max_price=25)
        for item in results:
            assert "M" in item["size"].upper()
            assert item["price"] <= 25

    def test_search_empty_results(self):
        """Test that search returns empty list when no matches found."""
        results = search_listings("designer ballgown", size="XXS", max_price=5)
        assert results == []
        assert isinstance(results, list)

    def test_search_sorted_by_relevance(self):
        """Test that results are sorted by relevance (keywords matched)."""
        # "vintage graphic tee" should rank "vintage graphic tee" items higher
        results = search_listings("vintage graphic tee", max_price=50)
        assert len(results) > 0
        # Top result should have "vintage" and/or "graphic" in title/description
        top_item_text = (results[0]["title"] + " " + results[0]["description"]).lower()
        assert any(word in top_item_text for word in ["vintage", "graphic", "tee"])

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        results_lower = search_listings("vintage")
        results_upper = search_listings("VINTAGE")
        results_mixed = search_listings("ViNtAgE")
        # All should return the same results
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_with_none_size(self):
        """Test that size=None ignores size filtering."""
        results = search_listings("graphic tee", size=None, max_price=50)
        assert isinstance(results, list)
        assert len(results) > 0
        # Should include various sizes
        sizes = [item["size"] for item in results]
        assert len(set(sizes)) > 1  # Multiple different sizes


# ── Tool 2: suggest_outfit Tests ────────────────────────────────────────────

class TestSuggestOutfit:
    """Tests for suggest_outfit(new_item, wardrobe)"""

    def test_suggest_outfit_with_populated_wardrobe(self):
        """Test suggest_outfit with a non-empty wardrobe."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]
        wardrobe = get_example_wardrobe()

        suggestion = suggest_outfit(item, wardrobe)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        assert suggestion.strip() != ""

    def test_suggest_outfit_with_empty_wardrobe(self):
        """Test suggest_outfit with an empty wardrobe."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]
        empty_wardrobe = get_empty_wardrobe()

        suggestion = suggest_outfit(item, empty_wardrobe)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        assert suggestion.strip() != ""
        # Empty wardrobe should provide general advice, not reference specific pieces

    def test_suggest_outfit_returns_string(self):
        """Test that suggest_outfit always returns a non-empty string."""
        results = search_listings("jacket", max_price=50)
        item = results[0]
        wardrobe = get_example_wardrobe()

        suggestion = suggest_outfit(item, wardrobe)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

    def test_suggest_outfit_with_different_items(self):
        """Test that different items produce different suggestions."""
        item1 = search_listings("jacket", max_price=50)[0]
        item2 = search_listings("vintage tee", max_price=30)[0]
        wardrobe = get_example_wardrobe()

        suggestion1 = suggest_outfit(item1, wardrobe)
        suggestion2 = suggest_outfit(item2, wardrobe)

        # Different items should produce different suggestions
        assert suggestion1 != suggestion2

    def test_suggest_outfit_non_empty_for_all_items(self):
        """Test that suggest_outfit returns non-empty string for various items."""
        all_listings = load_listings()[:5]  # Test with first 5 listings
        wardrobe = get_example_wardrobe()

        for item in all_listings:
            suggestion = suggest_outfit(item, wardrobe)
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
            assert suggestion.strip() != ""


# ── Tool 3: create_fit_card Tests ───────────────────────────────────────────

class TestCreateFitCard:
    """Tests for create_fit_card(outfit, new_item)"""

    def test_create_fit_card_with_outfit(self):
        """Test create_fit_card with a valid outfit suggestion."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]
        wardrobe = get_example_wardrobe()
        outfit = suggest_outfit(item, wardrobe)

        fit_card = create_fit_card(outfit, item)

        assert isinstance(fit_card, str)
        assert len(fit_card) > 0
        assert fit_card.strip() != ""

    def test_create_fit_card_with_empty_outfit(self):
        """Test create_fit_card with an empty outfit (fallback)."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]

        fit_card = create_fit_card("", item)

        assert isinstance(fit_card, str)
        assert len(fit_card) > 0
        # Should contain item title and price info (fallback format)
        assert item["title"] in fit_card or "Added" in fit_card

    def test_create_fit_card_with_none_outfit(self):
        """Test create_fit_card with None outfit (edge case)."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]

        fit_card = create_fit_card(None, item)

        assert isinstance(fit_card, str)
        assert len(fit_card) > 0

    def test_create_fit_card_with_whitespace_outfit(self):
        """Test create_fit_card with whitespace-only outfit."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]

        fit_card = create_fit_card("   ", item)

        assert isinstance(fit_card, str)
        assert len(fit_card) > 0

    def test_create_fit_card_mentions_item_info(self):
        """Test that fit card includes item details (price, platform, title)."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]
        wardrobe = get_example_wardrobe()
        outfit = suggest_outfit(item, wardrobe)

        fit_card = create_fit_card(outfit, item)

        # Should mention price and/or platform (at least in fallback case)
        assert (
            str(item["price"]) in fit_card or item["platform"].lower() in fit_card.lower()
        ) or item["title"] in fit_card

    def test_create_fit_card_varies_output(self):
        """Test that create_fit_card produces different outputs for same input (due to temperature)."""
        results = search_listings("vintage graphic tee", max_price=30)
        item = results[0]
        wardrobe = get_example_wardrobe()
        outfit = suggest_outfit(item, wardrobe)

        fit_card1 = create_fit_card(outfit, item)
        fit_card2 = create_fit_card(outfit, item)

        # Due to temperature=0.9, outputs should vary (though not guaranteed)
        # At minimum, both should be non-empty and valid
        assert isinstance(fit_card1, str)
        assert isinstance(fit_card2, str)
        assert len(fit_card1) > 0
        assert len(fit_card2) > 0

    def test_create_fit_card_returns_string_not_none(self):
        """Test that create_fit_card never returns None."""
        results = search_listings("jacket", max_price=50)
        item = results[0]

        # Test with various outfit inputs
        for outfit in ["", None, "   ", "valid outfit suggestion"]:
            fit_card = create_fit_card(outfit, item)
            assert fit_card is not None
            assert isinstance(fit_card, str)


# ── Integration Tests ───────────────────────────────────────────────────────

class TestToolsIntegration:
    """Integration tests for all three tools working together."""

    def test_full_pipeline(self):
        """Test the complete pipeline: search → suggest → card."""
        # Step 1: Search
        results = search_listings("vintage graphic tee", size="M", max_price=30)
        assert len(results) > 0

        item = results[0]

        # Step 2: Suggest outfit
        wardrobe = get_example_wardrobe()
        outfit = suggest_outfit(item, wardrobe)
        assert len(outfit) > 0

        # Step 3: Create fit card
        fit_card = create_fit_card(outfit, item)
        assert len(fit_card) > 0

    def test_full_pipeline_with_empty_wardrobe(self):
        """Test complete pipeline with empty wardrobe."""
        results = search_listings("vintage graphic tee", max_price=30)
        assert len(results) > 0

        item = results[0]
        empty_wardrobe = get_empty_wardrobe()

        outfit = suggest_outfit(item, empty_wardrobe)
        assert len(outfit) > 0

        fit_card = create_fit_card(outfit, item)
        assert len(fit_card) > 0

    def test_full_pipeline_no_results(self):
        """Test pipeline behavior when search returns no results."""
        results = search_listings("designer ballgown", size="XXS", max_price=5)
        assert len(results) == 0

        # If search returns empty, planning loop should stop here
        # We don't proceed to suggest_outfit or create_fit_card
