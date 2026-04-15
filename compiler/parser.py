"""
Parser for natural language queries
Analyzes token stream and builds AST
"""

import re
from typing import List, Optional
from .lexer import Token
from .ast_nodes import SelectQuery, CountQuery, Condition, Join, AggregateFunction
from .grammar import (
    INTENT_KEYWORDS, ENTITY_MAPPINGS, ATTRIBUTE_MAPPINGS,
    STATUS_VALUES, OPERATORS, AGGREGATES, ORDER_KEYWORDS, 
    POLLUTION_PATTERNS, SENSOR_TYPE_VALUES, TIME_PERIODS
)


class ParseError(Exception):
    """Raised when parsing fails"""
    pass


class Parser:
    """
    Parses tokenized natural language into AST
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = [t.value for t in tokens if t.type != 'PUNCTUATION']  # Filter punctuation
        self.raw_tokens = [t for t in tokens if t.type != 'PUNCTUATION']  # Keep Token objects for type checking
        self.position = 0
    
    def parse(self) -> SelectQuery | CountQuery:
        """
        Main parse method - determines query type and builds AST
        
        Returns:
            AST root node (SelectQuery or CountQuery)
        """
        # Determine query intent
        if self._has_keyword(INTENT_KEYWORDS['count']):
            return self._parse_count_query()
        else:
            return self._parse_select_query()
    
    def _parse_select_query(self) -> SelectQuery:
        """Parse a SELECT-type query"""
        
        # Detect entity
        entity = self._detect_entity()
        if not entity:
            raise ParseError("Cannot identify entity (table) in query")
        
        # Detect attributes/aggregations
        attributes = self._detect_attributes(entity)
        
        # Detect conditions
        conditions = self._detect_conditions(entity)
        
        # Detect ordering
        order_by, order_dir = self._detect_ordering(entity)
        
        # Detect limit
        limit = self._detect_limit()
        
        # Detect grouping (for aggregates)
        group_by = None
        if any('AVG' in attr or 'SUM' in attr or 'MAX' in attr or 'MIN' in attr for attr in attributes):
            group_by = self._detect_group_by(entity)
        
        # Detect joins
        joins = self._detect_joins(entity)
        
        return SelectQuery(
            entity=entity,
            attributes=attributes,
            conditions=conditions,
            group_by=group_by,
            order_by=order_by,
            order_dir=order_dir,
            limit=limit,
            joins=joins
        )
    
    def _parse_count_query(self) -> CountQuery:
        """Parse a COUNT query"""
        entity = self._detect_entity()
        conditions = self._detect_conditions(entity)
        
        return CountQuery(entity=entity, conditions=conditions)
    
    def _detect_entity(self) -> Optional[str]:
        """Identify the main entity (table) in query"""
        for token in self.tokens:
            for table, keywords in ENTITY_MAPPINGS.items():
                if token in keywords:
                    return table
        return None
    
    def _detect_attributes(self, entity: str) -> List[str]:
        """Detect which attributes to select"""
        attributes = []
        
        # Check for pollution query (special case)
        if self._has_keyword(POLLUTION_PATTERNS['avg_pm25']):
            if entity == 'zones':
                attributes.append('z.nom')
                attributes.append('AVG(m.valeur) AS pollution_moyenne')
                return attributes
        
        # Check for aggregate functions
        for func, keywords in AGGREGATES.items():
            if self._has_keyword(keywords):
                if func == 'COUNT':
                    return ['COUNT(*)']
                # Detect attribute to aggregate
                for attr, attr_keywords in ATTRIBUTE_MAPPINGS.items():
                    if self._has_keyword(attr_keywords):
                        attributes.append(f'{func}({attr})')
                        return attributes
        
        # Check for ecological score query
        if entity == 'citoyens' and self._has_keyword(ATTRIBUTE_MAPPINGS['score_ecologique']):
            return ['nom', 'score_ecologique']
        
        # Check for CO2 economy query
        if entity == 'trajets' and self._has_keyword(ATTRIBUTE_MAPPINGS['economie_co2']):
            return ['trajet_id', 'economie_co2']
        
        # Default: return main identifying attributes
        if entity == 'zones':
            return ['nom']
        elif entity == 'capteurs':
            return ['capteur_id', 'statut']
        elif entity == 'citoyens':
            return ['nom']
        elif entity == 'trajets':
            return ['trajet_id']
        
        return ['*']
    
    def _detect_conditions(self, entity: str) -> List[Condition]:
        """Detect WHERE conditions - FIXED to handle multiple conditions properly"""
        conditions = []
        
        # Join tokens to handle multi-word phrases
        query_text = ' '.join(self.tokens)
        
        # 1. Check for ZONE filters (e.g., "zone 2", "zone 5")
        zone_id = self._extract_zone_id()
        if zone_id is not None:
            conditions.append(Condition('zone_id', '=', zone_id))
        
        # 2. Check for SENSOR TYPE filters (e.g., "type air", "capteurs de bruit")
        sensor_type = self._extract_sensor_type()
        if sensor_type:
            conditions.append(Condition('type_capteur', '=', f"'{sensor_type}'"))
        
        # 3. Check for STATUS conditions (with longest-match priority)
        status_matches = []
        for status, keywords in STATUS_VALUES.items():
            for keyword in keywords:
                if keyword in query_text:
                    status_matches.append((len(keyword), status))
        
        if status_matches:
            # Sort by length descending, take the longest (most specific)
            status_matches.sort(reverse=True)
            most_specific_status = status_matches[0][1]
            conditions.append(Condition('statut', '=', f"'{most_specific_status}'"))
        
        # 4. Check for TIME PERIOD filters
        time_condition = self._extract_time_condition()
        if time_condition:
            conditions.append(time_condition)
        
        # 5. Check for comparison operators with numbers
        for i, token in enumerate(self.tokens):
            # Look for operator followed by number
            for op_symbol, op_keywords in OPERATORS.items():
                if token in op_keywords or token == op_symbol:
                    # Find the number
                    if i + 1 < len(self.tokens) and self.tokens[i + 1].replace('.', '').isdigit():
                        number = self.tokens[i + 1]
                        
                        # Determine which attribute this applies to
                        if self._has_keyword(ATTRIBUTE_MAPPINGS['score_ecologique']):
                            conditions.append(Condition('score_ecologique', op_symbol, number))
                        elif self._has_keyword(ATTRIBUTE_MAPPINGS['taux_erreur']):
                            conditions.append(Condition('taux_erreur', op_symbol, number))
        
        return conditions
    
    def _extract_zone_id(self) -> Optional[int]:
        """Extract zone number from query (e.g., 'zone 2' → 2)"""
        query_text = ' '.join(self.tokens)
        
        # Pattern: "zone <number>" or "zone_id <number>"
        match = re.search(r'zone\s+(\d+)', query_text)
        if match:
            return int(match.group(1))
        
        # Check for "de la zone <number>"
        match = re.search(r'de\s+la\s+zone\s+(\d+)', query_text)
        if match:
            return int(match.group(1))
        
        return None
    
    def _extract_sensor_type(self) -> Optional[str]:
        """Extract sensor type from query (air, bruit, trafic)"""
        query_text = ' '.join(self.tokens)
        
        # Check for explicit type mentions with longest match priority
        type_matches = []
        for sensor_type, keywords in SENSOR_TYPE_VALUES.items():
            for keyword in keywords:
                if keyword in query_text:
                    type_matches.append((len(keyword), sensor_type))
        
        if type_matches:
            type_matches.sort(reverse=True)
            return type_matches[0][1]
        
        return None
    
    def _extract_time_condition(self) -> Optional[Condition]:
        """Extract time-based filter conditions"""
        query_text = ' '.join(self.tokens)
        
        # Check for "ce mois-ci" (this month)
        for pattern in TIME_PERIODS['this_month']:
            if pattern in query_text:
                return Condition(
                    'date_installation',
                    '=',
                    "strftime('%Y-%m', date_installation) = strftime('%Y-%m', 'now')"
                )
        
        # Check for "cette semaine" (this week)
        for pattern in TIME_PERIODS['this_week']:
            if pattern in query_text:
                return Condition(
                    'date_installation',
                    '>=',
                    "date('now', 'weekday 0', '-7 days')"
                )
        
        # Check for "aujourd'hui" (today)
        for pattern in TIME_PERIODS['today']:
            if pattern in query_text:
                return Condition(
                    'date_installation',
                    '=',
                    "date('now')"
                )
        
        # Check for "récemment" (recently - last 30 days)
        for pattern in TIME_PERIODS['recently']:
            if pattern in query_text:
                return Condition(
                    'date_installation',
                    '>=',
                    "date('now', '-30 days')"
                )
        
        return None
    
    def _detect_ordering(self, entity: str) -> tuple:
        """Detect ORDER BY clause"""
        order_by = None
        order_dir = 'DESC'  # Default to descending for "top X" queries
        
        # Check for "plus" keyword (most polluted, most economical, etc.)
        if 'plus' in self.tokens:
            order_dir = 'DESC'
            
            if self._has_keyword(POLLUTION_PATTERNS['avg_pm25']):
                order_by = 'pollution_moyenne'
            elif self._has_keyword(ATTRIBUTE_MAPPINGS['economie_co2']):
                order_by = 'economie_co2'
            elif self._has_keyword(ATTRIBUTE_MAPPINGS['score_ecologique']):
                order_by = 'score_ecologique'
        
        return order_by, order_dir
    
    def _detect_limit(self) -> Optional[int]:
        """Detect LIMIT clause"""
        query_text = ' '.join(self.tokens)
        
        # Check for "le/la plus" pattern (the most/best)
        if 'le plus' in query_text or 'la plus' in query_text or 'le meilleur' in query_text:
            return 1
        
        # Check for explicit numbers like "les 5 zones"
        for i, token in enumerate(self.tokens):
            if token.isdigit() and i > 0:
                # Check if it's part of a "top N" or "N zones" pattern
                prev_token = self.tokens[i - 1]
                if prev_token in ['les', 'premiers', 'derniers'] or i == 1:
                    return int(token)
        
        return None
    
    def _detect_group_by(self, entity: str) -> Optional[str]:
        """Detect GROUP BY clause (for aggregates)"""
        if self._has_keyword(POLLUTION_PATTERNS['avg_pm25']) and entity == 'zones':
            return 'z.zone_id, z.nom'
        return None
    
    def _detect_joins(self, entity: str) -> List[Join]:
        """Detect necessary JOIN clauses"""
        joins = []
        
        # Pollution query needs joins: zones <- capteurs <- mesures
        if self._has_keyword(POLLUTION_PATTERNS['avg_pm25']) and entity == 'zones':
            joins.append(Join(
                table='capteurs c',
                on_left='c.zone_id',
                on_right='z.zone_id'
            ))
            joins.append(Join(
                table='mesures m',
                on_left='m.capteur_id',
                on_right='c.capteur_id'
            ))
        
        return joins
    
    def _has_keyword(self, keywords: List[str]) -> bool:
        """Check if any keyword exists in tokens"""
        return any(kw in self.tokens for kw in keywords)


# Example usage
if __name__ == "__main__":
    from .lexer import Lexer
    
    lexer = Lexer()
    parser_class = Parser
    
    test_queries = [
        "Combien de capteurs de la zone 2",
        "Combien de capteurs de type air existent",
        "Combien de capteurs de bruit sont actif",
        "Combien de capteurs ont été installés ce mois-ci",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        tokens = lexer.tokenize(query)
        parser = parser_class(tokens)
        
        try:
            ast = parser.parse()
            print(f"AST: {ast}")
        except ParseError as e:
            print(f"Parse Error: {e}")