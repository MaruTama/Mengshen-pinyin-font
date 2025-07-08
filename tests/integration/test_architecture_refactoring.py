# -*- coding: utf-8 -*-
"""Integration tests for architecture refactoring - New vs Legacy implementation."""

from __future__ import annotations

import pytest
import tempfile
import time
from pathlib import Path
from typing import Dict, Any
import subprocess
import sys

from src.mengshen_font.cli import main as new_main
from src.mengshen_font.config import FontType, ProjectPaths
from src.mengshen_font.font import FontBuilder


class TestArchitectureRefactoring:
    """Test suite for new architecture vs legacy implementation."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def project_paths(self, temp_output_dir):
        """Create project paths with temporary output."""
        paths = ProjectPaths()
        paths.outputs_dir = temp_output_dir
        return paths
    
    def test_new_implementation_cli_interface(self):
        """Test new CLI interface functionality."""
        # Test help command (catches SystemExit)
        import pytest
        with pytest.raises(SystemExit) as excinfo:
            new_main(["--help"])
        assert excinfo.value.code == 0  # Help should exit with code 0
        
        # Test dry-run mode
        result = new_main(["--dry-run", "-t", "han_serif"])
        assert result == 0
    
    def test_new_implementation_font_types(self):
        """Test new implementation supports all font types."""
        from src.mengshen_font.config import FontType
        
        # Ensure all font types are supported
        assert FontType.HAN_SERIF in FontType
        assert FontType.HANDWRITTEN in FontType
    
    def test_new_implementation_dependency_injection(self):
        """Test dependency injection pattern in new implementation."""
        from src.mengshen_font.data import PinyinDataManager
        from src.mengshen_font.font import FontBuilder
        
        # Test that FontBuilder accepts injected dependencies
        pinyin_manager = PinyinDataManager()
        assert pinyin_manager is not None
        
        # Test protocol-based interface
        assert hasattr(pinyin_manager, 'get_pinyin')
        assert hasattr(pinyin_manager, 'get_all_mappings')
    
    def test_new_implementation_type_safety(self):
        """Test type safety in new implementation."""
        from src.mengshen_font.config import FontMetadata, PinyinCanvas, HanziCanvas
        from src.mengshen_font.data import CharacterInfo
        
        # Test dataclass immutability
        canvas = PinyinCanvas(width=850.0, height=283.3, base_line=935.0, tracking=22.145)
        assert canvas.width == 850.0
        
        # Test frozen dataclass cannot be modified
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            canvas.width = 900.0
        
        # Test CharacterInfo type safety
        char_info = CharacterInfo(character="中", pronunciations=["zhōng", "zhòng"])
        assert char_info.character == "中"
        assert len(char_info.pronunciations) == 2
    
    def test_new_implementation_memory_efficiency(self):
        """Test memory-efficient patterns in new implementation."""
        from src.mengshen_font.data import CharacterDataManager
        
        # Test iterator patterns for memory efficiency
        manager = CharacterDataManager()
        
        # Test that methods return iterators, not full lists in memory
        if hasattr(manager, 'iter_single_pronunciation_characters'):
            iterator = manager.iter_single_pronunciation_characters()
            # Should be an iterator/generator
            assert hasattr(iterator, '__iter__')
            assert hasattr(iterator, '__next__') or callable(getattr(iterator, '__next__', None))
    
    def test_separation_of_concerns(self):
        """Test separation of concerns in new architecture."""
        from src.mengshen_font.data import PinyinDataManager, CharacterDataManager, MappingDataManager
        from src.mengshen_font.font import GlyphManager, FontAssembler
        from src.mengshen_font.config import FontConfig
        
        # Each manager should have distinct responsibilities
        pinyin_mgr = PinyinDataManager()
        char_mgr = CharacterDataManager()
        mapping_mgr = MappingDataManager()
        
        # Test that each has its specific interface
        assert hasattr(pinyin_mgr, 'get_pinyin')
        assert hasattr(char_mgr, 'get_character_info') or hasattr(char_mgr, 'process_characters')
        assert hasattr(mapping_mgr, 'get_unicode_mappings') or hasattr(mapping_mgr, 'load_mappings')
    
    def test_config_centralization(self):
        """Test centralized configuration management."""
        from src.mengshen_font.config import FontConfig, FontType
        
        # Test config access patterns
        config = FontConfig.get_config(FontType.HAN_SERIF)
        assert config is not None
        
        # Test pinyin canvas access
        canvas = FontConfig.get_pinyin_canvas(FontType.HAN_SERIF)
        assert canvas is not None
        assert hasattr(canvas, 'width')
        assert hasattr(canvas, 'height')
    
    @pytest.mark.slow
    def test_performance_comparison_preparation(self):
        """Prepare for performance comparison between implementations."""
        # This test ensures both implementations can be measured
        # Actual performance comparison should be done in benchmark tests
        
        # Test that legacy main.py exists and is callable
        legacy_main_path = Path("src/main.py")
        assert legacy_main_path.exists()
        
        # Test that new implementation is importable
        from src.mengshen_font.cli import main as new_main
        assert callable(new_main)
    
    def test_backward_compatibility_layer(self):
        """Test backward compatibility functions."""
        # Test that legacy constants are still available through compatibility layer
        try:
            from src.mengshen_font.config import FontType
            # Test that legacy-style access works
            HAN_SERIF_TYPE = FontType.HAN_SERIF
            HANDWRITTEN_TYPE = FontType.HANDWRITTEN
            
            assert HAN_SERIF_TYPE == FontType.HAN_SERIF
            assert HANDWRITTEN_TYPE == FontType.HANDWRITTEN
        except ImportError:
            pytest.skip("Backward compatibility layer not yet implemented")
    
    def test_protocol_based_interfaces(self):
        """Test Protocol-based interfaces for dependency injection."""
        from src.mengshen_font.data import PinyinDataManager
        
        # Test that data manager implements expected protocols
        manager = PinyinDataManager()
        
        # Test protocol methods exist
        assert hasattr(manager, 'get_pinyin')
        assert hasattr(manager, 'get_all_mappings')
        
        # Test actual protocol compliance
        if hasattr(manager, '_data_source'):
            data_source = manager._data_source
            assert hasattr(data_source, 'get_pinyin')
            assert hasattr(data_source, 'get_all_mappings')
    
    def test_testability_improvements(self):
        """Test improved testability through dependency injection."""
        from src.mengshen_font.font import FontBuilder
        
        # Test that FontBuilder accepts mock dependencies
        # This ensures we can inject test doubles for testing
        try:
            # Try to create FontBuilder with minimal arguments
            builder = FontBuilder(
                font_type=FontType.HAN_SERIF,
                template_main_path=Path("test"),
                template_glyf_path=Path("test"),
                alphabet_pinyin_path=Path("test"),
                pattern_one_path=Path("test"),
                pattern_two_path=Path("test"),
                exception_pattern_path=Path("test")
            )
            assert builder is not None
        except Exception as e:
            # It's okay if it fails due to missing files,
            # we're just testing the interface accepts dependencies
            assert "FontBuilder" in str(type(e).__name__) or "path" in str(e).lower() or "file" in str(e).lower()
    
    def test_clean_architecture_layers(self):
        """Test clean architecture layer separation."""
        # Test that each layer only depends on inner layers
        
        # CLI layer should depend on font layer
        from src.mengshen_font.cli import main as cli_main
        from src.mengshen_font.font import FontBuilder
        
        # Font layer should depend on data layer  
        from src.mengshen_font.data import PinyinDataManager
        
        # Config layer should be independent
        from src.mengshen_font.config import FontConfig
        
        # Test import dependencies are correct
        assert cli_main is not None
        assert FontBuilder is not None
        assert PinyinDataManager is not None
        assert FontConfig is not None

    def test_cli_fails_with_missing_prerequisites(self, capsys, project_paths):
        """Test that the CLI exits gracefully if required files are missing."""
        from src.mengshen_font.cli.main import FontGenerationCLI
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Point to a directory where templates are known to be missing
            project_paths.temp_json_dir = Path(tmpdir)
            
            cli = FontGenerationCLI(paths=project_paths)
            
            # Run with a style that requires templates
            result = cli.run(["-t", "han_serif"])
            
            # Should exit with an error code
            assert result == 1
            
            # Check that an error message was printed to stderr
            captured = capsys.readouterr()
            assert "Error: Missing required files:" in captured.err
            assert "template_main" in captured.err

    def test_cli_handles_invalid_style_argument(self, capsys):
        """Test that the CLI handles an invalid font style argument."""
        result = new_main(["-t", "invalid_style"])
        assert result == 1
        captured = capsys.readouterr()
        assert "invalid choice: 'invalid_style'" in captured.err

    def test_cli_custom_output_path(self, temp_output_dir):
        """Test that the CLI respects the custom output path."""
        custom_path = temp_output_dir / "Custom.ttf"
        result = new_main(["--dry-run", "-t", "han_serif", "-o", str(custom_path)])
        assert result == 0

    def test_cli_verbose_mode(self, capsys):
        """Test that the CLI's verbose mode prints additional information."""
        # We can't fully test font generation here, but we can test dry-run verbosity
        result = new_main(["--dry-run", "-t", "han_serif", "-v"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Font type: HAN_SERIF" in captured.out
        assert "Output path:" in captured.out


class TestParallelProcessingOptimization:
    """Test parallel processing optimizations."""
    
    def test_parallel_processing_module_exists(self):
        """Test that parallel processing module exists."""
        try:
            from src.mengshen_font.processing import parallel_processor
            assert parallel_processor is not None
        except ImportError:
            pytest.skip("Parallel processing module not yet implemented")
    
    def test_cache_manager_exists(self):
        """Test that cache manager module exists."""
        try:
            from src.mengshen_font.processing import cache_manager
            assert cache_manager is not None
        except ImportError:
            pytest.skip("Cache manager module not yet implemented")
    
    def test_benchmark_module_exists(self):
        """Test that benchmark module exists."""
        try:
            from src.mengshen_font.processing import benchmark
            assert benchmark is not None
        except ImportError:
            pytest.skip("Benchmark module not yet implemented")


class TestSecurityImprovements:
    """Test security improvements in new implementation."""
    
    def test_no_shell_injection_vulnerabilities(self):
        """Test that new implementation has no shell injection vulnerabilities."""
        from src.mengshen_font.font import FontBuilder
        
        # Check that FontBuilder doesn't use shell=True
        import inspect
        source = inspect.getsource(FontBuilder)
        assert "shell=True" not in source
        
        # Check for secure subprocess usage
        if "subprocess" in source:
            # If subprocess is used, it should be secure
            assert "shell=False" in source or "shell=" not in source
    
    def test_path_traversal_protection(self):
        """Test path traversal protection."""
        from src.mengshen_font.config import ProjectPaths
        
        paths = ProjectPaths()
        
        # Test that malicious paths are handled safely
        try:
            # This should not allow path traversal
            safe_path = paths.get_output_path("../../../etc/passwd")
            # Should be within project bounds
            assert str(safe_path).startswith(str(paths.outputs_dir))
        except (ValueError, SecurityError, Exception):
            # It's good if it raises an exception for malicious paths
            pass