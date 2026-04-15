from fastapi import APIRouter, HTTPException
from compiler.compiler import NLQueryCompiler, CompilationError
from database.db_utils import execute_query

router = APIRouter()
compiler = NLQueryCompiler()

@router.post("/query")
async def natural_language_query(query: str):
    """
    Execute natural language query
    
    Args:
        query: French natural language query
    
    Returns:
        Query results and generated SQL
    """
    try:
        # Compile to SQL
        sql = compiler.compile(query)
        
        # Execute against database
        results = execute_query(sql)
        
        return {
            "success": True,
            "query": query,
            "sql": sql,
            "results": [dict(row) for row in results],
            "count": len(results)
        }
        
    except CompilationError as e:
        raise HTTPException(status_code=400, detail={
            "error": "Compilation failed",
            "stage": e.stage,
            "message": e.message
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Execution failed",
            "message": str(e)
        })