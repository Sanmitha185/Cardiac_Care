import type { Patient, HealthMetrics, ChatResponse, Assessment } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL 
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, '')}/api` 
  : '/api';

export class ApiServiceError extends Error {
  readonly endpoint: string;
  readonly status?: number;

  constructor(
    message: string,
    endpoint: string,
    status?: number,
  ) {
    super(message);
    this.name = 'ApiServiceError';
    this.endpoint = endpoint;
    this.status = status;
  }
}

function userMessageFor(endpoint: string, status?: number): string {
  if (endpoint === '/metrics') {
    return "We couldn't save your health information. The assessment service is temporarily unavailable. Please try again.";
  }
  if (endpoint === '/patients') {
    return "We couldn't save your patient information. The assessment service is temporarily unavailable. Please try again.";
  }
  if (endpoint === '/assessments/init') {
    return "We couldn't prepare your cardiac assessment. The assessment service is temporarily unavailable. Please try again.";
  }
  if (endpoint === '/assessments/chat') {
    return 'Dr. Cardia is temporarily unavailable. Please try again.';
  }
  if (status === 404) return 'This assessment could not be found. Please start a new assessment.';
  return 'The Cardiac Care service is temporarily unavailable. Please try again.';
}

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(options.headers || {})
        }
      });

      const contentType = response.headers.get('content-type') || '';
      const responseText = await response.text();
      let data: Record<string, unknown> = {};

      if (contentType.includes('application/json') && responseText) {
        try {
          data = JSON.parse(responseText) as Record<string, unknown>;
        } catch {
          data = {};
        }
      }

      if (!response.ok || data.status === 'ERROR') {
        const serverMessage = typeof data.message === 'string' ? data.message : undefined;
        if (import.meta.env.DEV && !serverMessage && responseText) {
          console.error('[Cardiac Care API Non-JSON Response]', {
            endpoint,
            status: response.status,
            contentType,
            response: responseText.slice(0, 500),
          });
        }
        throw new ApiServiceError(
          serverMessage || userMessageFor(endpoint, response.status),
          endpoint,
          response.status,
        );
      }

      if (!contentType.includes('application/json')) {
        throw new ApiServiceError(userMessageFor(endpoint, response.status), endpoint, response.status);
      }

      return data as T;
    } catch (err: unknown) {
      if (import.meta.env.DEV) {
        console.error('[Cardiac Care API Error]', {
          endpoint,
          status: err instanceof ApiServiceError ? err.status : undefined,
          message: err instanceof Error ? err.message : 'Unknown API error',
        });
      }
      if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
        throw new ApiServiceError('Unable to connect to the Cardiac Care service. Please check your connection and try again.', endpoint);
      }
      throw err;
    }
  }

  async createPatient(patientData: Partial<Patient>): Promise<{ status: string; patient_id: string; uhid?: string; warning?: string }> {
    return this.request<{ status: string; patient_id: string; uhid?: string; warning?: string }>('/patients', {
      method: 'POST',
      body: JSON.stringify(patientData)
    });
  }

  async createMetrics(metricsData: Partial<HealthMetrics>): Promise<{ status: string; metrics_id: string; warning?: string }> {
    return this.request<{ status: string; metrics_id: string; warning?: string }>('/metrics', {
      method: 'POST',
      body: JSON.stringify(metricsData)
    });
  }

  async initAssessment(patientId: string, metricsId: string): Promise<{ status: string; assessment_id: string }> {
    return this.request<{ status: string; assessment_id: string }>('/assessments/init', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: patientId,
        metrics_id: metricsId
      })
    });
  }

  async sendAssessmentMessage(assessmentId: string, userMessage: string): Promise<ChatResponse> {
    return this.request<ChatResponse>('/assessments/chat', {
      method: 'POST',
      body: JSON.stringify({
        assessment_id: assessmentId,
        user_message: userMessage
      })
    });
  }

  async getAssessment(assessmentId: string): Promise<{ status: string; assessment: Assessment }> {
    return this.request<{ status: string; assessment: Assessment }>(`/assessments/${assessmentId}`, {
      method: 'GET'
    });
  }

  async getDiagnostics(): Promise<{ status: string; diagnostics: Record<string, unknown> }> {
    return this.request<{ status: string; diagnostics: Record<string, unknown> }>('/admin/diagnostics', {
      method: 'GET'
    });
  }

  async submitDeviceObservations(payload: {
    patient_id: string;
    assessment_id: string;
    device_id: string;
    observations: Array<Record<string, unknown>>;
  }): Promise<{ status: string; ingested_count: number; errors: string[] }> {
    return this.request<{ status: string; ingested_count: number; errors: string[] }>('/device/observations', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
}

export const apiService = new ApiService();
