"""
Code Generator - Converts AST to SQL
Generates valid SQL queries that match the database schema
"""

from .ast_nodes import SelectQuery, CountQuery, Condition, Join


class CodeGenerator:
    """
    Generates SQL code from AST
    """
    
    def generate(self, ast_node) -> str:
        """
        Generate SQL from AST node
        
        Args:
            ast_node: Root AST node (SelectQuery or CountQuery)
        
        Returns:
            Valid SQL string
        """
        if isinstance(ast_node, SelectQuery):
            return self._generate_select(ast_node)
        elif isinstance(ast_node, CountQuery):
            return self._generate_count(ast_node)
        else:
            raise ValueError(f"Unknown AST node type: {type(ast_node)}")
    
    def _generate_select(self, query: SelectQuery) -> str:
        """Generate SELECT query"""
        parts = []
        
        # SELECT clause
        select_clause = f"SELECT {', '.join(query.attributes)}"
        parts.append(select_clause)
        
        # FROM clause with table alias
        table_alias = self._get_table_alias(query.entity)
        from_clause = f"FROM {query.entity} {table_alias}"
        parts.append(from_clause)
        
        # JOIN clauses
        for join in query.joins:
            join_clause = f"{join.join_type} JOIN {join.table} ON {join.on_left} = {join.on_right}"
            parts.append(join_clause)
        
        # WHERE clause
        if query.conditions:
            where_conditions = ' AND '.join(self._format_condition(c) for c in query.conditions)
            parts.append(f"WHERE {where_conditions}")
        
        # Add pollution type filter for pollution queries
        if 'pollution_moyenne' in ' '.join(query.attributes):
            if query.conditions:
                parts[-1] += " AND m.type_mesure = 'PM2.5'"
            else:
                parts.append("WHERE m.type_mesure = 'PM2.5'")
        
        # GROUP BY clause
        if query.group_by:
            parts.append(f"GROUP BY {query.group_by}")
        
        # ORDER BY clause
        if query.order_by:
            parts.append(f"ORDER BY {query.order_by} {query.order_dir}")
        
        # LIMIT clause
        if query.limit:
            parts.append(f"LIMIT {query.limit}")
        
        return ' '.join(parts)
    
    def _generate_count(self, query: CountQuery) -> str:
        """Generate COUNT query"""
        parts = []
        
        parts.append("SELECT COUNT(*)")
        parts.append(f"FROM {query.entity}")
        
        if query.conditions:
            where_conditions = ' AND '.join(self._format_condition(c) for c in query.conditions)
            parts.append(f"WHERE {where_conditions}")
        
        return ' '.join(parts)
    
    def _format_condition(self, condition: Condition) -> str:
        """Format a single condition"""
        # Special handling for date functions (they're already SQL expressions)
        if condition.attribute == 'date_installation' and 'strftime' in str(condition.value):
            # Extract just the SQL expression without the = sign
            value_str = str(condition.value)
            if '=' in value_str:
                return value_str.split('=', 1)[1].strip()
            return value_str
        
        if condition.attribute == 'date_installation' and ('date(' in str(condition.value) or '>=' in str(condition.value)):
            # For date range queries
            value_str = str(condition.value)
            if 'date(' in value_str or '>=' in value_str:
                return f"{condition.attribute} {condition.operator} {value_str}"
            return f"{condition.attribute} {condition.operator} {condition.value}"
        
        return f"{condition.attribute} {condition.operator} {condition.value}"
    
    def _get_table_alias(self, table: str) -> str:
        """Get standard table alias"""
        aliases = {
            'zones': 'z',
            'capteurs': 'c',
            'mesures': 'm',
            'citoyens': 'cit',
            'vehicules': 'v',
            'trajets': 't',
            'interventions': 'i',
            'techniciens': 'tech'
        }
        return aliases.get(table, table[0])


# Example usage
if __name__ == "__main__":
    from compiler.lexer import Lexer
    from compiler.parser import Parser
    
    lexer = Lexer()
    
    test_queries = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"NL Query: {query}")
        print('='*60)
        
        tokens = lexer.tokenize(query)
        parser = Parser(tokens)
        ast = parser.parse()
        
        generator = CodeGenerator()
        sql = generator.generate(ast)
        
        print(f"SQL: {sql}")