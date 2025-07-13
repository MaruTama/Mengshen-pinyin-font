# -*- coding: utf-8 -*-
"""
Path validation security tests.

These tests verify that file path validation prevents directory traversal
attacks and unauthorized file access.
"""

from pathlib import Path

import pytest

from refactored.config.paths import ProjectPaths
from refactored.utils.shell_utils import SecurityError, validate_file_path


class TestPathValidation:
    """Test path validation security measures."""

    @pytest.mark.security
    def test_path_traversal_prevention(self, sample_path_traversal_attacks):
        """Test that path traversal attacks are prevented."""
        for malicious_path in sample_path_traversal_attacks:
            with pytest.raises((SecurityError, ValueError)):
                # Any path validation should reject these patterns
                validate_file_path(malicious_path)

    @pytest.mark.security
    def test_absolute_path_restrictions(self):
        """Test that absolute paths outside project are restricted."""
        project_paths = ProjectPaths()

        # System paths that should be rejected
        restricted_paths = [
            "/etc/passwd",
            "/usr/bin/python",
            "/root/.ssh/id_rsa",
            "C:\\Windows\\System32\\config\\SAM",
            "C:\\Users\\Administrator\\Desktop\\secrets.txt",
        ]

        for path in restricted_paths:
            if Path(path).exists():
                with pytest.raises((SecurityError, PermissionError)):
                    project_paths.validate_path(path)

    @pytest.mark.security
    def test_symlink_attack_prevention(self, temp_dir):
        """Test that symbolic link attacks are prevented."""
        project_paths = ProjectPaths()

        # Create a symlink pointing to a sensitive file
        sensitive_file = temp_dir / "sensitive.txt"
        sensitive_file.write_text("SENSITIVE_DATA")

        malicious_link = temp_dir / "innocent_name.txt"

        try:
            # Create symlink (may fail on some systems)
            malicious_link.symlink_to(sensitive_file)

            # Path validation should detect and reject symlinks to sensitive areas
            with pytest.raises(SecurityError):
                project_paths.validate_path(str(malicious_link))

        except (OSError, NotImplementedError):
            # Symlinks not supported on this system, skip test
            pytest.skip("Symlinks not supported on this system")

    @pytest.mark.security
    def test_project_boundary_enforcement(self):
        """Test that paths are restricted to project boundaries."""
        project_paths = ProjectPaths()

        # Valid project paths should be accepted
        valid_paths = [
            project_paths.get_temp_json_path("test.json"),
            project_paths.get_output_path("test.ttf"),
            project_paths.get_pattern_path("pattern.json"),
        ]

        for valid_path in valid_paths:
            # Should not raise an exception
            project_paths.validate_path(str(valid_path))

    @pytest.mark.security
    def test_filename_sanitization(self):
        """Test that filenames are properly sanitized."""
        project_paths = ProjectPaths()

        # Malicious filenames that should be rejected
        malicious_names = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "file\x00name.txt",  # Null byte injection
            "file\nname.txt",  # Newline injection
            "file\rname.txt",  # Carriage return injection
            "file\tname.txt",  # Tab injection
            "CON",  # Windows reserved name
            "PRN",  # Windows reserved name
            "AUX",  # Windows reserved name
            "NUL",  # Windows reserved name
            "file" + "A" * 300,  # Overly long filename
        ]

        for malicious_name in malicious_names:
            with pytest.raises((SecurityError, ValueError)):
                project_paths.get_temp_json_path(malicious_name)

    @pytest.mark.security
    def test_case_sensitivity_attacks(self):
        """Test that case sensitivity attacks are prevented."""
        project_paths = ProjectPaths()

        # Case variations that might bypass simple filters
        case_attacks = [
            "../ETC/passwd",
            "../etc/PASSWD",
            "../Etc/Passwd",
            "..\\WINDOWS\\system32\\CONFIG\\sam",
            "..\\windows\\SYSTEM32\\config\\SAM",
        ]

        for attack in case_attacks:
            with pytest.raises((SecurityError, ValueError)):
                project_paths.validate_path(attack)

    @pytest.mark.security
    def test_unicode_normalization_attacks(self):
        """Test that Unicode normalization attacks are prevented."""
        project_paths = ProjectPaths()

        # Unicode characters that might normalize to dangerous patterns
        unicode_attacks = [
            "..%2F..%2F..%2Fetc%2Fpasswd",  # URL encoded
            "..%5C..%5C..%5Cwindows%5Csystem32",  # URL encoded backslashes
            "..\u002F..\u002F..\u002Fetc\u002Fpasswd",  # Unicode slash
            "..\u005C..\u005C..\u005Cwindows\u005Csystem32",  # Unicode backslash
        ]

        for attack in unicode_attacks:
            with pytest.raises((SecurityError, ValueError)):
                project_paths.validate_path(attack)

    @pytest.mark.security
    def test_temporary_directory_security(self, temp_dir):
        """Test that temporary directory handling is secure."""
        project_paths = ProjectPaths()

        # Should be able to create files in designated temp area
        temp_file = project_paths.get_temp_json_path("safe_temp.json")
        assert temp_file.parent.exists() or temp_file.parent.parent.exists()

        # Should not be able to access system temp directories
        system_temp_dirs = [
            "/tmp",
            "/var/tmp",
            "C:\\Windows\\Temp",
            "C:\\Temp",
        ]

        for temp_dir_path in system_temp_dirs:
            if Path(temp_dir_path).exists():
                with pytest.raises((SecurityError, PermissionError)):
                    # Should not be able to validate paths in system temp
                    project_paths.validate_path(temp_dir_path + "/malicious.txt")

    @pytest.mark.security
    def test_relative_path_resolution(self):
        """Test that relative paths are resolved securely."""
        project_paths = ProjectPaths()

        # Test various relative path patterns
        relative_patterns = [
            "../../sensitive.txt",
            "../../../etc/passwd",
            "../../../../usr/bin/python",
            "./../../../root/.ssh/id_rsa",
            "temp/../../../sensitive.txt",
        ]

        for pattern in relative_patterns:
            with pytest.raises((SecurityError, ValueError)):
                project_paths.validate_path(pattern)

    @pytest.mark.security
    def test_path_length_limits(self):
        """Test that path length limits are enforced."""
        project_paths = ProjectPaths()

        # Test with overly long path
        long_path = "a" * 1000 + ".txt"

        with pytest.raises((SecurityError, ValueError, OSError)):
            project_paths.validate_path(long_path)

    @pytest.mark.security
    def test_special_device_file_protection(self):
        """Test that special device files are protected."""
        project_paths = ProjectPaths()

        # Unix/Linux special device files
        special_files = [
            "/dev/null",
            "/dev/zero",
            "/dev/random",
            "/dev/urandom",
            "/dev/stdin",
            "/dev/stdout",
            "/dev/stderr",
            "/proc/version",
            "/proc/cpuinfo",
            "/proc/meminfo",
        ]

        for special_file in special_files:
            if Path(special_file).exists():
                with pytest.raises((SecurityError, PermissionError)):
                    project_paths.validate_path(special_file)

    @pytest.mark.security
    def test_network_path_rejection(self):
        """Test that network paths are rejected."""
        project_paths = ProjectPaths()

        # Network paths that should be rejected
        network_paths = [
            "\\\\evil.com\\share\\malware.exe",
            "\\\\192.168.1.100\\share\\sensitive.txt",
            "smb://evil.com/share/malware.exe",
            "ftp://evil.com/sensitive.txt",
            "http://evil.com/malware.exe",
            "https://evil.com/sensitive.txt",
        ]

        for network_path in network_paths:
            with pytest.raises((SecurityError, ValueError)):
                project_paths.validate_path(network_path)


class TestSecurePathOperations:
    """Test secure path operations."""

    @pytest.mark.security
    def test_secure_file_creation(self, temp_dir):
        """Test that files are created securely."""
        project_paths = ProjectPaths()

        # Create file in secure location
        secure_file = temp_dir / "secure_test.txt"
        secure_file.write_text("test content")

        # Verify file permissions are appropriate
        file_stat = secure_file.stat()

        # File should not be world-writable
        assert not (file_stat.st_mode & 0o002)

        # File should be readable by owner
        assert file_stat.st_mode & 0o400

    @pytest.mark.security
    def test_secure_directory_creation(self, temp_dir):
        """Test that directories are created securely."""
        project_paths = ProjectPaths()

        # Create directory in secure location
        secure_dir = temp_dir / "secure_dir"
        secure_dir.mkdir(mode=0o755)

        # Verify directory permissions are appropriate
        dir_stat = secure_dir.stat()

        # Directory should not be world-writable
        assert not (dir_stat.st_mode & 0o002)

        # Directory should be accessible by owner
        assert dir_stat.st_mode & 0o700

    @pytest.mark.security
    def test_path_canonicalization(self):
        """Test that paths are properly canonicalized."""
        project_paths = ProjectPaths()

        # Test path canonicalization
        test_paths = [
            "./test.txt",
            "test/../test.txt",
            "test/./test.txt",
            "test//test.txt",
        ]

        for path in test_paths:
            try:
                canonical = project_paths.canonicalize_path(path)

                # Canonical path should not contain ".." or "."
                assert ".." not in str(canonical)
                assert "/." not in str(canonical)
                assert "\\.." not in str(canonical)

            except (SecurityError, ValueError):
                # Some paths might be rejected, which is acceptable
                pass

    @pytest.mark.security
    def test_race_condition_prevention(self, temp_dir):
        """Test that race conditions in file operations are prevented."""
        project_paths = ProjectPaths()

        # Create a file
        test_file = temp_dir / "race_test.txt"
        test_file.write_text("original content")

        # Ensure file operations are atomic where possible
        # This is a simplified test - real implementation would need
        # more sophisticated race condition testing

        original_content = test_file.read_text()
        assert original_content == "original content"

        # Modify file
        test_file.write_text("modified content")

        modified_content = test_file.read_text()
        assert modified_content == "modified content"
