#!/usr/bin/env python3
"""
Convert Word-exported HTML file to clean UTF-8 Markdown and plain text.

This script reads a Word HTML export file (gb2312 encoded) and converts it to:
1. Clean UTF-8 Markdown preserving structure
2. Plain text version

Requirements:
- Read HTML using declared charset (gb2312/cp936)
- Extract only body content (ignore MS Office XML, styles, etc.)
- Preserve structure: headings, paragraphs, lists, tables, links
- Normalize whitespace and remove Word-specific artifacts
- Ensure all Chinese characters render correctly in UTF-8
"""

import os
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md
import html2text


def clean_mso_attributes(soup):
    """Remove Microsoft Office specific attributes and elements."""
    # Remove MSO-specific attributes from all elements
    mso_attrs = ['style', 'class']  # We'll handle these more carefully
    
    for element in soup.find_all():
        if element.name:
            # Remove MSO-specific attributes
            attrs_to_remove = []
            for attr_name, attr_value in element.attrs.items():
                if isinstance(attr_value, str):
                    # Remove if it contains MSO-specific patterns
                    if any(pattern in attr_value.lower() for pattern in 
                          ['mso-', 'microsoft', 'word', 'office']):
                        attrs_to_remove.append(attr_name)
                elif isinstance(attr_value, list):
                    # For class attributes, remove MSO classes
                    new_classes = [cls for cls in attr_value 
                                 if not any(pattern in cls.lower() for pattern in 
                                          ['mso', 'microsoft', 'word', 'office'])]
                    if new_classes != attr_value:
                        if new_classes:
                            element.attrs[attr_name] = new_classes
                        else:
                            attrs_to_remove.append(attr_name)
            
            for attr in attrs_to_remove:
                del element.attrs[attr]
    
    # Remove MSO-specific elements entirely
    mso_tags = soup.find_all(re.compile(r'^(v|o|w):'))
    for tag in mso_tags:
        tag.decompose()
    
    # Remove style elements with MSO content
    style_tags = soup.find_all('style')
    for style_tag in style_tags:
        if style_tag.string and any(pattern in style_tag.string.lower() 
                                  for pattern in ['mso-', 'microsoft', 'word']):
            style_tag.decompose()
    
    return soup


def clean_html_content(html_content):
    """Clean and prepare HTML content for conversion."""
    # Parse HTML with lxml parser
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Find body content
    body = soup.find('body')
    if not body:
        # If no body tag, use the whole document
        body = soup
    
    # Clean MSO attributes and elements
    body = clean_mso_attributes(body)
    
    # Remove script and style tags
    for script in body(['script', 'style']):
        script.decompose()
    
    # Remove empty paragraphs and divs
    for element in body.find_all(['p', 'div']):
        if not element.get_text(strip=True):
            element.decompose()
    
    return str(body)


def convert_to_markdown(html_content):
    """Convert cleaned HTML to Markdown."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True  # Use Unicode characters
    h.decode_errors = 'ignore'
    
    # Convert to markdown
    markdown = h.handle(html_content)
    
    # Clean up extra whitespace
    markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)  # Multiple blank lines to double
    markdown = re.sub(r'[ \t]+\n', '\n', markdown)  # Trailing spaces
    markdown = markdown.strip()
    
    return markdown


def convert_to_text(html_content):
    """Convert HTML to plain text."""
    soup = BeautifulSoup(html_content, 'lxml')
    text = soup.get_text()
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple blank lines to double
    text = text.strip()
    
    return text


def read_html_file(file_path):
    """Read HTML file with proper encoding detection."""
    encodings_to_try = ['cp936', 'gb2312', 'gbk', 'utf-8', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            print(f"Successfully read file with encoding: {encoding}")
            return content
        except Exception as e:
            print(f"Failed to read with {encoding}: {e}")
            continue
    
    raise ValueError(f"Could not read file {file_path} with any of the tried encodings")


def main():
    """Main conversion function."""
    # Define paths
    repo_root = Path(__file__).parent.parent
    input_file = repo_root / "数据挖掘和数据分析相关文献分析.htm"
    output_md = repo_root / "docs" / "数据挖掘和数据分析相关文献分析.md"
    output_txt = repo_root / "docs" / "数据挖掘和数据分析相关文献分析.txt"
    
    # Check input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    print(f"Converting {input_file.name}...")
    
    # Read HTML content
    html_content = read_html_file(input_file)
    print(f"Read {len(html_content)} characters from input file")
    
    # Clean HTML content
    cleaned_html = clean_html_content(html_content)
    print(f"Cleaned HTML content: {len(cleaned_html)} characters")
    
    # Convert to Markdown
    markdown_content = convert_to_markdown(cleaned_html)
    print(f"Generated Markdown: {len(markdown_content)} characters, {markdown_content.count(chr(10))} lines")
    
    # Convert to plain text
    text_content = convert_to_text(cleaned_html)
    print(f"Generated text: {len(text_content)} characters, {text_content.count(chr(10))} lines")
    
    # Create output directory if it doesn't exist
    output_md.parent.mkdir(parents=True, exist_ok=True)
    
    # Write Markdown file
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"Wrote Markdown to: {output_md}")
    
    # Write text file
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(text_content)
    print(f"Wrote text to: {output_txt}")
    
    print("\nConversion completed successfully!")
    print(f"Summary:")
    print(f"  - Input:    {len(html_content):,} chars")
    print(f"  - Markdown: {len(markdown_content):,} chars, {markdown_content.count(chr(10)):,} lines")
    print(f"  - Text:     {len(text_content):,} chars, {text_content.count(chr(10)):,} lines")


if __name__ == "__main__":
    main()