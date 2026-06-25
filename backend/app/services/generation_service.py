"""
Generation engine using Azure OpenAI GPT-4o.
Generates requirements, test cases, user stories, and more from code context.
"""

import json
import uuid
import time
import asyncio
from datetime import datetime
from typing import Optional

from app.config import get_settings
from app.models.schemas import (
    GenerationResult, GenerationStatus, Requirement, RequirementType,
    UserStory, TestCase, EdgeCase, ValidationRule, Priority, Severity,
    RepositorySummary, FileAnalysis,
)
from app.utils.logger import get_logger
from app.utils.prompts import SYSTEM_PROMPT, build_generation_prompt
from app.utils.retry import retry_async

logger = get_logger("generation")


class GenerationEngine:
    """Core GPT-4o generation engine for requirements and test cases."""

    def __init__(self):
        self.settings = get_settings()
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            from openai import AzureOpenAI
            self._llm_client = AzureOpenAI(
                api_key=self.settings.AZURE_OPENAI_API_KEY,
                api_version=self.settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
            )
        return self._llm_client

    async def generate(self, repo_id: str, repo_summary: RepositorySummary,
                       code_chunks: list[dict], categories: list[str],
                       target_modules: list[str] = None) -> GenerationResult:
        generation_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        logger.info(f"Starting generation {generation_id} for repo {repo_id}")

        result = GenerationResult(
            generation_id=generation_id, repo_id=repo_id,
            status=GenerationStatus.GENERATING, repo_summary=repo_summary,
        )

        if self.settings.MOCK_MODE:
            result = self._mock_generate(result, categories)
        else:
            arch_summary = self._build_architecture_summary(repo_summary)
            
            if target_modules:
                logger.info(f"Using exhaustive map-reduce generation for modules: {target_modules}")
                await self._generate_map_reduce(result, code_chunks, arch_summary, categories)
            else:
                code_context = self._build_code_context(code_chunks)
                for category in categories:
                    try:
                        prompt = build_generation_prompt(category, code_context, arch_summary)
                        data = await self._call_llm(prompt)
                        self._parse_category_result(result, category, data)
                    except Exception as e:
                        logger.exception(f"Failed to generate {category}: {e}")

        result.status = GenerationStatus.COMPLETED
        result.processing_time_seconds = round(time.time() - start_time, 2)
        result.created_at = datetime.utcnow()
        logger.info(f"Generation {generation_id} completed in {result.processing_time_seconds}s")
        return result

    async def _generate_map_reduce(self, result: GenerationResult, code_chunks: list[dict], arch_summary: str, categories: list[str]):
        """File-by-file generation using asyncio.gather."""
        # Group chunks by file
        files_map = {}
        for c in code_chunks:
            fp = c.get("file_path", "unknown")
            if fp not in files_map:
                files_map[fp] = []
            files_map[fp].append(c.get("code_text", ""))
        
        # Limit concurrency to avoid Azure OpenAI rate limits
        sem = asyncio.Semaphore(3)
        
        async def process_file(file_path: str, file_chunks: list[str]):
            async with sem:
                code_context = "\n\n---\n\n".join(file_chunks)
                for category in categories:
                    try:
                        prompt = build_generation_prompt(category, code_context, arch_summary)
                        data = await self._call_llm(prompt)
                        self._parse_category_result(result, category, data)
                        logger.info(f"Map-reduce generated {category} for {file_path}")
                    except Exception as e:
                        logger.exception(f"Failed map-reduce on {file_path} for {category}: {e}")
                        
        tasks = [process_file(fp, chunks) for fp, chunks in files_map.items()]
        await asyncio.gather(*tasks)

    async def _call_llm(self, prompt: str) -> dict:
        async def _call():
            response = self.llm_client.chat.completions.create(
                model=self.settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2, max_tokens=4000,
            )
            return json.loads(response.choices[0].message.content)
        return await retry_async(_call, max_retries=2, operation_name="LLM generation")

    def _build_architecture_summary(self, summary: RepositorySummary) -> str:
        parts = [f"Repository: {summary.repo_name}"]
        if summary.detected_frameworks:
            parts.append(f"Frameworks: {', '.join(f.value for f in summary.detected_frameworks)}")
        parts.append(f"Languages: {summary.languages}")
        parts.append(f"Files: {summary.total_files}, Lines: {summary.total_lines}")
        parts.append(f"Routes: {summary.route_count}, Models: {summary.model_count}")
        parts.append(f"Components: {summary.component_count}, Services: {summary.service_count}")
        return "\n".join(parts)

    def _build_code_context(self, chunks: list[dict]) -> str:
        parts = []
        for chunk in chunks[:15]:
            parts.append(chunk.get("code_text", ""))
        return "\n\n---\n\n".join(parts)

    def _safe_priority(self, val: str) -> Priority:
        try:
            return Priority(str(val).lower())
        except (ValueError, TypeError):
            return Priority.MEDIUM

    def _safe_severity(self, val: str) -> Severity:
        try:
            return Severity(str(val).lower())
        except (ValueError, TypeError):
            return Severity.MAJOR

    def _parse_category_result(self, result: GenerationResult, category: str, data: dict):
        if category == "functional":
            for r in data.get("requirements", []):
                result.functional_requirements.append(Requirement(
                    requirement_id=r.get("requirement_id", f"FR-{len(result.functional_requirements)+1:03d}"),
                    module=r.get("module", ""), requirement_type=RequirementType.FUNCTIONAL,
                    description=r.get("description", ""), acceptance_criteria=r.get("acceptance_criteria", ""),
                    source_files=r.get("source_files", []),
                    priority=self._safe_priority(r.get("priority", "medium")), severity=self._safe_severity(r.get("severity", "major")),
                ))
        elif category == "non_functional":
            for r in data.get("requirements", []):
                result.non_functional_requirements.append(Requirement(
                    requirement_id=r.get("requirement_id", f"NFR-{len(result.non_functional_requirements)+1:03d}"),
                    module=r.get("module", ""), requirement_type=RequirementType.NON_FUNCTIONAL,
                    description=r.get("description", ""), acceptance_criteria=r.get("acceptance_criteria", ""),
                    source_files=r.get("source_files", []),
                    priority=self._safe_priority(r.get("priority", "medium")), severity=self._safe_severity(r.get("severity", "major")),
                ))
        elif category == "api":
            for r in data.get("requirements", []):
                result.api_requirements.append(Requirement(
                    requirement_id=r.get("requirement_id", f"API-{len(result.api_requirements)+1:03d}"),
                    module=r.get("module", ""), requirement_type=RequirementType.API,
                    description=r.get("description", ""), acceptance_criteria=r.get("acceptance_criteria", ""),
                    source_files=r.get("source_files", []),
                    priority=self._safe_priority(r.get("priority", "medium")), severity=self._safe_severity(r.get("severity", "major")),
                ))
        elif category == "user_story":
            for s in data.get("user_stories", []):
                result.user_stories.append(UserStory(
                    story_id=s.get("story_id", f"US-{len(result.user_stories)+1:03d}"),
                    module=s.get("module", ""), persona=s.get("persona", ""),
                    action=s.get("action", ""), benefit=s.get("benefit", ""),
                    acceptance_criteria=s.get("acceptance_criteria", []),
                    source_files=s.get("source_files", []),
                    priority=self._safe_priority(s.get("priority", "medium")),
                ))
        elif category == "validation_rule":
            for v in data.get("validation_rules", []):
                result.validation_rules.append(ValidationRule(
                    rule_id=v.get("rule_id", f"VR-{len(result.validation_rules)+1:03d}"),
                    module=v.get("module", ""), field_or_parameter=v.get("field_or_parameter", ""),
                    rule_description=v.get("rule_description", ""),
                    constraint_type=v.get("constraint_type", "custom"),
                    source_files=v.get("source_files", []),
                    priority=self._safe_priority(v.get("priority", "medium")),
                ))
        elif category == "edge_case":
            for e in data.get("edge_cases", []):
                result.edge_cases.append(EdgeCase(
                    edge_case_id=e.get("edge_case_id", f"EC-{len(result.edge_cases)+1:03d}"),
                    module=e.get("module", ""), scenario=e.get("scenario", ""),
                    description=e.get("description", ""),
                    boundary_condition=e.get("boundary_condition", ""),
                    expected_behavior=e.get("expected_behavior", ""),
                    source_files=e.get("source_files", []),
                    severity=self._safe_severity(e.get("severity", "major")),
                ))
        elif category == "unit_test":
            for t in data.get("test_cases", []):
                if not isinstance(t, dict): continue
                try:
                    result.test_cases.append(TestCase(
                        test_id=t.get("test_id", f"TC-{len(result.test_cases)+1:03d}"),
                        module=t.get("module", ""), scenario=t.get("scenario", ""),
                        description=t.get("description", ""), preconditions=t.get("preconditions", ""),
                        test_input=t.get("test_input", ""), expected_output=t.get("expected_output", ""),
                        edge_case=bool(t.get("edge_case", False)), source_files=t.get("source_files", []),
                        related_requirement=t.get("related_requirement", ""),
                        priority=self._safe_priority(t.get("priority", "medium")),
                    ))
                except Exception as e:
                    logger.warning(f"Skipping invalid test case: {e} - data: {t}")

    def _mock_generate(self, result: GenerationResult, categories: list[str]) -> GenerationResult:
        """Generate realistic mock data for development."""
        logger.info("[MOCK] Generating mock requirements")

        if "functional" in categories:
            result.functional_requirements = [
                Requirement(requirement_id="FR-001", module="Authentication", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow users to authenticate using email and password credentials",
                    acceptance_criteria="Given valid credentials, when the user submits login form, then a JWT token is returned",
                    source_files=["app/routers/auth.py", "app/services/auth_service.py"], priority=Priority.CRITICAL, severity=Severity.BLOCKER),
                Requirement(requirement_id="FR-002", module="Authentication", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow new users to register with email, password, and full name",
                    acceptance_criteria="Given valid registration data, when submitted, then a new account is created and JWT token returned",
                    source_files=["app/routers/auth.py"], priority=Priority.CRITICAL, severity=Severity.BLOCKER),
                Requirement(requirement_id="FR-003", module="Products", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall provide product listing with filtering by category, price range, and search text",
                    acceptance_criteria="Given filter parameters, when GET /api/products is called, then matching products are returned with pagination",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH, severity=Severity.CRITICAL),
                Requirement(requirement_id="FR-004", module="Products", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow administrators to create, update, and delete products",
                    acceptance_criteria="Given admin credentials and valid product data, CRUD operations succeed",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH, severity=Severity.CRITICAL),
                Requirement(requirement_id="FR-005", module="Orders", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow authenticated users to create orders with multiple line items",
                    acceptance_criteria="Given valid order items and shipping address, when submitted, then order is created with calculated total",
                    source_files=["app/routers/orders.py"], priority=Priority.CRITICAL, severity=Severity.BLOCKER),
                Requirement(requirement_id="FR-006", module="Orders", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow users to cancel pending or confirmed orders",
                    acceptance_criteria="Given a pending order, when cancel is requested, then order status changes to cancelled",
                    source_files=["app/routers/orders.py"], priority=Priority.HIGH, severity=Severity.MAJOR),
                Requirement(requirement_id="FR-007", module="Users", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow users to view and update their profile information",
                    source_files=["app/routers/users.py"], priority=Priority.MEDIUM, severity=Severity.MAJOR),
                Requirement(requirement_id="FR-008", module="Users", requirement_type=RequirementType.FUNCTIONAL,
                    description="The system shall allow administrators to list all users with pagination",
                    source_files=["app/routers/users.py"], priority=Priority.MEDIUM, severity=Severity.MINOR),
            ]

        if "api" in categories:
            result.api_requirements = [
                Requirement(requirement_id="API-001", module="Auth Router", requirement_type=RequirementType.API,
                    description="POST /api/auth/login — Authenticate user with email/password, returns JWT token with 3600s expiry",
                    acceptance_criteria="200: TokenResponse on success, 401: on invalid credentials",
                    source_files=["app/routers/auth.py"], priority=Priority.CRITICAL, severity=Severity.BLOCKER),
                Requirement(requirement_id="API-002", module="Auth Router", requirement_type=RequirementType.API,
                    description="POST /api/auth/register — Register new user account, returns JWT token",
                    acceptance_criteria="200: TokenResponse, 409: if email exists, 422: on validation error",
                    source_files=["app/routers/auth.py"], priority=Priority.CRITICAL, severity=Severity.BLOCKER),
                Requirement(requirement_id="API-003", module="Products Router", requirement_type=RequirementType.API,
                    description="GET /api/products — List products with optional category, price range, search, and pagination",
                    acceptance_criteria="200: List[Product], supports query params: category, min_price, max_price, search, skip, limit",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH, severity=Severity.CRITICAL),
                Requirement(requirement_id="API-004", module="Products Router", requirement_type=RequirementType.API,
                    description="POST /api/products — Create new product (admin only), validates name length, positive price, non-negative stock",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH, severity=Severity.CRITICAL),
                Requirement(requirement_id="API-005", module="Orders Router", requirement_type=RequirementType.API,
                    description="POST /api/orders — Create order with items list (min 1), shipping address, and payment method",
                    acceptance_criteria="200: Order with calculated total, 400: if total <= 0",
                    source_files=["app/routers/orders.py"], priority=Priority.CRITICAL, severity=Severity.BLOCKER),
                Requirement(requirement_id="API-006", module="Orders Router", requirement_type=RequirementType.API,
                    description="PUT /api/orders/{order_id}/cancel — Cancel an order, only allowed for pending/confirmed orders",
                    source_files=["app/routers/orders.py"], priority=Priority.HIGH, severity=Severity.MAJOR),
            ]

        if "user_story" in categories:
            result.user_stories = [
                UserStory(story_id="US-001", module="Authentication", persona="Customer",
                    action="log in with my email and password", benefit="I can access my account and order history",
                    acceptance_criteria=["Login form accepts email and password", "JWT token is returned on success", "Error message shown on invalid credentials"],
                    source_files=["app/routers/auth.py"], priority=Priority.CRITICAL),
                UserStory(story_id="US-002", module="Products", persona="Customer",
                    action="browse and search products by category and price range",
                    benefit="I can quickly find what I want to purchase",
                    acceptance_criteria=["Products can be filtered by category", "Price range filter works", "Search returns relevant results"],
                    source_files=["app/routers/products.py", "src/pages/ProductsPage.tsx"], priority=Priority.HIGH),
                UserStory(story_id="US-003", module="Orders", persona="Customer",
                    action="place an order with multiple items",
                    benefit="I can purchase everything in one transaction",
                    acceptance_criteria=["Order accepts multiple items", "Total is calculated correctly", "Shipping address is required"],
                    source_files=["app/routers/orders.py"], priority=Priority.CRITICAL),
                UserStory(story_id="US-004", module="Products", persona="Admin",
                    action="manage the product catalog (create, update, delete)",
                    benefit="I can keep the store inventory up to date",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH),
            ]

        if "validation_rule" in categories:
            result.validation_rules = [
                ValidationRule(rule_id="VR-001", module="Authentication", field_or_parameter="email",
                    rule_description="Email must be a valid email format (EmailStr validation)", constraint_type="format",
                    source_files=["app/routers/auth.py"], priority=Priority.CRITICAL),
                ValidationRule(rule_id="VR-002", module="Authentication", field_or_parameter="password",
                    rule_description="Password must be at least 8 characters long", constraint_type="range",
                    source_files=["app/services/auth_service.py"], priority=Priority.CRITICAL),
                ValidationRule(rule_id="VR-003", module="Products", field_or_parameter="name",
                    rule_description="Product name must be 1-200 characters", constraint_type="range",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH),
                ValidationRule(rule_id="VR-004", module="Products", field_or_parameter="price",
                    rule_description="Product price must be greater than 0", constraint_type="range",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH),
                ValidationRule(rule_id="VR-005", module="Products", field_or_parameter="stock",
                    rule_description="Product stock must be non-negative (>= 0)", constraint_type="range",
                    source_files=["app/routers/products.py"], priority=Priority.HIGH),
                ValidationRule(rule_id="VR-006", module="Orders", field_or_parameter="items",
                    rule_description="Order must contain at least 1 item", constraint_type="range",
                    source_files=["app/routers/orders.py"], priority=Priority.CRITICAL),
                ValidationRule(rule_id="VR-007", module="Users", field_or_parameter="user_id",
                    rule_description="User ID must be a positive integer", constraint_type="range",
                    source_files=["app/routers/users.py"], priority=Priority.MEDIUM),
                ValidationRule(rule_id="VR-008", module="Users", field_or_parameter="limit",
                    rule_description="Pagination limit must be between 1 and 100", constraint_type="range",
                    source_files=["app/routers/users.py"], priority=Priority.MEDIUM),
            ]

        if "edge_case" in categories:
            result.edge_cases = [
                EdgeCase(edge_case_id="EC-001", module="Authentication", scenario="Empty password login attempt",
                    description="User attempts login with empty or null password",
                    boundary_condition="password is empty string or None", expected_behavior="Return 401 Unauthorized",
                    source_files=["app/routers/auth.py"], severity=Severity.CRITICAL),
                EdgeCase(edge_case_id="EC-002", module="Orders", scenario="Order with zero-price items",
                    description="User creates order where all items have 0 total value",
                    boundary_condition="sum of (price * quantity) = 0", expected_behavior="Return 400 Bad Request",
                    source_files=["app/routers/orders.py"], severity=Severity.MAJOR),
                EdgeCase(edge_case_id="EC-003", module="Products", scenario="Negative product ID in path",
                    description="User requests product with negative or zero ID",
                    boundary_condition="product_id <= 0", expected_behavior="Return 400 with 'Invalid product ID'",
                    source_files=["app/routers/products.py"], severity=Severity.MINOR),
                EdgeCase(edge_case_id="EC-004", module="Users", scenario="Delete non-existent user",
                    description="Admin attempts to delete a user ID that doesn't exist in the database",
                    boundary_condition="user_id does not exist", expected_behavior="Return 404 Not Found",
                    source_files=["app/routers/users.py"], severity=Severity.MAJOR),
                EdgeCase(edge_case_id="EC-005", module="Authentication", scenario="Duplicate email registration",
                    description="User attempts to register with an email that already exists",
                    boundary_condition="email already in database", expected_behavior="Return 409 Conflict",
                    source_files=["app/routers/auth.py"], severity=Severity.CRITICAL),
            ]

        if "unit_test" in categories:
            result.test_cases = [
                TestCase(test_id="TC-001", module="Authentication", scenario="Successful login",
                    description="Verify that valid credentials return a JWT token",
                    preconditions="User account exists with valid email/password",
                    test_input='POST /api/auth/login {"email": "user@test.com", "password": "password123"}',
                    expected_output="200 OK with {access_token, token_type: 'bearer', expires_in: 3600}",
                    source_files=["app/routers/auth.py"], related_requirement="FR-001", priority=Priority.CRITICAL),
                TestCase(test_id="TC-002", module="Authentication", scenario="Login with invalid password",
                    description="Verify that wrong password returns 401",
                    test_input='POST /api/auth/login {"email": "user@test.com", "password": "wrong"}',
                    expected_output="401 Unauthorized", edge_case=True,
                    source_files=["app/routers/auth.py"], related_requirement="FR-001", priority=Priority.CRITICAL),
                TestCase(test_id="TC-003", module="Products", scenario="List products with category filter",
                    description="Verify product listing filters by category correctly",
                    test_input="GET /api/products?category=Electronics",
                    expected_output="200 OK with list of products in Electronics category",
                    source_files=["app/routers/products.py"], related_requirement="FR-003", priority=Priority.HIGH),
                TestCase(test_id="TC-004", module="Products", scenario="Create product with invalid price",
                    description="Verify that creating product with price <= 0 fails validation",
                    test_input='POST /api/products {"name": "Test", "price": -10, "category": "Test"}',
                    expected_output="422 Unprocessable Entity", edge_case=True,
                    source_files=["app/routers/products.py"], related_requirement="API-004", priority=Priority.HIGH),
                TestCase(test_id="TC-005", module="Orders", scenario="Create order and verify total calculation",
                    description="Verify order total is correctly calculated from item prices and quantities",
                    test_input='POST /api/orders {"items": [{"product_id": 1, "quantity": 2, "price": 25.00}], "shipping_address": "123 St", "payment_method": "card"}',
                    expected_output="200 OK with total_amount = 50.00",
                    source_files=["app/routers/orders.py"], related_requirement="FR-005", priority=Priority.CRITICAL),
                TestCase(test_id="TC-006", module="Orders", scenario="Create order with empty items list",
                    description="Verify that order with no items fails validation",
                    test_input='POST /api/orders {"items": [], "shipping_address": "123 St", "payment_method": "card"}',
                    expected_output="422 Unprocessable Entity (min_length=1)", edge_case=True,
                    source_files=["app/routers/orders.py"], related_requirement="VR-006", priority=Priority.HIGH),
                TestCase(test_id="TC-007", module="Users", scenario="Update user profile",
                    description="Verify that PUT /me updates the user's profile fields",
                    test_input='PUT /api/users/me {"full_name": "Jane Doe"}',
                    expected_output="200 OK with updated full_name",
                    source_files=["app/routers/users.py"], related_requirement="FR-007", priority=Priority.MEDIUM),
                TestCase(test_id="TC-008", module="Users", scenario="Delete user with invalid ID",
                    description="Verify that deleting user with ID <= 0 returns 400",
                    test_input="DELETE /api/users/0",
                    expected_output="400 Bad Request with 'Invalid user ID'", edge_case=True,
                    source_files=["app/routers/users.py"], related_requirement="VR-007", priority=Priority.MEDIUM),
            ]

        return result


def get_generation_engine() -> GenerationEngine:
    return GenerationEngine()
