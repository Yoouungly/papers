#!/usr/bin/env python3
"""
Extract section titled "复杂自然过程机理揭示" from converted Markdown and analyze papers.

This script loads the converted Markdown file and extracts the specific section,
then analyzes each paper entry to extract research entry points and data mining methods.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_markdown_file(file_path: Path) -> str:
    """Load the converted Markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def find_section(content: str, section_title: str) -> Optional[str]:
    """Find and extract the specified section from markdown content."""
    # Try different patterns to match the section
    patterns = [
        # Exact match
        rf'^#+\s*{re.escape(section_title)}\s*$',
        # Contains the title
        rf'^#+\s*.*{re.escape(section_title)}.*$',
        # Alternative characters or formatting
        rf'^#+\s*.*复杂.*自然.*过程.*机理.*揭示.*$',
        # Look for it in table headers or content
        rf'.*{re.escape(section_title)}.*',
    ]
    
    lines = content.split('\n')
    section_start = None
    section_end = None
    
    # Try each pattern
    for pattern in patterns:
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip(), re.IGNORECASE | re.MULTILINE):
                print(f"Found potential section match at line {i+1}: {line.strip()}")
                section_start = i
                break
        if section_start is not None:
            break
    
    if section_start is None:
        # Try searching in content for papers that might be in this category
        print("Direct section title not found. Searching for related content...")
        
        # Look for content that might contain relevant papers
        # Based on the preview, let's search for patterns that indicate this type of content
        complex_keywords = ['复杂', '自然过程', '机理', '揭示', '地幔', '地震', '流体', '火山']
        
        potential_sections = []
        current_section = []
        current_header = None
        
        for i, line in enumerate(lines):
            if re.match(r'^#+\s', line):  # Header line
                if current_section and any(keyword in '\n'.join(current_section) for keyword in complex_keywords):
                    potential_sections.append((current_header, i - len(current_section), '\n'.join(current_section)))
                current_section = [line]
                current_header = line
            else:
                current_section.append(line)
        
        # Check the last section
        if current_section and any(keyword in '\n'.join(current_section) for keyword in complex_keywords):
            potential_sections.append((current_header, len(lines) - len(current_section), '\n'.join(current_section)))
        
        if potential_sections:
            print(f"Found {len(potential_sections)} potential sections containing relevant keywords")
            # Return the first/largest relevant section
            return potential_sections[0][2] if potential_sections else None
        
        return None
    
    # Find the end of the section (next header of same or higher level)
    if section_start is not None:
        start_level = len(re.match(r'^(#+)', lines[section_start]).group(1))
        
        for i in range(section_start + 1, len(lines)):
            line = lines[i].strip()
            if re.match(r'^#+\s', line):
                current_level = len(re.match(r'^(#+)', line).group(1))
                if current_level <= start_level:
                    section_end = i
                    break
        
        if section_end is None:
            section_end = len(lines)
        
        section_content = '\n'.join(lines[section_start:section_end])
        return section_content
    
    return None


def extract_papers_from_section(section_content: str) -> List[Dict[str, str]]:
    """Extract individual papers from the section content."""
    papers = []
    
    # The content is a large table where each paper starts with a link on its own line
    # Split by lines and look for lines that start with links
    lines = section_content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines, table headers, and separators
        if not line or line.startswith('---|') or line.startswith('**文章**'):
            continue
        
        # Check if this line starts with a link - indicates a paper
        link_match = re.match(r'^\[([^\]]+)\]\(([^)]+)\)', line)
        if link_match:
            title = link_match.group(1)
            url = link_match.group(2)
            
            # The entire line is the content for this paper (table row)
            paper = {
                'title': title,
                'url': url,
                'context': line,  # The entire table row
                'number': len(papers) + 1,
                'core_problem': '',
                'data_source': '',
                'data_mining_methods': '',
                'conclusion': '',
                'summary': ''
            }
            
            # Try to extract table cell content from the line
            # The format appears to be: [title](url) description | core_problem | data_source | methods | conclusion | summary
            extracted_fields = extract_table_cells_from_line(line)
            paper.update(extracted_fields)
            
            papers.append(paper)
    
    print(f"Extracted {len(papers)} papers from table")
    return papers


def extract_table_cells_from_line(line: str) -> Dict[str, str]:
    """Extract table cell content from a single line."""
    # Split by | but be careful - content within cells can contain |
    # The table structure seems to be complex with nested content
    
    result = {
        'core_problem': '',
        'data_source': '',
        'data_mining_methods': '',
        'conclusion': '',
        'summary': ''
    }
    
    # Find major sections by looking for bold patterns and section dividers
    # Use a more robust approach - find patterns that indicate section breaks
    
    # Look for the main "|" separators that separate table columns
    # These usually come after complete sections
    parts = re.split(r'\s*\|\s*(?=(?:[^|]*\|)*[^|]*$)', line)
    
    if len(parts) >= 6:
        # We have all 6 columns: title, core_problem, data_source, methods, conclusion, summary
        result['core_problem'] = parts[1].strip() if len(parts) > 1 else ''
        result['data_source'] = parts[2].strip() if len(parts) > 2 else ''
        result['data_mining_methods'] = parts[3].strip() if len(parts) > 3 else ''
        result['conclusion'] = parts[4].strip() if len(parts) > 4 else ''
        result['summary'] = parts[5].strip() if len(parts) > 5 else ''
    else:
        # If simple split doesn't work, try to find content by keywords
        # This is more robust for complex nested content
        
        # Look for core problem - usually comes right after the title/description
        problem_patterns = [
            r'(?:（\d+）[^|]*\|)\s*([^|]+?)(?=\s*\|)',  # After date, before next |
            r'\*\*([^*]*(?:问题|原因|机制)[^*]*)\*\*',    # Bold text with problem keywords
        ]
        
        for pattern in problem_patterns:
            match = re.search(pattern, line)
            if match:
                result['core_problem'] = match.group(1).strip()
                break
        
        # Look for data mining methods - usually contains technical terms
        method_patterns = [
            r'(\*\*[^*]*(?:方法|分析|模型|算法)[^*]*\*\*[^|]*)',
            r'((?:机器学习|深度学习|数据挖掘|统计分析)[^|]*)',
        ]
        
        for pattern in method_patterns:
            matches = re.findall(pattern, line)
            if matches:
                result['data_mining_methods'] = ' '.join(matches)
                break
    
    # Clean up the extracted text
    for key in result:
        if result[key]:
            # Remove excessive whitespace
            result[key] = re.sub(r'\s+', ' ', result[key]).strip()
            # Remove markdown formatting
            result[key] = re.sub(r'\*\*', '', result[key])
    
    return result


def extract_research_details(paper: Dict[str, str]) -> Dict[str, str]:
    """Extract research entry point and data mining methods from paper content."""
    content = paper.get('context', '')
    
    # Also check in specific fields
    data_methods = paper.get('data_mining_methods', '')
    core_problem = paper.get('core_problem', '')
    
    # Look for research entry points - often mentioned as problems, questions, or objectives
    entry_patterns = [
        r'研究切入口[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'核心问题[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'研究目标[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'主要问题[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'\*\*([^*]+问题[^*]*)\*\*',  # Bold questions
    ]
    
    research_entry = core_problem if core_problem else ""
    
    if not research_entry:
        for pattern in entry_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                research_entry = match.group(1).strip()
                # Clean up markdown and extra whitespace
                research_entry = re.sub(r'\*\*', '', research_entry)
                research_entry = re.sub(r'\s+', ' ', research_entry)
                break
    
    # Look for data mining and analysis methods
    method_patterns = [
        r'数据挖掘及分析方法[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'方法[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'分析方法[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'技术[：:]\s*([^|]+?)(?:\s*\||\s*$)',
        r'\*\*方法[^*]*\*\*[：:]\s*([^|]+?)(?:\s*\||\s*$)',
    ]
    
    methods = data_methods if data_methods else ""
    
    if not methods:
        for pattern in method_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                methods = match.group(1).strip()
                # Clean up markdown and extra whitespace  
                methods = re.sub(r'\*\*', '', methods)
                methods = re.sub(r'\s+', ' ', methods)
                break
    
    # If still no methods found, look for specific technical terms
    if not methods:
        tech_patterns = [
            r'(机器学习[^|]*)',
            r'(深度学习[^|]*)',
            r'(数据挖掘[^|]*)',
            r'(统计分析[^|]*)',
            r'(模型[^|]*)',
            r'(算法[^|]*)',
            r'(分析[^|]*方法[^|]*)',
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, content)
            if match:
                methods = match.group(1).strip()
                break
    
    return {
        'research_entry_point': research_entry,
        'data_mining_methods': methods
    }


def generate_analysis_report(papers: List[Dict[str, str]], output_file: Path):
    """Generate the analysis report in the specified format."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 复杂自然过程机理揭示 - 论文分析报告\n\n")
        f.write(f"本报告分析了 {len(papers)} 篇相关论文，提取了每篇论文的研究切入口和数据挖掘分析方法。\n\n")
        f.write("## 分析方法说明\n\n")
        f.write("- 数据来源：docs/数据挖掘和数据分析相关文献分析.md\n")
        f.write("- 提取标准：基于论文内容中明确提及的研究方法和切入点\n")
        f.write("- 引用格式：保持原文引用，标注来源位置\n\n")
        f.write("---\n\n")
        
        for i, paper in enumerate(papers, 1):
            f.write(f"## 论文 {i}\n\n")
            
            # Title and link
            if paper.get('url'):
                f.write(f"### 标题：[{paper.get('title', 'N/A')}]({paper.get('url')})\n\n")
            else:
                f.write(f"### 标题：{paper.get('title', 'N/A')}\n\n")
            
            # Research entry point
            f.write("#### 研究切入口：\n")
            entry_point = paper.get('research_entry_point') or paper.get('core_problem', '')
            if entry_point:
                f.write(f"> {entry_point}\n\n")
                f.write("*来源：docs/数据挖掘和数据分析相关文献分析.md*\n\n")
            else:
                f.write("> 未在源文中找到明确的研究切入口描述\n\n")
            
            # Data mining methods
            f.write("#### 数据挖掘及分析方法：\n")
            methods = paper.get('data_mining_methods') or ''
            if methods:
                f.write(f"> {methods}\n\n")
                f.write("*来源：docs/数据挖掘和数据分析相关文献分析.md*\n\n")
            else:
                f.write("> 未在源文中找到明确的数据挖掘方法描述\n\n")
            
            # Additional context if available
            if paper.get('conclusion'):
                f.write("#### 主要结论：\n")
                f.write(f"> {paper.get('conclusion')}\n\n")
            
            f.write("---\n\n")
        
        f.write("## 总结\n\n")
        f.write(f"本次分析共处理了 {len(papers)} 篇论文。")
        
        if papers:
            valid_entries = sum(1 for p in papers if p.get('research_entry_point') or p.get('core_problem'))
            valid_methods = sum(1 for p in papers if p.get('data_mining_methods'))
            
            f.write(f"其中：\n")
            f.write(f"- {valid_entries} 篇论文提取到了研究切入口信息\n")
            f.write(f"- {valid_methods} 篇论文提取到了数据挖掘方法信息\n\n")
        
        f.write("所有引用内容均来源于转换后的Markdown文件，确保零编造性。\n")


def main():
    """Main extraction function."""
    # Define paths
    repo_root = Path(__file__).parent.parent
    input_file = repo_root / "docs" / "数据挖掘和数据分析相关文献分析.md"
    output_file = repo_root / "analysis" / "复杂自然过程机理揭示.md"
    
    # Check input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    print(f"Loading Markdown file: {input_file}")
    
    # Load content
    content = load_markdown_file(input_file)
    print(f"Loaded {len(content)} characters from Markdown file")
    
    # Find target section
    target_section_title = "复杂自然过程机理揭示"
    print(f"Searching for section: {target_section_title}")
    
    section_content = find_section(content, target_section_title)
    
    if section_content:
        print(f"Found section with {len(section_content)} characters")
        print(f"Section preview (first 500 chars):")
        print("=" * 50)
        print(section_content[:500])
        print("=" * 50)
    else:
        print("Target section not found. Analyzing entire document for relevant papers...")
        # If specific section not found, analyze the whole document
        section_content = content
    
    # Extract papers
    print("Extracting papers from section...")
    papers = extract_papers_from_section(section_content)
    print(f"Extracted {len(papers)} papers")
    
    # Extract research details for each paper
    for i, paper in enumerate(papers):
        print(f"Processing paper {i+1}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...")
        details = extract_research_details(paper)
        paper.update(details)
    
    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate analysis report
    print(f"Generating analysis report: {output_file}")
    generate_analysis_report(papers, output_file)
    
    print(f"\nExtraction completed successfully!")
    print(f"Analysis report saved to: {output_file}")
    print(f"Total papers analyzed: {len(papers)}")


if __name__ == "__main__":
    main()