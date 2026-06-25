import asyncio
import json
from app.services.generation_service import get_generation_engine
from app.models.schemas import RepositorySummary, GenerationResult

async def test_generation():
    engine = get_generation_engine()
    repo_summary = RepositorySummary(
        repo_id="test", repo_name="test-repo", detected_frameworks=[],
        languages={"Python": 100}, total_files=10, total_lines=500,
        route_count=5, model_count=2, component_count=0, service_count=3, test_file_count=0
    )
    code_chunks = [{"code_text": "def my_func(): pass"}]
    categories = ["functional", "api", "user_story", "validation_rule", "edge_case", "unit_test"]
    
    # Run generation
    try:
        result = await engine.generate("test", repo_summary, code_chunks, categories)
        print("Generated functional reqs:", len(result.functional_requirements))
        print("Generated API reqs:", len(result.api_requirements))
        print("Generated unit tests:", len(result.test_cases))
        print("Error field on result:", result.error)
    except Exception as e:
        print("Top-level Exception:", e)

if __name__ == "__main__":
    asyncio.run(test_generation())
