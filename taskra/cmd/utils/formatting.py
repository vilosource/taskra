"""Formatting utilities for CLI output."""

from typing import Dict, Any, Optional, List
from rich.text import Text

def _extract_text_from_adf(doc):
    """Extract plain text from Atlassian Document Format."""
    if not doc or not isinstance(doc, dict):
        return ""
    
    # Handle the ADF document structure
    def _process_node(node):
        if not isinstance(node, dict):
            return ""
        
        node_type = node.get("type", "")
        
        # Direct text node
        if node_type == "text":
            return node.get("text", "")
        
        # Process content array if it exists
        result = []
        if "content" in node and isinstance(node.get("content"), list):
            for child in node.get("content", []):
                child_text = _process_node(child)
                if child_text:
                    result.append(child_text)
        # Join text within this node based on the node type
        if node_type in ["paragraph", "heading"]:
            # Add newline after paragraphs or headings
            return " ".join(result) + "\n"
        elif node_type == "list-item":
            # Add bullet point for list items
            return "• " + " ".join(result) + "\n"
        elif node_type in ["bulletList", "orderedList"]:
            # Just join list items
            return "".join(result)
        elif node_type in ["hardBreak"]:
            # Hard break gets converted to newline
            return "\n"
        else:
            # Default: just join the text
            return " ".join(result)
    
    # Process the document from the top level
    return _process_node(doc).strip()

def convert_adf_to_rich_text(doc: Dict[str, Any]) -> Text:
    """Convert Atlassian Document Format to Rich Text with formatting.
    
    Args:
        doc: The Atlassian Document Format document
        
    Returns:
        Rich Text object with formatting preserved
    """
    if not doc or not isinstance(doc, dict):
        return Text("No content")
    
    result = Text()
    
    def process_node(node: Dict[str, Any], parent_styles: List[str] = None) -> Optional[Text]:
        """Process a node in the ADF and convert to Rich Text.
        
        Args:
            node: The ADF node to process
            parent_styles: Style strings inherited from parent nodes
            
        Returns:
            Rich Text object with formatting
        """
        if not isinstance(node, dict):
            return None
        
        # Initialize with parent styles or empty list
        styles = parent_styles.copy() if parent_styles else []
        node_text = Text()
        node_type = node.get("type", "")
        
        # Handle text nodes with marks/formatting
        if node_type == "text":
            text_content = node.get("text", "")
            if not text_content:
                return None
                
            # Process text marks (bold, italic, etc.)
            if "marks" in node and isinstance(node["marks"], list):
                for mark in node["marks"]:
                    mark_type = mark.get("type", "")
                    
                    if mark_type == "strong":
                        styles.append("bold")
                    elif mark_type == "em":
                        styles.append("italic")
                    elif mark_type == "strike":
                        styles.append("strike")
                    elif mark_type == "code":
                        styles.append("on grey15")
                        styles.append("bright_white")
                    elif mark_type == "textColor" and "attrs" in mark:
                        # Handle text color attribute
                        color = mark["attrs"].get("color")
                        if color:
                            # Convert Atlassian color to closest Rich color
                            styles.append(map_atlassian_color_to_rich(color))
                    elif mark_type == "link" and "attrs" in mark:
                        # Handle links
                        href = mark["attrs"].get("href")
                        if href:
                            styles.append("blue")
                            styles.append("underline")
            
            # Apply combined styles to the text
            style_str = " ".join(styles)
            return Text(text_content, style=style_str if style_str else None)
            
        # Container nodes that have content to process
        elif "content" in node and isinstance(node.get("content"), list):
            # Handle heading levels
            if node_type.startswith("heading"):
                try:
                    level = int(node_type[-1])
                    styles.append("bold")
                    if level == 1:
                        styles.append("bright_yellow")
                        styles.append("underline")
                    elif level == 2:
                        styles.append("bright_yellow")
                    elif level == 3:
                        styles.append("yellow")
                except (ValueError, IndexError):
                    pass
            
            # Process all child nodes
            for child in node.get("content", []):
                child_text = process_node(child, styles)
                if child_text:
                    node_text.append(child_text)
            
            # Add appropriate formatting based on node type
            if node_type in ["paragraph"]:
                node_text.append("\n")
            elif node_type in ["heading"]:
                node_text.append("\n\n")
            elif node_type == "list-item":
                # Prepend bullet point to list items
                bullet = Text("• ", style="dim")
                return Text.assemble(bullet, node_text)
            elif node_type == "hardBreak":
                return Text("\n")
            elif node_type == "rule":
                return Text("\n" + "-" * 40 + "\n", style="dim")
            
        return node_text
    
    # Process the document from the top level    
    if "content" in doc and isinstance(doc["content"], list):
        for node in doc["content"]:
            node_text = process_node(node)
            if node_text:
                result.append(node_text)
    
    return result

def map_atlassian_color_to_rich(color: str) -> str:
    """Map Atlassian color values to Rich color names.
    
    Args:
        color: Atlassian color (e.g., "#ff0000" or "red")
        
    Returns:
        Closest Rich color name
    """
    # Common color mappings
    color_map = {
        "#ff0000": "red",
        "#00ff00": "green",
        "#0000ff": "blue",
        "#ffff00": "yellow",
        "#00ffff": "cyan",
        "#ff00ff": "magenta",
        "#000000": "black",
        "#ffffff": "white",
        "#ff7f50": "orange_red",
        "#800080": "purple",
        "#008000": "green4",
        "#a52a2a": "brown",
        "#808080": "grey",
        "#ffa500": "orange1"
    }
    
    # Check if color is in our map
    if color.lower() in color_map:
        return color_map[color.lower()]
    
    # Try to match by hex value
    if color.startswith("#"):
        if color.lower() in color_map:
            return color_map[color.lower()]
        
        # Default approximations for colors we don't have a direct mapping for
        if color.startswith("#f"):  # Light colors
            return "bright_white"
        elif color.startswith("#0"):  # Dark blue/green shades
            return "blue"
        elif color.startswith("#8") or color.startswith("#7"):  # Mid-tones
            return "grey"
    
    # Default fallback
    return "default"
