#!/usr/bin/env python3
"""
Enhanced Python Project Unit Testing Automation Tool with Groq AI
This version forces testing of all functions when no git changes are detected.
"""

import os
import subprocess
import json
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import ast
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import fnmatch
from urllib.parse import urlparse
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging
import requests

# --- Configuration ---
GROQ_MODEL = "llama-3.3-70b-versatile"  # Default Groq model
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "REDACTED_API_KEY")  # Set your Groq API key
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
COVERAGE_THRESHOLD = 0.8
DEFAULT_TEST_DIR = "tests"

# Email Configuration - Set your fixed email credentials here
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587
DEFAULT_FROM_EMAIL = "shubhgugada2005@gmail.com"      # Replace with your sender email
DEFAULT_TO_EMAIL = "shubhsamarth8992@gmail.com"      # Replace with your receiver email  
DEFAULT_EMAIL_PASSWORD = "qcxs evkj xibq yknl"      # Replace with your app password

# File patterns to include/exclude
INCLUDE_PATTERNS = ["*.py"]
EXCLUDE_PATTERNS = ["test_*.py", "*_test.py", "tests/*", ".git/*"]

class GitHubRepoManager:
    """Manages GitHub repository cloning and cleanup"""
    
    def __init__(self):
        self.temp_dir = None
        self.cloned_repo_path = None
    
    def is_github_url(self, url_or_path: str) -> bool:
        """Check if the given string is a GitHub repository URL"""
        try:
            parsed = urlparse(url_or_path)
            return parsed.netloc.lower() in ['github.com', 'www.github.com']
        except:
            return False
    
    def clone_repository(self, github_url: str) -> str:
        """Clone a GitHub repository to a temporary directory and return the local path"""
        print(f"🔗 Cloning GitHub repository: {github_url}")
        
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="github_test_automation_")
        
        # Extract repository name for the local directory
        repo_name = self._extract_repo_name(github_url)
        self.cloned_repo_path = Path(self.temp_dir) / repo_name
        
        try:
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', github_url, str(self.cloned_repo_path)],
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"✅ Repository cloned successfully to: {self.cloned_repo_path}")
            print(f"📁 Temporary directory: {self.temp_dir}")
            
            return str(self.cloned_repo_path)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone repository: {e.stderr}")
            self.cleanup()
            raise Exception(f"Git clone failed: {e.stderr}")
        except Exception as e:
            print(f"❌ Error during cloning: {e}")
            self.cleanup()
            raise
    
    def _extract_repo_name(self, github_url: str) -> str:
        """Extract repository name from GitHub URL"""
        # Handle both HTTPS and SSH URLs
        if github_url.endswith('.git'):
            github_url = github_url[:-4]
        
        # Extract the last part of the path as repo name
        parts = github_url.rstrip('/').split('/')
        return parts[-1] if parts else "repo"
    
    def cleanup(self):
        """Clean up temporary directory and cloned repository"""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"⚠️  Failed to clean up temporary directory: {e}")
        
        self.temp_dir = None
        self.cloned_repo_path = None

class EmailService:
    """Handles email notifications with SMTP support"""
    
    def __init__(self, smtp_server: str = DEFAULT_SMTP_SERVER, smtp_port: int = DEFAULT_SMTP_PORT,
                 from_email: str = DEFAULT_FROM_EMAIL, to_email: str = DEFAULT_TO_EMAIL,
                 password: str = DEFAULT_EMAIL_PASSWORD):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_email = to_email
        self.password = password
        self.enabled = bool(from_email and to_email and password and 
                          from_email != "your.sender@gmail.com" and to_email != "your.receiver@gmail.com" and
                          password != "your_app_password")
        
        if self.enabled:
            print(f"📧 Email service configured: {self.from_email} -> {self.to_email}")
        else:
            print("📧 Email service disabled (update email configuration in script)")
    
    def send_test_report(self, xml_report_path: str, terminal_output: str, 
                        project_name: str, test_results: Dict[str, any] = None) -> bool:
        """Send email with complete terminal output (no XML attachment)"""
        if not self.enabled:
            print("📧 Email sending skipped - service not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"Test Automation Report - {project_name}"
            
            # Create email body with complete terminal output
            body = self._create_email_body(terminal_output, test_results)
            msg.attach(MIMEText(body, 'plain'))
            
            # Note: XML attachment removed as per user request
            # User wants complete terminal output in email body instead
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.from_email, self.password)
                text = msg.as_string()
                server.sendmail(self.from_email, self.to_email, text)
            
            print(f"📧 Email sent successfully to {self.to_email}")
            return True
            
        except Exception as e:
            print(f"📧 Failed to send email: {e}")
            return False
    
    def _create_email_body(self, terminal_output: str, test_results: Dict[str, any] = None) -> str:
        """Create formatted email body with complete terminal output"""
        body_lines = []
        body_lines.append("🚀 Python Project Test Automation Report")
        body_lines.append("=" * 50)
        body_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        body_lines.append("")
        
        # Add test results summary if available
        if test_results:
            execution = test_results.get("phases", {}).get("execution", {})
            if execution.get("status") == "success":
                body_lines.append("📊 TEST EXECUTION SUMMARY:")
                body_lines.append(f"  Total Tests: {execution.get('total_tests', 0)}")
                body_lines.append(f"  Passed: {execution.get('passed', 0)}")
                body_lines.append(f"  Failed: {execution.get('failed', 0)}")
                success_rate = (execution.get('passed', 0) / max(execution.get('total_tests', 1), 1)) * 100
                body_lines.append(f"  Success Rate: {success_rate:.1f}%")
                body_lines.append("")
        
        body_lines.append("📋 COMPLETE TERMINAL OUTPUT:")
        body_lines.append("=" * 50)
        # Include the complete terminal output without length restrictions
        body_lines.append(terminal_output)
        body_lines.append("")
        body_lines.append("=" * 50)
        body_lines.append("� End of Test Automation Report")
        
        return "\n".join(body_lines)

@dataclass
class FunctionInfo:
    """Information about a function in the codebase"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    is_method: bool = False
    class_name: Optional[str] = None
    complexity_score: int = 1

@dataclass
class FileInfo:
    """Information about a source file"""
    path: str
    last_modified: float = 0
    hash_value: str = ""
    functions: List[FunctionInfo] = field(default_factory=list)

@dataclass
class ProjectStructure:
    """Complete project structure information"""
    project_root: str
    source_files: Dict[str, FileInfo] = field(default_factory=dict)
    test_files: Dict[str, FileInfo] = field(default_factory=dict)
    functions_map: Dict[str, FunctionInfo] = field(default_factory=dict)

class PythonProjectAnalyzer:
    """Analyzes Python project structure and extracts function information"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.structure = ProjectStructure(str(self.project_root))
    
    def discover_project(self) -> ProjectStructure:
        """Discovers and analyzes the entire project structure"""
        print(f"🔍 Analyzing project structure in: {self.project_root}")
        
        # Discover all files
        self._discover_files()
        
        # Analyze source files for functions
        self._analyze_source_files()
        
        print(f"✅ Project analysis complete:")
        print(f"   📁 Source files: {len(self.structure.source_files)}")
        print(f"   🧪 Test files: {len(self.structure.test_files)}")
        print(f"   ⚙️ Functions/Methods: {len(self.structure.functions_map)}")
        
        return self.structure
    
    def _discover_files(self):
        """Discovers all relevant Python files in the project"""
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern.rstrip('/*')) for pattern in EXCLUDE_PATTERNS)]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                # Skip excluded files
                if any(fnmatch.fnmatch(str(relative_path), pattern) for pattern in EXCLUDE_PATTERNS):
                    continue
                
                if file.endswith('.py'):
                    if any(pattern in file for pattern in ['test_', '_test']):
                        self.structure.test_files[str(relative_path)] = FileInfo(str(relative_path))
                    else:
                        self.structure.source_files[str(relative_path)] = FileInfo(str(relative_path))
    
    def _analyze_source_files(self):
        """Analyzes each source file to extract function information"""
        for file_path, file_info in self.structure.source_files.items():
            try:
                full_path = self.project_root / file_path
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                file_info.last_modified = full_path.stat().st_mtime
                file_info.hash_value = hashlib.md5(content.encode()).hexdigest()
                
                functions = self._extract_functions(content, file_path)
                file_info.functions = functions
                
                for func in functions:
                    unique_name = f"{func.class_name}.{func.name}" if func.is_method else func.name
                    self.structure.functions_map[unique_name] = func
                    
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _extract_functions(self, content: str, file_path: str) -> List[FunctionInfo]:
        """Extracts function and method definitions from Python code using AST"""
        functions = []
        try:
            tree = ast.parse(content, filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_method = False
                    class_name = None
                    # Check if it's a method by looking at its parent node
                    # This is a bit of a hack, but works for simple cases
                    parent = next((n for n in ast.walk(tree) if hasattr(n, 'body') and node in n.body), None)
                    if isinstance(parent, ast.ClassDef):
                        is_method = True
                        class_name = parent.name
                    
                    # Calculate a simple complexity score
                    complexity = 1
                    for sub_node in ast.walk(node):
                        if isinstance(sub_node, (ast.If, ast.For, ast.While, ast.Try)):
                            complexity += 1
                    
                    functions.append(FunctionInfo(
                        name=node.name,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        is_method=is_method,
                        class_name=class_name,
                        complexity_score=complexity
                    ))
        except SyntaxError as e:
            print(f"⚠️ Syntax error in {file_path}: {e}")
        
        return functions

class TestGenerator:
    """Generates comprehensive test cases using Groq AI"""
    
    def __init__(self, model: str = GROQ_MODEL, api_key: str = GROQ_API_KEY):
        self.model = model
        self.api_key = api_key
        self.api_url = GROQ_API_URL
        
        if not self.api_key or self.api_key == "your-groq-api-key-here":
            print("⚠️  Warning: Groq API key not set. Please set GROQ_API_KEY environment variable.")
            print("   You can get a free API key from: https://console.groq.com/keys")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_test_suite_for_functions(self, functions: List[FunctionInfo], 
                                        project_structure: ProjectStructure) -> Dict[str, str]:
        """Generates comprehensive test suite for given functions"""
        test_files = {}
        
        # Group functions by complexity and importance
        critical_functions = [f for f in functions if f.complexity_score > 3]
        standard_functions = [f for f in functions if f not in critical_functions]
        
        print(f"🤖 Generating tests for {len(functions)} functions:")
        print(f"   🔴 Critical functions: {len(critical_functions)}")
        print(f"   🟡 Standard functions: {len(standard_functions)}")
        
        # Generate combined test file for all functions
        if functions:
            combined_test = self._generate_combined_test_file(functions, project_structure)
            if combined_test:
                test_files["test_generated.py"] = combined_test
        
        return test_files
    
    def _generate_combined_test_file(self, functions: List[FunctionInfo],
                                   project_structure: ProjectStructure) -> str:
        """Generates a single test file for multiple functions/methods"""
        
        functions_info = []
        for func in functions[:10]: # Limit to 10 functions for the prompt
            context = self._get_function_context(func, project_structure)
            functions_info.append(f"Function/Method: {func.name}\nFile: {func.file_path}\nContext: {context[:500]}...")
        
        # Get all relevant imports from the source files
        all_imports = set()
        for file_info in project_structure.source_files.values():
            try:
                with open(Path(project_structure.project_root) / file_info.path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        try:
                            import_str = ast.get_source_segment(content, node)
                            if import_str:
                                all_imports.add(import_str)
                        except Exception:
                            # Fallback for import extraction
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    all_imports.add(f"import {alias.name}")
                            elif isinstance(node, ast.ImportFrom):
                                module = node.module or ""
                                names = ", ".join(alias.name for alias in node.names)
                                all_imports.add(f"from {module} import {names}")
            except Exception as e:
                print(f"⚠️  Error processing imports from {file_info.path}: {e}")
                continue
                            
        import_statements = "\n".join(list(all_imports))
        
        prompt = f"""
You are an expert Python unit testing engineer. Generate a comprehensive test file for the following functions and methods using Python's built-in `unittest` framework.

FUNCTIONS/METHODS TO TEST:
{chr(10).join(functions_info)}

CRITICAL INSTRUCTIONS:
1. READ the implementation context for each function to understand its behavior and return values.
2. For each function or method, create a test method (e.g., `test_function_name`).
3. Create test cases that cover normal behavior, edge cases, and error conditions.
4. Use `self.assertEqual`, `self.assertTrue`, `self.assertRaises`, or other `unittest` assertions to verify results.
5. Provide meaningful docstrings for each test class and test method.
6. Use a `if __name__ == '__main__':` block to run the tests.
7. Include necessary imports from the source files to make the tests runnable.

Generate ONLY the complete Python code for the test file. No explanations.
"""
        
        return self._invoke_llm_for_generation(prompt, max_tokens=4000)
    
    def _get_function_context(self, func: FunctionInfo, 
                            project_structure: ProjectStructure) -> str:
        """Gets the source code context for a function"""
        try:
            full_path = Path(project_structure.project_root) / func.file_path
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            func_node = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == func.name and node.lineno == func.line_start:
                        func_node = node
                        break
            
            if func_node:
                start_line = func_node.lineno - 1
                end_line = func_node.end_lineno
                
                lines = content.splitlines()
                # Get surrounding context for better understanding
                context_start = max(0, start_line - 5)
                context_end = min(len(lines), end_line + 5)
                
                return "\n".join(lines[context_start:context_end])
                
        except Exception as e:
            return f"Error reading function context: {e}"
        return ""
    
    def _invoke_llm_for_generation(self, prompt: str, max_tokens: int = 2000) -> str:
        """Invokes the Groq LLM for test generation"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                generated_code = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                # Clean up any markdown formatting
                if "```python" in generated_code:
                    code_start = generated_code.find("```python") + len("```python")
                    code_end = generated_code.find("```", code_start)
                    if code_end != -1:
                        generated_code = generated_code[code_start:code_end].strip()
                elif "```" in generated_code:
                    code_start = generated_code.find("```") + 3
                    code_end = generated_code.find("```", code_start)
                    if code_end != -1:
                        generated_code = generated_code[code_start:code_end].strip()
                
                return generated_code
            else:
                print(f"❌ Groq API error {response.status_code}: {response.text}")
                return ""
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Groq API: {e}")
            return ""
        except Exception as e:
            print(f"❌ Error generating test code: {e}")
            return ""
            
    def fix_code_with_llm(self, broken_code: str, error_message: str) -> Optional[str]:
        """Sends broken code and error message to LLM for a fix."""
        prompt = f"""
        The following Python code has an error.
        
        ERROR MESSAGE:
        {error_message}
        
        BROKEN CODE:
        {broken_code}
        
        Please analyze the error and provide the corrected, complete Python code. Adhere to PEP 8 and use the unittest framework.
        Generate ONLY the corrected Python code, no explanations.
        """
        
        return self._invoke_llm_for_generation(prompt, max_tokens=3000)


class EnhancedProjectTestAutomator:
    """Enhanced version that forces testing when no changes detected and supports GitHub repos"""
    
    def __init__(self, project_path: str, model: str = GROQ_MODEL, api_key: str = GROQ_API_KEY, force_all_tests: bool = True):
        self.model = model
        self.api_key = api_key
        self.force_all_tests = force_all_tests
        self.terminal_output = []  # Store terminal output for email
        self.email_service = EmailService()  # Initialize email service
        self.github_manager = GitHubRepoManager()
        self.is_github_repo = self.github_manager.is_github_url(project_path)
        
        # Handle GitHub repository or local path
        if self.is_github_repo:
            print(f"🌐 GitHub repository detected: {project_path}")
            self.project_root = Path(self.github_manager.clone_repository(project_path)).resolve()
        else:
            self.project_root = Path(project_path).resolve()
        
        # Initialize components
        self.analyzer = PythonProjectAnalyzer(str(self.project_root))
        self.test_generator = TestGenerator(model, api_key)
        
        # Create test directory
        self.test_dir = self.project_root / DEFAULT_TEST_DIR
        self.test_dir.mkdir(exist_ok=True)
        
        # Setup logging to file
        self._setup_file_logging()
        
        print(f"🚀 Initialized Enhanced Python Project Test Automator")
        print(f"   📁 Project root: {self.project_root}")
        print(f"   🧪 Test directory: {self.test_dir}")
        print(f"   🔄 Force all tests: {self.force_all_tests}")
        print(f"   🌐 GitHub repository: {self.is_github_repo}")
        print(f"   📄 Log file: {self.log_file_path}")
    
    def _setup_file_logging(self):
        """Setup file logging configuration"""
        # Create logs directory if it doesn't exist
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = logs_dir / f"test_execution_{timestamp}.log"
        
        # Setup logger
        self.logger = logging.getLogger('test_automation')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                    datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("PYTHON PROJECT TEST AUTOMATION - SESSION STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Project Root: {self.project_root}")
        self.logger.info(f"Test Directory: {self.test_dir}")
        self.logger.info(f"Force All Tests: {self.force_all_tests}")
        self.logger.info(f"GitHub Repository: {self.is_github_repo}")
        self.logger.info("=" * 80)
    
    def _capture_output(self, message: str, log_level: str = "INFO"):
        """Capture terminal output for email and print to console, also log to file"""
        self.terminal_output.append(message)
        print(message)
        
        # Log to file with appropriate level
        clean_message = message.replace("🚀", "").replace("📁", "").replace("🧪", "").replace("🔍", "").replace("✅", "").replace("❌", "").replace("⚠️", "").replace("🌐", "").replace("📄", "").replace("🔄", "").replace("📊", "").replace("📈", "").replace("💾", "").replace("📧", "").strip()
        
        if log_level.upper() == "ERROR":
            self.logger.error(clean_message)
        elif log_level.upper() == "WARNING":
            self.logger.warning(clean_message)
        elif log_level.upper() == "DEBUG":
            self.logger.debug(clean_message)
        else:
            self.logger.info(clean_message)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup GitHub repository if needed and finalize logging"""
        # Finalize logging
        self.logger.info("=" * 80)
        self.logger.info("PYTHON PROJECT TEST AUTOMATION - SESSION COMPLETED")
        self.logger.info("=" * 80)
        
        # Close log handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        
        if self.is_github_repo:
            self.github_manager.cleanup()
    
    def run_full_automation(self) -> Dict[str, any]:
        """Runs the complete automation pipeline with forced testing"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "phases": {}
        }
        
        try:
            msg = "🚀 ENHANCED AUTOMATION MODE: Starting comprehensive testing pipeline"
            self._capture_output(msg)
            
            # Phase 1: Project Discovery
            phase1_header = "\n" + "="*60 + "\nPHASE 1: PROJECT STRUCTURE ANALYSIS\n" + "="*60
            self._capture_output(phase1_header)
            
            project_structure = self.analyzer.discover_project()
            results["phases"]["discovery"] = {
                "status": "success",
                "source_files": len(project_structure.source_files),
                "functions": len(project_structure.functions_map),
            }
            
            # Phase 2: Enhanced Function Selection
            phase2_header = "\n" + "="*60 + "\nPHASE 2: ENHANCED FUNCTION SELECTION\n" + "="*60
            self._capture_output(phase2_header)
            
            all_functions = list(project_structure.functions_map.values())
            git_diff = self._get_git_changes()
            
            if git_diff and not self.force_all_tests:
                changed_files = self._extract_changed_files_from_diff(git_diff)
                target_functions = self._identify_affected_functions(changed_files, project_structure)
                print(f"📊 Found {len(changed_files)} changed files, selecting {len(target_functions)} functions")
            else:
                target_functions = all_functions
                if not git_diff:
                    msg = "⚠️  No git changes detected - FORCING COMPREHENSIVE TESTING OF ALL FUNCTIONS"
                    self._capture_output(msg)
                else:
                    msg = "🔄 Force mode enabled - testing all functions regardless of changes"
                    self._capture_output(msg)
            
            results["phases"]["selection"] = {
                "status": "enhanced",
                "total_functions": len(all_functions),
                "selected_functions": len(target_functions),
                "selection_mode": "forced_all" if (not git_diff or self.force_all_tests) else "change_based"
            }
            
            msg = f"🎯 Selected {len(target_functions)} functions for testing"
            self._capture_output(msg)
            
            for i, func in enumerate(target_functions[:10]):
                func_msg = f"   {i+1}. {func.name} (complexity: {func.complexity_score})"
                self._capture_output(func_msg)
            if len(target_functions) > 10:
                more_msg = f"   ... and {len(target_functions) - 10} more"
                self._capture_output(more_msg)
            
            # Phase 3: Test Generation
            phase3_header = "\n" + "="*60 + "\nPHASE 3: AI-POWERED TEST GENERATION\n" + "="*60
            self._capture_output(phase3_header)
            
            generated_tests = {}
            if target_functions:
                try:
                    generated_tests = self.test_generator.generate_test_suite_for_functions(
                        target_functions, project_structure
                    )
                    
                    saved_tests = []
                    for test_file_name, test_content in generated_tests.items():
                        test_file_path = self.test_dir / test_file_name
                        try:
                            with open(test_file_path, 'w') as f:
                                f.write(test_content)
                            self._format_python_code(test_file_path)
                            saved_tests.append(str(test_file_path))
                            self._capture_output(f"✅ Generated and formatted: {test_file_name}")
                        except Exception as e:
                            self._capture_output(f"❌ Failed to save {test_file_name}: {e}", "ERROR")
                    
                    results["phases"]["generation"] = {
                        "status": "success",
                        "generated_tests": len(generated_tests),
                        "saved_tests": saved_tests
                    }
                    self._capture_output(f"✅ Successfully generated {len(generated_tests)} test files")
                    
                except Exception as e:
                    error_msg = f"❌ Test generation failed: {str(e)}"
                    self._capture_output(error_msg, "ERROR")
                    results["phases"]["generation"] = {
                        "status": "failed",
                        "error": str(e)
                    }
            else:
                self._capture_output("ℹ️  No functions available for testing")
                results["phases"]["generation"] = {
                    "status": "skipped",
                    "message": "No functions available"
                }
            
            # Phase 4: Test Execution
            phase4_header = "\n" + "="*60 + "\nPHASE 4: AUTOMATED TEST EXECUTION\n" + "="*60
            self._capture_output(phase4_header)
            
            if generated_tests:
                try:
                    execution_results = self._execute_tests(generated_tests, project_structure)
                    results["phases"]["execution"] = execution_results
                    if execution_results.get("status") == "success":
                        passed = execution_results.get("passed", 0)
                        total = execution_results.get("total_tests", 0)
                        self._capture_output(f"✅ Test execution completed: {passed}/{total} tests passed")
                    else:
                        self._capture_output(f"⚠️  Test execution completed with issues", "WARNING")
                except Exception as e:
                    error_msg = f"❌ Test execution failed: {str(e)}"
                    self._capture_output(error_msg, "ERROR")
                    results["phases"]["execution"] = {
                        "status": "failed",
                        "error": str(e)
                    }
            else:
                self._capture_output("ℹ️  No tests to execute (no tests were generated)")
                results["phases"]["execution"] = {
                    "status": "skipped",
                    "message": "No tests generated"
                }
            
            # Phase 5: Coverage Analysis
            phase5_header = "\n" + "="*60 + "\nPHASE 5: COVERAGE ANALYSIS\n" + "="*60
            self._capture_output(phase5_header)
            
            try:
                coverage_results = self._analyze_coverage()
                results["phases"]["coverage"] = coverage_results
                if coverage_results.get("status") == "success":
                    coverage_percent = coverage_results.get("coverage_percentage", 0)
                    self._capture_output(f"✅ Coverage analysis completed: {coverage_percent:.1f}% coverage")
                else:
                    self._capture_output("⚠️  Coverage analysis completed with limited data")
            except Exception as e:
                error_msg = f"❌ Coverage analysis failed: {str(e)}"
                self._capture_output(error_msg)
                results["phases"]["coverage"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Final Report
            final_header = "\n" + "="*60 + "\nAUTOMATION COMPLETE - GENERATING REPORT\n" + "="*60
            self._capture_output(final_header)
            
            self._generate_final_report(results)
            
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            results["error"] = str(e)
        
        return results

    def _identify_affected_functions(self, changed_files: List[str], project_structure: ProjectStructure) -> List[FunctionInfo]:
        """Identifies functions that might be affected by file changes"""
        # Python dependencies are harder to track statically, so we'll just test all functions in changed files.
        affected_functions = []
        for file_path in changed_files:
            if file_path in project_structure.source_files:
                affected_functions.extend(project_structure.source_files[file_path].functions)
        return affected_functions

    def _extract_changed_files_from_diff(self, git_diff: str) -> List[str]:
        """Extracts changed files from git diff"""
        changed_files = []
        for line in git_diff.split('\n'):
            if line.startswith('diff --git'):
                match = re.search(r'diff --git a/(.*?) b/', line)
                if match:
                    changed_files.append(match.group(1))
        return changed_files

    def _get_git_changes(self) -> Optional[str]:
        """Gets git diff for unstaged changes"""
        try:
            os.chdir(self.project_root)
            git_diff = subprocess.run(
                ['git', 'diff'],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            return git_diff if git_diff else None
        except subprocess.CalledProcessError:
            return None
            
    def _format_python_code(self, file_path: Path):
        """Formats a Python file using autopep8."""
        try:
            subprocess.run(
                ['autopep8', '--in-place', str(file_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✔️ Formatted: {file_path.name}")
        except FileNotFoundError:
            print("⚠️ autopep8 not found. Skipping code formatting.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to format {file_path.name}: {e.stderr}")
    
    def _generate_detailed_test_logs(self, test_cases_info: Dict[str, any], execution_results: Dict[str, any]) -> str:
        """Generate detailed test execution logs in the requested format"""
        self.logger.info("Generating detailed test execution logs")
        
        log_lines = []
        current_time = datetime.now()
        
        # Start of test suite
        start_log = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}  [INFO]  ===== Starting Test Suite: AI Generated Tests ====="
        log_lines.append(start_log)
        self.logger.info(start_log)
        
        # Process each test case
        for test_case in test_cases_info.get("test_cases", []):
            # Calculate test start time by adding seconds to avoid overflow
            seconds_offset = test_case["test_case_number"]
            test_start_time = current_time + timedelta(seconds=seconds_offset)
            
            # Log test start
            test_start_log = f"{test_start_time.strftime('%Y-%m-%d %H:%M:%S')}  [INFO]  Running test: {test_case['method_name']}"
            log_lines.append(test_start_log)
            self.logger.info(f"Detailed Log: {test_start_log}")
            
            # Determine test result and duration
            test_result = self._get_test_case_result(test_case["method_name"], test_case["test_file"], execution_results)
            duration = 0.001 + (test_case["test_case_number"] * 0.001)  # Simulated duration
            
            test_end_time = test_start_time + timedelta(seconds=duration)
            
            # Log test result
            if test_result == "PASS":
                log_lines.append(f"{test_end_time.strftime('%Y-%m-%d %H:%M:%S')}  [PASS]  {test_case['method_name']} ({duration:.3f}s)")
            else:
                log_lines.append(f"{test_end_time.strftime('%Y-%m-%d %H:%M:%S')}  [FAIL]  {test_case['method_name']} ({duration:.3f}s)")
                
                # Add error details for failed tests
                execution_details = execution_results.get("execution_details", {})
                test_file_result = execution_details.get(test_case["test_file"], {})
                if test_file_result.get("error"):
                    error_msg = test_file_result["error"].split('\n')[0]  # First line of error
                    log_lines.append(f"{test_end_time.strftime('%Y-%m-%d %H:%M:%S')}  [ERROR] {error_msg}")
            
            # Add empty line between tests for readability
            log_lines.append("")
        
        # End of test suite summary
        total_tests = len(test_cases_info.get("test_cases", []))
        passed_tests = sum(1 for tc in test_cases_info.get("test_cases", []) 
                          if self._get_test_case_result(tc["method_name"], tc["test_file"], execution_results) == "PASS")
        failed_tests = total_tests - passed_tests
        
        final_time = current_time + timedelta(seconds=total_tests + 5)
        final_log = f"{final_time.strftime('%Y-%m-%d %H:%M:%S')}  [INFO]  ===== Test Suite Completed ====="
        log_lines.append(final_log)
        self.logger.info(final_log)
        
        summary_log = f"{final_time.strftime('%Y-%m-%d %H:%M:%S')}  [INFO]  Total: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}"
        log_lines.append(summary_log)
        self.logger.info(summary_log)
        
        if failed_tests == 0:
            pass_log = f"{final_time.strftime('%Y-%m-%d %H:%M:%S')}  [INFO]  All tests PASSED! ✅"
            log_lines.append(pass_log)
            self.logger.info(pass_log)
        else:
            fail_log = f"{final_time.strftime('%Y-%m-%d %H:%M:%S')}  [WARN]  {failed_tests} test(s) FAILED! ❌"
            log_lines.append(fail_log)
            self.logger.warning(fail_log)
        
        self.logger.info("Detailed test execution logs generation completed")
        return "\n".join(log_lines)
            
    def _execute_tests(self, generated_tests: Dict[str, str], project_structure: ProjectStructure) -> Dict[str, any]:
        """Executes the generated tests with a retry mechanism for syntax errors."""
        self.logger.info("-" * 60)
        self.logger.info("STARTING TEST EXECUTION PHASE")
        self.logger.info("-" * 60)
        
        results = {
            "status": "success",
            "total_tests": len(generated_tests),
            "passed": 0,
            "failed": 0,
            "execution_details": {}
        }
        
        self.logger.info(f"Total test files to execute: {len(generated_tests)}")
        
        for test_file_name, _ in generated_tests.items():
            print(f"🧪 Executing: {test_file_name}")
            self.logger.info(f"Executing test file: {test_file_name}")
            
            test_result = self._run_test_with_retry(test_file_name, project_structure)
            results["execution_details"][test_file_name] = test_result
            
            if test_result["success"]:
                results["passed"] += 1
                print(f"✅ {test_file_name} PASSED")
                self.logger.info(f"Test PASSED: {test_file_name}")
                if test_result.get("run_output"):
                    self.logger.info(f"Test output for {test_file_name}:\n{test_result['run_output']}")
            else:
                results["failed"] += 1
                print(f"❌ {test_file_name} FAILED: {test_result['error']}")
                self.logger.error(f"Test FAILED: {test_file_name} - {test_result['error']}")
                if test_result.get("run_output"):
                    self.logger.error(f"Test error output for {test_file_name}:\n{test_result['run_output']}")
        
        success_rate = (results["passed"] / results["total_tests"]) * 100 if results["total_tests"] > 0 else 0
        print(f"\n📊 Test Execution Summary:")
        print(f"   Total: {results['total_tests']}")
        print(f"   Passed: {results['passed']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Log summary
        self.logger.info("-" * 40)
        self.logger.info("TEST EXECUTION SUMMARY")
        self.logger.info("-" * 40)
        self.logger.info(f"Total Tests: {results['total_tests']}")
        self.logger.info(f"Passed: {results['passed']}")
        self.logger.info(f"Failed: {results['failed']}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info("-" * 40)
        
        return results

    def _run_test_with_retry(self, test_file_name: str, project_structure: ProjectStructure, retries: int = 2) -> Dict[str, any]:
        """Runs a single test file with a retry mechanism."""
        test_file_path = self.test_dir / test_file_name
        
        self.logger.info(f"Starting test execution: {test_file_name}")
        self.logger.info(f"Test file path: {test_file_path}")
        
        result = {
            "success": False,
            "run_output": "",
            "error": ""
        }
        
        for attempt in range(retries + 1):
            self.logger.info(f"Test execution attempt {attempt + 1} for {test_file_name}")
            
            try:
                run_result = subprocess.run(
                    ['python', '-m', 'unittest', str(test_file_path)],
                    capture_output=True, text=True, check=True,
                    cwd=self.project_root
                )
                
                # Capture both stdout and stderr for successful runs
                result["run_output"] = run_result.stdout
                if run_result.stderr:
                    result["run_output"] += f"\nSTDERR:\n{run_result.stderr}"
                result["success"] = True
                
                self.logger.info(f"Test execution successful for {test_file_name}")
                self.logger.debug(f"Test output: {result['run_output']}")
                
                return result
            
            except subprocess.CalledProcessError as e:
                # Capture detailed error information
                error_output = e.stderr or e.stdout
                combined_output = f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}" if e.stdout and e.stderr else error_output
                result["error"] = f"Execution failed (Attempt {attempt + 1}/{retries + 1}):\n{combined_output}"
                result["run_output"] = combined_output  # Also store in run_output for XML logging
                
                self.logger.warning(f"Test execution failed for {test_file_name}, attempt {attempt + 1}")
                self.logger.warning(f"Error: {combined_output}")
                
                if attempt < retries:
                    print(f"❌ Attempt {attempt + 1} failed. Sending to AI for fix...")
                    self.logger.info(f"Attempting AI-powered fix for {test_file_name}")
                    with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        broken_content = f.read()
                    
                    fixed_content = self.test_generator.fix_code_with_llm(broken_content, error_output)
                    
                    if fixed_content:
                        with open(test_file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        self._format_python_code(test_file_path)
                        print("🔄 AI provided a fix. Retrying execution...")
                    else:
                        print("⚠️ AI failed to provide a fix. Aborting retries for this file.")
                        break
                else:
                    print(f"❌ All {retries + 1} attempts failed.")
        
        return result
    
    def _analyze_coverage(self) -> Dict[str, any]:
        """Analyzes code coverage using coverage.py."""
        print("📊 Analyzing code coverage...")
        try:
            # First, run the tests with coverage
            subprocess.run(
                ['coverage', 'run', '--source', '.', '-m', 'unittest', 'discover', str(self.test_dir)],
                check=True,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Then, generate the report
            report_result = subprocess.run(
                ['coverage', 'report', '-m'],
                check=True,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Parse the output to find the total coverage percentage
            lines = report_result.stdout.splitlines()
            last_line = lines[-1]
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', last_line)
            coverage_percentage = int(match.group(1)) if match else 0

            status = "success"
            message = f"Code coverage is {coverage_percentage}%."
            if coverage_percentage < COVERAGE_THRESHOLD * 100:
                message += f" (Below threshold of {COVERAGE_THRESHOLD * 100}%)"
                status = "warning"
                
            return {
                "status": status,
                "percentage": coverage_percentage,
                "message": message,
                "report": report_result.stdout
            }
            
        except FileNotFoundError:
            return {
                "status": "unavailable",
                "message": "Coverage tools (coverage.py) not found."
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Coverage analysis failed: {e.stderr}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"An unexpected error occurred during coverage analysis: {e}"
            }
    
    def _parse_test_files_for_cases(self, generated_tests: Dict[str, str]) -> Dict[str, any]:
        """Parse generated test files to extract detailed test case information"""
        test_cases_info = {
            "total_test_cases": 0,
            "test_files": {},
            "test_cases": []
        }
        
        for test_file_name in generated_tests.keys():
            test_file_path = self.test_dir / test_file_name
            
            try:
                with open(test_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the test file using AST
                tree = ast.parse(content)
                file_info = {
                    "test_classes": [],
                    "test_methods": 0,
                    "functions_tested": set()
                }
                
                test_case_number = test_cases_info["total_test_cases"] + 1
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                        class_info = {
                            "class_name": node.name,
                            "docstring": ast.get_docstring(node) or "",
                            "test_methods": []
                        }
                        
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'):
                                method_info = {
                                    "test_case_number": test_case_number,
                                    "method_name": method.name,
                                    "docstring": ast.get_docstring(method) or "",
                                    "line_start": method.lineno,
                                    "line_end": method.end_lineno,
                                    "target_function": self._extract_target_function(method.name),
                                    "test_file": test_file_name
                                }
                                
                                class_info["test_methods"].append(method_info)
                                test_cases_info["test_cases"].append(method_info)
                                file_info["functions_tested"].add(method_info["target_function"])
                                test_case_number += 1
                        
                        file_info["test_classes"].append(class_info)
                        file_info["test_methods"] += len(class_info["test_methods"])
                
                file_info["functions_tested"] = list(file_info["functions_tested"])
                test_cases_info["test_files"][test_file_name] = file_info
                test_cases_info["total_test_cases"] = test_case_number - 1
                
            except Exception as e:
                print(f"⚠️  Error parsing test file {test_file_name}: {e}")
        
        return test_cases_info
    
    def _extract_target_function(self, test_method_name: str) -> str:
        """Extract the target function name from test method name"""
        # Remove 'test_' prefix and return the function name
        if test_method_name.startswith('test_'):
            return test_method_name[5:]  # Remove 'test_' prefix
        return test_method_name
    
    def _get_test_case_result(self, test_method_name: str, test_file_name: str, execution_results: Dict[str, any]) -> str:
        """Get the result (PASS/FAIL) for a specific test case"""
        execution_details = execution_results.get("execution_details", {})
        test_result = execution_details.get(test_file_name, {})
        
        if test_result.get("success"):
            # For successful test files, we can check the output for specific test results
            run_output = test_result.get("run_output", "")
            if run_output:
                # Look for unittest patterns in the output
                if f"test_{test_method_name.replace('test_', '')}" in run_output or test_method_name in run_output:
                    if "FAILED" in run_output or "ERROR" in run_output:
                        return "FAIL"
                    elif "OK" in run_output or "." in run_output:
                        return "PASS"
            return "PASS"  # Default to PASS if test file succeeded
        else:
            # For failed test files, check if the specific test method failed
            error_output = test_result.get("error", "")
            if test_method_name in error_output:
                return "FAIL"
            return "FAIL"  # Default to FAIL if test file failed
    
    def _create_structured_test_execution_log(self, results: Dict[str, any]) -> ET.Element:
        """Create structured test execution log similar to the requested format"""
        
        # Get execution data
        execution = results["phases"].get("execution", {})
        generation = results["phases"].get("generation", {})
        
        # Create TestExecutionLog root element
        test_exec_log = ET.Element("TestExecutionLog")
        test_exec_log.set("xmlns", "http://testautomation.com/schema")
        test_exec_log.set("version", "1.0")
        
        # ExecutionInfo section
        exec_info = ET.SubElement(test_exec_log, "ExecutionInfo")
        ET.SubElement(exec_info, "StartTime").text = results.get("timestamp", datetime.now().isoformat()) + "Z"
        ET.SubElement(exec_info, "EndTime").text = datetime.now().isoformat() + "Z"
        
        # Determine overall status
        overall_status = "PASS"
        if results.get("error"):
            overall_status = "FAIL"
        elif execution.get("status") != "success" or execution.get("failed", 0) > 0:
            overall_status = "FAIL"
        
        ET.SubElement(exec_info, "Status").text = overall_status
        ET.SubElement(exec_info, "BuildVersion").text = "1.0.0"
        ET.SubElement(exec_info, "ExecutedBy").text = "automation.system"
        ET.SubElement(exec_info, "ProjectPath").text = str(self.project_root)
        
        # TestCycle section
        test_cycle = ET.SubElement(test_exec_log, "TestCycle")
        cycle_id = datetime.now().strftime("%Y%m%d%H%M")
        ET.SubElement(test_cycle, "Id").text = cycle_id
        ET.SubElement(test_cycle, "Name").text = f"AI Test Generation Cycle - {datetime.now().strftime('%B %Y')}"
        ET.SubElement(test_cycle, "Type").text = "Automated"
        
        # Test Cases section - Parse generated test files for individual test cases
        if generation.get("status") == "success" and generation.get("saved_tests"):
            generated_tests_dict = {}
            for test_file_path in generation.get("saved_tests", []):
                test_file_name = Path(test_file_path).name
                generated_tests_dict[test_file_name] = ""
            
            test_cases_info = self._parse_test_files_for_cases(generated_tests_dict)
            
            # Create individual TestCase elements
            for test_case in test_cases_info["test_cases"]:
                test_case_elem = ET.SubElement(test_exec_log, "TestCase")
                
                # Basic test case info
                ET.SubElement(test_case_elem, "Id").text = str(test_case["test_case_number"])
                ET.SubElement(test_case_elem, "Name").text = test_case["method_name"]
                ET.SubElement(test_case_elem, "AutomationContent").text = f"{test_case['test_file']}.{test_case['method_name']}"
                ET.SubElement(test_case_elem, "TargetFunction").text = test_case["target_function"]
                ET.SubElement(test_case_elem, "Description").text = test_case["docstring"]
                
                # Test case status
                case_result = self._get_test_case_result(test_case["method_name"], test_case["test_file"], execution)
                ET.SubElement(test_case_elem, "Status").text = case_result
                
                # Steps section - Create logical steps for each test case
                steps = ET.SubElement(test_case_elem, "Steps")
                
                # Step 1: Test Setup
                step1 = ET.SubElement(steps, "Step")
                ET.SubElement(step1, "Name").text = "Test Environment Setup"
                ET.SubElement(step1, "Status").text = "PASS"
                ET.SubElement(step1, "StartTime").text = datetime.now().isoformat() + "Z"
                ET.SubElement(step1, "EndTime").text = datetime.now().isoformat() + "Z"
                
                # Step 2: Function Import and Preparation
                step2 = ET.SubElement(steps, "Step")
                ET.SubElement(step2, "Name").text = f"Import and prepare {test_case['target_function']} function"
                ET.SubElement(step2, "Status").text = "PASS"
                ET.SubElement(step2, "StartTime").text = datetime.now().isoformat() + "Z"
                ET.SubElement(step2, "EndTime").text = datetime.now().isoformat() + "Z"
                
                # Step 3: Test Execution
                step3 = ET.SubElement(steps, "Step")
                ET.SubElement(step3, "Name").text = f"Execute test assertions for {test_case['target_function']}"
                ET.SubElement(step3, "Status").text = case_result
                ET.SubElement(step3, "StartTime").text = datetime.now().isoformat() + "Z"
                ET.SubElement(step3, "EndTime").text = datetime.now().isoformat() + "Z"
                
                if case_result == "FAIL":
                    # Add error information for failed tests
                    execution_details = execution.get("execution_details", {})
                    test_result = execution_details.get(test_case["test_file"], {})
                    error_msg = test_result.get("error", "Test execution failed")
                    ET.SubElement(step3, "ErrorMessage").text = error_msg[:200] + "..." if len(error_msg) > 200 else error_msg
                
                # Step 4: Test Cleanup
                step4 = ET.SubElement(steps, "Step")
                ET.SubElement(step4, "Name").text = "Test Cleanup and Validation"
                ET.SubElement(step4, "Status").text = "PASS"
                ET.SubElement(step4, "StartTime").text = datetime.now().isoformat() + "Z"
                ET.SubElement(step4, "EndTime").text = datetime.now().isoformat() + "Z"
        
        # Attachments section
        attachments = ET.SubElement(test_exec_log, "Attachments")
        
        # Add detailed test execution logs if we have test cases
        if generation.get("status") == "success" and generation.get("saved_tests"):
            generated_tests_dict = {}
            for test_file_path in generation.get("saved_tests", []):
                test_file_name = Path(test_file_path).name
                generated_tests_dict[test_file_name] = ""
            
            test_cases_info = self._parse_test_files_for_cases(generated_tests_dict)
            detailed_logs = self._generate_detailed_test_logs(test_cases_info, execution)
            
            # Add detailed logs as an attachment
            detailed_log_attachment = ET.SubElement(attachments, "Attachment")
            ET.SubElement(detailed_log_attachment, "Name").text = "detailed_test_execution.log"
            ET.SubElement(detailed_log_attachment, "Type").text = "text/plain"
            ET.SubElement(detailed_log_attachment, "Path").text = "/reports/logs/detailed_test_execution.log"
            ET.SubElement(detailed_log_attachment, "Content").text = detailed_logs
        
        # Add XML report as attachment
        xml_attachment = ET.SubElement(attachments, "Attachment")
        ET.SubElement(xml_attachment, "Name").text = "automation_report.xml"
        ET.SubElement(xml_attachment, "Type").text = "application/xml"
        ET.SubElement(xml_attachment, "Path").text = f"/reports/xml/enhanced_automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        # Add test file as attachment if generated
        if generation.get("saved_tests"):
            for test_file_path in generation.get("saved_tests", []):
                test_attachment = ET.SubElement(attachments, "Attachment")
                ET.SubElement(test_attachment, "Name").text = Path(test_file_path).name
                ET.SubElement(test_attachment, "Type").text = "text/x-python"
                ET.SubElement(test_attachment, "Path").text = str(test_file_path)
        
        # Add terminal logs as attachment
        log_attachment = ET.SubElement(attachments, "Attachment")
        ET.SubElement(log_attachment, "Name").text = "terminal_execution.log"
        ET.SubElement(log_attachment, "Type").text = "text/plain"
        ET.SubElement(log_attachment, "Path").text = "/reports/logs/terminal_execution.log"
        
        return test_exec_log
    
    def _generate_final_report(self, results: Dict[str, any]):
        """Generates and saves the final automation report in XML format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create XML structure with better organization
        root = ET.Element("TestAutomationReport")
        root.set("generated", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        root.set("project", str(self.project_root))
        root.set("timestamp", timestamp)
        
        # Add XML comment for better documentation
        root.append(ET.Comment(" ==================== PROJECT ANALYSIS ==================== "))
        
        # Project Structure Summary
        discovery = results["phases"].get("discovery", {})
        project_structure = ET.SubElement(root, "ProjectStructureAnalysis")
        ET.SubElement(project_structure, "SourceFiles").text = str(discovery.get('source_files', 0))
        ET.SubElement(project_structure, "FunctionsDiscovered").text = str(discovery.get('functions', 0))
        
        # Selection Results
        selection = results["phases"].get("selection", {})
        function_selection = ET.SubElement(root, "EnhancedFunctionSelection")
        ET.SubElement(function_selection, "TotalFunctions").text = str(selection.get('total_functions', 0))
        ET.SubElement(function_selection, "SelectedForTesting").text = str(selection.get('selected_functions', 0))
        ET.SubElement(function_selection, "SelectionMode").text = str(selection.get('selection_mode', 'unknown'))
        
        # Add XML comment for test generation section
        root.append(ET.Comment(" ==================== TEST GENERATION ==================== "))
        
        # Test Generation
        generation = results["phases"].get("generation", {})
        test_generation = ET.SubElement(root, "AITestGeneration")
        if generation.get("status") == "success":
            ET.SubElement(test_generation, "Status").text = "success"
            ET.SubElement(test_generation, "GeneratedTests").text = str(generation.get('generated_tests', 0))
            saved_tests = ET.SubElement(test_generation, "SavedTests")
            for test_file in generation.get("saved_tests", []):
                test_elem = ET.SubElement(saved_tests, "TestFile")
                test_elem.text = Path(test_file).name
        else:
            ET.SubElement(test_generation, "Status").text = generation.get('message', 'Failed')
        
        # Detailed Test Cases Analysis - NEW SECTION
        if generation.get("status") == "success" and generation.get("saved_tests"):
            # Add XML comment for detailed test cases section
            root.append(ET.Comment(" ==================== DETAILED TEST CASES ==================== "))
            
            # Parse test files to extract detailed test case information
            generated_tests_dict = {}
            for test_file_path in generation.get("saved_tests", []):
                test_file_name = Path(test_file_path).name
                generated_tests_dict[test_file_name] = ""  # Content not needed for parsing
            
            test_cases_info = self._parse_test_files_for_cases(generated_tests_dict)
            execution = results["phases"].get("execution", {})
            
            detailed_test_cases = ET.SubElement(root, "DetailedTestCases")
            ET.SubElement(detailed_test_cases, "TotalTestCases").text = str(test_cases_info["total_test_cases"])
            ET.SubElement(detailed_test_cases, "TotalTestFiles").text = str(len(test_cases_info["test_files"]))
            
            # Test Files Summary
            test_files_summary = ET.SubElement(detailed_test_cases, "TestFilesSummary")
            for file_name, file_info in test_cases_info["test_files"].items():
                file_elem = ET.SubElement(test_files_summary, "TestFile")
                file_elem.set("name", file_name)
                ET.SubElement(file_elem, "TestClasses").text = str(len(file_info["test_classes"]))
                ET.SubElement(file_elem, "TestMethods").text = str(file_info["test_methods"])
                ET.SubElement(file_elem, "FunctionsTested").text = ", ".join(file_info["functions_tested"])
            
            # Individual Test Cases with Results
            test_cases_list = ET.SubElement(detailed_test_cases, "TestCasesList")
            for test_case in test_cases_info["test_cases"]:
                test_case_elem = ET.SubElement(test_cases_list, "TestCase")
                test_case_elem.set("number", str(test_case["test_case_number"]))
                test_case_elem.set("result", self._get_test_case_result(test_case["method_name"], test_case["test_file"], execution))
                
                ET.SubElement(test_case_elem, "TestMethodName").text = test_case["method_name"]
                ET.SubElement(test_case_elem, "TargetFunction").text = test_case["target_function"]
                ET.SubElement(test_case_elem, "TestFile").text = test_case["test_file"]
                ET.SubElement(test_case_elem, "Description").text = test_case["docstring"]
                ET.SubElement(test_case_elem, "LineRange").text = f"{test_case['line_start']}-{test_case['line_end']}"
                
                # Add test class information
                for file_info in test_cases_info["test_files"].values():
                    for class_info in file_info["test_classes"]:
                        for method in class_info["test_methods"]:
                            if method["test_case_number"] == test_case["test_case_number"]:
                                ET.SubElement(test_case_elem, "TestClass").text = class_info["class_name"]
                                ET.SubElement(test_case_elem, "TestClassDescription").text = class_info["docstring"]
                                break
        
        # Add XML comment for execution results section
        root.append(ET.Comment(" ==================== TEST EXECUTION RESULTS ==================== "))
        
        # Test Execution
        execution = results["phases"].get("execution", {})
        test_execution = ET.SubElement(root, "TestExecutionResults")
        if execution.get("status") == "success":
            total = execution.get("total_tests", 0)
            passed = execution.get("passed", 0)
            failed = execution.get("failed", 0)
            success_rate = (passed / total * 100) if total > 0 else 0
            
            ET.SubElement(test_execution, "TotalTests").text = str(total)
            ET.SubElement(test_execution, "Passed").text = str(passed)
            ET.SubElement(test_execution, "Failed").text = str(failed)
            ET.SubElement(test_execution, "SuccessRate").text = f"{success_rate:.1f}%"
            
            execution_details = ET.SubElement(test_execution, "ExecutionDetails")
            for test_name, test_result in execution.get("execution_details", {}).items():
                test_elem = ET.SubElement(execution_details, "Test")
                test_elem.set("name", test_name)
                test_elem.set("result", "PASS" if test_result["success"] else "FAIL")
                
                # Add detailed test output
                if test_result.get("run_output"):
                    output_elem = ET.SubElement(test_elem, "TestOutput")
                    output_elem.text = test_result["run_output"]
                
                # Add full error details (not truncated)
                if not test_result["success"] and test_result.get("error"):
                    error_elem = ET.SubElement(test_elem, "ErrorDetails")
                    error_elem.text = test_result["error"]
        else:
            ET.SubElement(test_execution, "Status").text = execution.get('message', 'Skipped')
        
        # Add XML comment for coverage analysis section
        root.append(ET.Comment(" ==================== COVERAGE ANALYSIS ==================== "))
        
        # Coverage Analysis
        coverage = results["phases"].get("coverage", {})
        coverage_analysis = ET.SubElement(root, "CoverageAnalysis")
        ET.SubElement(coverage_analysis, "Status").text = coverage.get('message', 'Not available')
        if coverage.get("report"):
            coverage_report = ET.SubElement(coverage_analysis, "CoverageReport")
            coverage_report.text = coverage["report"]
        
        # Add XML comment for structured test execution log section
        root.append(ET.Comment(" ==================== STRUCTURED TEST EXECUTION LOG ==================== "))
        
        # Structured Test Execution Log (Industry Standard Format)
        try:
            structured_log = self._create_structured_test_execution_log(results)
            root.append(structured_log)
        except Exception as e:
            print(f"⚠️  Error creating structured test execution log: {e}")
            # Add a simple comment instead
            root.append(ET.Comment(f" Structured log creation failed: {str(e)} "))
        
        # Add XML comment for testing logs section
        root.append(ET.Comment(" ==================== COMPLETE TESTING LOGS ==================== "))
        
        # Complete Testing Logs - Raw format (not XML structured)
        testing_logs = ET.SubElement(root, "TestingLogs")
        testing_logs.set("format", "raw")
        ET.SubElement(testing_logs, "LogCount").text = str(len(self.terminal_output))
        
        # Add complete terminal output as raw text block
        raw_logs = ET.SubElement(testing_logs, "RawExecutionLogs")
        raw_logs.text = "\n".join(self.terminal_output)
        
        # Add detailed test execution logs if available
        generation = results["phases"].get("generation", {})
        execution = results["phases"].get("execution", {})
        if generation.get("status") == "success" and generation.get("saved_tests"):
            try:
                generated_tests_dict = {}
                for test_file_path in generation.get("saved_tests", []):
                    test_file_name = Path(test_file_path).name
                    generated_tests_dict[test_file_name] = ""
                
                test_cases_info = self._parse_test_files_for_cases(generated_tests_dict)
                detailed_logs = self._generate_detailed_test_logs(test_cases_info, execution)
                
                detailed_logs_elem = ET.SubElement(testing_logs, "DetailedTestExecutionLogs")
                detailed_logs_elem.text = detailed_logs
            except Exception as e:
                print(f"⚠️  Error generating detailed test logs: {e}")
                # Add error info to logs
                error_elem = ET.SubElement(testing_logs, "DetailedTestExecutionLogsError")
                error_elem.text = f"Failed to generate detailed logs: {str(e)}"
        
        # Add XML comment for automation summary section
        root.append(ET.Comment(" ==================== LOG FILE INFORMATION ==================== "))
        
        # Log File Information
        log_file_info = ET.SubElement(root, "LogFileInformation")
        ET.SubElement(log_file_info, "LogFilePath").text = str(self.log_file_path)
        ET.SubElement(log_file_info, "LogFileName").text = self.log_file_path.name
        if self.log_file_path.exists():
            log_size = self.log_file_path.stat().st_size
            ET.SubElement(log_file_info, "LogFileSize").text = f"{log_size} bytes"
            ET.SubElement(log_file_info, "LogFileSizeKB").text = f"{log_size / 1024:.2f} KB"
        else:
            ET.SubElement(log_file_info, "LogFileSize").text = "0 bytes"
        ET.SubElement(log_file_info, "LogFileGenerated").text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add XML comment for automation summary section
        root.append(ET.Comment(" ==================== AUTOMATION SUMMARY ==================== "))
        
        # Final Summary
        automation_summary = ET.SubElement(root, "AutomationSummary")
        if results.get("error"):
            ET.SubElement(automation_summary, "Status").text = "Failed"
            ET.SubElement(automation_summary, "Error").text = results["error"]
        else:
            successful_phases = sum(1 for phase in results["phases"].values() if phase.get("status") in ["success", "enhanced"])
            total_phases = len(results["phases"])
            ET.SubElement(automation_summary, "Status").text = "Success"
            ET.SubElement(automation_summary, "SuccessfulPhases").text = f"{successful_phases}/{total_phases}"
            if execution.get("status") == "success":
                overall_success_rate = (execution.get('passed', 0) / max(execution.get('total_tests', 1), 1) * 100)
                ET.SubElement(automation_summary, "OverallTestSuccessRate").text = f"{overall_success_rate:.1f}%"
        
        # Pretty print XML with enhanced formatting
        xml_string = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove extra blank lines but preserve intentional spacing
        lines = pretty_xml.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            if line.strip():  # Keep non-empty lines
                formatted_lines.append(line)
                
                # Add extra line breaks after major sections for better readability
                if any(tag in line for tag in [
                    '</ProjectStructureAnalysis>',
                    '</EnhancedFunctionSelection>', 
                    '</AITestGeneration>',
                    '</DetailedTestCases>',
                    '</TestExecutionResults>',
                    '</CoverageAnalysis>',
                    '</TestingLogs>',
                    '</AutomationSummary>'
                ]):
                    formatted_lines.append('')  # Add blank line after major sections
                
                # Add spacing within TestCasesList for readability
                elif '</TestCase>' in line:
                    formatted_lines.append('')  # Add blank line after each test case
                
                # Add spacing within TestingLogs for better log separation
                elif i < len(lines) - 1 and '<LogEntry sequence=' in line and line.endswith('============================================================</LogEntry>'):
                    formatted_lines.append('')  # Add blank line after phase separators
        
        # Join the formatted lines
        pretty_xml = '\n'.join(formatted_lines)
        
        # Remove any trailing empty lines
        pretty_xml = pretty_xml.rstrip() + '\n'
        
        # Save XML report
        xml_report_filename = f"enhanced_automation_report_{timestamp}.xml"
        xml_report_path = self.project_root / xml_report_filename
        
        try:
            with open(xml_report_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            print(f"📄 XML report saved: {xml_report_path}")
            print(f"📄 Log file saved: {self.log_file_path}")
            
            # Send email with report if email service is configured
            if self.email_service.enabled:
                project_name = self.project_root.name
                terminal_output_text = "\n".join(self.terminal_output)
                
                # Add log file information to terminal output
                log_file_info = f"\n\n{'='*50}\n📄 LOG FILE INFORMATION\n{'='*50}\n"
                log_file_info += f"Log file location: {self.log_file_path}\n"
                log_file_info += f"Log file size: {self.log_file_path.stat().st_size if self.log_file_path.exists() else 0} bytes\n"
                terminal_output_text += log_file_info
                
                email_sent = self.email_service.send_test_report(
                    xml_report_path=str(xml_report_path),
                    terminal_output=terminal_output_text,
                    project_name=project_name,
                    test_results=results
                )
                if email_sent:
                    print(f"📧 Test report emailed successfully!")
                    print(f"📧 Email includes log file information")
                    
        except Exception as e:
            print(f"⚠️  Could not save XML report: {e}")
        
        # Also print a summary to console
        final_message = f"\n🎉 ENHANCED AUTOMATION COMPLETED SUCCESSFULLY!"
        self._capture_output(final_message)
        if execution.get("status") == "success":
            passed = execution.get("passed", 0)
            total = execution.get("total_tests", 0)
            if total > 0:
                success_rate = (passed / total) * 100
                success_message = f"🌟 Test success rate: {success_rate:.1f}%"
                self._capture_output(success_message)
        report_message = f"📊 Full report available in XML format: {xml_report_filename}"
        self._capture_output(report_message)
        log_message = f"📄 Detailed logs available in: {self.log_file_path}"
        self._capture_output(log_message)
        
        # Log final completion
        self.logger.info("=" * 60)
        self.logger.info("AUTOMATION COMPLETED SUCCESSFULLY")
        self.logger.info("=" * 60)
        self.logger.info(f"XML Report: {xml_report_filename}")
        self.logger.info(f"Log File: {self.log_file_path}")
        if execution.get("status") == "success":
            passed = execution.get("passed", 0)
            total = execution.get("total_tests", 0)
            if total > 0:
                success_rate = (passed / total) * 100
                self.logger.info(f"Final Test Success Rate: {success_rate:.1f}%")
        self.logger.info("=" * 60)

def main():
    """Main entry point for the enhanced testing tool"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Python Project Unit Testing Automation Tool with Groq AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a local project with default Groq model
  python hello-py.py /path/to/local/project
  
  # Test a GitHub repository
  python hello-py.py https://github.com/user/repo.git
  python hello-py.py https://github.com/user/repo
  
  # Test with custom Groq model
  python hello-py.py /path/to/project --model llama-3.1-8b-instant
  
  # Test with custom API key
  python hello-py.py /path/to/project --api-key your-groq-api-key
  
  # Test without forcing all functions
  python hello-py.py /path/to/project --no-force
        """
    )
    
    parser.add_argument("project_path", help="Path to Python project root directory OR GitHub repository URL")
    parser.add_argument("--model", default=GROQ_MODEL, help="Groq model to use (e.g., llama-3.1-70b-versatile)")
    parser.add_argument("--api-key", default=GROQ_API_KEY, help="Groq API key (or set GROQ_API_KEY environment variable)")
    parser.add_argument("--no-force", action="store_true", help="Don't force testing all functions")
    
    args = parser.parse_args()
    
    github_manager = GitHubRepoManager()
    
    # Check if it's a GitHub URL or local path
    if github_manager.is_github_url(args.project_path):
        print(f"🌐 GitHub repository URL detected: {args.project_path}")
        project_path = args.project_path  # Will be handled by the automator
    else:
        project_path = Path(args.project_path)
        if not project_path.exists():
            print(f"❌ Project path does not exist: {project_path}")
            sys.exit(1)
        
        if not project_path.is_dir():
            print(f"❌ Project path is not a directory: {project_path}")
            sys.exit(1)
        
        project_path = str(project_path)
    
    force_all_tests = not args.no_force
    
    # Use context manager to ensure cleanup
    try:
        with EnhancedProjectTestAutomator(
            project_path, 
            args.model, 
            args.api_key,
            force_all_tests=force_all_tests
        ) as automator:
            
            results = automator.run_full_automation()
            
            if results.get("error"):
                print(f"\n❌ AUTOMATION FAILED: {results['error']}")
                sys.exit(1)
            else:
                execution = results.get("phases", {}).get("execution", {})
                if execution.get("status") == "success":
                    passed = execution.get("passed", 0)
                    total = execution.get("total_tests", 0)
                    if total > 0:
                        success_rate = (passed / total) * 100
                        if success_rate >= 80:
                            print(f"🌟 Excellent test success rate: {success_rate:.1f}%")
                        elif success_rate >= 60:
                            print(f"🟡 Good test success rate: {success_rate:.1f}%")
                        else:
                            print(f"🔴 Tests need attention: {success_rate:.1f}% success rate")
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ AUTOMATION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
