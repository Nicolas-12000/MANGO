import type { Analysis, Classification, CustomerInput } from "./types";

const BOUNDS = {
  age: [15, 100],
  annual_income_k: [0, 500],
  spending_score: [1, 100],
} as const;

export function classifyLocally(analysis: Analysis, customer: CustomerInput): Classification {
  for (const [field, [lower, upper]] of Object.entries(BOUNDS)) {
    const value = customer[field as keyof typeof BOUNDS];
    if (value < lower || value > upper) {
      throw new Error(`${field}_out_of_bounds`);
    }
  }
  const incomeMean = analysis.scaling.mean.annual_income_k;
  const incomeScale = analysis.scaling.scale.annual_income_k;
  const spendingMean = analysis.scaling.mean.spending_score;
  const spendingScale = analysis.scaling.scale.spending_score;
  const scaledIncome = (customer.annual_income_k - incomeMean) / incomeScale;
  const scaledSpending = (customer.spending_score - spendingMean) / spendingScale;

  let winner = analysis.clusters[0];
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const cluster of analysis.clusters) {
    const distance = Math.hypot(
      scaledIncome - cluster.scaled_centroid.annual_income_k,
      scaledSpending - cluster.scaled_centroid.spending_score,
    );
    if (distance < bestDistance) {
      bestDistance = distance;
      winner = cluster;
    }
  }

  const incomes = analysis.customers.map((point) => point.annual_income_k);
  const scores = analysis.customers.map((point) => point.spending_score);
  const outside: string[] = [];
  if (customer.annual_income_k < Math.min(...incomes) || customer.annual_income_k > Math.max(...incomes)) {
    outside.push("annual_income_k");
  }
  if (customer.spending_score < Math.min(...scores) || customer.spending_score > Math.max(...scores)) {
    outside.push("spending_score");
  }

  return {
    cluster_id: winner.cluster_id,
    profile: winner.profile,
    headline: winner.headline,
    description: winner.description,
    strategy: winner.strategy,
    distance_to_centroid: bestDistance,
    features_used: ["annual_income_k", "spending_score"],
    features_ignored: ["gender", "age"],
    outside_training_range: outside,
    centroid: winner.centroid,
    source: "bundle",
  };
}
