#!/usr/bin/env python3
"""
Cleanup script for Taskra project after Pydantic migration.
This script identifies remaining dictionary-based code patterns
that could be refactored to use models directly.
"""

import os
import re
import argparse
from typing import List, Dict, Tuple, Set

def find_dict_patterns(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Find dictionary access patterns in a file.
    
    Returns:
        List of (line_number, line, pattern) tuples
    """
    patterns = [
        r'\.get\([\'"](\w+)[\'"]\)',  # dict.get("field")
        r'\[[\'"](\w+)[\'"]\]',  # dict["field"]
        r'for \w+ in (\w+)\.(?:items|keys|values)\(\)',  # for k in dict.items()
    ]
    
    findings = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            for pattern in patterns:
                matches = re.findall(pattern, line)
                if matches and not line.strip().startswith('#'):
                    findings.append((i, line.strip(), f"Found dict pattern: {matches}"))
    
    return findings

def find_files(directory: str, extensions: Set[str]) -> List[str]:
    """
    Find all files with the given extensions in the directory.
    
    Args:
        directory: Directory to search
        extensions: Set of file extensions to include
        
    Returns:
        List of file paths
    """
    result = []
    
    for root, _, files in os.walk(directory):
        # Skip tests directory as that's expected to have test-specific patterns
        if '/tests/' in root or root.endswith('/tests'):
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                result.append(os.path.join(root, file))
    
    return result

def analyze_codebase(directory: str) -> Dict[str, List[Tuple[int, str, str]]]:
    """
    Analyze the codebase for dictionary patterns.
    
    Args:
        directory: Root directory to analyze
        
    Returns:
        Dictionary mapping file paths to lists of findings
    """
    py_files = find_files(directory, {'.py'})
    
    results = {}
    
    for file_path in py_files:
        findings = find_dict_patterns(file_path)
        if findings:
            results[file_path] = findings
    
    return results

def main():
    """Run the cleanup analysis."""
    parser = argparse.ArgumentParser(description='Find dictionary patterns in code')
    parser.add_argument('--dir', default='.', help='Directory to analyze')
    parser.add_argument('--output', default='cleanup_report.txt', help='Output file')
    args = parser.parse_args()
    
    print(f"Analyzing codebase in {args.dir}...")
    results = analyze_codebase(args.dir)
    
    total_findings = sum(len(findings) for findings in results.values())
    print(f"Found {total_findings} potential dict patterns in {len(results)} files")
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("# Dictionary Pattern Cleanup Report\n\n")
        f.write(f"Found {total_findings} potential dict patterns in {len(results)} files\n\n")
        
        for file_path, findings in sorted(results.items()):
            relative_path = os.path.relpath(file_path, args.dir)
            f.write(f"## {relative_path}\n\n")
            
            for line_num, line, pattern in findings:
                f.write(f"Line {line_num}: {pattern}\n")
                f.write(f"```\n{line}\n```\n\n")
    
    print(f"Report written to {args.output}")

if __name__ == "__main__":
    main()
