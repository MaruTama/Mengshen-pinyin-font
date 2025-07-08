# -*- coding: utf-8 -*-
"""
Meta Tests for TDD and Refactoring Documentation.
"""

import pytest
from pathlib import Path


class TestMeta:
    """Meta tests for project documentation and standards."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_tdd_cycle_enforcement(self, project_root):
        """
        Test that TDD cycle enforcement is in place.
        """
        claude_md = project_root / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md must exist with TDD instructions"

        with open(claude_md, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'TDD' in content, "CLAUDE.md must mention TDD"
            assert 'Red' in content and 'Green' in content, "Must describe Red-Green-Refactor"
            assert 'Pipeline' in content, "Must include pipeline validation"

        refactor_md = project_root / "REFACTOR.md"
        assert refactor_md.exists(), "REFACTOR.md must exist with TDD strategy"

        with open(refactor_md, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'TDD原則' in content or 'TDD' in content, "REFACTOR.md must describe TDD principles"
            assert 'Pipeline' in content, "Must include pipeline integration"
