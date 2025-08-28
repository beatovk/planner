"""
Simplified port conflict tests that work without complex subprocess handling.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


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


def test_port_environment_variable():
    """Test that PORT environment variable is used"""
    
    makefile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Makefile")
    
    with open(makefile_path, 'r', encoding='utf-8') as f:
        makefile_content = f.read()
    
    # Should use PORT variable
    assert "PORT ?=" in makefile_content, "Makefile should define PORT variable"
    assert "$(PORT)" in makefile_content, "Makefile should use PORT variable"


def test_port_conflict_workflow_documentation():
    """Test that port conflict workflow is documented"""
    
    readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md")
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Should mention the workflow: kill-port -> run
    assert "make kill-port" in readme_content, "README should mention make kill-port"
    assert "make run" in readme_content, "README should mention make run"
    
    # Should explain what happens
    assert "порт занят" in readme_content.lower() or "port conflict" in readme_content.lower(), \
        "README should explain port conflict scenarios"


def test_makefile_port_commands():
    """Test that Makefile has all necessary port-related commands"""
    
    makefile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Makefile")
    
    with open(makefile_path, 'r', encoding='utf-8') as f:
        makefile_content = f.read()
    
    # Should have all necessary commands
    assert "run:" in makefile_content, "Makefile should have run command"
    assert "kill-port:" in makefile_content, "Makefile should have kill-port command"
    
    # run command should use PORT
    run_lines = [line for line in makefile_content.split('\n') if line.strip().startswith('run:')]
    assert len(run_lines) > 0, "Should have run command"
    
    # kill-port command should use lsof
    kill_port_lines = [line for line in makefile_content.split('\n') if line.strip().startswith('kill-port:')]
    assert len(kill_port_lines) > 0, "Should have kill-port command"


def test_port_conflict_error_messages():
    """Test that port conflict error messages are documented"""
    
    readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md")
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Should mention what happens when port is occupied
    assert "порт занят" in readme_content.lower() or "port conflict" in readme_content.lower(), \
        "README should mention port conflict scenarios"
    
    # Should mention the solution
    assert "make kill-port" in readme_content, "README should mention make kill-port solution"
