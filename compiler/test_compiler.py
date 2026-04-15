"""
Test suite for the NL to SQL compiler
Tests all example queries from the project PDF
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler import NLQueryCompiler, CompilationError
from database.db_utils import execute_query


def test_compiler_syntax():
    """Test compilation without database execution"""
    compiler = NLQueryCompiler()
    
    test_cases = [
        {
            'query': "Affiche les 5 zones les plus polluées",
            'expected_keywords': ['SELECT', 'zones', 'AVG', 'PM2.5', 'LIMIT 5', 'DESC']
        },
        {
            'query': "Combien de capteurs sont hors service ?",
            'expected_keywords': ['COUNT', 'capteurs', 'hors_service']
        },
        {
            'query': "Quels citoyens ont un score écologique > 80 ?",
            'expected_keywords': ['SELECT', 'citoyens', 'score_ecologique', '> 80']
        },
        {
            'query': "Donne-moi le trajet le plus économique en CO2",
            'expected_keywords': ['SELECT', 'trajets', 'economie_co2', 'DESC', 'LIMIT 1']
        },
    ]
    
    print("\n" + "="*70)
    print("COMPILATION TESTS (Syntax Only)")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['query']}")
        
        try:
            sql = compiler.compile(test['query'])
            print(f"✅ Compiled: {sql}")
            
            # Check if expected keywords are present
            missing = [kw for kw in test['expected_keywords'] if kw not in sql]
            if missing:
                print(f"⚠️  Missing expected keywords: {missing}")
                failed += 1
            else:
                passed += 1
                
        except CompilationError as e:
            print(f"❌ Compilation failed: {e.message}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return passed, failed


def test_compiler_with_database():
    """Test compilation AND execution against real database"""
    compiler = NLQueryCompiler()
    
    test_queries = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
        "Donne-moi le trajet le plus économique en CO2",
    ]
    
    print("\n" + "="*70)
    print("END-TO-END TESTS (Compilation + Database Execution)")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}] {query}")
        
        try:
            # Compile
            sql = compiler.compile(query)
            print(f"SQL: {sql}")
            
            # Execute
            results = execute_query(sql)
            print(f"✅ Returned {len(results)} rows")
            
            # Show first few results
            for row in results[:3]:
                print(f"   {dict(row)}")
            
            passed += 1
            
        except CompilationError as e:
            print(f"❌ Compilation error: {e.message}")
            failed += 1
        except Exception as e:
            print(f"❌ Execution error: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return passed, failed


if __name__ == "__main__":
    print("\n🧪 COMPILER TEST SUITE\n")
    
    # Run syntax tests
    syntax_passed, syntax_failed = test_compiler_syntax()
    
    # Run database tests
    db_passed, db_failed = test_compiler_with_database()
    
    # Summary
    total_passed = syntax_passed + db_passed
    total_failed = syntax_failed + db_failed
    
    print(f"\n{'='*70}")
    print(f"📊 FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("="*70 + "\n")