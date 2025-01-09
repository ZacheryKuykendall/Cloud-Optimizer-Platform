"""Tests for the base parser implementation."""

import os
from pathlib import Path
import pytest

from resource_requirements_parser import (
    ResourceType,
    SourceType,
)
from resource_requirements_parser.exceptions import (
    FileAccessError,
    ResourceTypeError,
)
from resource_requirements_parser.parser import BaseParser


class TestParser(BaseParser):
    """Test implementation of BaseParser."""

    def get_source_type(self) -> SourceType:
        """Get source type for testing."""
        return SourceType.CUSTOM

    def parse(self):
        """Dummy parse implementation."""
        pass

    def validate(self, requirements):
        """Dummy validate implementation."""
        return []


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory with test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    
    # Create a test file
    test_file = test_dir / "test.txt"
    test_file.write_text("Test content")

    return test_dir


def test_parser_initialization(temp_test_dir):
    """Test that the parser can be initialized with a valid path."""
    parser = TestParser(temp_test_dir)
    assert parser.source_path == Path(temp_test_dir)
    assert parser.get_source_type() == SourceType.CUSTOM


def test_parser_initialization_invalid_path():
    """Test that parser initialization fails with invalid path."""
    with pytest.raises(FileAccessError) as exc_info:
        TestParser("nonexistent/path")
    assert "does not exist" in str(exc_info.value)


def test_parser_initialization_invalid_file_type(temp_test_dir):
    """Test that parser initialization fails with invalid file type."""
    # Create a special file (like a device file) that's neither regular file nor directory
    special_file = temp_test_dir / "special"
    try:
        os.mkfifo(special_file)  # Create a named pipe
    except (OSError, AttributeError):
        pytest.skip("Cannot create special file for testing")

    with pytest.raises(FileAccessError) as exc_info:
        TestParser(special_file)
    assert "must be a file or directory" in str(exc_info.value)


def test_read_file(temp_test_dir):
    """Test reading file contents."""
    parser = TestParser(temp_test_dir)
    content = parser._read_file(temp_test_dir / "test.txt")
    assert content == "Test content"


def test_read_file_nonexistent():
    """Test reading nonexistent file."""
    parser = TestParser("dummy/path")
    with pytest.raises(FileAccessError) as exc_info:
        parser._read_file(Path("nonexistent.txt"))
    assert "Failed to read file" in str(exc_info.value)


def test_identify_resource_type():
    """Test resource type identification."""
    parser = TestParser("dummy/path")

    # Test with explicit type
    resource_data = {"type": "compute"}
    assert parser._identify_resource_type("test", resource_data) == ResourceType.COMPUTE

    # Test inference from name
    assert parser._identify_resource_type("web_instance", {}) == ResourceType.COMPUTE
    assert parser._identify_resource_type("data_bucket", {}) == ResourceType.STORAGE
    assert parser._identify_resource_type("main_vpc", {}) == ResourceType.NETWORK
    assert parser._identify_resource_type("mysql_db", {}) == ResourceType.DATABASE
    assert parser._identify_resource_type("redis_cache", {}) == ResourceType.CACHE
    assert parser._identify_resource_type("lambda_function", {}) == ResourceType.SERVERLESS
    assert parser._identify_resource_type("message_queue", {}) == ResourceType.QUEUE
    assert parser._identify_resource_type("app_loadbalancer", {}) == ResourceType.LOAD_BALANCER
    assert parser._identify_resource_type("dns_zone", {}) == ResourceType.DNS
    assert parser._identify_resource_type("cdn_distribution", {}) == ResourceType.CDN
    assert parser._identify_resource_type("log_monitor", {}) == ResourceType.MONITORING
    assert parser._identify_resource_type("waf_rule", {}) == ResourceType.SECURITY
    assert parser._identify_resource_type("user_role", {}) == ResourceType.IAM

    # Test unknown resource type
    with pytest.raises(ResourceTypeError) as exc_info:
        parser._identify_resource_type("unknown_resource", {})
    assert "Could not identify resource type" in str(exc_info.value)


def test_extract_dependencies():
    """Test dependency extraction."""
    parser = TestParser("dummy/path")

    # Test direct dependencies
    resource_data = {
        "depends_on": ["resource1", "resource2"]
    }
    deps = parser._extract_dependencies(resource_data)
    assert "resource1" in deps
    assert "resource2" in deps

    # Test string dependency
    resource_data = {
        "depends_on": "resource1"
    }
    deps = parser._extract_dependencies(resource_data)
    assert "resource1" in deps

    # Test nested dependencies
    resource_data = {
        "nested": {
            "deeper": {
                "depends_on": ["resource1"],
                "dependson": ["resource2"],
                "dependencies": "resource3"
            }
        }
    }
    deps = parser._extract_dependencies(resource_data)
    assert "resource1" in deps
    assert "resource2" in deps
    assert "resource3" in deps

    # Test empty dependencies
    assert not parser._extract_dependencies({})


def test_extract_tags():
    """Test tag extraction."""
    parser = TestParser("dummy/path")

    # Test direct tags
    resource_data = {
        "tags": {
            "Name": "test",
            "Environment": "prod"
        }
    }
    tags = parser._extract_tags(resource_data)
    assert tags["Name"] == "test"
    assert tags["Environment"] == "prod"

    # Test empty tags
    assert not parser._extract_tags({})

    # Test invalid tags
    assert not parser._extract_tags({"tags": "invalid"})


def test_parser_registry():
    """Test parser registry functionality."""
    from resource_requirements_parser.parser import ParserRegistry

    # Register test parser
    ParserRegistry.register(SourceType.CUSTOM, TestParser)

    # Get supported types
    supported_types = ParserRegistry.get_supported_types()
    assert SourceType.CUSTOM in supported_types

    # Get parser instance
    parser = ParserRegistry.get_parser(SourceType.CUSTOM, "dummy/path")
    assert isinstance(parser, TestParser)

    # Test unsupported type
    class UnsupportedType(str, SourceType):
        UNSUPPORTED = "unsupported"

    with pytest.raises(Exception) as exc_info:
        ParserRegistry.get_parser(UnsupportedType.UNSUPPORTED, "dummy/path")
    assert "No parser registered" in str(exc_info.value)
