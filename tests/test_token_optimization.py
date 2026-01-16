"""
Tests for token usage optimization in phase configuration.

Verifies that thinking budgets are set to minimal levels for deterministic
operations while maintaining quality for phases that benefit from reasoning.
"""

import sys
from pathlib import Path

import pytest

# Add auto-claude to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from phase_config import (
    DEFAULT_PHASE_THINKING,
    SPEC_PHASE_THINKING_LEVELS,
    THINKING_BUDGET_MAP,
    get_spec_phase_thinking_budget,
    get_thinking_budget,
)


class TestTokenOptimization:
    """Test token usage optimization across all phases."""

    def test_discovery_uses_minimal_tokens(self):
        """Discovery phase should use minimal tokens (runs deterministic script)."""
        budget = get_spec_phase_thinking_budget("discovery")
        expected = THINKING_BUDGET_MAP["low"]  # 1024 tokens
        assert budget == expected, (
            f"Discovery phase should use 'low' budget ({expected} tokens), "
            f"got {budget} tokens. Discovery runs deterministic analyzer script "
            "and doesn't benefit from extended thinking."
        )

    def test_spec_writing_uses_moderate_tokens(self):
        """Spec writing should use moderate tokens for analysis."""
        budget = get_spec_phase_thinking_budget("spec_writing")
        expected = THINKING_BUDGET_MAP["medium"]  # 4096 tokens
        assert budget == expected, (
            f"Spec writing should use 'medium' budget ({expected} tokens), "
            f"got {budget} tokens. Medium provides sufficient reasoning for most specs."
        )

    def test_self_critique_uses_ultrathink(self):
        """Self-critique phase should use ultrathink for deep analysis."""
        budget = get_spec_phase_thinking_budget("self_critique")
        expected = THINKING_BUDGET_MAP["ultrathink"]  # 60000 tokens
        assert budget == expected, (
            f"Self-critique should use 'ultrathink' budget ({expected} tokens), "
            f"got {budget} tokens. This is the only phase that needs deep analysis."
        )

    def test_light_phases_use_minimal_tokens(self):
        """Light phases (data collection) should use minimal tokens."""
        light_phases = [
            "requirements",
            "research",
            "context",
            "planning",
            "validation",
            "quick_spec",
            "historical_context",
            "complexity_assessment",
        ]
        expected = THINKING_BUDGET_MAP["low"]  # 1024 tokens

        for phase in light_phases:
            budget = get_spec_phase_thinking_budget(phase)
            assert budget == expected, (
                f"Light phase '{phase}' should use 'low' budget ({expected} tokens), "
                f"got {budget} tokens. Light phases are data collection and don't need "
                "extended thinking."
            )

    def test_default_phase_thinking_optimized(self):
        """Default phase thinking should be optimized for common cases."""
        # Spec phase (default for spec runner)
        assert DEFAULT_PHASE_THINKING["spec"] == "low", (
            "Default spec phase should use 'low' for minimal token usage"
        )

        # Planning phase
        assert DEFAULT_PHASE_THINKING["planning"] == "medium", (
            "Planning phase should use 'medium' for reasonable analysis"
        )

        # Coding phase
        assert DEFAULT_PHASE_THINKING["coding"] == "low", (
            "Coding phase should use 'low' - implementation is mostly straightforward"
        )

        # QA phase
        assert DEFAULT_PHASE_THINKING["qa"] == "medium", (
            "QA phase should use 'medium' for validation reasoning"
        )

    def test_token_savings_for_simple_task(self):
        """Verify token savings for a simple task workflow."""
        # Simple task phases: discovery → historical_context → quick_spec → validation
        simple_phases = ["discovery", "historical_context", "quick_spec", "validation"]

        total_tokens = sum(
            get_spec_phase_thinking_budget(phase) or 0 for phase in simple_phases
        )

        # Expected: 4 phases × 1024 tokens = 4096 tokens
        expected_total = 4 * THINKING_BUDGET_MAP["low"]

        assert total_tokens == expected_total, (
            f"Simple task should use ~{expected_total} tokens total, got {total_tokens}. "
            f"This is a {((expected_total / 68000) * 100):.0f}% reduction from the old "
            "68K tokens (discovery used 60K ultrathink before optimization)."
        )

    def test_token_savings_for_standard_task(self):
        """Verify token savings for a standard task workflow."""
        # Standard phases: discovery → requirements → research → context → spec_writing → planning
        standard_phases = [
            "discovery",
            "requirements",
            "research",
            "context",
            "spec_writing",
            "planning",
        ]

        total_tokens = sum(
            get_spec_phase_thinking_budget(phase) or 0 for phase in standard_phases
        )

        # Expected: 5 phases × 1K (low) + 1 phase × 4K (spec_writing medium) = 9K tokens
        expected_total = 5 * THINKING_BUDGET_MAP["low"] + THINKING_BUDGET_MAP["medium"]

        assert total_tokens == expected_total, (
            f"Standard task should use ~{expected_total} tokens total, got {total_tokens}. "
            "This is a significant reduction from 128K tokens before optimization."
        )

    def test_no_ultrathink_except_critique(self):
        """Only self-critique should use ultrathink to prevent token waste."""
        ultrathink_phases = [
            phase
            for phase, level in SPEC_PHASE_THINKING_LEVELS.items()
            if level == "ultrathink"
        ]

        assert ultrathink_phases == ["self_critique"], (
            f"Only 'self_critique' should use ultrathink, but found: {ultrathink_phases}. "
            "Ultrathink (60K tokens) should be reserved for deep analysis in complex tasks only."
        )

    def test_spec_phase_levels_complete(self):
        """Verify all spec phases have thinking levels defined."""
        # All known spec phases should have a thinking level
        expected_phases = {
            "discovery",
            "spec_writing",
            "self_critique",
            "requirements",
            "research",
            "context",
            "planning",
            "validation",
            "quick_spec",
            "historical_context",
            "complexity_assessment",
        }

        defined_phases = set(SPEC_PHASE_THINKING_LEVELS.keys())

        assert defined_phases == expected_phases, (
            f"Missing or extra phases in SPEC_PHASE_THINKING_LEVELS. "
            f"Missing: {expected_phases - defined_phases}, "
            f"Extra: {defined_phases - expected_phases}"
        )

    def test_thinking_budget_values_unchanged(self):
        """Verify thinking budget token values haven't changed."""
        assert THINKING_BUDGET_MAP["none"] is None
        assert THINKING_BUDGET_MAP["low"] == 1024
        assert THINKING_BUDGET_MAP["medium"] == 4096
        assert THINKING_BUDGET_MAP["high"] == 16384
        assert THINKING_BUDGET_MAP["ultrathink"] == 60000
