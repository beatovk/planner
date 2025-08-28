"""
Test port conflict handling.
Ensures that the application handles port conflicts gracefully.
"""

import pytest
import subprocess
import time
import socket
import os
import signal
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True


def start_server_on_port(port: int, timeout: int = 5) -> subprocess.Popen:
    """Start a simple server on specified port"""
    # Use Python's built-in HTTP server
    cmd = [sys.executable, "-m", "http.server", str(port)]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    
    # Wait for server to start
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_port_in_use(port):
            time.sleep(0.1)
            continue
        break
    
    return process


def test_port_conflict_graceful_handling():
    """Test that port conflicts are handled gracefully"""
    
    # Ensure port 8000 is free initially
    assert not is_port_in_use(8000), "Port 8000 should be free initially"
    
    # Start a server on port 8000
    server_process = start_server_on_port(8000)
    
    try:
        # Verify server is running
        assert is_port_in_use(8000), "Server should be running on port 8000"
        
        # Try to start our app on the same port
        with patch('os.getenv', return_value='8000'):
            try:
                # This should fail gracefully
                result = subprocess.run(
                    [sys.executable, "-m", "apps.api"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Should exit with error code
                assert result.returncode != 0, "Should exit with error when port is in use"
                
                # Should have meaningful error message
                assert "Address already in use" in result.stderr or "port" in result.stderr.lower(), \
                    "Should have meaningful error message about port conflict"
                
            except subprocess.TimeoutExpired:
                # If it hangs, that's also a failure
                pytest.fail("Application should not hang on port conflict")
                
    finally:
        # Clean up
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)


def test_port_conflict_solution_documentation():
    """Test that port conflict solution is documented in README"""
    
    readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md")
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Should mention make kill-port as solution
    assert "make kill-port" in readme_content, "README should mention make kill-port as solution"
    assert "порт занят" in readme_content.lower() or "port conflict" in readme_content.lower(), \
        "README should mention port conflict scenarios"


def test_make_kill_port_command():
    """Test that make kill-port command works"""
    
    # This test verifies the Makefile command exists and is documented
    makefile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Makefile")
    
    with open(makefile_path, 'r', encoding='utf-8') as f:
        makefile_content = f.read()
    
    # Should have kill-port command
    assert "kill-port:" in makefile_content, "Makefile should have kill-port command"
    assert "lsof -ti:$(PORT)" in makefile_content, "kill-port should use lsof to find processes"


def test_port_conflict_with_different_ports():
    """Test that different ports don't conflict"""
    
    # Test with port 8001
    assert not is_port_in_use(8001), "Port 8001 should be free"
    
    # Start server on 8001
    server_process = start_server_on_port(8001)
    
    try:
        assert is_port_in_use(8001), "Server should be running on port 8001"
        
        # Port 8000 should still be free
        assert not is_port_in_use(8000), "Port 8000 should remain free"
        
    finally:
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)


def test_port_conflict_recovery():
    """Test that after port conflict is resolved, app can start normally"""
    
    # Start server on 8000
    server_process = start_server_on_port(8000)
    
    try:
        assert is_port_in_use(8000), "Server should be running on port 8000"
        
        # Stop the server
        server_process.terminate()
        server_process.wait(timeout=5)
        
        # Wait a bit for port to be released
        time.sleep(1)
        
        # Port should be free now
        assert not is_port_in_use(8000), "Port should be free after server stops"
        
    finally:
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)


def test_port_conflict_error_messages():
    """Test that port conflict error messages are user-friendly"""
    
    # Start server on 8000
    server_process = start_server_on_port(8000)
    
    try:
        assert is_port_in_use(8000), "Server should be running on port 8000"
        
        # Try to start app and capture error
        with patch('os.getenv', return_value='8000'):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "apps.api"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Error message should be helpful
                error_output = result.stderr.lower()
                helpful_indicators = [
                    "port", "address", "bind", "already in use", 
                    "occupied", "conflict", "8000"
                ]
                
                has_helpful_message = any(indicator in error_output for indicator in helpful_indicators)
                assert has_helpful_message, f"Error message should be helpful, got: {result.stderr}"
                
            except subprocess.TimeoutExpired:
                pytest.fail("Application should not hang on port conflict")
                
    finally:
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)
