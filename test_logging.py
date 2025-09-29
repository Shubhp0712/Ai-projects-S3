#!/usr/bin/env python3
"""
Simple test to verify the enhanced logging functionality
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def main():
    """Test the logging functionality with simple_py.py"""
    try:
        # Import the enhanced automator
        import importlib.util
        spec = importlib.util.spec_from_file_location("hello_py", project_dir / "hello-py.py")
        hello_py_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hello_py_module)
        
        EnhancedProjectTestAutomator = hello_py_module.EnhancedProjectTestAutomator
        
        # Use simple_py.py for testing
        project_path = str(project_dir / "simple_py.py")
        
        print("🧪 Testing Enhanced Logging Functionality")
        print(f"📁 Testing project: {project_path}")
        print("-" * 60)
        
        # Run automation with context manager to ensure proper cleanup
        with EnhancedProjectTestAutomator(project_path) as automator:
            results = automator.run_full_automation()
            
            print("\n" + "=" * 60)
            print("✅ LOGGING TEST COMPLETED")
            print("=" * 60)
            
            # Check if log file was created
            if hasattr(automator, 'log_file_path') and automator.log_file_path.exists():
                log_size = automator.log_file_path.stat().st_size
                print(f"📄 Log file created: {automator.log_file_path}")
                print(f"📊 Log file size: {log_size} bytes ({log_size/1024:.2f} KB)")
                
                # Display first few lines of log
                with open(automator.log_file_path, 'r', encoding='utf-8') as log_file:
                    lines = log_file.readlines()
                    print(f"📋 Log contains {len(lines)} lines")
                    
                    print("\n📝 First 10 lines of log file:")
                    print("-" * 40)
                    for i, line in enumerate(lines[:10], 1):
                        print(f"{i:2d}: {line.rstrip()}")
                    
                    if len(lines) > 10:
                        print(f"... and {len(lines) - 10} more lines")
                        
                        print(f"\n📝 Last 5 lines of log file:")
                        print("-" * 40)
                        for i, line in enumerate(lines[-5:], len(lines)-4):
                            print(f"{i:2d}: {line.rstrip()}")
            else:
                print("❌ Log file was not created")
                
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)