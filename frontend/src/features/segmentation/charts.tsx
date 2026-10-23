import { PROFILE_COLOR } from "@/lib/profiles";
import type { Analysis, ProfileName } from "@/lib/types";

const PROFILE_ORDER: ProfileName[] = [
  "high_value",
  "potential",
  "average",
  "budget_constrained",
  "low_value",
];

export function ElbowChart({ analysis }: { analysis: Analysis }) {
  const width = 640;
  const height = 260;
  const pad = { left: 44, right: 12, top: 16, bottom: 32 };
  const points = analysis.elbow;
  const minInertia = Math.min(...points.map((point) => point.inertia));
  const maxInertia = Math.max(...points.map((point) => point.inertia));
  const minK = points[0].k;
  const maxK = points[points.length - 1].k;
  const xOf = (k: number) => pad.left + ((k - minK) / (maxK - minK)) * (width - pad.left - pad.right);
  const yOf = (inertia: number) =>
    pad.top + (1 - (inertia - minInertia) / (maxInertia - minInertia || 1)) * (height - pad.top - pad.bottom);
  const path = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xOf(point.k).toFixed(1)} ${yOf(point.inertia).toFixed(1)}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="Método del codo">
      <path d={path} fill="none" stroke="#C2410C" strokeWidth="2.5" />
      {points.map((point) => (
        <g key={point.k}>
          <circle
            cx={xOf(point.k)}
            cy={yOf(point.inertia)}
            r={point.k === analysis.selected_k ? 6 : 4}
            fill={point.k === analysis.selected_k ? "#2C1210" : "#C2410C"}
          />
          <text x={xOf(point.k)} y={height - 8} textAnchor="middle" className="fill-secondary text-[11px]">
            {point.k}
          </text>
        </g>
      ))}
    </svg>
  );
}

export function SilhouetteChart({ analysis }: { analysis: Analysis }) {
  const width = 640;
  const height = 260;
  const pad = { left: 36, right: 12, top: 16, bottom: 32 };
  const points = analysis.silhouette_curve;
  const maxScore = Math.max(...points.map((point) => point.score), 0.01);
  const slot = (width - pad.left - pad.right) / points.length;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="Coeficiente de silueta">
      {points.map((point, index) => {
        const barHeight = (point.score / maxScore) * (height - pad.top - pad.bottom);
        const x = pad.left + index * slot + 6;
        const y = height - pad.bottom - barHeight;
        return (
          <g key={point.k}>
            <rect
              x={x}
              y={y}
              width={slot - 12}
              height={barHeight}
              rx="4"
              fill={point.k === analysis.selected_k ? "#2C1210" : "#C2410C"}
            />
            <text x={x + (slot - 12) / 2} y={height - 8} textAnchor="middle" className="fill-secondary text-[11px]">
              {point.k}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function ClusterChart({ analysis }: { analysis: Analysis }) {
  const width = 640;
  const height = 420;
  const pad = { left: 44, right: 16, top: 16, bottom: 36 };
  const incomes = analysis.customers.map((point) => point.annual_income_k);
  const scores = analysis.customers.map((point) => point.spending_score);
  const minIncome = Math.min(...incomes);
  const maxIncome = Math.max(...incomes);
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);
  const xOf = (income: number) =>
    pad.left + ((income - minIncome) / (maxIncome - minIncome || 1)) * (width - pad.left - pad.right);
  const yOf = (score: number) =>
    pad.top + (1 - (score - minScore) / (maxScore - minScore || 1)) * (height - pad.top - pad.bottom);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="Segmentos de clientes">
      {analysis.customers.map((point) => (
        <circle
          key={point.customer_id}
          cx={xOf(point.annual_income_k)}
          cy={yOf(point.spending_score)}
          r="5"
          fill={PROFILE_COLOR[point.profile]}
        />
      ))}
      {analysis.clusters.map((cluster) => (
        <path
          key={cluster.cluster_id}
          d={`M ${xOf(cluster.centroid.annual_income_k) - 6} ${yOf(cluster.centroid.spending_score)} h 12 M ${xOf(cluster.centroid.annual_income_k)} ${yOf(cluster.centroid.spending_score) - 6} v 12`}
          stroke="#2C1210"
          strokeWidth="2"
        />
      ))}
      <text x={width / 2} y={height - 8} textAnchor="middle" className="fill-secondary text-[12px]">
        Ingreso anual
      </text>
      <text
        x="14"
        y={height / 2}
        textAnchor="middle"
        transform={`rotate(-90 14 ${height / 2})`}
        className="fill-secondary text-[12px]"
      >
        Ganas de comprar
      </text>
    </svg>
  );
}

export function ProfileLegend({ analysis }: { analysis: Analysis }) {
  return (
    <ul className="flex flex-wrap gap-3">
      {PROFILE_ORDER.map((profile) => {
        const cluster = analysis.clusters.find((item) => item.profile === profile);
        if (!cluster) return null;
        return (
          <li key={profile} className="type-small flex items-center gap-2 text-secondary">
            <span className="size-2.5 rounded-full" style={{ backgroundColor: PROFILE_COLOR[profile] }} />
            {cluster.headline}
          </li>
        );
      })}
    </ul>
  );
}
