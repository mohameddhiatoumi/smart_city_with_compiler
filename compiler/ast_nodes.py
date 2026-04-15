"""
Abstract Syntax Tree (AST) node definitions
Represents the structure of a parsed query
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass


@dataclass
class SelectQuery(ASTNode):
    """Represents a SELECT query"""
    entity: str                      # Table name (e.g., 'zones', 'capteurs')
    attributes: List[str]            # Columns to select (e.g., ['nom', 'AVG(pollution)'])
    conditions: List['Condition']    # WHERE conditions
    group_by: Optional[str] = None   # GROUP BY column
    order_by: Optional[str] = None   # ORDER BY column
    order_dir: str = 'DESC'          # ASC or DESC
    limit: Optional[int] = None      # LIMIT value
    joins: List['Join'] = None       # JOIN clauses
    
    def __post_init__(self):
        if self.joins is None:
            self.joins = []


@dataclass
class CountQuery(ASTNode):
    """Represents a COUNT query"""
    entity: str                      # Table to count from
    conditions: List['Condition']    # WHERE conditions


@dataclass
class Condition(ASTNode):
    """Represents a WHERE condition"""
    attribute: str      # Column name
    operator: str       # Comparison operator (>, <, =, etc.)
    value: any          # Value to compare against
    
    def __repr__(self):
        return f"{self.attribute} {self.operator} {self.value}"


@dataclass
class Join(ASTNode):
    """Represents a JOIN clause"""
    table: str          # Table to join
    on_left: str        # Left side of ON condition (e.g., 'c.zone_id')
    on_right: str       # Right side of ON condition (e.g., 'z.zone_id')
    join_type: str = 'INNER'  # INNER, LEFT, RIGHT, etc.


@dataclass
class AggregateFunction(ASTNode):
    """Represents an aggregate function like AVG, SUM, etc."""
    function: str       # AVG, SUM, COUNT, MAX, MIN
    attribute: str      # Column to aggregate
    alias: Optional[str] = None  # AS alias
    
    def __repr__(self):
        result = f"{self.function}({self.attribute})"
        if self.alias:
            result += f" AS {self.alias}"
        return result