#!/usr/bin/env python3
"""
Code Quality Improvement Script for Lawvriksh Backend
This script identifies and fixes common code smells and issues.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Analyzes Python code for common issues and smells."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
    
    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a single Python file for issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Check for various code smells
            issues.extend(self._check_function_length(tree, file_path))
            issues.extend(self._check_duplicate_code(content, file_path))
            issues.extend(self._check_error_handling(tree, file_path))
            issues.extend(self._check_security_issues(content, file_path))
            issues.extend(self._check_performance_issues(tree, file_path))
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return issues
    
    def _check_function_length(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """Check for overly long functions."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count lines in function
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno
                    if length > 50:  # Functions longer than 50 lines
                        issues.append({
                            'type': 'long_function',
                            'file': file_path,
                            'line': node.lineno,
                            'function': node.name,
                            'length': length,
                            'severity': 'medium',
                            'message': f"Function '{node.name}' is {length} lines long (consider breaking it down)"
                        })
        
        return issues
    
    def _check_duplicate_code(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Check for duplicate code patterns."""
        issues = []
        lines = content.split('\n')
        
        # Simple duplicate line detection
        line_counts = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 10 and not stripped.startswith('#'):
                if stripped in line_counts:
                    line_counts[stripped].append(i + 1)
                else:
                    line_counts[stripped] = [i + 1]
        
        for line, occurrences in line_counts.items():
            if len(occurrences) > 2:
                issues.append({
                    'type': 'duplicate_code',
                    'file': file_path,
                    'lines': occurrences,
                    'severity': 'low',
                    'message': f"Duplicate code found on lines {occurrences}: '{line[:50]}...'"
                })
        
        return issues
    
    def _check_error_handling(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """Check for poor error handling patterns."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        'type': 'bare_except',
                        'file': file_path,
                        'line': node.lineno,
                        'severity': 'high',
                        'message': "Bare except clause found - should catch specific exceptions"
                    })
            
            # Check for pass in except blocks
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append({
                        'type': 'silent_exception',
                        'file': file_path,
                        'line': node.lineno,
                        'severity': 'high',
                        'message': "Silent exception handling - should log or handle properly"
                    })
        
        return issues
    
    def _check_security_issues(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Check for potential security issues."""
        issues = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's a placeholder or environment variable
                    if not any(placeholder in line.lower() for placeholder in ['your_', 'example', 'placeholder', 'env', 'getenv']):
                        issues.append({
                            'type': 'hardcoded_secret',
                            'file': file_path,
                            'line': i + 1,
                            'severity': 'critical',
                            'message': "Potential hardcoded secret found"
                        })
        
        # Check for SQL injection vulnerabilities
        if 'execute(' in content and '%' in content:
            issues.append({
                'type': 'sql_injection_risk',
                'file': file_path,
                'severity': 'high',
                'message': "Potential SQL injection risk - use parameterized queries"
            })
        
        return issues
    
    def _check_performance_issues(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """Check for performance issues."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for inefficient loops
            if isinstance(node, ast.For):
                # Look for list comprehensions that could be generators
                if isinstance(node.iter, ast.ListComp):
                    issues.append({
                        'type': 'inefficient_loop',
                        'file': file_path,
                        'line': node.lineno,
                        'severity': 'low',
                        'message': "Consider using generator expression instead of list comprehension in loop"
                    })
        
        return issues
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze the entire project."""
        logger.info(f"Analyzing project at {self.project_root}")
        
        python_files = list(self.project_root.rglob("*.py"))
        # Exclude virtual environment and cache files
        python_files = [f for f in python_files if not any(part.startswith('.') or part in ['__pycache__', '.venv', 'venv'] for part in f.parts)]
        
        all_issues = []
        for file_path in python_files:
            file_issues = self.analyze_file(file_path)
            all_issues.extend(file_issues)
        
        # Categorize issues by severity
        critical_issues = [i for i in all_issues if i['severity'] == 'critical']
        high_issues = [i for i in all_issues if i['severity'] == 'high']
        medium_issues = [i for i in all_issues if i['severity'] == 'medium']
        low_issues = [i for i in all_issues if i['severity'] == 'low']
        
        return {
            'total_files': len(python_files),
            'total_issues': len(all_issues),
            'critical': critical_issues,
            'high': high_issues,
            'medium': medium_issues,
            'low': low_issues,
            'all_issues': all_issues
        }

def generate_fixes_report(analysis_result: Dict[str, Any]) -> str:
    """Generate a report with recommended fixes."""
    report = []
    report.append("# Code Quality Analysis Report")
    report.append("=" * 50)
    report.append(f"Total files analyzed: {analysis_result['total_files']}")
    report.append(f"Total issues found: {analysis_result['total_issues']}")
    report.append("")
    
    # Summary by severity
    report.append("## Issues by Severity")
    report.append(f"🔴 Critical: {len(analysis_result['critical'])}")
    report.append(f"🟠 High: {len(analysis_result['high'])}")
    report.append(f"🟡 Medium: {len(analysis_result['medium'])}")
    report.append(f"🟢 Low: {len(analysis_result['low'])}")
    report.append("")
    
    # Detailed issues
    for severity, issues in [
        ("Critical", analysis_result['critical']),
        ("High", analysis_result['high']),
        ("Medium", analysis_result['medium']),
        ("Low", analysis_result['low'])
    ]:
        if issues:
            report.append(f"## {severity} Issues")
            for issue in issues:
                report.append(f"- **{issue['type']}** in {issue['file']}")
                if 'line' in issue:
                    report.append(f"  Line {issue['line']}: {issue['message']}")
                else:
                    report.append(f"  {issue['message']}")
                report.append("")
    
    return "\n".join(report)

def main():
    """Main function."""
    project_root = Path(__file__).parent
    
    logger.info("🔍 Starting code quality analysis...")
    
    analyzer = CodeAnalyzer(project_root)
    results = analyzer.analyze_project()
    
    # Generate report
    report = generate_fixes_report(results)
    
    # Save report
    with open("code_quality_report.md", "w", encoding='utf-8') as f:
        f.write(report)
    
    logger.info("📄 Report saved to code_quality_report.md")
    
    # Print summary
    print("\n" + "="*50)
    print("📊 CODE QUALITY SUMMARY")
    print("="*50)
    print(f"Files analyzed: {results['total_files']}")
    print(f"Issues found: {results['total_issues']}")
    print(f"🔴 Critical: {len(results['critical'])}")
    print(f"🟠 High: {len(results['high'])}")
    print(f"🟡 Medium: {len(results['medium'])}")
    print(f"🟢 Low: {len(results['low'])}")
    
    if results['critical'] or results['high']:
        print("\n⚠️  Critical and high-priority issues should be addressed immediately!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
