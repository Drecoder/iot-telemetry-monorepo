#!/usr/bin/env python3
"""
UNIVERSAL MONOREPO AUDIT ENGINE
No hardcoded paths. Auto-discovers everything. Works on ANY repository.
OPTIMIZED: 
- JSON: smart truncation (preserves all keys)
- TypeScript: multi-pass CHAOS (micro-prompts)
- Terraform: multi-pass BLAST (micro-prompts for infrastructure)
"""

import os
import subprocess
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import hashlib
import json as json_lib

# ========== CONFIGURATION ==========
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OUTPUT_DIR = Path("./analysis_reports")
MAX_FILE_SIZE = 100 * 1024  # 100KB max per file

# Language detection and prompt mapping (by extension)
LANGUAGE_PROMPTS = {
    ".go": "blast",
    ".ts": "chaos",        # Production TypeScript = CHAOS
    ".tsx": "docs",
    ".js": "simple",
    ".py": "simple",
    ".tf": "blast",        # Terraform = BLAST
    ".rs": "perf",
    ".java": "blast",
    ".rb": "simple",
    ".cs": "blast",
    ".json": "json_config",
}

# Config file patterns (detected by filename, not extension)
CONFIG_PATTERNS = [
    "eslint.config", ".eslintrc", "prettierrc", ".prettierrc",
    "tsconfig", "webpack.config", "vite.config", "rollup.config",
    "babel.config", ".stylelintrc", "commitlint.config",
    "jest.config", "jest.setup", "jest.teardown",
    "playwright.config", "cypress.config", "wdio.conf",
    "nodemon.json", "pm2.json", "ecosystem.config",
    "nginx.conf", "apache.conf", "supervisord.conf",
    "docker-compose", "Dockerfile",
    ".gitignore", ".dockerignore", ".npmignore",
]

# Test file patterns
TEST_PATTERNS = [
    ".test.", ".spec.", "_test", "_spec",
    "test.", "spec.", ".test", ".spec",
    "test/", "spec/", "__tests__",
]

# Directories to ALWAYS ignore
IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", ".env",
    "dist", "build", "target", "out", "bin", "obj",
    "__pycache__", ".pytest_cache", ".cache",
    "coverage", ".terraform", ".idea", ".vscode",
    "vendor", "tmp", "temp", "logs",
    ".next", "nuget", "packages",
    "analysis_reports", ".nx", "istio-1.30.0",
}

# File patterns to skip
SKIP_PATTERNS = [
    "node_modules",
    ".git",
    "__pycache__",
    ".event-schemas",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.sum",
    ".DS_Store",
    "Thumbs.db",
    "analysis_reports",
    ".md",
    ".txt",
    ".log",
    "run_analysis.py",
    "compile_reports.py",
    "file-map.json",  # Nx internal cache
    "coverage/",      # Coverage reports
    "*.test.js",      # Test files
]

# ========== PROMPTS ==========
PROMPTS = {
    "blast": """You are a Senior Software Architect. Review the following code file. Map out exact data-flow and internal dependencies present in this file. If I modify core data structures or types in this file, what is the 'blast radius' of that change? Which downstream functions, modules, or API contracts in a monorepo structure will explicitly require updates or break? Provide a structured list of touchpoints, referencing specific functions and line numbers where possible.""",
    
    "simple": """You are a hyper-pragmatic Staff Engineer who aggressively despises technical debt, over-engineering, and premature abstractions. Review the provided code file. Identify any 'clever' logic, redundant memory allocations, unnecessarily deep if-else nesting, or complex patterns that could be written more simply. Point out exact locations (line/function) that introduce cognitive overhead, and provide dead-simple refactored versions that a junior engineer could understand instantly without losing performance.""",
    
    "chaos": """You are a cynical QA Automation and Site Reliability Engineer. Perform a 'chaos analysis' on the following code. Do NOT look at the happy path. Instead, tell me exactly how this code fails. If the database drops mid-transaction, if an external API payload arrives malformed or massive, or if a network timeout occurs, where will this code panic, leak memory, or hang indefinitely? Point out the exact lines missing robust error handling or defensive guards. Be specific.""",
    
    "perf": """You are a Performance Engineer specialized in high-throughput systems. Analyze the time complexity (Big-O) and space complexity of the data transformations, loops, and logic in this file. Are there any hidden O(N^2) traps, unnecessary struct copying instead of passing pointers, or redundant string allocations? Tell me how to optimize execution speed and minimize RAM/CPU footprint using better logic rather than adding complex concurrency.""",
    
    "docs": """You are a Technical Writer and Developer Advocate. Generate clean, idiomatic inline documentation (GoDoc for Go, JSDoc for TypeScript) for the following code. Do not just repeat function names. Focus on documenting the 'why' behind logic, constraints of input parameters, and what return values represent. Provide the fully documented version of the code ready to be dropped back into the IDE, preserving existing functionality.""",
    
    "governance": """You are a Senior Platform Engineer focused on developer productivity and governance. Review this configuration file.

Answer these specific questions:

1. **What rules are disabled?** List any security or quality rules that are turned off.

2. **What's too strict?** Identify configurations that cause developer friction.

3. **What's missing?** What common rules or plugins are absent?

4. **Blind spots:** Any ignore patterns hiding critical files?

5. **Portability issues:** Does this config rely on environment assumptions?

6. **Recommendations:** 2-3 specific improvements.

Keep response under 300 words.""",

    "json_config": """You are a Configuration Analyst. Review this JSON configuration file.

Answer these specific questions (be VERY brief, under 150 words total):

1. **What is this config for?** (tsconfig, package.json, etc.) - 1 sentence

2. **Key settings:** List the 3 most important settings and their values.

3. **Potential issues:**
   - Any paths that might break in different environments?
   - Any deprecated or risky options?
   - Any missing recommended settings?

4. **Recommendations:** 1 specific improvement.

Keep response concise. Focus only on what matters."""
}

# ========== SMART TRUNCATION FUNCTIONS ==========

def simplify_json_smart(content: str, max_chars: int = 8000) -> str:
    """Simplify JSON by preserving all keys but truncating long values."""
    try:
        data = json_lib.loads(content)
        
        def truncate_values(obj, depth=0):
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    if isinstance(v, str) and len(v) > 150:
                        result[k] = v[:150] + "...[TRUNCATED]"
                    elif isinstance(v, list) and len(v) > 15:
                        result[k] = v[:15] + ["... [TRUNCATED]"]
                    elif isinstance(v, (dict, list)):
                        result[k] = truncate_values(v, depth + 1)
                    else:
                        result[k] = v
                return result
            elif isinstance(obj, list) and len(obj) > 20:
                return obj[:20] + ["... [TRUNCATED]"]
            return obj
        
        simplified = truncate_values(data)
        result = json_lib.dumps(simplified, indent=2)
        
        if len(result) > max_chars:
            result = result[:max_chars] + "\n... [FULL OUTPUT TRUNCATED]"
        return result
    except json_lib.JSONDecodeError as e:
        return f"ERROR parsing JSON: {e}\n{content[:max_chars]}"
    except Exception as e:
        return f"ERROR: {e}\n{content[:max_chars]}"

def simplify_ts_for_chaos(content: str, max_lines: int = 150) -> str:
    """Smart TypeScript simplification for CHAOS analysis."""
    lines = content.split('\n')
    simplified = []
    i = 0
    total_lines = len(lines)
    
    while i < min(total_lines, max_lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.startswith('import ') or stripped.startswith('export import'):
            if len(line) > 150:
                line = line[:150] + "...'"
            simplified.append(line)
            i += 1
            continue
        
        if stripped.startswith('export '):
            if len(line) > 200:
                brace_idx = line.find('{')
                if brace_idx > 0:
                    line = line[:brace_idx] + ' { ... }'
                else:
                    line = line[:200] + "..."
            simplified.append(line)
            i += 1
            continue
        
        if stripped.startswith('type ') or stripped.startswith('interface '):
            brace_idx = line.find('{')
            if brace_idx > 0:
                line = line[:brace_idx] + ' { ... }'
            simplified.append(line)
            i += 1
            continue
        
        if stripped.startswith('class '):
            brace_idx = line.find('{')
            if brace_idx > 0:
                line = line[:brace_idx] + ' { ... }'
            simplified.append(line)
            i += 1
            continue
        
        if ('function ' in stripped or 
            ('(' in stripped and ')' in stripped and ('=>' in stripped or ':' in stripped))):
            
            if len(line) > 200:
                line = line[:200] + "..."
            simplified.append(line)
            
            if '{' in line:
                brace_count = line.count('{') - line.count('}')
                i += 1
                while i < total_lines and brace_count > 0:
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1
                simplified.append("  // ... function body truncated ...")
                continue
            i += 1
            continue
        
        if 'try' in stripped or 'catch' in stripped or 'finally' in stripped:
            if len(line) > 150:
                line = line[:150] + "..."
            simplified.append(line)
            i += 1
            continue
        
        if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            if len(line) > 150:
                line = line[:150] + "..."
            simplified.append(line)
            i += 1
            continue
        
        if '{' in stripped:
            if len(line) < 100:
                simplified.append(line)
            brace_count = 1
            i += 1
            while i < total_lines and brace_count > 0:
                brace_count += lines[i].count('{') - lines[i].count('}')
                i += 1
            simplified.append("  // ... implementation truncated ...")
            continue
        
        if any(keyword in stripped for keyword in ['if ', 'else', 'switch', 'for ', 'while ']):
            if len(line) > 150:
                line = line[:150] + "..."
            simplified.append(line)
            i += 1
            continue
        
        if 'return' in stripped:
            if len(line) > 100:
                line = line[:100] + "..."
            simplified.append(line)
            i += 1
            continue
        
        if stripped == '' or stripped in ['{', '}', '});', '];']:
            i += 1
            continue
        
        if len(line) > 150:
            line = line[:150] + "..."
        simplified.append(line)
        i += 1
    
    result = '\n'.join(simplified)
    
    if total_lines > max_lines:
        result += f"\n\n// [CHAOS: Preserved structure from {total_lines} lines]"
    
    return result

def simplify_terraform(content: str, max_resources: int = 8) -> str:
    """Smart Terraform simplification - extract key resources."""
    lines = content.split('\n')
    simplified = []
    i = 0
    resource_count = 0
    
    while i < len(lines) and resource_count <= max_resources:
        line = lines[i]
        stripped = line.strip()
        
        # Keep provider blocks
        if stripped.startswith('provider ') or stripped.startswith('terraform {'):
            simplified.append(line)
            i += 1
            continue
        
        # Keep variable blocks (signature only)
        if stripped.startswith('variable '):
            brace_idx = line.find('{')
            if brace_idx > 0:
                simplified.append(line[:brace_idx] + ' { ... }')
            else:
                simplified.append(line)
            i += 1
            continue
        
        # Keep resource blocks
        if stripped.startswith('resource '):
            simplified.append(line)
            brace_count = line.count('{') - line.count('}')
            i += 1
            # Skip to end of resource block
            while i < len(lines) and brace_count > 0:
                brace_count += lines[i].count('{') - lines[i].count('}')
                i += 1
            simplified.append("  # ... resource configuration ...")
            resource_count += 1
            continue
        
        # Keep output blocks
        if stripped.startswith('output '):
            brace_idx = line.find('{')
            if brace_idx > 0:
                simplified.append(line[:brace_idx] + ' { ... }')
            else:
                simplified.append(line)
            i += 1
            continue
        
        # Keep comments
        if stripped.startswith('#') or stripped.startswith('//'):
            simplified.append(line)
            i += 1
            continue
        
        i += 1
    
    result = '\n'.join(simplified)
    
    if resource_count >= max_resources:
        result += f"\n\n# [Terraform: First {max_resources} resources shown]"
    
    return result

# ========== MULTI-PASS ANALYSIS FUNCTIONS ==========

def chaos_multipass(content: str, file_path: Path, output_dir: Path, out_file: str, root_dir: Path) -> bool:
    """Multi-pass CHAOS analysis for TypeScript."""
    results = []
    
    micro_prompts = [
        ("error_handling", "Q1: Does this code have error handling (try/catch, .catch(), if err)? Answer YES/NO. 1 sentence."),
        ("timeouts", "Q2: Does this code handle timeouts (setTimeout, Promise.race)? Answer YES/NO. 1 sentence."),
        ("input_validation", "Q3: Does this code validate input parameters? Answer YES/NO. 1 sentence."),
        ("crash_risk", "Q4: What is the #1 way this code could crash in production? Answer in 15 words."),
        ("null_safety", "Q5: Does this code check for null/undefined? Answer YES/NO. 1 sentence."),
        ("async_errors", "Q6: Are async/await errors caught? Answer YES/NO. 1 sentence."),
        ("recommendation", "Q7: What is the single most important fix? Answer in 15 words."),
    ]
    
    for name, prompt in micro_prompts:
        print(f"      🔍 CHAOS pass: {name}...", flush=True)
        response = call_ollama(prompt, content, MODEL, ".ts", timeout=30)
        if response:
            results.append(f"**{name.replace('_', ' ').title()}:** {response.strip()}")
        else:
            results.append(f"**{name.replace('_', ' ').title()}:** [Analysis timeout]")
    
    combined = "# CHAOS Analysis (Multi-Pass)\n\n" + "\n\n".join(results)
    
    try:
        rel_path = file_path.relative_to(root_dir)
        display_path = str(rel_path)
    except:
        display_path = str(file_path)
    
    out_path = output_dir / out_file
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# Qwen Analysis for {display_path}\n")
            f.write(f"# Lens: CHAOS (Multi-Pass)\n")
            f.write(f"# Source: {file_path}\n\n")
            f.write(combined)
        return True
    except Exception as e:
        print(f"      ❌ Write error: {e}")
        return False

def terraform_blast_multipass(content: str, file_path: Path, output_dir: Path, out_file: str, root_dir: Path) -> bool:
    """Multi-pass BLAST analysis for Terraform files."""
    results = []
    
    # Simplify Terraform content
    simplified = simplify_terraform(content)
    
    micro_prompts = [
        ("resources", "Q1: List the main resource types in this Terraform file (VPC, EKS, DynamoDB, etc.). 1 sentence."),
        ("dependencies", "Q2: What are the key dependencies between resources? (Which resources depend on which?) 1 sentence."),
        ("blast_radius", "Q3: Which resource would cause the most damage if deleted or misconfigured? 1 sentence."),
        ("variables", "Q4: What variables are required to deploy this infrastructure? 1 sentence."),
        ("risk", "Q5: What is the highest risk configuration in this file? 1 sentence."),
        ("recommendation", "Q6: What is the single most important improvement? 1 sentence."),
    ]
    
    for name, prompt in micro_prompts:
        print(f"      🔍 BLAST pass: {name}...", flush=True)
        response = call_ollama(prompt, simplified, MODEL, ".tf", timeout=45)
        if response:
            results.append(f"**{name.replace('_', ' ').title()}:** {response.strip()}")
        else:
            results.append(f"**{name.replace('_', ' ').title()}:** [Analysis timeout]")
    
    combined = "# BLAST Analysis (Multi-Pass - Terraform)\n\n" + "\n\n".join(results)
    
    try:
        rel_path = file_path.relative_to(root_dir)
        display_path = str(rel_path)
    except:
        display_path = str(file_path)
    
    out_path = output_dir / out_file
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# Qwen Analysis for {display_path}\n")
            f.write(f"# Lens: BLAST (Multi-Pass - Terraform)\n")
            f.write(f"# Source: {file_path}\n\n")
            f.write(combined)
        return True
    except Exception as e:
        print(f"      ❌ Write error: {e}")
        return False

# ========== UTILITIES ==========

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    text = ansi_escape.sub('', text)
    text = re.sub(r'.\x08', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text

def is_test_file(file_path: Path) -> bool:
    name = file_path.name.lower()
    for pattern in TEST_PATTERNS:
        if pattern in name:
            return True
    parts = file_path.parts
    if "test" in parts or "tests" in parts or "__tests__" in parts:
        return True
    return False

def should_skip_path(file_path: Path) -> bool:
    path_str = str(file_path).lower()
    parts = file_path.parts
    
    for ignore_dir in IGNORE_DIRS:
        if ignore_dir in parts:
            return True
    
    for pattern in SKIP_PATTERNS:
        if pattern in path_str:
            return True
    
    return False

def get_display_path(file_path: Path, root_dir: Path, max_len: int = 60) -> str:
    try:
        rel_path = file_path.relative_to(root_dir)
        path_str = str(rel_path).replace('\\', '/')
        
        if len(path_str) <= max_len:
            return path_str
        
        parts = path_str.split('/')
        if len(parts) > 2:
            first = parts[0]
            last = '/'.join(parts[-2:])
            return f"{first}/.../{last}"
        
        return "..." + path_str[-(max_len-3):]
    except:
        return file_path.name

def get_prompt_key(file_path: Path) -> str:
    name = file_path.name.lower()
    ext = file_path.suffix.lower()
    
    if ext == ".json":
        return "json_config"
    
    if is_test_file(file_path):
        return "simple"
    
    for pattern in CONFIG_PATTERNS:
        if pattern in name:
            return "governance"
    
    if "mock" in name or "fake" in name or "stub" in name:
        return "simple"
    
    if ext == ".ts":
        return "chaos"
    
    if ext == ".tf":
        return "blast"
    
    path_str = str(file_path).lower()
    if "main" in name or "handler" in path_str or "controller" in path_str:
        if ext in [".go", ".rs", ".java"]:
            return "blast"
    
    if "scanner" in path_str or "scan" in path_str:
        return "perf"
    
    if ext in LANGUAGE_PROMPTS:
        return LANGUAGE_PROMPTS[ext]
    
    return "simple"

def read_file_safe(file_path: Path, max_chars: int = 50000) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(max_chars)
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
                return f.read(max_chars)
        except Exception as e:
            return f"ERROR: Cannot decode file - {e}"
    except Exception as e:
        return f"ERROR: Cannot read file - {e}"

def call_ollama(prompt: str, content: str, model: str, file_ext: str = "", timeout: int = 30) -> Optional[str]:
    full_prompt = f"{prompt}\n\n{content}"
    cmd = ["ollama", "run", model]
    
    if len(full_prompt) > 60000:
        full_prompt = full_prompt[:60000] + "\n\n...[TRUNCATED]..."
    
    for attempt in range(2):
        try:
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                check=False
            )
            if result.returncode == 0 and result.stdout and len(result.stdout) > 10:
                return strip_ansi(result.stdout)
            else:
                if attempt < 1:
                    time.sleep(2)
                    continue
                return None
        except subprocess.TimeoutExpired:
            if attempt < 1:
                time.sleep(2)
                continue
            return None
        except Exception as e:
            if attempt < 1:
                time.sleep(2)
                continue
            return None
    
    return None

def process_single_file(file_info: Tuple[Path, str, str], model: str, output_dir: Path, index: int, total: int, root_dir: Path) -> bool:
    file_path, out_file, prompt_key = file_info
    ext = file_path.suffix.lower()
    is_test = is_test_file(file_path)
    
    display_path = get_display_path(file_path, root_dir)
    print(f"   [{index}/{total}] 🧠 Analyzing: {display_path} (Lens: {prompt_key.upper()})", flush=True)
    
    content = read_file_safe(file_path)
    
    if not content or len(content) < 10:
        print(f"      ⏭️ Skipping (empty or unreadable)")
        return False
    
    original_size = len(content)
    
    # JSON files
    if ext == ".json":
        content = simplify_json_smart(content)
        print(f"      📦 JSON Smart: {original_size} → {len(content)} chars", flush=True)
        
        system_prompt = PROMPTS.get(prompt_key, PROMPTS["simple"])
        user_message = f"### FILE: {display_path} ###\n{content}\n"
        response = call_ollama(system_prompt, user_message, model, ext, timeout=45)
        
        if response is None:
            print(f"      ❌ FAILED")
            return False
        
        out_path = output_dir / out_file
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"# Qwen Analysis for {display_path}\n")
                f.write(f"# Lens: {prompt_key.upper()}\n")
                f.write(f"# Type: {'TEST' if is_test else 'SOURCE'}\n")
                f.write(f"# Source: {file_path}\n\n")
                f.write(response)
            return True
        except Exception as e:
            print(f"      ❌ Write error: {e}")
            return False
    
    # TypeScript CHAOS - multi-pass
    elif ext == ".ts" and not is_test:
        content = simplify_ts_for_chaos(content, max_lines=150)
        print(f"      🔥 TS for CHAOS: {original_size} → {len(content)} chars", flush=True)
        return chaos_multipass(content, file_path, output_dir, out_file, root_dir)
    
    # TypeScript test files - SIMPLE
    elif ext == ".ts" and is_test:
        content = simplify_ts_for_chaos(content, max_lines=150)
        print(f"      📝 TS Test: {original_size} → {len(content)} chars", flush=True)
        
        system_prompt = PROMPTS.get("simple", PROMPTS["simple"])
        user_message = f"### FILE: {display_path} ###\n{content}\n"
        response = call_ollama(system_prompt, user_message, model, ext, timeout=60)
        
        if response is None:
            print(f"      ❌ FAILED")
            return False
        
        out_path = output_dir / out_file
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"# Qwen Analysis for {display_path}\n")
                f.write(f"# Lens: SIMPLE\n")
                f.write(f"# Type: TEST\n")
                f.write(f"# Source: {file_path}\n\n")
                f.write(response)
            return True
        except Exception as e:
            print(f"      ❌ Write error: {e}")
            return False
    
    # Terraform BLAST - multi-pass
    elif ext == ".tf":
        print(f"      🏗️ Terraform: {original_size} chars", flush=True)
        return terraform_blast_multipass(content, file_path, output_dir, out_file, root_dir)
    
    # Other files - single pass
    else:
        system_prompt = PROMPTS.get(prompt_key, PROMPTS["simple"])
        user_message = f"### FILE: {display_path} ###\n{content}\n"
        response = call_ollama(system_prompt, user_message, model, ext, timeout=60)
        
        if response is None:
            print(f"      ❌ FAILED")
            return False
        
        out_path = output_dir / out_file
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"# Qwen Analysis for {display_path}\n")
                f.write(f"# Lens: {prompt_key.upper()}\n")
                f.write(f"# Type: {'TEST' if is_test else 'SOURCE'}\n")
                f.write(f"# Source: {file_path}\n\n")
                f.write(response)
            return True
        except Exception as e:
            print(f"      ❌ Write error: {e}")
            return False

def discover_files(root_dir: Path) -> List[Tuple[Path, str, str]]:
    files_to_process = []
    seen_paths = set()
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirpath_obj = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        
        for filename in filenames:
            file_path = dirpath_obj / filename
            
            if should_skip_path(file_path):
                continue
            
            name = filename.lower()
            is_config = any(pattern in name for pattern in CONFIG_PATTERNS)
            
            ext = file_path.suffix.lower()
            if ext not in LANGUAGE_PROMPTS and not is_config:
                continue
            
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
                if file_path.stat().st_size < 50:
                    continue
            except OSError:
                continue
            
            prompt_key = get_prompt_key(file_path)
            
            try:
                rel_path = file_path.relative_to(root_dir)
                path_str = str(rel_path).replace('\\', '_').replace('/', '_').replace('.', '_')
                path_str = re.sub(r'[^a-zA-Z0-9_-]', '_', path_str)
                if len(path_str) > 100:
                    parts = path_str.split('_')
                    if len(parts) > 2:
                        path_str = f"{parts[0]}_{parts[1]}_..._{parts[-1]}"
                    else:
                        path_str = path_str[:50] + '...' + path_str[-40:]
                safe_name = f"{prompt_key}_{path_str}.md"
            except ValueError:
                path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                safe_name = f"{prompt_key}_{path_hash}_{file_path.stem}.md"
            
            if safe_name in seen_paths:
                path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:4]
                safe_name = f"{prompt_key}_{path_hash}_{safe_name[:50]}"
            seen_paths.add(safe_name)
            
            files_to_process.append((file_path, safe_name, prompt_key))
    
    return files_to_process

def print_lens_distribution(files: List[Tuple[Path, str, str]]) -> None:
    lens_counts = defaultdict(int)
    test_count = 0
    prod_ts_count = 0
    json_count = 0
    tf_count = 0
    
    for file_path, _, prompt_key in files:
        lens_counts[prompt_key] += 1
        if is_test_file(file_path):
            test_count += 1
        elif file_path.suffix.lower() == ".ts":
            prod_ts_count += 1
        elif file_path.suffix.lower() == ".json":
            json_count += 1
        elif file_path.suffix.lower() == ".tf":
            tf_count += 1
    
    print("\n📊 Lens distribution:")
    lens_order = ["json_config", "governance", "blast", "chaos", "perf", "simple", "docs"]
    for lens in lens_order:
        if lens in lens_counts:
            print(f"   {lens.upper()}: {lens_counts[lens]} files")
    
    if json_count > 0:
        print(f"\n   📦 JSON files: {json_count} (smart truncation)")
    if prod_ts_count > 0:
        print(f"   🔥 Production .ts files: {prod_ts_count} (CHAOS - multi-pass)")
    if tf_count > 0:
        print(f"   🏗️ Terraform files: {tf_count} (BLAST - multi-pass)")
    if test_count > 0:
        print(f"   🧪 Test files: {test_count} (SIMPLE lens)")

# ========== MAIN ==========

def main():
    print("\n" + "=" * 60)
    print("🔍 UNIVERSAL MONOREPO AUDIT ENGINE")
    print("   JSON: Smart truncation")
    print("   .ts: Multi-pass CHAOS")
    print("   .tf: Multi-pass BLAST")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        repo_path = Path(sys.argv[1])
    else:
        repo_path = Path.cwd()
    
    if not repo_path.exists():
        print(f"❌ Repository path not found: {repo_path}")
        return
    
    print(f"\n📂 Target repository: {repo_path.resolve()}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("✅ Ollama detected")
    except:
        print("❌ Ollama not found")
        return
    
    print("\n🔎 Discovering code files...")
    all_files = discover_files(repo_path)
    
    if not all_files:
        print("❌ No supported code files found.")
        return
    
    print(f"✅ Found {len(all_files)} code files")
    
    print("\n📊 Breakdown by file type:")
    ext_counts = defaultdict(int)
    for file_path, _, _ in all_files:
        ext = file_path.suffix.lower()
        ext_counts[ext] += 1
    
    for ext, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True):
        ext_name = ext if ext else "(no extension)"
        print(f"   {ext_name}: {count} files")
    
    print_lens_distribution(all_files)
    
    print(f"\n🚀 Processing {len(all_files)} files one at a time...\n")
    
    total_success = 0
    total_failed = 0
    
    for i, file_info in enumerate(all_files, 1):
        success = process_single_file(file_info, MODEL, OUTPUT_DIR, i, len(all_files), repo_path)
        if success:
            total_success += 1
        else:
            total_failed += 1
    
    print("\n" + "=" * 60)
    print("✨ AUDIT COMPLETE")
    print("=" * 60)
    print(f"📊 Files processed: {total_success + total_failed}")
    print(f"✅ Successful: {total_success}")
    print(f"❌ Failed: {total_failed}")
    print(f"📁 Reports saved in: {OUTPUT_DIR.resolve()}")
    
    if total_success > 0:
        print("\n📋 Next step: python compile_reports.py")

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
        sys.stderr.reconfigure(encoding="utf-8", errors="ignore")
    main()