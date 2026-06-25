"""
LLM prompt templates for requirement and test case generation.
All prompts are centralized here for easy iteration and testing.
"""


SYSTEM_PROMPT = """You are a senior software architect, requirements engineer, and QA specialist with 20+ years of experience.
You analyze source code and infer comprehensive software requirements, business rules, and test scenarios.
You produce structured, actionable outputs in JSON format.
Always be thorough but concise. Focus on real functional behaviors observed in the code, not generic boilerplate."""


FUNCTIONAL_REQUIREMENTS_PROMPT = """## Task
Analyze the following source code context and generate detailed functional requirements.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
For each distinct feature or behavior you observe in the code, generate a functional requirement.
Focus on:
- What the system does (user-facing features)
- Data processing and transformations
- Integration points with external systems
- Authentication and authorization flows
- Business logic and rules

Return a JSON object with this structure:
{{
    "requirements": [
        {{
            "requirement_id": "FR-001",
            "module": "module/component name",
            "description": "The system shall ...",
            "acceptance_criteria": "Given/When/Then format",
            "source_files": ["file1.py", "file2.tsx"],
            "priority": "critical" | "high" | "medium" | "low",
            "severity": "blocker" | "critical" | "major" | "minor" | "trivial"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


NON_FUNCTIONAL_REQUIREMENTS_PROMPT = """## Task
Analyze the following source code context and generate non-functional requirements.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
Infer non-functional requirements based on code patterns:
- Performance (response times, throughput, caching)
- Security (authentication, encryption, input validation)
- Scalability (concurrency, batch processing, connection pooling)
- Reliability (error handling, retries, circuit breakers)
- Maintainability (logging, monitoring, configuration)

Return a JSON object with this structure:
{{
    "requirements": [
        {{
            "requirement_id": "NFR-001",
            "module": "module/component name",
            "description": "The system shall ...",
            "acceptance_criteria": "Measurable criteria",
            "source_files": ["file1.py"],
            "priority": "critical" | "high" | "medium" | "low",
            "severity": "blocker" | "critical" | "major" | "minor" | "trivial"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


API_REQUIREMENTS_PROMPT = """## Task
Analyze the following source code context and generate API requirements.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
For each API endpoint found in the code, generate a requirement covering:
- HTTP method and path
- Request body/parameters schema
- Response format and status codes
- Authentication requirements
- Rate limiting and validation
- Error handling

Return a JSON object with this structure:
{{
    "requirements": [
        {{
            "requirement_id": "API-001",
            "module": "module/router name",
            "description": "Endpoint: METHOD /path — description of purpose and behavior",
            "acceptance_criteria": "Expected request/response behavior",
            "source_files": ["router.py"],
            "priority": "critical" | "high" | "medium" | "low",
            "severity": "blocker" | "critical" | "major" | "minor" | "trivial"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


USER_STORIES_PROMPT = """## Task
Analyze the following source code context and generate user stories.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
Infer user stories from the features implemented in the code.
Use standard format: As a [persona], I want [action], so that [benefit].

Return a JSON object with this structure:
{{
    "user_stories": [
        {{
            "story_id": "US-001",
            "module": "module name",
            "persona": "role/user type",
            "action": "what they want to do",
            "benefit": "why they want to do it",
            "acceptance_criteria": ["criterion 1", "criterion 2"],
            "source_files": ["file.tsx"],
            "priority": "critical" | "high" | "medium" | "low"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


VALIDATION_RULES_PROMPT = """## Task
Analyze the following source code context and extract validation rules.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
Identify all input validation, data constraints, and business rules:
- Type constraints (string, int, enum values)
- Range constraints (min/max values, lengths)
- Format constraints (email, URL, date formats)
- Required fields
- Custom business validation logic
- Cross-field validations

Return a JSON object with this structure:
{{
    "validation_rules": [
        {{
            "rule_id": "VR-001",
            "module": "module name",
            "field_or_parameter": "field name",
            "rule_description": "description of the validation",
            "constraint_type": "type" | "range" | "format" | "required" | "custom",
            "source_files": ["models.py"],
            "priority": "critical" | "high" | "medium" | "low"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


EDGE_CASES_PROMPT = """## Task
Analyze the following source code context and identify edge cases.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
Identify boundary conditions, error scenarios, and edge cases:
- Null/empty inputs
- Maximum/minimum values
- Concurrent access scenarios
- Network failures and timeouts
- Invalid state transitions
- Resource exhaustion (memory, connections, rate limits)
- Unicode/special character handling

Return a JSON object with this structure:
{{
    "edge_cases": [
        {{
            "edge_case_id": "EC-001",
            "module": "module name",
            "scenario": "brief scenario title",
            "description": "detailed description of the edge case",
            "boundary_condition": "what boundary is being tested",
            "expected_behavior": "how the system should handle it",
            "source_files": ["service.py"],
            "severity": "blocker" | "critical" | "major" | "minor" | "trivial"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


UNIT_TEST_CASES_PROMPT = """## Task
Analyze the following source code context and generate unit test case scenarios.

## Code Context
{code_context}

## Repository Architecture Summary
{architecture_summary}

## Instructions
Generate comprehensive unit test scenarios for the code:
- Happy path tests
- Error/failure path tests
- Boundary value tests
- Input validation tests
- Mock/stub requirements for external dependencies
- Integration test scenarios

Return a JSON object with this structure:
{{
    "test_cases": [
        {{
            "test_id": "TC-001",
            "module": "module name",
            "scenario": "brief test scenario title",
            "description": "what this test verifies",
            "preconditions": "setup required before test",
            "test_input": "input data or action",
            "expected_output": "expected result",
            "edge_case": true | false,
            "source_files": ["service.py"],
            "related_requirement": "FR-001 or API-001 etc.",
            "priority": "critical" | "high" | "medium" | "low"
        }}
    ]
}}

Return ONLY valid JSON, no markdown formatting or extra text."""


# ─── Prompt category mapping ───

CATEGORY_PROMPTS = {
    "functional": FUNCTIONAL_REQUIREMENTS_PROMPT,
    "non_functional": NON_FUNCTIONAL_REQUIREMENTS_PROMPT,
    "api": API_REQUIREMENTS_PROMPT,
    "user_story": USER_STORIES_PROMPT,
    "validation_rule": VALIDATION_RULES_PROMPT,
    "edge_case": EDGE_CASES_PROMPT,
    "unit_test": UNIT_TEST_CASES_PROMPT,
}


def build_generation_prompt(
    category: str,
    code_context: str,
    architecture_summary: str,
) -> str:
    """Build the generation prompt for a specific category."""
    template = CATEGORY_PROMPTS.get(category, FUNCTIONAL_REQUIREMENTS_PROMPT)
    return template.format(
        code_context=code_context,
        architecture_summary=architecture_summary,
    )
