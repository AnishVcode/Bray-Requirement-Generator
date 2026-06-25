/* TypeScript types for the Requirement Generator frontend */

export interface Requirement {
  requirement_id: string;
  module: string;
  requirement_type: string;
  description: string;
  acceptance_criteria: string;
  source_files: string[];
  priority: string;
  severity: string;
  related_requirements: string[];
}

export interface UserStory {
  story_id: string;
  module: string;
  persona: string;
  action: string;
  benefit: string;
  acceptance_criteria: string[];
  source_files: string[];
  priority: string;
}

export interface TestCase {
  test_id: string;
  module: string;
  scenario: string;
  description: string;
  preconditions: string;
  test_input: string;
  expected_output: string;
  edge_case: boolean;
  source_files: string[];
  related_requirement: string;
  priority: string;
}

export interface EdgeCase {
  edge_case_id: string;
  module: string;
  scenario: string;
  description: string;
  boundary_condition: string;
  expected_behavior: string;
  source_files: string[];
  severity: string;
}

export interface ValidationRule {
  rule_id: string;
  module: string;
  field_or_parameter: string;
  rule_description: string;
  constraint_type: string;
  source_files: string[];
  priority: string;
}

export interface RepositorySummary {
  repo_id: string;
  repo_name: string;
  detected_frameworks: string[];
  languages: Record<string, number>;
  total_files: number;
  total_lines: number;
  route_count: number;
  model_count: number;
  component_count: number;
  service_count: number;
  test_file_count: number;
}

export interface GenerationResult {
  generation_id: string;
  repo_id: string;
  status: string;
  functional_requirements: Requirement[];
  non_functional_requirements: Requirement[];
  api_requirements: Requirement[];
  user_stories: UserStory[];
  validation_rules: ValidationRule[];
  edge_cases: EdgeCase[];
  test_cases: TestCase[];
  repo_summary: RepositorySummary | null;
  created_at: string;
  processing_time_seconds: number;
  error: string;
}

export interface UploadResponse {
  repo_id: string;
  status: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  mock_mode: boolean;
  services: Record<string, string>;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface GenerationRequest {
  categories: string[];
  target_modules?: string[];
}

export interface ChatRequest {
  messages: ChatMessage[];
}

export interface ChatResponse {
  message: ChatMessage;
  retrieved_chunks: Record<string, any>[];

