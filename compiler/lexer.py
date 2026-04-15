"""
Lexical analyzer (Lexer) for natural language queries
Tokenizes input text into meaningful units
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Token:
    """Represents a single token"""
    type: str      # TOKEN_TYPE (e.g., 'INTENT', 'ENTITY', 'NUMBER')
    value: str     # Original text
    position: int  # Position in input string
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', pos={self.position})"


class Lexer:
    """
    Tokenizes natural language input into structured tokens
    """
    
    # Token type definitions
    TOKEN_PATTERNS = [
        ('NUMBER', r'\d+\.?\d*'),           # Numbers (int or float)
        ('WORD', r'[a-zàâäéèêëïîôùûüÿæœç]+'),  # French words
        ('OPERATOR', r'[><=]+'),            # Comparison operators
        ('PUNCTUATION', r'[?!.,;:]'),       # Punctuation
        ('WHITESPACE', r'\s+'),             # Spaces (will be filtered)
    ]
    
    def __init__(self):
        # Compile patterns into single regex
        self.token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_PATTERNS)
        self.compiled_regex = re.compile(self.token_regex, re.IGNORECASE | re.UNICODE)
    
    def tokenize(self, text: str) -> List[Token]:
        """
        Convert input text into list of tokens
        
        Args:
            text: Natural language query
        
        Returns:
            List of Token objects
        """
        tokens = []
        
        for match in self.compiled_regex.finditer(text):
            token_type = match.lastgroup
            token_value = match.group()
            position = match.start()
            
            # Skip whitespace tokens
            if token_type == 'WHITESPACE':
                continue
            
            # Normalize words to lowercase
            if token_type == 'WORD':
                token_value = token_value.lower()
            
            tokens.append(Token(token_type, token_value, position))
        
        return tokens
    
    def get_tokens_as_strings(self, tokens: List[Token]) -> List[str]:
        """Get just the token values as a list of strings"""
        return [token.value for token in tokens]


# Example usage
if __name__ == "__main__":
    lexer = Lexer()
    
    test_queries = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        tokens = lexer.tokenize(query)
        for token in tokens:
            print(f"  {token}")