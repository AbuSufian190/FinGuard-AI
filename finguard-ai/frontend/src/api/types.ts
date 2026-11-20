export type TransactionType =
  | "PAYMENT"
  | "TRANSFER"
  | "CASH_OUT"
  | "CASH_IN"
  | "DEBIT";

export interface TransactionInput {
  step: number;
  type: TransactionType;
  amount: number;
  oldbalanceOrg: number;
  newbalanceOrig: number;
  oldbalanceDest: number;
  newbalanceDest: number;
}

export interface ExplanationFeature {
  feature: string;
  contribution: number;
  value: number;
  direction: string;
}

export interface Explanation {
  method: string;
  top_features: ExplanationFeature[];
}

export interface PredictionResponse {
  id: number;
  created_at: string;
  fraud_probability: number;
  is_fraud: boolean;
  risk_level: string;
  threshold: number;
  model_name: string;
  model_version: string;
  transaction: TransactionInput;
  explanation: Explanation | null;
}

export interface BatchRowResult {
  row: number;
  fraud_probability: number;
  is_fraud: boolean;
  risk_level: string;
}

export interface BatchSummary {
  total_rows: number;
  flagged_fraud: number;
  fraud_rate: number;
  high_risk: number;
}

export interface BatchPredictionResponse {
  summary: BatchSummary;
  results: BatchRowResult[];
  result_csv_base64: string | null;
}

export interface HistoryItem {
  id: number;
  created_at: string;
  type: string;
  amount: number;
  fraud_probability: number;
  is_fraud: boolean;
  risk_level: string;
  source: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardSummary {
  total_transactions: number;
  fraudulent_detected: number;
  fraud_detection_rate: number;
  average_amount: number;
  trend: { date: string; total: number; fraud: number }[];
  fraud_distribution: { risk_level: string; count: number }[];
  recent_suspicious: HistoryItem[];
}

export interface Metrics {
  pr_auc: number;
  roc_auc: number;
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
}

export interface EvaluationReport {
  selected_model: string;
  selection_metric: string;
  decision_threshold: number;
  data_source: string;
  synthetic: boolean;
  models: Record<string, { validation: Metrics; test: Metrics }>;
  test_roc_curve: { fpr: number[]; tpr: number[] };
  test_pr_curve: { precision: number[]; recall: number[] };
  generated_at: string;
}

export interface ModelInfo {
  model_name: string;
  model_version: string;
  selection_metric: string;
  decision_threshold: number;
  trained_at: string | null;
  data_source: string | null;
  synthetic_data: boolean | null;
  features: string[];
  loaded: boolean;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  database: string;
  version: string;
}
