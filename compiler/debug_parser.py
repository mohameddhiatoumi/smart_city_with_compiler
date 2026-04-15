# Save as compiler/debug_parser.py
from lexer import Lexer
from parser import Parser

lexer = Lexer()

test_query = "Combien de capteurs de bruit sont actif"

print(f"Query: {test_query}")
print("="*60)

# Tokenize
tokens = lexer.tokenize(test_query)
print(f"\nTokens: {[t.value for t in tokens]}")

# Parse
parser = Parser(tokens)
ast = parser.parse()

print(f"\nAST: {ast}")
print(f"\nConditions detected:")
for condition in ast.conditions:
    print(f"  - {condition}")

# Generate SQL
from code_generator import CodeGenerator
generator = CodeGenerator()
sql = generator.generate(ast)
print(f"\nGenerated SQL: {sql}")