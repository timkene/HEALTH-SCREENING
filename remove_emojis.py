#!/usr/bin/env python3
"""
Script to remove emojis from the individual_report_generator.py file
and replace them with text alternatives that display properly in PDFs.
"""

import re

def remove_emojis_from_file(file_path):
    """Remove emojis and replace with text alternatives"""
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define emoji replacements
    emoji_replacements = {
        '🤖': '',
        '💚': '',
        '🧮': '',
        '📊': '',
        '👉': '',
        '📏': '',
        '✨': '',
        '💡': '',
        '🥗': '•',
        '💪': '•',
        '🍎': '•',
        '🩺': '•',
        '🏃': '•',
        '⚖️': '•',
        '💧': '•',
        '❤️': '',
        '🔗': '',
        '🍬': '',
        '🧈': '',
        '💧': '',
        '🍬': '',
        '🥚': '',
        '🌟': '',
        '✅': '',
        '🚀': '',
        '🎉': '',
        '👀': '•',
        '📈': '•',
        '💊': '•',
        '🌱': '•',
        '📊': '•',
        '🧂': '•',
        '🥑': '•',
        '🚶': '•',
        '🔍': '',
        '💚': ''
    }
    
    # Apply replacements
    for emoji, replacement in emoji_replacements.items():
        content = content.replace(emoji, replacement)
    
    # Clean up any remaining emoji patterns
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    content = emoji_pattern.sub('', content)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Emojis removed successfully!")

if __name__ == "__main__":
    remove_emojis_from_file("individual_report_generator.py")
