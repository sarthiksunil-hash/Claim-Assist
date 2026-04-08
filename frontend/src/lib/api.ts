import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Interceptor: attach JWT token and X-User-Email header to every request ──
api.interceptors.request.use((config) => {
  try {
    // Priority 1: JWT token
    const token = localStorage.getItem("claimassist_token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }

    // Priority 2: X-User-Email (backward compatibility)
    const stored = localStorage.getItem("claimassist_user");
    if (stored) {
      const user = JSON.parse(stored);
      if (user?.email) {
        config.headers["X-User-Email"] = user.email;
      }
    }
  } catch {
    // ignore
  }
  return config;
});

// ── Interceptor: auto-redirect to login on 401 (except for auth endpoints) ──
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't auto-redirect if we're already on an auth endpoint
      // (login returns 401 for wrong password — we want to show that error, not redirect)
      const requestUrl = error.config?.url || "";
      const isAuthEndpoint = requestUrl.includes("/api/auth/");
      
      if (!isAuthEndpoint) {
        // Clear stored user and redirect for non-auth 401s
        localStorage.removeItem("claimassist_user");
        localStorage.removeItem("claimassist_token");
        if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Dashboard
export const getDashboardStats = () => api.get("/api/dashboard/stats");

// Documents
export const uploadDocument = (file: File, fileType: string) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("file_type", fileType);
  return api.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const listDocuments = () => api.get("/api/documents/");
export const getDocument = (id: number) => api.get(`/api/documents/${id}`);
export const processDocument = (id: number) =>
  api.post(`/api/documents/${id}/process`);
export const getExtractedDetails = () =>
  api.get("/api/documents/extracted-details");

// Claims
export const analyzeClaim = (data: {
  patient_name: string;
  insurer_name: string;
  claim_amount: number;
  denial_reason: string;
  policy_document_id?: number;
  medical_report_id?: number;
  denial_letter_id?: number;
}) => api.post("/api/claims/analyze", data);

export const listClaims = () => api.get("/api/claims/");
export const getClaim = (claimId: string) =>
  api.get(`/api/claims/${claimId}`);

// Appeals
export const generateAppeal = (data: {
  claim_id: string;
  tone?: string;
  include_regulations?: boolean;
  include_medical_evidence?: boolean;
}) => api.post("/api/appeals/generate", data);

export const listAppeals = () => api.get("/api/appeals/");
export const getAppeal = (id: number) => api.get(`/api/appeals/${id}`);

// Knowledge Graph
export const getKnowledgeGraph = () => api.get("/api/knowledge/graph");
export const searchKnowledge = (query: string) =>
  api.get(`/api/knowledge/search?q=${encodeURIComponent(query)}`);

// Chat
export const chatWithAI = (message: string) =>
  api.post("/api/chat/", { message });

// Authentication
export const signupUser = (data: {
  email: string;
  password: string;
  full_name: string;
}) => api.post("/api/auth/signup", data);

export const loginUser = (data: { email: string; password: string }) =>
  api.post("/api/auth/login", data);

export const verifyOtp = (data: { email: string; otp: string }) =>
  api.post("/api/auth/verify-otp", data);

export const resendOtp = (data: { email: string }) =>
  api.post("/api/auth/resend-otp", data);

export const forgotPassword = (data: { email: string }) =>
  api.post("/api/auth/forgot-password", data);

export const resetPassword = (data: { token: string; new_password: string }) =>
  api.post("/api/auth/reset-password", data);

// Agent Pipeline
export const runPipeline = (data: {
  patient_name: string;
  insurer_name: string;
  claim_amount: number;
  denial_reason: string;
  policy_inception_date?: string;
  claim_date?: string;
  document_types?: string[];
  user_email?: string;
}) => api.post("/api/pipeline/run", data);

export const getAgentOutput = (agentId: string) =>
  api.get(`/api/pipeline/agent/${agentId}`);

export const listAgents = () => api.get("/api/pipeline/agents");

export const getInsuranceKB = () => api.get("/api/pipeline/knowledge/insurance");
export const getMedicalKB = () => api.get("/api/pipeline/knowledge/medical");
export const searchKnowledgeBases = (query: string) =>
  api.get(`/api/pipeline/knowledge/search?q=${encodeURIComponent(query)}`);

// Pipeline latest result
export const getLatestPipelineResult = () => api.get("/api/pipeline/latest-result");

export default api;
