"""
Advanced Code Analyzers for World-Class Code Scanning
======================================================
Provides:
1. Semantic Code Analysis (AST parsing)
2. Git History Scanning (secrets in commits)
3. Dependency Vulnerability Scan (CVEs)
4. Code Complexity Metrics (cyclomatic complexity)
5. Binary File Analysis (compiled code detection)
"""

import ast
import os
import re
import json
import hashlib
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("scanner.advanced_analyzers")


class SemanticCodeAnalyzer:
    """
    AST-based semantic code analysis for Python, JavaScript, and Java.
    Provides deeper analysis than pattern matching alone.
    """
    
    def __init__(self):
        self.findings = []
        
        self.dangerous_python_calls = {
            'eval': ('Critical', 'Code Injection', 'eval() can execute arbitrary code - use ast.literal_eval() instead'),
            'exec': ('Critical', 'Code Injection', 'exec() can execute arbitrary code - avoid dynamic code execution'),
            'compile': ('High', 'Code Injection', 'compile() can be used for code injection - validate input carefully'),
            'pickle.loads': ('Critical', 'Deserialization', 'pickle.loads() can execute arbitrary code - use json instead'),
            'pickle.load': ('Critical', 'Deserialization', 'pickle.load() can execute arbitrary code - use json instead'),
            'yaml.load': ('High', 'Deserialization', 'yaml.load() without Loader is unsafe - use yaml.safe_load()'),
            'subprocess.call': ('Medium', 'Command Injection', 'subprocess with shell=True can be vulnerable - use shell=False'),
            'subprocess.Popen': ('Medium', 'Command Injection', 'subprocess with shell=True can be vulnerable - use shell=False'),
            'os.system': ('High', 'Command Injection', 'os.system() is vulnerable to injection - use subprocess instead'),
            'os.popen': ('High', 'Command Injection', 'os.popen() is vulnerable to injection - use subprocess instead'),
            '__import__': ('Medium', 'Dynamic Import', 'Dynamic imports can be security risks - use static imports'),
            'input': ('Low', 'User Input', 'input() returns unsanitized user input - validate before use'),
        }
        
        self.dangerous_js_patterns = [
            (r'\beval\s*\(', 'Critical', 'Code Injection', 'eval() can execute arbitrary code'),
            (r'new\s+Function\s*\(', 'Critical', 'Code Injection', 'new Function() can execute arbitrary code'),
            (r'innerHTML\s*=', 'High', 'XSS Vulnerability', 'innerHTML can lead to XSS - use textContent instead'),
            (r'document\.write\s*\(', 'High', 'XSS Vulnerability', 'document.write can lead to XSS'),
            (r'\.outerHTML\s*=', 'High', 'XSS Vulnerability', 'outerHTML can lead to XSS'),
            (r'setTimeout\s*\(\s*["\']', 'Medium', 'Code Injection', 'setTimeout with string is like eval'),
            (r'setInterval\s*\(\s*["\']', 'Medium', 'Code Injection', 'setInterval with string is like eval'),
            (r'dangerouslySetInnerHTML', 'High', 'XSS Vulnerability', 'React dangerouslySetInnerHTML can lead to XSS'),
            (r'__proto__', 'Medium', 'Prototype Pollution', 'Direct __proto__ access can lead to prototype pollution'),
            (r'Object\.assign\s*\(\s*\{\}', 'Low', 'Prototype Pollution', 'Object.assign with user input can cause pollution'),
        ]
        
        self.dangerous_java_patterns = [
            (r'Runtime\.getRuntime\(\)\.exec', 'Critical', 'Command Injection', 'Runtime.exec can execute system commands'),
            (r'ProcessBuilder', 'Medium', 'Command Injection', 'ProcessBuilder can execute system commands'),
            (r'ObjectInputStream', 'Critical', 'Deserialization', 'Java deserialization can lead to RCE'),
            (r'XMLDecoder', 'Critical', 'Deserialization', 'XMLDecoder can lead to arbitrary code execution'),
            (r'ScriptEngine.*eval', 'Critical', 'Code Injection', 'ScriptEngine eval can execute arbitrary code'),
            (r'Class\.forName', 'Medium', 'Reflection', 'Dynamic class loading can be a security risk'),
            (r'\.invoke\s*\(', 'Medium', 'Reflection', 'Reflection invoke can bypass security'),
            (r'PreparedStatement.*\+', 'High', 'SQL Injection', 'String concatenation in SQL is vulnerable'),
            (r'createQuery\s*\(\s*".*\+', 'High', 'SQL Injection', 'String concatenation in queries is vulnerable'),
        ]
    
    def analyze_python_ast(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Python code using AST for semantic issues."""
        findings = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    finding = self._check_python_call(node, file_path)
                    if finding:
                        findings.append(finding)
                
                elif isinstance(node, ast.Assign):
                    finding = self._check_python_assignment(node, file_path)
                    if finding:
                        findings.append(finding)
                        
                elif isinstance(node, ast.FunctionDef):
                    findings.extend(self._check_python_function(node, file_path))
                    
        except SyntaxError as e:
            findings.append({
                'type': 'Semantic Analysis: Syntax Error',
                'severity': 'Medium',
                'value': f'Syntax error at line {e.lineno}: {e.msg}',
                'line': e.lineno or 0,
                'file': file_path,
                'category': 'code_quality',
                'remediation': 'Fix syntax error before deployment'
            })
        except Exception as e:
            logger.debug(f"AST parsing failed for {file_path}: {e}")
            
        return findings
    
    def _check_python_call(self, node: ast.Call, file_path: str) -> Optional[Dict[str, Any]]:
        """Check Python function calls for dangerous patterns."""
        func_name = None
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
            else:
                func_name = node.func.attr
                
        if func_name and func_name in self.dangerous_python_calls:
            severity, issue_type, remediation = self.dangerous_python_calls[func_name]
            return {
                'type': f'Semantic Analysis: {issue_type}',
                'severity': severity,
                'value': f'Dangerous function call: {func_name}()',
                'line': node.lineno,
                'file': file_path,
                'category': 'security_vulnerability',
                'remediation': remediation,
                'compliance_reference': 'OWASP Top 10 + CWE-94/78/502'
            }
        return None
    
    def _check_python_assignment(self, node: ast.Assign, file_path: str) -> Optional[Dict[str, Any]]:
        """Check Python assignments for hardcoded secrets."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                secret_patterns = ['password', 'secret', 'api_key', 'apikey', 'token', 'private_key']
                
                if any(pattern in var_name for pattern in secret_patterns):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        if len(node.value.value) > 5:
                            return {
                                'type': 'Semantic Analysis: Hardcoded Secret',
                                'severity': 'Critical',
                                'value': f'Hardcoded secret in variable: {target.id}',
                                'line': node.lineno,
                                'file': file_path,
                                'category': 'secrets_exposure',
                                'remediation': 'Use environment variables or secret management',
                                'compliance_reference': 'GDPR Art. 32 + NIS2 Art. 21'
                            }
        return None
    
    def _check_python_function(self, node: ast.FunctionDef, file_path: str) -> List[Dict[str, Any]]:
        """Check Python functions for security issues."""
        findings = []
        
        if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
            findings.append({
                'type': 'Semantic Analysis: Empty Function',
                'severity': 'Low',
                'value': f'Empty function: {node.name}()',
                'line': node.lineno,
                'file': file_path,
                'category': 'code_quality',
                'remediation': 'Implement function or remove placeholder'
            })
        
        if node.name.startswith('_') and not node.name.startswith('__'):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id in ['app.route', 'route', 'api']:
                    findings.append({
                        'type': 'Semantic Analysis: Private API Exposure',
                        'severity': 'Medium',
                        'value': f'Private function {node.name} exposed as API',
                        'line': node.lineno,
                        'file': file_path,
                        'category': 'security_design',
                        'remediation': 'Review if private function should be exposed'
                    })
                    
        return findings
    
    def analyze_javascript(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript code for security issues."""
        findings = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, severity, issue_type, remediation in self.dangerous_js_patterns:
                if re.search(pattern, line):
                    findings.append({
                        'type': f'Semantic Analysis: {issue_type}',
                        'severity': severity,
                        'value': f'{issue_type} detected: {line.strip()[:60]}...',
                        'line': line_num,
                        'file': file_path,
                        'category': 'security_vulnerability',
                        'remediation': remediation,
                        'compliance_reference': 'OWASP Top 10 A03:2021'
                    })
                    
        return findings
    
    def analyze_java(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Java code for security issues."""
        findings = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, severity, issue_type, remediation in self.dangerous_java_patterns:
                if re.search(pattern, line):
                    findings.append({
                        'type': f'Semantic Analysis: {issue_type}',
                        'severity': severity,
                        'value': f'{issue_type} detected: {line.strip()[:60]}...',
                        'line': line_num,
                        'file': file_path,
                        'category': 'security_vulnerability',
                        'remediation': remediation,
                        'compliance_reference': 'OWASP Top 10 + CWE'
                    })
                    
        return findings
    
    def analyze(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze code based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            return self.analyze_python_ast(code, file_path)
        elif ext in ['.js', '.jsx', '.ts', '.tsx', '.mjs']:
            return self.analyze_javascript(code, file_path)
        elif ext == '.java':
            return self.analyze_java(code, file_path)
        else:
            return []


class GitHistoryScanner:
    """
    Scans Git commit history for secrets and sensitive data.
    """
    
    def __init__(self):
        self.secret_patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API Key'),
            (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Secret Key'),
            (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{8,})["\']?', 'Password'),
            (r'(?i)(token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Token'),
            (r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*["\']?([A-Z0-9]{20})["\']?', 'AWS Access Key'),
            (r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9/+]{40})["\']?', 'AWS Secret Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
            (r'gho_[a-zA-Z0-9]{36}', 'GitHub OAuth Token'),
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            (r'sk_live_[a-zA-Z0-9]{24,}', 'Stripe Live Key'),
            (r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', 'Private Key'),
            (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer Token'),
        ]
    
    def scan_git_history(self, repo_path: str, max_commits: int = 100) -> List[Dict[str, Any]]:
        """Scan Git commit history for secrets."""
        findings = []
        
        try:
            git_dir = os.path.join(repo_path, '.git')
            if not os.path.isdir(git_dir):
                return []
            
            result = subprocess.run(
                ['git', 'log', '--all', f'-{max_commits}', '--pretty=format:%H|%s|%an|%ad', '--date=short'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            commits = result.stdout.strip().split('\n')
            
            for commit_line in commits[:max_commits]:
                if not commit_line:
                    continue
                    
                parts = commit_line.split('|')
                if len(parts) < 4:
                    continue
                    
                commit_hash = parts[0]
                commit_msg = parts[1]
                author = parts[2]
                date = parts[3]
                
                diff_result = subprocess.run(
                    ['git', 'show', commit_hash, '--no-color', '--format='],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if diff_result.returncode == 0:
                    diff_content = diff_result.stdout
                    
                    for pattern, secret_type in self.secret_patterns:
                        matches = re.findall(pattern, diff_content)
                        if matches:
                            findings.append({
                                'type': f'Git History: {secret_type} Exposed',
                                'severity': 'Critical',
                                'value': f'{secret_type} found in commit {commit_hash[:8]} by {author}',
                                'commit': commit_hash,
                                'author': author,
                                'date': date,
                                'message': commit_msg[:50],
                                'file': repo_path,
                                'category': 'git_history_secrets',
                                'remediation': f'Rotate {secret_type} immediately. Use git filter-branch to remove from history.',
                                'compliance_reference': 'GDPR Art. 32 + NIS2 Art. 21 + SOC2 CC6.1'
                            })
                            
        except subprocess.TimeoutExpired:
            logger.warning(f"Git history scan timed out for {repo_path}")
        except Exception as e:
            logger.debug(f"Git history scan failed: {e}")
            
        return findings


class DependencyVulnerabilityScanner:
    """
    Scans package manifests for known CVEs and vulnerabilities.
    """
    
    def __init__(self):
        self.known_vulnerabilities = {
            'lodash': [
                {'version_range': '<4.17.21', 'cve': 'CVE-2021-23337', 'severity': 'High', 'description': 'Command Injection'},
                {'version_range': '<4.17.19', 'cve': 'CVE-2020-8203', 'severity': 'High', 'description': 'Prototype Pollution'},
            ],
            'axios': [
                {'version_range': '<0.21.1', 'cve': 'CVE-2020-28168', 'severity': 'Medium', 'description': 'SSRF vulnerability'},
            ],
            'minimist': [
                {'version_range': '<1.2.6', 'cve': 'CVE-2021-44906', 'severity': 'Critical', 'description': 'Prototype Pollution'},
            ],
            'node-fetch': [
                {'version_range': '<2.6.7', 'cve': 'CVE-2022-0235', 'severity': 'High', 'description': 'Exposure of sensitive information'},
            ],
            'express': [
                {'version_range': '<4.17.3', 'cve': 'CVE-2022-24999', 'severity': 'High', 'description': 'Open Redirect'},
            ],
            'requests': [
                {'version_range': '<2.31.0', 'cve': 'CVE-2023-32681', 'severity': 'Medium', 'description': 'Information disclosure'},
            ],
            'flask': [
                {'version_range': '<2.2.5', 'cve': 'CVE-2023-30861', 'severity': 'High', 'description': 'Session cookie vulnerability'},
            ],
            'django': [
                {'version_range': '<4.2.4', 'cve': 'CVE-2023-41164', 'severity': 'Medium', 'description': 'Denial of Service'},
            ],
            'pillow': [
                {'version_range': '<10.0.1', 'cve': 'CVE-2023-44271', 'severity': 'High', 'description': 'Denial of Service'},
            ],
            'pyyaml': [
                {'version_range': '<5.4', 'cve': 'CVE-2020-14343', 'severity': 'Critical', 'description': 'Arbitrary Code Execution'},
            ],
            'urllib3': [
                {'version_range': '<2.0.6', 'cve': 'CVE-2023-45803', 'severity': 'Medium', 'description': 'Cookie leakage'},
            ],
            'cryptography': [
                {'version_range': '<41.0.4', 'cve': 'CVE-2023-38325', 'severity': 'High', 'description': 'Memory corruption'},
            ],
        }
    
    def _parse_version(self, version_str: str) -> Tuple[int, ...]:
        """Parse version string to tuple for comparison."""
        try:
            clean = re.sub(r'[^\d.]', '', version_str.split(',')[0])
            parts = clean.split('.')
            return tuple(int(p) for p in parts[:3] if p.isdigit())
        except:
            return (0, 0, 0)
    
    def _version_in_range(self, version: str, range_str: str) -> bool:
        """Check if version is in vulnerable range."""
        try:
            v = self._parse_version(version)
            if range_str.startswith('<'):
                max_v = self._parse_version(range_str[1:])
                return v < max_v
            elif range_str.startswith('<='):
                max_v = self._parse_version(range_str[2:])
                return v <= max_v
            return False
        except:
            return False
    
    def scan_package_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan package.json for vulnerable dependencies."""
        findings = []
        
        try:
            with open(file_path, 'r') as f:
                package = json.load(f)
            
            all_deps = {}
            all_deps.update(package.get('dependencies', {}))
            all_deps.update(package.get('devDependencies', {}))
            
            for pkg_name, version in all_deps.items():
                pkg_lower = pkg_name.lower()
                if pkg_lower in self.known_vulnerabilities:
                    for vuln in self.known_vulnerabilities[pkg_lower]:
                        if self._version_in_range(version, vuln['version_range']):
                            findings.append({
                                'type': f"Dependency CVE: {vuln['cve']}",
                                'severity': vuln['severity'],
                                'value': f"{pkg_name}@{version}: {vuln['description']}",
                                'package': pkg_name,
                                'version': version,
                                'cve': vuln['cve'],
                                'file': file_path,
                                'category': 'dependency_vulnerability',
                                'remediation': f"Upgrade {pkg_name} to a version >= {vuln['version_range'][1:]}",
                                'compliance_reference': 'NIS2 Art. 21 + SOC2 CC6.1 + ISO 27001 A.12.6.1'
                            })
                            
        except Exception as e:
            logger.debug(f"Failed to scan package.json: {e}")
            
        return findings
    
    def scan_requirements_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan requirements.txt for vulnerable dependencies."""
        findings = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                match = re.match(r'^([a-zA-Z0-9_\-]+)([=<>!]+)?(.+)?$', line)
                if match:
                    pkg_name = match.group(1).lower()
                    version = match.group(3) or '0.0.0'
                    
                    if pkg_name in self.known_vulnerabilities:
                        for vuln in self.known_vulnerabilities[pkg_name]:
                            if self._version_in_range(version, vuln['version_range']):
                                findings.append({
                                    'type': f"Dependency CVE: {vuln['cve']}",
                                    'severity': vuln['severity'],
                                    'value': f"{pkg_name}=={version}: {vuln['description']}",
                                    'package': pkg_name,
                                    'version': version,
                                    'cve': vuln['cve'],
                                    'file': file_path,
                                    'category': 'dependency_vulnerability',
                                    'remediation': f"Upgrade {pkg_name} to version >= {vuln['version_range'][1:]}",
                                    'compliance_reference': 'NIS2 Art. 21 + SOC2 CC6.1 + ISO 27001 A.12.6.1'
                                })
                                
        except Exception as e:
            logger.debug(f"Failed to scan requirements.txt: {e}")
            
        return findings
    
    def scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan dependency file based on filename."""
        filename = os.path.basename(file_path).lower()
        
        if filename == 'package.json':
            return self.scan_package_json(file_path)
        elif filename in ['requirements.txt', 'requirements-dev.txt', 'requirements-prod.txt']:
            return self.scan_requirements_txt(file_path)
        elif filename == 'pyproject.toml':
            return []
        else:
            return []


class CodeComplexityAnalyzer:
    """
    Analyzes code complexity metrics including cyclomatic complexity,
    lines of code, and technical debt scoring.
    """
    
    def __init__(self):
        self.complexity_thresholds = {
            'low': 5,
            'medium': 10,
            'high': 20,
            'critical': 30
        }
    
    def calculate_cyclomatic_complexity(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Calculate cyclomatic complexity for Python code."""
        findings = []
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext != '.py':
            return self._calculate_generic_complexity(code, file_path)
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_function_complexity(node)
                    
                    if complexity > self.complexity_thresholds['critical']:
                        severity = 'Critical'
                    elif complexity > self.complexity_thresholds['high']:
                        severity = 'High'
                    elif complexity > self.complexity_thresholds['medium']:
                        severity = 'Medium'
                    elif complexity > self.complexity_thresholds['low']:
                        severity = 'Low'
                    else:
                        continue
                    
                    findings.append({
                        'type': 'Code Complexity: High Cyclomatic Complexity',
                        'severity': severity,
                        'value': f'Function {node.name}() has complexity {complexity}',
                        'line': node.lineno,
                        'file': file_path,
                        'complexity_score': complexity,
                        'category': 'code_complexity',
                        'remediation': f'Refactor {node.name}() - extract methods, reduce conditionals',
                        'compliance_reference': 'ISO/IEC 25010 Maintainability'
                    })
                    
        except SyntaxError:
            pass
        except Exception as e:
            logger.debug(f"Complexity analysis failed: {e}")
            
        return findings
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
            elif isinstance(child, ast.IfExp):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
                
        return complexity
    
    def _calculate_generic_complexity(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Calculate approximate complexity for non-Python files."""
        findings = []
        
        lines = code.split('\n')
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith(('//', '#', '*', '/*'))])
        
        complexity_indicators = 0
        for line in lines:
            complexity_indicators += len(re.findall(r'\b(if|else|elif|for|while|switch|case|catch|&&|\|\|)\b', line))
        
        if total_lines > 500:
            findings.append({
                'type': 'Code Complexity: Large File',
                'severity': 'Medium' if total_lines < 1000 else 'High',
                'value': f'File has {total_lines} lines ({code_lines} code lines)',
                'line': 1,
                'file': file_path,
                'category': 'code_complexity',
                'remediation': 'Consider splitting into smaller modules',
                'compliance_reference': 'ISO/IEC 25010 Maintainability'
            })
            
        if complexity_indicators > 100:
            findings.append({
                'type': 'Code Complexity: High Branch Count',
                'severity': 'Medium',
                'value': f'File has {complexity_indicators} branching statements',
                'line': 1,
                'file': file_path,
                'category': 'code_complexity',
                'remediation': 'Reduce conditional complexity',
                'compliance_reference': 'ISO/IEC 25010 Maintainability'
            })
            
        return findings
    
    def calculate_tech_debt(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Calculate technical debt indicators."""
        findings = []
        lines = code.split('\n')
        
        todo_count = 0
        fixme_count = 0
        hack_count = 0
        deprecated_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line_upper = line.upper()
            if 'TODO' in line_upper:
                todo_count += 1
            if 'FIXME' in line_upper:
                fixme_count += 1
            if 'HACK' in line_upper or 'WORKAROUND' in line_upper:
                hack_count += 1
            if '@DEPRECATED' in line_upper or '# DEPRECATED' in line_upper:
                deprecated_count += 1
        
        if todo_count + fixme_count + hack_count > 10:
            debt_score = todo_count + (fixme_count * 2) + (hack_count * 3) + (deprecated_count * 2)
            
            findings.append({
                'type': 'Technical Debt: High Debt Indicators',
                'severity': 'Medium' if debt_score < 20 else 'High',
                'value': f'Technical debt score: {debt_score} (TODO: {todo_count}, FIXME: {fixme_count}, HACK: {hack_count})',
                'line': 1,
                'file': file_path,
                'debt_score': debt_score,
                'category': 'technical_debt',
                'remediation': 'Address TODO/FIXME items and remove hacks',
                'compliance_reference': 'ISO/IEC 25010 Maintainability'
            })
            
        return findings
    
    def analyze(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Run all complexity analyses."""
        findings = []
        # Skip very large files to prevent performance issues
        if len(code) > 50000:
            return findings
        findings.extend(self.calculate_cyclomatic_complexity(code, file_path))
        findings.extend(self.calculate_tech_debt(code, file_path))
        return findings


class BinaryFileAnalyzer:
    """
    Analyzes binary files for compiled code, executables, and embedded secrets.
    """
    
    def __init__(self):
        self.binary_signatures = {
            b'\x7fELF': ('ELF Executable', 'Linux/Unix executable binary'),
            b'MZ': ('PE Executable', 'Windows executable binary'),
            b'\xca\xfe\xba\xbe': ('Mach-O', 'macOS universal binary'),
            b'\xfe\xed\xfa\xce': ('Mach-O 32-bit', 'macOS 32-bit binary'),
            b'\xfe\xed\xfa\xcf': ('Mach-O 64-bit', 'macOS 64-bit binary'),
            b'\xcf\xfa\xed\xfe': ('Mach-O 64-bit LE', 'macOS 64-bit binary (little-endian)'),
            b'PK\x03\x04': ('ZIP/JAR/APK', 'Compressed archive or Java/Android package'),
            b'\xd0\xcf\x11\xe0': ('OLE', 'Microsoft Office document'),
            b'%PDF': ('PDF', 'PDF document'),
            b'\x89PNG': ('PNG', 'PNG image'),
            b'\xff\xd8\xff': ('JPEG', 'JPEG image'),
            b'GIF8': ('GIF', 'GIF image'),
        }
        
        self.suspicious_strings = [
            (b'password', 'Password Reference'),
            (b'secret', 'Secret Reference'),
            (b'api_key', 'API Key Reference'),
            (b'private_key', 'Private Key Reference'),
            (b'BEGIN RSA', 'RSA Key'),
            (b'BEGIN EC', 'EC Key'),
            (b'eyJ', 'JWT Token'),
            (b'Basic ', 'Basic Auth'),
            (b'Bearer ', 'Bearer Token'),
        ]
    
    def is_binary(self, file_path: str) -> bool:
        """Check if file is binary."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return True
                text_chars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
                non_text = chunk.translate(None, text_chars)
                return len(non_text) > len(chunk) * 0.30
        except:
            return False
    
    def identify_binary_type(self, file_path: str) -> Optional[Tuple[str, str]]:
        """Identify binary file type from magic bytes."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                
            for signature, (name, description) in self.binary_signatures.items():
                if header.startswith(signature):
                    return (name, description)
                    
            return ('Unknown Binary', 'Unidentified binary format')
        except:
            return None
    
    def scan_binary_for_secrets(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan binary file for embedded secrets."""
        findings = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024 * 1024)
            
            for pattern, secret_type in self.suspicious_strings:
                if pattern.lower() in content.lower():
                    findings.append({
                        'type': f'Binary Analysis: Embedded {secret_type}',
                        'severity': 'High',
                        'value': f'{secret_type} found embedded in binary',
                        'file': file_path,
                        'category': 'binary_secrets',
                        'remediation': 'Remove embedded credentials from binary. Use environment variables.',
                        'compliance_reference': 'GDPR Art. 32 + NIS2 Art. 21'
                    })
                    
        except Exception as e:
            logger.debug(f"Binary scan failed: {e}")
            
        return findings
    
    def analyze(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze binary file."""
        findings = []
        
        if not os.path.isfile(file_path):
            return []
        
        if not self.is_binary(file_path):
            return []
        
        binary_type = self.identify_binary_type(file_path)
        
        if binary_type:
            name, description = binary_type
            
            if name in ['ELF Executable', 'PE Executable', 'Mach-O', 'Mach-O 32-bit', 'Mach-O 64-bit']:
                findings.append({
                    'type': f'Binary Analysis: {name} Detected',
                    'severity': 'Medium',
                    'value': f'{description} found: {os.path.basename(file_path)}',
                    'file': file_path,
                    'binary_type': name,
                    'category': 'binary_executable',
                    'remediation': 'Review if compiled binaries should be in repository. Consider source-only distribution.',
                    'compliance_reference': 'Supply Chain Security + SLSA Framework'
                })
        
        findings.extend(self.scan_binary_for_secrets(file_path))
        
        return findings


class AdvancedCodeAnalyzerManager:
    """
    Manages all advanced code analyzers and provides unified interface.
    """
    
    def __init__(self):
        self.semantic_analyzer = SemanticCodeAnalyzer()
        self.git_scanner = GitHistoryScanner()
        self.dependency_scanner = DependencyVulnerabilityScanner()
        self.complexity_analyzer = CodeComplexityAnalyzer()
        self.binary_analyzer = BinaryFileAnalyzer()
    
    def analyze_file(self, file_path: str, content: Optional[str] = None, 
                    enable_semantic: bool = True,
                    enable_complexity: bool = True,
                    enable_binary: bool = True) -> List[Dict[str, Any]]:
        """
        Run all applicable analyzers on a file.
        """
        findings = []
        
        if not os.path.isfile(file_path):
            return []
        
        if self.binary_analyzer.is_binary(file_path):
            if enable_binary:
                findings.extend(self.binary_analyzer.analyze(file_path))
            return findings
        
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                return []
        
        if enable_semantic:
            findings.extend(self.semantic_analyzer.analyze(content, file_path))
        
        if enable_complexity:
            findings.extend(self.complexity_analyzer.analyze(content, file_path))
        
        filename = os.path.basename(file_path).lower()
        if filename in ['package.json', 'requirements.txt', 'requirements-dev.txt']:
            findings.extend(self.dependency_scanner.scan(file_path))
        
        return findings
    
    def analyze_repository(self, repo_path: str, 
                          enable_git_history: bool = True,
                          max_git_commits: int = 50) -> List[Dict[str, Any]]:
        """
        Analyze entire repository including Git history.
        """
        findings = []
        
        if enable_git_history:
            findings.extend(self.git_scanner.scan_git_history(repo_path, max_git_commits))
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
            
            for file in files:
                file_path = os.path.join(root, file)
                findings.extend(self.analyze_file(file_path))
        
        return findings
    
    def get_analysis_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of analysis findings."""
        summary = {
            'total_findings': len(findings),
            'by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0},
            'by_category': {},
            'by_type': {}
        }
        
        for finding in findings:
            severity = finding.get('severity', 'Medium')
            if severity in summary['by_severity']:
                summary['by_severity'][severity] += 1
            
            category = finding.get('category', 'other')
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
            
            finding_type = finding.get('type', 'Unknown')
            summary['by_type'][finding_type] = summary['by_type'].get(finding_type, 0) + 1
        
        return summary


advanced_analyzer_manager = AdvancedCodeAnalyzerManager()
