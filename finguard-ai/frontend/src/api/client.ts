import axios from "axios";
import type {
  BatchPredictionResponse,
  DashboardSummary,
  EvaluationReport,
  HealthResponse,
  HistoryItem,
  ModelInfo,
  Page,
  PredictionResponse,
  TransactionInput,
} from "./types";

const baseURL = (import.meta.env.VITE_API_BASE_URL as string) || "/api";

export const api = axios.create({ baseURL, timeout: 60000 });

export async function getHealth() {
  return (await api.get<HealthResponse>("/health")).data;
}

export async function getDashboard() {
  return (await api.get<DashboardSummary>("/dashboard/summary")).data;
}

export async function predict(tx: TransactionInput) {
  return (await api.post<PredictionResponse>("/predictions", tx)).data;
}

export async function batchPredict(file: File) {
  const form = new FormData();
  form.append("file", file);
  return (
    await api.post<BatchPredictionResponse>("/predictions/batch", form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  ).data;
}

export interface HistoryParams {
  page?: number;
  page_size?: number;
  risk_level?: string;
  is_fraud?: boolean;
  type?: string;
  search?: string;
}

export async function getHistory(params: HistoryParams) {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== "")
  );
  return (await api.get<Page<HistoryItem>>("/predictions/history", { params: clean }))
    .data;
}

export async function getModelInfo() {
  return (await api.get<ModelInfo>("/models/info")).data;
}

export async function getModelPerformance() {
  return (await api.get<EvaluationReport>("/models/performance")).data;
}
