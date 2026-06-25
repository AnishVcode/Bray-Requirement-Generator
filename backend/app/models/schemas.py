"""
Pydantic models for the Requirement Generator application.
Defines schemas for requests, responses, and internal data structures.
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Enums ──────────────────────────────────────────────────────────────────────

class ProcessingStatus(str, Enum):
    """Status of repository processing."""
    PENDING = "pending"
    CLONING = "cloning"
    PREPROCESSING = "preprocessing"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationStatus(str, Enum):
    """Status of requirement generation."""
    PENDING = "pending"
    RETRIEVING = "retrieving"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class RequirementType(str, Enum):
    """Type of requirement."""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    API = "api"
    USER_STORY = "user_story"
    VALIDATION_RULE = "validation_rule"
    EDGE_CASE = "edge_case"
    UNIT_TEST = "unit_test"


class Priority(str, Enum):
    """Priority level."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    """Severity level."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class ExportFormat(str, Enum):
    """Export format."""
    EXCEL = "excel"
    PDF = "pdf"
    MARKDOWN = "markdown"


class DetectedFramework(str, Enum):
    """Detected application framework."""
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    ANGULAR = "angular"
    EXPRESS = "express"
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    NESTJS = "nestjs"
    SPRING = "spring"
    UNKNOWN = "unknown"


# ─── Code Analysis Models ───────────────────────────────────────────────────────

class CodeElement(BaseModel):
    """A single extracted code element (function, class, route, etc.)."""
    name: str
    element_type: str  # function, class, route, model, component, middleware
    file_path: str
    line_number: int = 0
    decorators: list[str] = Field(default_factory=list)
    parameters: list[str] = Field(default_factory=list)
    return_type: str = ""
    docstring: str = ""
    http_method: str = ""  # GET, POST, etc. for routes
    route_path: str = ""  # /api/users etc.
    parent_class: str = ""


class FileAnalysis(BaseModel):
    """Analysis result for a single file."""
    file_path: str
    language: str  # python, javascript, typescript
    framework: DetectedFramework = DetectedFramework.UNKNOWN
    elements: list[CodeElement] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    line_count: int = 0
    has_tests: bool = False


class RepositorySummary(BaseModel):
    """Summary of a parsed repository."""
    repo_id: str
    repo_name: str
    detected_frameworks: list[DetectedFramework] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)  # language -> file count
    total_files: int = 0
    total_lines: int = 0
    route_count: int = 0
    model_count: int = 0
    component_count: int = 0
    service_count: int = 0
    test_file_count: int = 0
    file_analyses: list[FileAnalysis] = Field(default_factory=list)


# ─── Request Models ─────────────────────────────────────────────────────────────

class GitHubURLRequest(BaseModel):
    """Request to analyze a GitHub repository."""
    github_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to analyze")


class GenerationRequest(BaseModel):
    """Request to generate requirements for a processed repo."""
    categories: list[RequirementType] = Field(
        default_factory=lambda: [
            RequirementType.FUNCTIONAL,
            RequirementType.API,
            RequirementType.USER_STORY,
            RequirementType.VALIDATION_RULE,
            RequirementType.EDGE_CASE,
            RequirementType.UNIT_TEST,
        ],
        description="Categories of requirements to generate",
    )
    target_modules: list[str] = Field(default_factory=list, description="List of module directories to perform exhaustive generation on. If empty, uses generic vector search.")


# ─── Response Models ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    mock_mode: bool
    services: dict[str, str] = Field(default_factory=dict)


class RepositoryStatusResponse(BaseModel):
    """Repository processing status response."""
    repo_id: str
    status: ProcessingStatus
    progress_message: str = ""
    progress_percent: int = 0
    error: str = ""


class UploadResponse(BaseModel):
    """Response after uploading/cloning a repository."""
    repo_id: str
    status: ProcessingStatus
    message: str


# ─── Requirement Models ─────────────────────────────────────────────────────────

class Requirement(BaseModel):
    """A single generated requirement."""
    requirement_id: str
    module: str
    requirement_type: RequirementType
    description: str
    acceptance_criteria: str = ""
    source_files: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    severity: Severity = Severity.MAJOR
    related_requirements: list[str] = Field(default_factory=list)


class UserStory(BaseModel):
    """A user story in As-a/I-want/So-that format."""
    story_id: str
    module: str
    persona: str
    action: str
    benefit: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM


class TestCase(BaseModel):
    """A unit test case."""
    test_id: str
    module: str
    scenario: str
    description: str
    preconditions: str = ""
    test_input: str = ""
    expected_output: str = ""
    edge_case: bool = False
    source_files: list[str] = Field(default_factory=list)
    related_requirement: str = ""
    priority: Priority = Priority.MEDIUM


class EdgeCase(BaseModel):
    """An identified edge case."""
    edge_case_id: str
    module: str
    scenario: str
    description: str
    boundary_condition: str = ""
    expected_behavior: str = ""
    source_files: list[str] = Field(default_factory=list)
    severity: Severity = Severity.MAJOR


class ValidationRule(BaseModel):
    """A validation rule."""
    rule_id: str
    module: str
    field_or_parameter: str
    rule_description: str
    constraint_type: str = ""  # type, range, format, required, custom
    source_files: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM


class GenerationResult(BaseModel):
    """Complete generation results."""
    generation_id: str
    repo_id: str
    status: GenerationStatus = GenerationStatus.COMPLETED
    functional_requirements: list[Requirement] = Field(default_factory=list)
    non_functional_requirements: list[Requirement] = Field(default_factory=list)
    api_requirements: list[Requirement] = Field(default_factory=list)
    user_stories: list[UserStory] = Field(default_factory=list)
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    edge_cases: list[EdgeCase] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)
    repo_summary: Optional[RepositorySummary] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: float = 0.0
    error: str = ""


class GenerationStatusResponse(BaseModel):
    """Generation status response."""
    generation_id: str
    repo_id: str
    status: GenerationStatus
    progress_message: str = ""
    progress_percent: int = 0
    error: str = ""


# ─── Chat Models ────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request for a new chat completion."""
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    """Response from the chat completion."""
    message: ChatMessage
    retrieved_chunks: list[dict] = Field(default_factory=list)

