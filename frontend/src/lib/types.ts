export type ProfileName =
  | "high_value"
  | "potential"
  | "average"
  | "budget_constrained"
  | "low_value";

export type ClusterSummary = {
  cluster_id: number;
  profile: ProfileName;
  headline: string;
  description: string;
  strategy: string;
  size: number;
  share: number;
  centroid: { annual_income_k: number; spending_score: number };
  scaled_centroid: { annual_income_k: number; spending_score: number };
  mean_age: number;
  female_count: number;
  male_count: number;
  female_share: number;
};

export type CustomerPoint = {
  customer_id: number;
  gender: "Female" | "Male";
  age: number;
  annual_income_k: number;
  spending_score: number;
  cluster_id: number;
  profile: ProfileName;
  anomaly_category: "normal" | "statistical_tail";
};

export type Analysis = {
  dataset: {
    rows: number;
    gender_counts: Record<string, number>;
    correlations: Record<string, Record<string, number>>;
    numeric_summary: Record<string, Record<string, number>>;
  };
  quality: {
    rows_ready: number;
    rows_removed: number;
    statistical_tail_count: number;
    removal_policy: string;
  };
  feature_selection: {
    selected_features: string[];
    comparison: { features: string[]; best_k: number; silhouette: number }[];
  };
  scaling: {
    mean: Record<string, number>;
    scale: Record<string, number>;
  };
  elbow: { k: number; inertia: number }[];
  silhouette_curve: { k: number; score: number }[];
  k_selection: {
    selected_k: number;
    elbow_k: number;
    silhouette_k: number;
    methods_agree: boolean;
    rule: string;
  };
  selected_k: number;
  model_silhouette: number;
  clusters: ClusterSummary[];
  growth_opportunity: ProfileName;
  growth_headline: string;
  customers: CustomerPoint[];
};

export type CustomerInput = {
  gender: "Female" | "Male";
  age: number;
  annual_income_k: number;
  spending_score: number;
};

export type Classification = {
  cluster_id: number;
  profile: ProfileName;
  headline: string;
  description: string;
  strategy: string;
  distance_to_centroid: number;
  features_used: string[];
  features_ignored: string[];
  outside_training_range: string[];
  centroid: { annual_income_k: number; spending_score: number };
  source: "api" | "bundle";
};
