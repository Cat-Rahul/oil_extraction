/**
 * API Service for Valve Datasheet Automation
 *
 * This module provides typed API calls to the Python backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// === Types ===

export interface DecodedVDS {
  raw_vds: string;
  valve_type_prefix: string;
  valve_type_name: string;
  valve_type_full: string;
  bore_type: string;
  bore_type_name: string;
  piping_class: string;
  end_connection: string;
  end_connection_name: string;
  is_nace_compliant: boolean;
  is_low_temp: boolean;
  is_metal_seated: boolean;
  primary_standard: string;
}

export interface ValidationResult {
  vds_no: string;
  is_valid: boolean;
  error: string | null;
}

export interface FieldTraceability {
  source_type: string;
  source_document: string | null;
  source_value: string | null;
  derivation_rule: string | null;
  clause_reference: string | null;
  confidence: number;
  notes: string | null;
}

export interface DatasheetField {
  field_name: string;
  display_name: string;
  section: string;
  value: unknown;
  is_required: boolean;
  is_populated: boolean;
  validation_status: string;
  traceability: FieldTraceability;
}

export interface CompletionInfo {
  populated: number;
  total: number;
  percentage: number;
}

export interface DatasheetMetadata {
  generated_at: string;
  generation_version: string;
  validation_status: string;
  validation_errors: string[];
  warnings: string[];
  completion: CompletionInfo;
}

export interface DatasheetResponse {
  metadata: DatasheetMetadata;
  sections: Record<string, DatasheetField[]>;
}

export interface FlatDatasheetResponse {
  vds_no: string;
  data: Record<string, unknown>;
  validation_status: string;
  completion_percentage: number;
}

export interface ValveTypeInfo {
  prefix: string;
  name: string;
  standards: string[];
  bore_types?: string[];
}

export interface MetadataResponse {
  valve_types: ValveTypeInfo[];
  piping_classes: string[];
  end_connections: { code: string; name: string }[];
  bore_types: { code: string; name: string }[];
  pressure_classes: string[];
}

export interface VDSListResponse {
  vds_numbers: string[];
  total: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  data_loaded: boolean;
  vds_index_count: number;
  piping_classes_count: number;
}

export interface BatchResult {
  vds_no: string;
  status: "success" | "error";
  data?: Record<string, unknown>;
  validation_status?: string;
  completion_percentage?: number;
  error?: string;
}

export interface BatchResponse {
  total: number;
  successful: number;
  failed: number;
  results: BatchResult[];
}

// === API Error Handling ===

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

// === API Functions ===

/**
 * Check API health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse<HealthResponse>(response);
}

/**
 * Decode a VDS number into its constituent parts
 */
export async function decodeVDS(vdsNo: string): Promise<DecodedVDS> {
  const response = await fetch(`${API_BASE_URL}/vds/${encodeURIComponent(vdsNo)}/decode`);
  return handleResponse<DecodedVDS>(response);
}

/**
 * Validate a VDS number
 */
export async function validateVDS(vdsNo: string): Promise<ValidationResult> {
  const response = await fetch(`${API_BASE_URL}/vds/${encodeURIComponent(vdsNo)}/validate`);
  return handleResponse<ValidationResult>(response);
}

/**
 * Generate a complete datasheet from VDS number
 */
export async function generateDatasheet(vdsNo: string): Promise<DatasheetResponse> {
  const response = await fetch(`${API_BASE_URL}/datasheet/${encodeURIComponent(vdsNo)}`);
  return handleResponse<DatasheetResponse>(response);
}

/**
 * Generate a flat datasheet (field_name -> value only)
 */
export async function generateFlatDatasheet(vdsNo: string): Promise<FlatDatasheetResponse> {
  const response = await fetch(`${API_BASE_URL}/datasheet/${encodeURIComponent(vdsNo)}/flat`);
  return handleResponse<FlatDatasheetResponse>(response);
}

/**
 * Generate datasheets for multiple VDS numbers
 */
export async function generateBatch(vdsNumbers: string[]): Promise<BatchResponse> {
  const response = await fetch(`${API_BASE_URL}/datasheet/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vds_numbers: vdsNumbers }),
  });
  return handleResponse<BatchResponse>(response);
}

/**
 * Get all metadata for form dropdowns
 */
export async function getMetadata(): Promise<MetadataResponse> {
  const response = await fetch(`${API_BASE_URL}/metadata`);
  return handleResponse<MetadataResponse>(response);
}

/**
 * Get list of supported valve types
 */
export async function getValveTypes(): Promise<{ valve_types: ValveTypeInfo[] }> {
  const response = await fetch(`${API_BASE_URL}/metadata/valve-types`);
  return handleResponse<{ valve_types: ValveTypeInfo[] }>(response);
}

/**
 * Get list of available piping classes
 */
export async function getPipingClasses(): Promise<{ piping_classes: string[]; total: number }> {
  const response = await fetch(`${API_BASE_URL}/metadata/piping-classes`);
  return handleResponse<{ piping_classes: string[]; total: number }>(response);
}

/**
 * Get list of indexed VDS numbers
 */
export async function getVDSNumbers(params?: {
  limit?: number;
  offset?: number;
  valve_type?: string;
}): Promise<VDSListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.valve_type) searchParams.set("valve_type", params.valve_type);

  const url = `${API_BASE_URL}/metadata/vds-numbers?${searchParams}`;
  const response = await fetch(url);
  return handleResponse<VDSListResponse>(response);
}

/**
 * Get end connection types
 */
export async function getEndConnections(): Promise<{
  end_connections: { code: string; name: string; description: string }[];
}> {
  const response = await fetch(`${API_BASE_URL}/metadata/end-connections`);
  return handleResponse<{ end_connections: { code: string; name: string; description: string }[] }>(response);
}

/**
 * Get bore types
 */
export async function getBoreTypes(): Promise<{ bore_types: { code: string; name: string }[] }> {
  const response = await fetch(`${API_BASE_URL}/metadata/bore-types`);
  return handleResponse<{ bore_types: { code: string; name: string }[] }>(response);
}

// === Default Export ===

const api = {
  checkHealth,
  decodeVDS,
  validateVDS,
  generateDatasheet,
  generateFlatDatasheet,
  generateBatch,
  getMetadata,
  getValveTypes,
  getPipingClasses,
  getVDSNumbers,
  getEndConnections,
  getBoreTypes,
};

export default api;
