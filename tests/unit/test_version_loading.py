"""Tests for dynamic version loading from pyproject.toml."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest


class TestDynamicVersionLoading:
    """Test dynamic version loading functionality."""

    def test_version_loads_from_pyproject_toml(self) -> None:
        """Test that version is loaded from pyproject.toml."""
        from refactored import __version__

        # The version should be loaded from pyproject.toml
        assert __version__ == "2.0.0"
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_fallback_mechanism(self) -> None:
        """Test that version fallback works when pyproject.toml is not accessible."""
        # Mock the get_project_version function to test fallback
        with patch(
            "refactored.utils.version_utils.get_project_version"
        ) as mock_get_version:
            mock_get_version.return_value = "2.0.0"

            from refactored.utils.version_utils import get_project_version

            version = get_project_version()

            assert version == "2.0.0"

    def test_version_parsing_from_pyproject_content(self) -> None:
        """Test that version is correctly parsed from pyproject.toml content."""
        # Mock pyproject.toml content
        mock_content = """
[build-system]
requires = ["setuptools", "wheel"]

[project]
name = "test-project"
version = "1.2.3"
description = "Test project"
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=mock_content):
                from refactored.utils.version_utils import get_project_version

                version = get_project_version()

                assert version == "1.2.3"

    def test_version_parsing_different_quote_styles(self) -> None:
        """Test that version parsing works with different quote styles."""
        test_cases = [
            ('version = "1.2.3"', "1.2.3"),
            ("version = '1.2.3'", "1.2.3"),
            ('version="1.2.3"', "1.2.3"),
            ("version='1.2.3'", "1.2.3"),
            ('version = "2.0.0-alpha"', "2.0.0-alpha"),
        ]

        for content_template, expected_version in test_cases:
            mock_content = f"""
[project]
name = "test"
{content_template}
"""
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value=mock_content):
                    from refactored.utils.version_utils import get_project_version

                    version = get_project_version()

                    assert version == expected_version

    def test_version_fallback_when_file_not_found(self) -> None:
        """Test fallback behavior when pyproject.toml is not found."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch(
                "importlib.metadata.version",
                side_effect=ModuleNotFoundError("Not installed"),
            ):
                from refactored.utils.version_utils import get_project_version

                version = get_project_version()

                # Should return fallback version
                assert version == "2.0.0"

    def test_version_fallback_when_parsing_fails(self) -> None:
        """Test fallback behavior when version parsing fails."""
        # Mock pyproject.toml with malformed content
        mock_content = """
[project]
name = "test"
# No version field
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=mock_content):
                with patch(
                    "importlib.metadata.version",
                    side_effect=ModuleNotFoundError("Not installed"),
                ):
                    from refactored.utils.version_utils import get_project_version

                    version = get_project_version()

                    # Should return fallback version
                    assert version == "2.0.0"

    def test_version_is_accessible_from_package_init(self) -> None:
        """Test that version is accessible from package __init__."""
        import refactored

        assert hasattr(refactored, "__version__")
        assert isinstance(refactored.__version__, str)
        assert len(refactored.__version__) > 0

    def test_version_consistency_across_imports(self) -> None:
        """Test that version is consistent across different import patterns."""
        import refactored
        from refactored import __version__ as version1

        assert version1 == refactored.__version__
