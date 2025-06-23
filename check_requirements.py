#!/usr/bin/env python3
"""
Requirements Checker for Cloud Orchestrator
Analyzes the codebase and checks if all required dependencies are included in requirements.txt
"""

import os
import re
import ast
from pathlib import Path
from typing import Set, Dict, List

def extract_imports_from_file(file_path: str) -> Set[str]:
    """Extract all import statements from a Python file"""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to extract imports
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
    
    return imports

def scan_python_files(directory: str) -> Dict[str, Set[str]]:
    """Scan all Python files in a directory and extract imports"""
    imports_by_file = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.venv', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                imports = extract_imports_from_file(file_path)
                if imports:
                    imports_by_file[file_path] = imports
    
    return imports_by_file

def parse_requirements(requirements_file: str) -> Set[str]:
    """Parse requirements.txt and extract package names"""
    packages = set()
    
    try:
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (remove version specifiers)
                    package = re.split(r'[<>=!~]', line)[0].strip()
                    packages.add(package)
    except FileNotFoundError:
        print(f"Warning: {requirements_file} not found")
    
    return packages

def categorize_imports(imports: Set[str]) -> Dict[str, List[str]]:
    """Categorize imports into different types"""
    categories = {
        'standard_library': [],
        'third_party': [],
        'google_cloud': [],
        'google_adk': [],
        'local': []
    }
    
    # Standard library modules
    stdlib_modules = {
        'os', 'sys', 'json', 're', 'ast', 'pathlib', 'tempfile', 'shutil',
        'subprocess', 'time', 'datetime', 'typing', 'uuid', 'webbrowser',
        'zoneinfo', 'collections', 'itertools', 'functools', 'contextlib'
    }
    
    for imp in imports:
        if imp in stdlib_modules or imp.startswith('_'):
            categories['standard_library'].append(imp)
        elif imp.startswith('google.adk'):
            categories['google_adk'].append(imp)
        elif imp.startswith('google.cloud') or imp.startswith('google.generativeai'):
            categories['google_cloud'].append(imp)
        elif imp.startswith('cloud_orchestrator') or imp.startswith('.'):
            categories['local'].append(imp)
        else:
            categories['third_party'].append(imp)
    
    return categories

def check_missing_dependencies(imports: Set[str], requirements: Set[str]) -> Set[str]:
    """Check which imports are missing from requirements"""
    missing = set()
    
    # Map of import names to package names
    import_to_package = {
        'google.adk': 'google-adk',
        'google.cloud': 'google-cloud-aiplatform',
        'google.generativeai': 'google-generativeai',
        'vertexai': 'google-cloud-aiplatform',
        'requests': 'requests',
        'yaml': 'pyyaml',
        'flask': 'flask',
        'dotenv': 'python-dotenv',
        'pydantic': 'pydantic',
        'cloudpickle': 'cloudpickle',
        'sklearn': 'scikit-learn',
        'reportlab': 'reportlab',
        'pdfplumber': 'pdfplumber',
        'pytest': 'pytest',
        'overrides': 'overrides',
        'pysqlite3': 'pysqlite3-binary',
        'toolbox': 'toolbox-langchain'
    }
    
    for imp in imports:
        if imp in import_to_package:
            package = import_to_package[imp]
            if package not in requirements:
                missing.add(f"{imp} -> {package}")
        elif imp.startswith('google.cloud.'):
            # Handle specific Google Cloud packages
            service = imp.split('.')[2]  # google.cloud.SERVICE
            package = f"google-cloud-{service}"
            if package not in requirements:
                missing.add(f"{imp} -> {package}")
    
    return missing

def main():
    """Main function to check requirements"""
    print("🔍 Cloud Orchestrator Requirements Checker")
    print("=" * 50)
    
    # Scan all Python files
    print("📁 Scanning Python files...")
    imports_by_file = scan_python_files('.')
    
    # Collect all unique imports
    all_imports = set()
    for imports in imports_by_file.values():
        all_imports.update(imports)
    
    print(f"✅ Found {len(all_imports)} unique imports across {len(imports_by_file)} files")
    
    # Parse requirements.txt
    print("📋 Parsing requirements.txt...")
    requirements = parse_requirements('requirements.txt')
    print(f"✅ Found {len(requirements)} packages in requirements.txt")
    
    # Categorize imports
    print("📊 Categorizing imports...")
    categories = categorize_imports(all_imports)
    
    print("\n📈 Import Categories:")
    for category, imports in categories.items():
        if imports:
            print(f"  {category}: {len(imports)} imports")
            if category in ['third_party', 'google_cloud', 'google_adk']:
                for imp in sorted(imports):
                    print(f"    - {imp}")
    
    # Check for missing dependencies
    print("\n🔍 Checking for missing dependencies...")
    missing = check_missing_dependencies(all_imports, requirements)
    
    if missing:
        print(f"❌ Found {len(missing)} potentially missing dependencies:")
        for item in sorted(missing):
            print(f"  - {item}")
        
        print("\n💡 Suggested additions to requirements.txt:")
        for item in sorted(missing):
            package = item.split(' -> ')[1]
            print(f"  {package}")
    else:
        print("✅ All dependencies appear to be covered!")
    
    # Show summary
    print(f"\n📊 Summary:")
    print(f"  Total imports: {len(all_imports)}")
    print(f"  Requirements: {len(requirements)}")
    print(f"  Missing: {len(missing)}")
    
    # Show files with most imports
    print(f"\n📁 Files with most imports:")
    sorted_files = sorted(imports_by_file.items(), key=lambda x: len(x[1]), reverse=True)
    for file_path, imports in sorted_files[:5]:
        rel_path = os.path.relpath(file_path)
        print(f"  {rel_path}: {len(imports)} imports")

if __name__ == "__main__":
    main() 