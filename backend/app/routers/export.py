"""
Export router — download generated requirements in Excel/PDF/Markdown.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.services.export_service import get_export_service
from app.utils.logger import get_logger

logger = get_logger("router.export")
router = APIRouter()


@router.get("/export/{generation_id}/excel")
async def export_excel(generation_id: str, request: Request):
    """Download requirements as Excel spreadsheet."""
    result = request.app.state.generations.get(generation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation not found")

    export_service = get_export_service()
    content = export_service.export_to_excel(result)
    repo_name = result.repo_summary.repo_name.replace("/", "_") if result.repo_summary else "requirements"

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{repo_name}_requirements.xlsx"'},
    )


@router.get("/export/{generation_id}/pdf")
async def export_pdf(generation_id: str, request: Request):
    """Download requirements as PDF report."""
    result = request.app.state.generations.get(generation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation not found")

    export_service = get_export_service()
    content = export_service.export_to_pdf(result)
    repo_name = result.repo_summary.repo_name.replace("/", "_") if result.repo_summary else "requirements"

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{repo_name}_requirements.pdf"'},
    )


@router.get("/export/{generation_id}/markdown")
async def export_markdown(generation_id: str, request: Request):
    """Download requirements as Markdown document."""
    result = request.app.state.generations.get(generation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation not found")

    export_service = get_export_service()
    content = export_service.export_to_markdown(result)
    repo_name = result.repo_summary.repo_name.replace("/", "_") if result.repo_summary else "requirements"

    return Response(
        content=content.encode("utf-8"),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{repo_name}_requirements.md"'},
    )
