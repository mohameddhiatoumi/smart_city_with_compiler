"""
Main compiler orchestrator
Coordinates lexer, parser, and code generator
"""

from typing import Tuple
from .lexer import Lexer, Token
from .parser import Parser, ParseError
from .code_generator import CodeGenerator


class CompilationError(Exception):
    """Raised when compilation fails"""
    def __init__(self, message: str, stage: str, details: str = None):
        self.message = message
        self.stage = stage  # 'lexer', 'parser', 'codegen'
        self.details = details
        super().__init__(self.message)


class NLQueryCompiler:
    """
    Complete Natural Language to SQL compiler
    Usage:
        compiler = NLQueryCompiler()
        sql = compiler.compile("Affiche les 5 zones les plus polluées")
    """
    
    def __init__(self):
        self.lexer = Lexer()
        self.code_generator = CodeGenerator()
    
    def compile(self, query: str) -> str:
        """
        Compile natural language query to SQL
        
        Args:
            query: Natural language query string (French)
        
        Returns:
            Valid SQL query string
        
        Raises:
            CompilationError: If compilation fails at any stage
        """
        try:
            # Stage 1: Lexical Analysis
            tokens = self.lexer.tokenize(query)
            if not tokens:
                raise CompilationError(
                    "No valid tokens found",
                    stage='lexer',
                    details="Query appears to be empty or contains no recognizable words"
                )
            
            # Stage 2: Syntax Analysis
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Stage 3: Code Generation
            sql = self.code_generator.generate(ast)
            
            return sql
            
        except ParseError as e:
            raise CompilationError(
                f"Parsing failed: {str(e)}",
                stage='parser',
                details=str(e)
            )
        except Exception as e:
            raise CompilationError(
                f"Compilation failed: {str(e)}",
                stage='unknown',
                details=str(e)
            )
    
    def compile_with_debug(self, query: str) -> Tuple[str, dict]:
        """
        Compile with debug information
        
        Returns:
            Tuple of (sql, debug_info)
        """
        debug_info = {
            'query': query,
            'tokens': [],
            'ast': None,
            'sql': None,
            'errors': []
        }
        
        try:
            # Tokenization
            tokens = self.lexer.tokenize(query)
            debug_info['tokens'] = [str(t) for t in tokens]
            
            # Parsing
            parser = Parser(tokens)
            ast = parser.parse()
            debug_info['ast'] = str(ast)
            
            # Code generation
            sql = self.code_generator.generate(ast)
            debug_info['sql'] = sql
            
            return sql, debug_info
            
        except Exception as e:
            debug_info['errors'].append(str(e))
            raise CompilationError(str(e), 'compilation', str(e))


# Example usage
if __name__ == "__main__":
    compiler = NLQueryCompiler()
    
    test_queries = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
        "Donne-moi le trajet le plus économique en CO2",
    ]
    
    print("="*70)
    print("NATURAL LANGUAGE TO SQL COMPILER - TEST SUITE")
    print("="*70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}]")
        print(f"NL: {query}")
        
        try:
            sql, debug = compiler.compile_with_debug(query)
            print(f"✅ SQL: {sql}")
        except CompilationError as e:
            print(f"❌ Error ({e.stage}): {e.message}")