#!/usr/bin/env python3
"""
MONOREPO REPORT COMPILER - Fixed with Retry Logic and Better Timeouts
Now recognizes JSON_CONFIG reports properly.
"""

import os
import re
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict

# ========== CONFIGURATION ==========
REPORTS_DIR = Path("./analysis_reports")
OUTPUT_MASTER = Path("./MASTER_ARCHITECTURE_REPORT.md")
OUTPUT_EXECUTIVE = Path("./EXECUTIVE_SUMMARY.md")
OUTPUT_ROADMAP = Path("./REMEDIATION_ROADMAP.md")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

# Conservative limits to prevent timeouts
CHUNK_SIZE_LIMIT = 15000
TIMEOUT_PER_CHUNK = 180
MAX_RETRIES = 3

# Priority order for report types (lower number = higher priority)
REPORT_PRIORITY = {
    "blast": 1,
    "chaos": 2,
    "perf": 3,
    "simple": 4,
    "docs": 5,
    "governance": 6,
    "json_config": 7,      # 👈 ADDED
}

# ========== UTILITIES ==========

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    text = ansi_escape.sub('', text)
    text = re.sub(r'.\x08', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text

def classify_report(filename: str) -> Tuple[str, int]:
    """Classify report by filename prefix and return priority."""
    for prefix, priority in REPORT_PRIORITY.items():
        if filename.startswith(prefix):
            return (prefix, priority)
    # Also check for json_config in filename (handles variations)
    if "json_config" in filename:
        return ("json_config", REPORT_PRIORITY["json_config"])
    return ("other", 99)

def extract_metadata_from_report(report_path: Path) -> Tuple[str, str]:
    """Extract chunk/layer and source file from report metadata."""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            first_lines = f.read(1000)
    except:
        first_lines = ""
    
    # Try to find Layer (from the report content)
    chunk_match = re.search(r'# Layer:\s*(.+)', first_lines)
    if chunk_match:
        chunk = chunk_match.group(1).strip()
    else:
        # Fallback: derive chunk from filename
        name = report_path.name
        if name.startswith("blast"):
            chunk = "infrastructure"
        elif name.startswith("chaos"):
            chunk = "ingest_services"
        elif name.startswith("simple"):
            chunk = "business_logic"
        elif name.startswith("docs"):
            chunk = "tests"
        elif name.startswith("governance"):
            chunk = "configs"
        elif name.startswith("json_config"):
            chunk = "configs"
        else:
            chunk = "unknown"
    
    # Extract source file path
    file_match = re.search(r'# Source:\s*(.+?)(?:\n|$)', first_lines)
    if file_match:
        file_path = file_match.group(1).strip()
        file_path = file_path.replace("./", "")
    else:
        file_path = report_path.stem.replace("_", "/")
    
    return (chunk, file_path)

def sort_reports(report_files: List[Path]) -> List[Path]:
    """Sort reports by: chunk name, then file path, then report priority."""
    reports_with_metadata = []
    for report in report_files:
        chunk, file_path = extract_metadata_from_report(report)
        report_type, priority = classify_report(report.name)
        reports_with_metadata.append({
            "path": report,
            "chunk": chunk,
            "file_path": file_path,
            "report_type": report_type,
            "priority": priority,
        })
    
    # Sort: by chunk, then by priority, then by file_path
    reports_with_metadata.sort(key=lambda x: (
        x["chunk"],
        x["priority"],
        x["file_path"]
    ))
    
    return [r["path"] for r in reports_with_metadata]

def call_ollama_with_retry(prompt: str, context: str, timeout: int = TIMEOUT_PER_CHUNK, retries: int = MAX_RETRIES) -> Optional[str]:
    """Call Ollama with retry logic and exponential backoff."""
    full_prompt = f"{prompt}\n\n{context}"
    cmd = ["ollama", "run", MODEL]
    
    for attempt in range(retries):
        try:
            print(f"      Attempt {attempt + 1}/{retries}...", end=" ", flush=True)
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                check=False
            )
            
            if result.returncode == 0 and result.stdout and len(result.stdout.strip()) > 50:
                print("✅")
                return strip_ansi(result.stdout)
            else:
                error_msg = result.stderr[:100] if result.stderr else "empty response"
                print(f"❌ (Exit {result.returncode}, {error_msg})")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout after {timeout}s")
            
        except Exception as e:
            print(f"💥 Exception: {str(e)[:50]}")
        
        if attempt < retries - 1:
            wait_time = 2 ** attempt
            print(f"      Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return None

def summarize_chunk_simple(chunk_name: str, chunk_content: List[str]) -> Optional[str]:
    """Simplified chunk summarization with smaller context."""
    combined = "\n\n".join(chunk_content)
    if len(combined) > CHUNK_SIZE_LIMIT:
        print(f"   ⚠️ Truncating from {len(combined):,} to {CHUNK_SIZE_LIMIT:,} chars")
        combined = combined[:CHUNK_SIZE_LIMIT] + "\n\n...[TRUNCATED]..."
    
    prompt = f"""Summarize the '{chunk_name}' layer code analysis.

Give me:
- What this layer does (1 sentence)
- Critical issues found (bullet points, max 3)
- One key recommendation

Keep under 200 words. Be direct."""
    
    print(f"   🧠 Summarizing '{chunk_name}' ({len(combined):,} chars)...")
    return call_ollama_with_retry(prompt, combined)

def compile_master_report() -> Tuple[bool, str, Dict[str, List[str]]]:
    """Compile master report and extract per-chunk content."""
    
    if not REPORTS_DIR.exists():
        print(f"❌ Reports directory not found: {REPORTS_DIR}")
        return False, "", {}
    
    report_files = list(REPORTS_DIR.glob("*.md"))
    if not report_files:
        print("❌ No report files found")
        return False, "", {}
    
    print(f"📊 Found {len(report_files)} report files")
    sorted_reports = sort_reports(report_files)
    print(f"📋 Sorted into logical order")
    
    master_content = []
    chunk_contents = defaultdict(list)
    
    # Header
    master_content.append("# MONOREPO ARCHITECTURE MASTER REPORT\n\n")
    master_content.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    master_content.append("---\n\n")
    
    # Table of Contents
    master_content.append("## 📑 Table of Contents\n\n")
    current_chunk = None
    toc_entries = []
    for report_path in sorted_reports:
        chunk, file_path = extract_metadata_from_report(report_path)
        if chunk != current_chunk:
            current_chunk = chunk
            anchor = chunk.lower().replace(" ", "_").replace("/", "_")
            toc_entries.append(f"- **[📁 {chunk}](#{anchor})**")
        toc_entries.append(f"  - [{report_path.name}](#{report_path.stem.lower().replace(' ', '_')})")
    master_content.append("\n".join(toc_entries))
    master_content.append("\n\n---\n\n")
    
    # Report contents
    current_chunk = None
    chunk_file_count = defaultdict(int)
    
    for report_path in sorted_reports:
        chunk, file_path = extract_metadata_from_report(report_path)
        chunk_file_count[chunk] += 1
        
        if chunk != current_chunk:
            current_chunk = chunk
            anchor = chunk.lower().replace(" ", "_").replace("/", "_")
            master_content.append(f"\n<a id=\"{anchor}\"></a>\n")
            master_content.append(f"## 📁 CHUNK: {chunk}\n\n")
        
        anchor_id = report_path.stem.lower().replace(' ', '_').replace('.', '_')
        master_content.append(f"\n<a id=\"{anchor_id}\"></a>\n")
        master_content.append(f"### 📄 {report_path.name}\n\n")
        master_content.append(f"**Source**: `{file_path}`\n\n---\n\n")
        
        try:
            with open(report_path, 'r', encoding='utf-8') as src:
                content = src.read()
                lines = content.split('\n')
                if lines and lines[0].startswith('# Qwen Analysis'):
                    content = '\n'.join(lines[3:])
                master_content.append(content)
                
                truncated = content[:5000]
                chunk_contents[chunk].append(f"### {report_path.name}\n{truncated}")
        except Exception as e:
            master_content.append(f"*Error: {e}*\n")
        
        master_content.append("\n\n---\n\n")
    
    full_content = "".join(master_content)
    
    with open(OUTPUT_MASTER, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print(f"✅ Master report compiled: {OUTPUT_MASTER} ({OUTPUT_MASTER.stat().st_size / 1024:.1f} KB)")
    
    return True, full_content, chunk_contents

def generate_combined_summary(chunk_summaries: Dict[str, str]) -> Optional[str]:
    """Generate final executive summary from all chunk summaries."""
    
    if not chunk_summaries:
        return None
    
    combined = "\n\n---\n\n".join([f"## {chunk}\n{summary}" for chunk, summary in chunk_summaries.items()])
    
    prompt = """Based on these layer summaries, produce an Executive Summary with:

1. **Overall Health** (2 sentences)
2. **Top 5 Issues** (ranked)
3. **Key Recommendations** (this week / this month)

Keep under 500 words."""
    
    print(f"\n📝 Generating final executive summary from {len(chunk_summaries)} layers...")
    return call_ollama_with_retry(prompt, combined, timeout=240)

def generate_roadmap_from_summaries(chunk_summaries: Dict[str, str]) -> Optional[str]:
    """Generate remediation roadmap from chunk summaries."""
    
    if not chunk_summaries:
        return None
    
    combined = "\n\n".join([f"{chunk}:\n{summary}" for chunk, summary in chunk_summaries.items()])
    
    prompt = """Create a Remediation Roadmap:

**Immediate (Week 1):** Critical fixes
**Short-term (Month):** High-impact improvements  
**Long-term (Quarter):** Strategic changes

For each: Priority (P0-P2) | Effort (S/M/L)"""
    
    print(f"\n🗺️ Generating remediation roadmap...")
    return call_ollama_with_retry(prompt, combined, timeout=240)

# ========== MAIN ==========

def main():
    print("\n" + "=" * 60)
    print("🔨 MONOREPO REPORT COMPILER (Fixed)")
    print("=" * 60 + "\n")
    
    # Check Ollama
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("✅ Ollama detected\n")
        ollama_available = True
    except:
        print("⚠️ Ollama not found\n")
        ollama_available = False
    
    # Step 1: Compile master report
    print("📁 STEP 1: Compiling reports...\n")
    success, master_content, chunk_contents = compile_master_report()
    
    if not success:
        print("❌ Compilation failed")
        return
    
    # Step 2: Summarize each chunk
    if ollama_available and chunk_contents:
        print("\n📊 STEP 2: Summarizing Chunks\n")
        
        chunk_summaries = {}
        
        for chunk_name, content_list in chunk_contents.items():
            print(f"\n📁 Chunk: {chunk_name}")
            print(f"   📄 Contains {len(content_list)} report(s)")
            
            summary = summarize_chunk_simple(chunk_name, content_list)
            
            if summary:
                chunk_summaries[chunk_name] = summary
                print(f"   ✅ Summarized successfully")
            else:
                print(f"   ❌ Failed after {MAX_RETRIES} attempts")
                chunk_summaries[chunk_name] = f"*Failed to summarize {chunk_name}*"
        
        # Step 3: Generate final outputs
        if chunk_summaries:
            print("\n" + "=" * 60)
            print("📊 STEP 3: Generating Final Outputs")
            print("=" * 60)
            
            # Executive summary
            exec_summary = generate_combined_summary(chunk_summaries)
            if exec_summary:
                full_summary = f"""# EXECUTIVE SUMMARY: Monorepo Architecture Audit

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Layers summarized: {len(chunk_summaries)}*

---

{exec_summary}

---

## Layer Summaries

{chr(10).join([f"### {chunk}\n{summary}\n" for chunk, summary in chunk_summaries.items()])}
"""
                with open(OUTPUT_EXECUTIVE, 'w', encoding='utf-8') as f:
                    f.write(full_summary)
                print(f"✅ Executive summary saved: {OUTPUT_EXECUTIVE}")
            
            # Remediation roadmap
            roadmap = generate_roadmap_from_summaries(chunk_summaries)
            if roadmap:
                full_roadmap = f"""# REMEDIATION ROADMAP

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

{roadmap}
"""
                with open(OUTPUT_ROADMAP, 'w', encoding='utf-8') as f:
                    f.write(full_roadmap)
                print(f"✅ Remediation roadmap saved: {OUTPUT_ROADMAP}")
    
    # Final output
    print("\n" + "=" * 60)
    print("✨ COMPLETE! Generated files:")
    print("=" * 60)
    
    if OUTPUT_MASTER.exists():
        size = OUTPUT_MASTER.stat().st_size / 1024
        print(f"   📄 {OUTPUT_MASTER} ({size:.1f} KB)")
    if OUTPUT_EXECUTIVE.exists():
        size = OUTPUT_EXECUTIVE.stat().st_size / 1024
        print(f"   📄 {OUTPUT_EXECUTIVE} ({size:.1f} KB)")
    if OUTPUT_ROADMAP.exists():
        size = OUTPUT_ROADMAP.stat().st_size / 1024
        print(f"   📄 {OUTPUT_ROADMAP} ({size:.1f} KB)")
    
    print("\n📋 Next steps:")
    print("   1. Review MASTER_ARCHITECTURE_REPORT.md")
    print("   2. Share EXECUTIVE_SUMMARY.md with leadership")
    print("   3. Turn REMEDIATION_ROADMAP.md into tickets")
    print("\n")

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
        sys.stderr.reconfigure(encoding="utf-8", errors="ignore")
    main()