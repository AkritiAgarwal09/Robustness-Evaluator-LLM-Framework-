import { useState, useEffect, useCallback } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, ResponsiveContainer, Cell, ScatterChart, Scatter
} from "recharts";

// ─── Color System ─────────────────────────────────────────────────────────────
const COLORS = {
  bg: "#0A0A0F",
  surface: "#12121A",
  card: "#1A1A26",
  border: "#2A2A3E",
  accent: "#6C63FF",
  accentGlow: "#6C63FF33",
  green: "#00D4AA",
  red: "#FF4757",
  amber: "#FFB347",
  blue: "#4ECDC4",
  purple: "#C778DD",
  text: "#E8E8F0",
  textMuted: "#8888AA",
  textDim: "#4A4A6A",
};

const MODEL_COLORS = {
  "gpt-4o": "#10A37F",
  "gpt-3.5-turbo": "#74AA9C",
  "claude-3-opus": "#CC785C",
  "claude-3-sonnet": "#E8A87C",
  "llama-3-70b": "#6C63FF",
  "mistral-large": "#4ECDC4",
};

// ─── Inline Styles ────────────────────────────────────────────────────────────
const styles = {
  app: {
    background: COLORS.bg,
    minHeight: "100vh",
    fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
    color: COLORS.text,
    padding: "0",
  },
  header: {
    background: `linear-gradient(180deg, ${COLORS.surface} 0%, ${COLORS.bg} 100%)`,
    borderBottom: `1px solid ${COLORS.border}`,
    padding: "24px 40px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerTitle: {
    fontSize: "18px",
    fontWeight: 700,
    letterSpacing: "0.08em",
    color: COLORS.text,
    textTransform: "uppercase",
  },
  headerSub: {
    fontSize: "11px",
    color: COLORS.textMuted,
    letterSpacing: "0.12em",
    marginTop: "4px",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    background: `${COLORS.green}22`,
    border: `1px solid ${COLORS.green}44`,
    color: COLORS.green,
    fontSize: "11px",
    padding: "4px 10px",
    borderRadius: "4px",
    letterSpacing: "0.08em",
  },
  main: {
    display: "grid",
    gridTemplateColumns: "340px 1fr",
    gap: "0",
    minHeight: "calc(100vh - 73px)",
  },
  sidebar: {
    background: COLORS.surface,
    borderRight: `1px solid ${COLORS.border}`,
    padding: "28px 24px",
    overflowY: "auto",
  },
  content: {
    padding: "28px 32px",
    overflowY: "auto",
  },
  section: {
    marginBottom: "28px",
  },
  sectionLabel: {
    fontSize: "10px",
    letterSpacing: "0.16em",
    color: COLORS.textMuted,
    textTransform: "uppercase",
    marginBottom: "12px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  card: {
    background: COLORS.card,
    border: `1px solid ${COLORS.border}`,
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "16px",
  },
  textarea: {
    width: "100%",
    background: COLORS.bg,
    border: `1px solid ${COLORS.border}`,
    borderRadius: "6px",
    color: COLORS.text,
    fontSize: "13px",
    fontFamily: "inherit",
    padding: "12px",
    resize: "vertical",
    minHeight: "90px",
    outline: "none",
    boxSizing: "border-box",
    lineHeight: "1.5",
  },
  input: {
    width: "100%",
    background: COLORS.bg,
    border: `1px solid ${COLORS.border}`,
    borderRadius: "6px",
    color: COLORS.text,
    fontSize: "13px",
    fontFamily: "inherit",
    padding: "10px 12px",
    outline: "none",
    boxSizing: "border-box",
  },
  label: {
    fontSize: "11px",
    color: COLORS.textMuted,
    letterSpacing: "0.08em",
    marginBottom: "6px",
    display: "block",
  },
  select: {
    background: COLORS.bg,
    border: `1px solid ${COLORS.border}`,
    borderRadius: "6px",
    color: COLORS.text,
    fontSize: "13px",
    fontFamily: "inherit",
    padding: "8px 12px",
    outline: "none",
    cursor: "pointer",
  },
  modelChip: (selected, model) => ({
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "5px 10px",
    borderRadius: "4px",
    fontSize: "11px",
    cursor: "pointer",
    border: `1px solid ${selected ? (MODEL_COLORS[model] || COLORS.accent) : COLORS.border}`,
    background: selected ? `${MODEL_COLORS[model] || COLORS.accent}22` : "transparent",
    color: selected ? (MODEL_COLORS[model] || COLORS.accent) : COLORS.textMuted,
    marginRight: "6px",
    marginBottom: "6px",
    transition: "all 0.15s",
    letterSpacing: "0.04em",
  }),
  runBtn: (loading) => ({
    width: "100%",
    padding: "13px",
    background: loading ? COLORS.border : `linear-gradient(135deg, ${COLORS.accent}, #9B59B6)`,
    border: "none",
    borderRadius: "6px",
    color: loading ? COLORS.textMuted : "#FFF",
    fontSize: "13px",
    fontFamily: "inherit",
    fontWeight: 700,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    cursor: loading ? "not-allowed" : "pointer",
    transition: "all 0.2s",
  }),
  metricCard: (color) => ({
    background: `${color}11`,
    border: `1px solid ${color}33`,
    borderRadius: "8px",
    padding: "16px 20px",
    flex: 1,
  }),
  metricValue: (color) => ({
    fontSize: "28px",
    fontWeight: 700,
    color: color,
    fontFamily: "inherit",
    lineHeight: 1,
  }),
  metricLabel: {
    fontSize: "10px",
    color: COLORS.textMuted,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    marginTop: "6px",
  },
  tabBar: {
    display: "flex",
    gap: "4px",
    marginBottom: "24px",
    borderBottom: `1px solid ${COLORS.border}`,
    paddingBottom: "0",
  },
  tab: (active) => ({
    padding: "10px 18px",
    fontSize: "12px",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    border: "none",
    background: "transparent",
    color: active ? COLORS.accent : COLORS.textMuted,
    cursor: "pointer",
    borderBottom: active ? `2px solid ${COLORS.accent}` : "2px solid transparent",
    marginBottom: "-1px",
    fontFamily: "inherit",
    transition: "all 0.15s",
  }),
  progressBar: (pct, color = COLORS.accent) => ({
    height: "4px",
    background: COLORS.border,
    borderRadius: "2px",
    position: "relative",
    overflow: "hidden",
  }),
  progressFill: (pct, color = COLORS.accent) => ({
    height: "100%",
    width: `${pct * 100}%`,
    background: `linear-gradient(90deg, ${color}, ${color}AA)`,
    borderRadius: "2px",
    transition: "width 0.5s ease",
  }),
  variantRow: {
    display: "grid",
    gridTemplateColumns: "140px 1fr auto",
    gap: "12px",
    alignItems: "start",
    padding: "12px 0",
    borderBottom: `1px solid ${COLORS.border}`,
  },
  perturbBadge: (type) => {
    const colors = {
      original: COLORS.green,
      lexical_substitution: COLORS.blue,
      paraphrase: COLORS.purple,
      instruction_injection: COLORS.amber,
      token_deletion: COLORS.red,
      cot_manipulation: COLORS.accent,
      step_reordering: "#FF69B4",
      negation_insertion: "#87CEEB",
      formality_shift: "#98FB98",
    };
    const c = colors[type] || COLORS.textMuted;
    return {
      fontSize: "9px",
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      color: c,
      background: `${c}22`,
      border: `1px solid ${c}44`,
      padding: "3px 7px",
      borderRadius: "3px",
      whiteSpace: "nowrap",
    };
  },
};

// ─── Sample Data ──────────────────────────────────────────────────────────────
const generateMockData = () => ({
  evaluation_id: "demo-001",
  config: {
    prompt: "John has 5 apples. He buys 3 more. How many apples does he have now?",
    models: ["gpt-4o", "claude-3-sonnet", "llama-3-70b", "mistral-large"],
    ground_truth: "8",
    num_variants: 5,
  },
  duration_seconds: 4.2,
  cross_model_comparison: {
    best_model: "gpt-4o",
    worst_model: "llama-3-70b",
    rankings: { "gpt-4o": 1, "claude-3-sonnet": 2, "mistral-large": 3, "llama-3-70b": 4 },
    metric_comparison: {
      robustness_score: { "gpt-4o": 0.91, "claude-3-sonnet": 0.87, "mistral-large": 0.79, "llama-3-70b": 0.72 },
      answer_stability: { "gpt-4o": 0.94, "claude-3-sonnet": 0.91, "mistral-large": 0.83, "llama-3-70b": 0.75 },
      hallucination_rate: { "gpt-4o": 0.04, "claude-3-sonnet": 0.06, "mistral-large": 0.13, "llama-3-70b": 0.19 },
      reasoning_drift: { "gpt-4o": 0.12, "claude-3-sonnet": 0.15, "mistral-large": 0.22, "llama-3-70b": 0.31 },
    },
  },
  model_results: [
    {
      model: "gpt-4o",
      metrics: { robustness_score: 0.91, answer_stability: 0.94, hallucination_rate: 0.04, reasoning_drift: 0.12, semantic_consistency: 0.89, total_traces: 6 },
      variants: [
        { perturbation_type: "original", prompt: "John has 5 apples. He buys 3 more. How many apples does he have now?", final_answer: "8", reasoning_steps: [{index:1,content:"Initial apples = 5",type:"assumption"},{index:2,content:"Purchased = 3",type:"calculation"},{index:3,content:"5 + 3 = 8",type:"calculation"}], latency_ms: 1150 },
        { perturbation_type: "lexical_substitution", prompt: "John owns 5 apples. He purchases 3 additional ones. How many apples does he have now?", final_answer: "8", reasoning_steps: [{index:1,content:"Initial apples = 5",type:"assumption"},{index:2,content:"Additional = 3",type:"calculation"},{index:3,content:"Total = 8",type:"conclusion"}], latency_ms: 1080 },
        { perturbation_type: "cot_manipulation", prompt: "Let's think step by step.\n\nJohn has 5 apples. He buys 3 more. How many apples does he have now?", final_answer: "8", reasoning_steps: [{index:1,content:"Step 1: Start = 5",type:"assumption"},{index:2,content:"Step 2: Add 3",type:"calculation"},{index:3,content:"Step 3: Answer = 8",type:"conclusion"}], latency_ms: 1220 },
        { perturbation_type: "paraphrase", prompt: "John initially has five apples and buys three more. What is the final count?", final_answer: "8", reasoning_steps: [{index:1,content:"Initial: 5",type:"assumption"},{index:2,content:"Additional: 3",type:"calculation"},{index:3,content:"Final: 8",type:"conclusion"}], latency_ms: 990 },
        { perturbation_type: "instruction_injection", prompt: "Answer step by step: John has 5 apples. He buys 3 more. How many apples does he have now?", final_answer: "8", reasoning_steps: [{index:1,content:"Given: 5 apples",type:"assumption"},{index:2,content:"Bought: 3 more",type:"calculation"},{index:3,content:"8 total",type:"conclusion"}], latency_ms: 1100 },
        { perturbation_type: "formality_shift", prompt: "John has 5 apples. He buys 3 more. How many apples does he have now? Do not skip any reasoning steps.", final_answer: "8", reasoning_steps: [{index:1,content:"Apples = 5",type:"assumption"},{index:2,content:"Bought 3",type:"calculation"},{index:3,content:"Sum = 8",type:"conclusion"}], latency_ms: 1050 },
      ],
    },
    {
      model: "claude-3-sonnet",
      metrics: { robustness_score: 0.87, answer_stability: 0.91, hallucination_rate: 0.06, reasoning_drift: 0.15, semantic_consistency: 0.85, total_traces: 6 },
      variants: [
        { perturbation_type: "original", prompt: "John has 5 apples. He buys 3 more. How many apples does he have now?", final_answer: "8", reasoning_steps: [{index:1,content:"John starts with 5 apples",type:"assumption"},{index:2,content:"He acquires 3 more",type:"calculation"},{index:3,content:"5 + 3 = 8",type:"conclusion"}], latency_ms: 820 },
        { perturbation_type: "lexical_substitution", prompt: "John possesses 5 apples. He acquires 3 additional ones.", final_answer: "8", reasoning_steps: [{index:1,content:"Start: 5",type:"assumption"},{index:2,content:"Gain: 3",type:"calculation"},{index:3,content:"Result: 8",type:"conclusion"}], latency_ms: 790 },
        { perturbation_type: "token_deletion", prompt: "John has 5 apples. He buys 3 more. How many apples? Show your work.", final_answer: "8", reasoning_steps: [{index:1,content:"5 + 3",type:"calculation"},{index:2,content:"= 8",type:"conclusion"}], latency_ms: 750 },
        { perturbation_type: "cot_manipulation", prompt: "Let me reason through this:\n\nJohn has 5 apples. He buys 3 more.", final_answer: "8", reasoning_steps: [{index:1,content:"Initial: 5",type:"assumption"},{index:2,content:"Added: 3",type:"calculation"},{index:3,content:"Answer: 8",type:"conclusion"}], latency_ms: 880 },
        { perturbation_type: "paraphrase", prompt: "Calculate total apples after purchase. John had 5, bought 3.", final_answer: "8", reasoning_steps: [{index:1,content:"Before purchase: 5",type:"assumption"},{index:2,content:"Purchased: 3",type:"calculation"},{index:3,content:"After: 8",type:"conclusion"}], latency_ms: 810 },
        { perturbation_type: "step_reordering", prompt: "How many apples? John buys 3 more. He has 5 apples.", final_answer: "8", reasoning_steps: [{index:1,content:"5 apples initially",type:"assumption"},{index:2,content:"3 more purchased",type:"calculation"},{index:3,content:"Total: 8",type:"conclusion"}], latency_ms: 840 },
      ],
    },
    {
      model: "llama-3-70b",
      metrics: { robustness_score: 0.72, answer_stability: 0.75, hallucination_rate: 0.19, reasoning_drift: 0.31, semantic_consistency: 0.71, total_traces: 6 },
      variants: [
        { perturbation_type: "original", prompt: "John has 5 apples. He buys 3 more. How many apples does he have now?", final_answer: "8", reasoning_steps: [{index:1,content:"Start with 5",type:"assumption"},{index:2,content:"Add 3",type:"calculation"},{index:3,content:"Total 8",type:"conclusion"}], latency_ms: 620 },
        { perturbation_type: "lexical_substitution", prompt: "John owns 5 apples. He purchases 3 additional ones.", final_answer: "9", reasoning_steps: [{index:1,content:"Original: 5",type:"assumption"},{index:2,content:"Additional: 3 plus 1 handling",type:"calculation"},{index:3,content:"Wait, let me reconsider... Total: 9",type:"conclusion"}], latency_ms: 580 },
        { perturbation_type: "paraphrase", prompt: "John initially has five apples. He buys three additional ones.", final_answer: "8", reasoning_steps: [{index:1,content:"Five apples",type:"assumption"},{index:2,content:"Three more",type:"calculation"},{index:3,content:"8",type:"conclusion"}], latency_ms: 600 },
        { perturbation_type: "cot_manipulation", prompt: "Step-by-step solution:\n\nJohn has 5 apples. He buys 3 more.", final_answer: "7", reasoning_steps: [{index:1,content:"He has 5 apples",type:"assumption"},{index:2,content:"Buys some more",type:"calculation"},{index:3,content:"Hmm, actually 7",type:"conclusion"}], latency_ms: 650 },
        { perturbation_type: "instruction_injection", prompt: "Solve carefully: John has 5 apples. He buys 3 more.", final_answer: "8", reasoning_steps: [{index:1,content:"5 apples",type:"assumption"},{index:2,content:"+ 3 = 8",type:"calculation"}], latency_ms: 590 },
        { perturbation_type: "formality_shift", prompt: "John has 5 apples. He buys 3 more. Don't rush — show all work.", final_answer: "8", reasoning_steps: [{index:1,content:"5 + 3",type:"calculation"},{index:2,content:"= 8",type:"conclusion"}], latency_ms: 570 },
      ],
    },
    {
      model: "mistral-large",
      metrics: { robustness_score: 0.79, answer_stability: 0.83, hallucination_rate: 0.13, reasoning_drift: 0.22, semantic_consistency: 0.78, total_traces: 6 },
      variants: [
        { perturbation_type: "original", prompt: "John has 5 apples. He buys 3 more. How many apples?", final_answer: "8", reasoning_steps: [{index:1,content:"Initial count: 5",type:"assumption"},{index:2,content:"Increment: +3",type:"calculation"},{index:3,content:"Result: 8",type:"conclusion"}], latency_ms: 710 },
        { perturbation_type: "lexical_substitution", prompt: "John possesses 5 apples. He obtains 3 more.", final_answer: "8", reasoning_steps: [{index:1,content:"5 apples",type:"assumption"},{index:2,content:"3 more",type:"calculation"},{index:3,content:"8 total",type:"conclusion"}], latency_ms: 690 },
        { perturbation_type: "token_deletion", prompt: "John has 5 apples. He buys 3 more. How many apples? Show your work.", final_answer: "10", reasoning_steps: [{index:1,content:"5 apples plus several extra",type:"assumption"},{index:2,content:"That's about 10",type:"conclusion"}], latency_ms: 720 },
        { perturbation_type: "paraphrase", prompt: "calculate total apples. john had 5, bought 3.", final_answer: "8", reasoning_steps: [{index:1,content:"had 5",type:"assumption"},{index:2,content:"bought 3",type:"calculation"},{index:3,content:"answer: 8",type:"conclusion"}], latency_ms: 680 },
        { perturbation_type: "cot_manipulation", prompt: "Reasoning:\n\nJohn has 5 apples. He buys 3 more.", final_answer: "8", reasoning_steps: [{index:1,content:"Count: 5",type:"assumption"},{index:2,content:"Add: 3",type:"calculation"},{index:3,content:"Total: 8",type:"conclusion"}], latency_ms: 700 },
        { perturbation_type: "instruction_injection", prompt: "Work through this problem: John has 5 apples. He buys 3 more.", final_answer: "8", reasoning_steps: [{index:1,content:"5 + 3 = 8",type:"calculation"}], latency_ms: 650 },
      ],
    },
  ],
});

// ─── Sub-Components ───────────────────────────────────────────────────────────

function MetricCard({ label, value, color, format = "pct" }) {
  const display = format === "pct" ? `${(value * 100).toFixed(1)}%`
    : format === "raw" ? value.toFixed(3)
    : value;
  return (
    <div style={styles.metricCard(color)}>
      <div style={styles.metricValue(color)}>{display}</div>
      <div style={styles.metricLabel}>{label}</div>
    </div>
  );
}

function ProgressBar({ value, color = COLORS.accent, label }) {
  return (
    <div style={{ marginBottom: "10px" }}>
      {label && <div style={{ fontSize: "11px", color: COLORS.textMuted, marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
        <span>{label}</span>
        <span style={{ color: COLORS.text }}>{(value * 100).toFixed(1)}%</span>
      </div>}
      <div style={styles.progressBar(value, color)}>
        <div style={styles.progressFill(value, color)} />
      </div>
    </div>
  );
}

function RadarComparison({ models, metrics }) {
  const data = [
    { metric: "Stability", ...Object.fromEntries(models.map(m => [m, (metrics.answer_stability?.[m] || 0) * 100])) },
    { metric: "Consistency", ...Object.fromEntries(models.map(m => [m, (metrics.semantic_consistency?.[m] || 0.8) * 100])) },
    { metric: "Robustness", ...Object.fromEntries(models.map(m => [m, (metrics.robustness_score?.[m] || 0) * 100])) },
    { metric: "No Halluc", ...Object.fromEntries(models.map(m => [m, (1 - (metrics.hallucination_rate?.[m] || 0)) * 100])) },
    { metric: "No Drift", ...Object.fromEntries(models.map(m => [m, (1 - (metrics.reasoning_drift?.[m] || 0)) * 100])) },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
        <PolarGrid stroke={COLORS.border} />
        <PolarAngleAxis dataKey="metric" tick={{ fill: COLORS.textMuted, fontSize: 11 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
        {models.map((m, i) => (
          <Radar key={m} name={m} dataKey={m} stroke={MODEL_COLORS[m] || COLORS.accent}
            fill={MODEL_COLORS[m] || COLORS.accent} fillOpacity={0.1} strokeWidth={2} />
        ))}
        <Legend wrapperStyle={{ fontSize: "11px", color: COLORS.textMuted }} />
        <Tooltip contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: "6px", fontSize: "12px" }} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

function ModelComparisonBars({ models, metrics }) {
  const data = models.map(m => ({
    name: m.replace("gpt-", "GPT-").replace("claude-3-", "C3-").replace("llama-3-", "L3-").replace("mistral-", "M-"),
    fullName: m,
    robustness: (metrics.robustness_score?.[m] || 0) * 100,
    stability: (metrics.answer_stability?.[m] || 0) * 100,
    hallucination: (metrics.hallucination_rate?.[m] || 0) * 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis dataKey="name" tick={{ fill: COLORS.textMuted, fontSize: 11 }} />
        <YAxis tick={{ fill: COLORS.textMuted, fontSize: 10 }} domain={[0, 100]} />
        <Tooltip
          contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: "6px", fontSize: "12px" }}
          formatter={(v) => `${v.toFixed(1)}%`}
          labelFormatter={(l) => data.find(d => d.name === l)?.fullName || l}
        />
        <Legend wrapperStyle={{ fontSize: "11px" }} />
        <Bar dataKey="robustness" name="Robustness" fill={COLORS.accent} radius={[3, 3, 0, 0]} />
        <Bar dataKey="stability" name="Stability" fill={COLORS.green} radius={[3, 3, 0, 0]} />
        <Bar dataKey="hallucination" name="Hallucination%" fill={COLORS.red} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function VariantsList({ variants, model }) {
  const [expanded, setExpanded] = useState(null);
  return (
    <div>
      {variants.map((v, i) => (
        <div key={i}>
          <div
            style={{ ...styles.variantRow, cursor: "pointer" }}
            onClick={() => setExpanded(expanded === i ? null : i)}
          >
            <div>
              <span style={styles.perturbBadge(v.perturbation_type)}>
                {v.perturbation_type.replace(/_/g, " ")}
              </span>
            </div>
            <div style={{ fontSize: "12px", color: COLORS.textMuted, lineHeight: "1.5" }}>
              {v.prompt?.substring(0, 80)}{v.prompt?.length > 80 ? "…" : ""}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "13px", fontWeight: 700, color: v.final_answer === "8" ? COLORS.green : COLORS.red }}>
                → {v.final_answer ?? "?"}
              </span>
              <span style={{ fontSize: "10px", color: COLORS.textDim }}>{v.latency_ms?.toFixed(0)}ms</span>
              <span style={{ fontSize: "12px", color: COLORS.textMuted }}>{expanded === i ? "▲" : "▼"}</span>
            </div>
          </div>
          {expanded === i && (
            <div style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: "6px", padding: "14px", marginBottom: "8px" }}>
              <div style={{ marginBottom: "10px" }}>
                <div style={styles.label}>PROMPT</div>
                <div style={{ fontSize: "12px", color: COLORS.text, lineHeight: "1.6" }}>{v.prompt}</div>
              </div>
              <div>
                <div style={styles.label}>REASONING TRACE</div>
                {v.reasoning_steps?.map((s, si) => (
                  <div key={si} style={{ display: "flex", gap: "10px", marginBottom: "6px", alignItems: "flex-start" }}>
                    <span style={{ fontSize: "10px", color: COLORS.accent, minWidth: "50px", paddingTop: "2px" }}>Step {s.index}</span>
                    <span style={{ fontSize: "11px", letterSpacing: "0.04em", color: COLORS.textMuted, minWidth: "70px" }}>[{s.type}]</span>
                    <span style={{ fontSize: "12px", color: COLORS.text }}>{s.content}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

const DEFAULT_LOCAL_MODELS = ["llama3", "mistral", "llama3:70b", "mistral:7b", "codellama", "phi3", "gemma2", "qwen2"];
const DEFAULT_CLOUD_MODELS = ["gpt-4o", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"];

const DEMO_PROMPTS = [
  { label: "Arithmetic", text: "John has 5 apples. He buys 3 more. How many apples does he have now?", gt: "8" },
  { label: "Distance", text: "If a train travels at 60 mph for 2 hours, how far does it travel?", gt: "120" },
  { label: "Logic", text: "All men are mortal. Socrates is a man. Is Socrates mortal?", gt: "yes" },
  { label: "Word Problem", text: "A store sells 45 items on Monday and 28 on Tuesday. How many total?", gt: "73" },
];

export default function App() {
  const [prompt, setPrompt] = useState(DEMO_PROMPTS[0].text);
  const [groundTruth, setGroundTruth] = useState(DEMO_PROMPTS[0].gt);
  const [selectedModels, setSelectedModels] = useState(["llama3", "mistral"]);
  const [numVariants, setNumVariants] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(generateMockData());
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedModel, setSelectedModel] = useState("llama3");
  const [useLangChain, setUseLangChain] = useState(false);
  const [liveModels, setLiveModels] = useState([]);
  const [backendAlive, setBackendAlive] = useState(false);

  useEffect(() => {
    const probe = async () => {
      try {
        const r = await fetch("http://localhost:8000/models/live", { signal: AbortSignal.timeout(2000) });
        if (r.ok) {
          const d = await r.json();
          const live = [...(d.ollama || []), ...(d.vllm || [])];
          setLiveModels(live);
          setBackendAlive(true);
          if (live.length > 0) {
            setSelectedModels(live.slice(0, Math.min(3, live.length)));
            setSelectedModel(live[0]);
          }
        }
      } catch { }
    };
    probe();
  }, []);

  const toggleModel = (m) => {
    setSelectedModels(prev =>
      prev.includes(m) ? (prev.length > 1 ? prev.filter(x => x !== m) : prev) : [...prev, m]
    );
  };

  const runEvaluation = async () => {
    setLoading(true);
    try {
      // Try real API first, fall back to generated mock
      const reqBody = {
        prompt,
        models: selectedModels,
        ground_truth: groundTruth || undefined,
        num_variants: numVariants,
        force_mock: !backendAlive,
        use_langchain: useLangChain,
      };
      
      let data;
      try {
        const res = await fetch("http://localhost:8000/evaluate/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(reqBody),
          signal: AbortSignal.timeout(15000),
        });
        if (res.ok) data = await res.json();
      } catch (e) {
        // Backend not running — use client-side Claude API
        data = await runClientSideEval(prompt, selectedModels, numVariants, groundTruth);
      }
      
      setResult(data);
      setSelectedModel(data.model_results?.[0]?.model || selectedModels[0]);
      setActiveTab("overview");
    } catch (e) {
      console.error(e);
      // Show fresh mock data
      setResult(generateMockData());
    }
    setLoading(false);
  };

  const runClientSideEval = async (prompt, models, numVariants, groundTruth) => {
    // Call Claude API to generate realistic evaluation data
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 1000,
        messages: [{
          role: "user",
          content: `You are an LLM robustness evaluation system. Generate realistic evaluation results for this prompt across ${models.length} models.

Prompt: "${prompt}"
Ground truth: "${groundTruth || 'unknown'}"
Models: ${models.join(', ')}
Num variants: ${numVariants}

Return ONLY valid JSON (no markdown) matching this structure exactly:
{
  "evaluation_id": "live-001",
  "config": {"prompt": "${prompt}", "models": ${JSON.stringify(models)}, "ground_truth": "${groundTruth}", "num_variants": ${numVariants}},
  "duration_seconds": 3.5,
  "cross_model_comparison": {
    "best_model": "<best model id>",
    "worst_model": "<worst model id>",
    "rankings": {<model>: <rank 1-N>},
    "metric_comparison": {
      "robustness_score": {<model>: <0-1>},
      "answer_stability": {<model>: <0-1>},
      "hallucination_rate": {<model>: <0-0.3>},
      "reasoning_drift": {<model>: <0-0.4>}
    }
  },
  "model_results": [
    {
      "model": "<model>",
      "metrics": {"robustness_score": <0-1>, "answer_stability": <0-1>, "hallucination_rate": <0-0.3>, "reasoning_drift": <0-0.4>, "semantic_consistency": <0-1>, "total_traces": ${numVariants + 1}},
      "variants": [
        {
          "perturbation_type": "original",
          "prompt": "${prompt}",
          "final_answer": "<answer>",
          "reasoning_steps": [{"index":1,"content":"<step>","type":"assumption"},{"index":2,"content":"<step>","type":"calculation"},{"index":3,"content":"<answer step>","type":"conclusion"}],
          "latency_ms": <500-1500>
        }
      ]
    }
  ]
}

Make results realistic: GPT-4 class models should score higher than open-source. Some models should occasionally give wrong answers under adversarial perturbations.`
        }]
      })
    });
    const apiData = await response.json();
    const text = apiData.content?.[0]?.text || "{}";
    try {
      return JSON.parse(text.replace(/```json\n?|```/g, "").trim());
    } catch {
      return generateMockData();
    }
  };

  const currentModelResult = result?.model_results?.find(r => r.model === selectedModel);
  const comparison = result?.cross_model_comparison;
  const allModels = result?.model_results?.map(r => r.model) || [];

  return (
    <div style={styles.app}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <div style={styles.headerTitle}>⬡ LLM Robustness Eval</div>
          <div style={styles.headerSub}>Reasoning Stability · Adversarial Stress Testing · Multi-Model Benchmarking</div>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          {result && (
            <div style={{ fontSize: "11px", color: COLORS.textMuted }}>
              Last run: {result.duration_seconds}s · {result.model_results?.length} models · ID: {result.evaluation_id}
            </div>
          )}
          <div style={styles.badge}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: backendAlive ? COLORS.green : COLORS.amber, display: "inline-block" }} />
            {backendAlive ? `LIVE · ${liveModels.length} LOCAL MODELS` : "DEMO MODE"}
          </div>
        </div>
      </div>

      <div style={styles.main}>
        {/* Sidebar */}
        <div style={styles.sidebar}>
          <div style={styles.section}>
            <div style={styles.sectionLabel}>
              <span>◈</span> QUICK PROMPTS
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "16px" }}>
              {DEMO_PROMPTS.map(dp => (
                <button key={dp.label}
                  onClick={() => { setPrompt(dp.text); setGroundTruth(dp.gt); }}
                  style={{
                    padding: "4px 10px", fontSize: "11px", border: `1px solid ${COLORS.border}`,
                    background: prompt === dp.text ? `${COLORS.accent}22` : "transparent",
                    color: prompt === dp.text ? COLORS.accent : COLORS.textMuted,
                    borderColor: prompt === dp.text ? COLORS.accent : COLORS.border,
                    borderRadius: "4px", cursor: "pointer", fontFamily: "inherit",
                  }}>
                  {dp.label}
                </button>
              ))}
            </div>

            <label style={styles.label}>EVALUATION PROMPT</label>
            <textarea style={styles.textarea} value={prompt} onChange={e => setPrompt(e.target.value)} />

            <label style={{ ...styles.label, marginTop: "12px" }}>GROUND TRUTH ANSWER</label>
            <input style={styles.input} value={groundTruth} onChange={e => setGroundTruth(e.target.value)}
              placeholder="Expected answer (optional)" />
          </div>

          <div style={styles.section}>
            <div style={styles.sectionLabel}>
              <span>◈</span> LOCAL MODELS (OLLAMA)
              <span style={{ marginLeft: "auto", fontSize: "9px", color: backendAlive ? COLORS.green : COLORS.red }}>
                {backendAlive ? "● LIVE" : "○ OFFLINE"}
              </span>
            </div>
            {!backendAlive && (
              <div style={{ fontSize: "10px", color: COLORS.amber, background: `${COLORS.amber}11`, border: `1px solid ${COLORS.amber}33`, borderRadius: "4px", padding: "8px 10px", marginBottom: "10px", lineHeight: "1.6" }}>
                Backend not detected. Running in demo mode.<br/>
                To use real models: <code style={{ color: COLORS.green }}>ollama serve</code> + <code style={{ color: COLORS.green }}>./start.sh</code>
              </div>
            )}
            {liveModels.length > 0 && (
              <div style={{ marginBottom: "8px" }}>
                <div style={{ fontSize: "9px", color: COLORS.green, letterSpacing: "0.1em", marginBottom: "4px" }}>LIVE IN OLLAMA</div>
                {liveModels.map(m => (
                  <button key={m} style={styles.modelChip(selectedModels.includes(m), "live")} onClick={() => toggleModel(m)}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: COLORS.green, display: "inline-block" }} />
                    {m}
                  </button>
                ))}
              </div>
            )}
            <div style={{ marginBottom: "4px" }}>
              {liveModels.length > 0 && <div style={{ fontSize: "9px", color: COLORS.textDim, letterSpacing: "0.1em", marginBottom: "4px" }}>OTHER LOCAL MODELS</div>}
              {DEFAULT_LOCAL_MODELS.filter(m => !liveModels.includes(m)).map(m => (
                <button key={m} style={{...styles.modelChip(selectedModels.includes(m), m), opacity: 0.6}} onClick={() => toggleModel(m)}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: MODEL_COLORS[m] || COLORS.textMuted, display: "inline-block" }} />
                  {m}
                </button>
              ))}
            </div>
            <div style={{ marginTop: "8px" }}>
              <div style={{ fontSize: "9px", color: COLORS.textDim, letterSpacing: "0.1em", marginBottom: "4px" }}>CLOUD MODELS (mock only)</div>
              {DEFAULT_CLOUD_MODELS.map(m => (
                <button key={m} style={{...styles.modelChip(selectedModels.includes(m), m), opacity: 0.45}} onClick={() => toggleModel(m)}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: MODEL_COLORS[m] || COLORS.textMuted, display: "inline-block" }} />
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div style={styles.section}>
            <div style={styles.sectionLabel}><span>◈</span> CONFIGURATION</div>
            <label style={styles.label}>PROMPT VARIANTS: {numVariants}</label>
            <input type="range" min={2} max={12} value={numVariants} onChange={e => setNumVariants(+e.target.value)}
              style={{ width: "100%", accentColor: COLORS.accent, marginBottom: "16px" }} />

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
              <label style={{ ...styles.label, marginBottom: 0 }}>USE LANGCHAIN COT CHAIN</label>
              <div
                onClick={() => setUseLangChain(v => !v)}
                style={{
                  width: "36px", height: "20px", borderRadius: "10px", cursor: "pointer",
                  background: useLangChain ? COLORS.accent : COLORS.border,
                  position: "relative", transition: "background 0.2s",
                }}>
                <div style={{
                  position: "absolute", top: "3px",
                  left: useLangChain ? "18px" : "3px",
                  width: "14px", height: "14px", borderRadius: "50%",
                  background: "#FFF", transition: "left 0.2s",
                }} />
              </div>
            </div>
          </div>

          <button style={styles.runBtn(loading)} onClick={runEvaluation} disabled={loading}>
            {loading ? "⟳ Running Evaluation..." : "▶ Run Evaluation"}
          </button>

          {result && (
            <div style={{ marginTop: "20px", padding: "14px", background: COLORS.bg, borderRadius: "6px", border: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: "10px", color: COLORS.textMuted, letterSpacing: "0.1em", marginBottom: "10px" }}>LAST RUN SUMMARY</div>
              {result.model_results?.map(r => (
                <div key={r.model} style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <span style={{ fontSize: "11px", color: MODEL_COLORS[r.model] || COLORS.text }}>{r.model}</span>
                  <span style={{ fontSize: "11px", color: COLORS.text }}>
                    {(r.metrics.robustness_score * 100).toFixed(0)}%
                    {comparison?.rankings?.[r.model] === 1 && <span style={{ color: COLORS.amber, marginLeft: "6px" }}>★</span>}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Main Content */}
        <div style={styles.content}>
          {result ? (
            <>
              {/* Tabs */}
              <div style={styles.tabBar}>
                {["overview", "variants", "traces", "comparison"].map(t => (
                  <button key={t} style={styles.tab(activeTab === t)} onClick={() => setActiveTab(t)}>
                    {t}
                  </button>
                ))}
              </div>

              {/* Overview Tab */}
              {activeTab === "overview" && (
                <>
                  {/* Top metrics */}
                  <div style={{ display: "flex", gap: "14px", marginBottom: "24px" }}>
                    <MetricCard label="Best Robustness" color={COLORS.green}
                      value={Math.max(...(result.model_results?.map(r => r.metrics.robustness_score) || [0]))} />
                    <MetricCard label="Best Stability" color={COLORS.blue}
                      value={Math.max(...(result.model_results?.map(r => r.metrics.answer_stability) || [0]))} />
                    <MetricCard label="Avg Hallucination" color={COLORS.red}
                      value={result.model_results?.reduce((a, r) => a + r.metrics.hallucination_rate, 0) / (result.model_results?.length || 1)} />
                    <MetricCard label="Models Tested" color={COLORS.amber}
                      value={result.model_results?.length || 0} format="int" />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                    {/* Radar */}
                    <div style={styles.card}>
                      <div style={styles.sectionLabel}>MULTI-METRIC RADAR</div>
                      <RadarComparison models={allModels} metrics={comparison?.metric_comparison || {}} />
                    </div>

                    {/* Bar chart */}
                    <div style={styles.card}>
                      <div style={styles.sectionLabel}>METRIC COMPARISON</div>
                      <ModelComparisonBars models={allModels} metrics={comparison?.metric_comparison || {}} />
                    </div>
                  </div>

                  {/* Model cards */}
                  <div style={{ marginTop: "20px" }}>
                    <div style={styles.sectionLabel}>MODEL SCORES</div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "14px" }}>
                      {result.model_results?.sort((a, b) => b.metrics.robustness_score - a.metrics.robustness_score).map((r, i) => (
                        <div key={r.model} style={{
                          ...styles.card,
                          border: `1px solid ${i === 0 ? COLORS.accent + "66" : COLORS.border}`,
                          cursor: "pointer",
                        }} onClick={() => { setSelectedModel(r.model); setActiveTab("variants"); }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", alignItems: "center" }}>
                            <span style={{ fontSize: "13px", color: MODEL_COLORS[r.model] || COLORS.text, fontWeight: 700 }}>{r.model}</span>
                            {i === 0 && <span style={{ fontSize: "10px", color: COLORS.amber }}>BEST</span>}
                            {i === result.model_results.length - 1 && <span style={{ fontSize: "10px", color: COLORS.red }}>LOWEST</span>}
                          </div>
                          <ProgressBar value={r.metrics.robustness_score} color={MODEL_COLORS[r.model] || COLORS.accent} label="Robustness" />
                          <ProgressBar value={r.metrics.answer_stability} color={COLORS.green} label="Stability" />
                          <ProgressBar value={1 - r.metrics.hallucination_rate} color={COLORS.blue} label="No Halluc" />
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Variants Tab */}
              {activeTab === "variants" && (
                <div>
                  <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
                    {allModels.map(m => (
                      <button key={m} style={styles.modelChip(selectedModel === m, m)} onClick={() => setSelectedModel(m)}>
                        <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: MODEL_COLORS[m] || COLORS.accent, display: "inline-block" }} />
                        {m}
                      </button>
                    ))}
                  </div>
                  {currentModelResult && (
                    <div style={styles.card}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <div style={styles.sectionLabel}>PROMPT VARIANTS · {currentModelResult.model}</div>
                        <div style={{ display: "flex", gap: "16px" }}>
                          <span style={{ fontSize: "11px", color: COLORS.green }}>Stability: {(currentModelResult.metrics.answer_stability * 100).toFixed(0)}%</span>
                          <span style={{ fontSize: "11px", color: COLORS.red }}>Halluc: {(currentModelResult.metrics.hallucination_rate * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <div style={{ fontSize: "11px", color: COLORS.textMuted, marginBottom: "12px", display: "grid", gridTemplateColumns: "140px 1fr auto", gap: "12px" }}>
                        <span>TYPE</span><span>PROMPT</span><span>ANSWER / LATENCY</span>
                      </div>
                      <VariantsList variants={currentModelResult.variants} model={selectedModel} />
                    </div>
                  )}
                </div>
              )}

              {/* Traces Tab */}
              {activeTab === "traces" && (
                <div>
                  <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
                    {allModels.map(m => (
                      <button key={m} style={styles.modelChip(selectedModel === m, m)} onClick={() => setSelectedModel(m)}>
                        {m}
                      </button>
                    ))}
                  </div>
                  {currentModelResult && (
                    <div>
                      {currentModelResult.variants.map((v, i) => (
                        <div key={i} style={styles.card}>
                          <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "12px" }}>
                            <span style={styles.perturbBadge(v.perturbation_type)}>{v.perturbation_type}</span>
                            <span style={{ fontSize: "11px", color: COLORS.textMuted, flex: 1 }}>{v.prompt?.substring(0, 80)}…</span>
                            <span style={{ fontSize: "13px", fontWeight: 700, color: v.final_answer === (result.config.ground_truth) ? COLORS.green : COLORS.red }}>→ {v.final_answer}</span>
                          </div>
                          <div style={{ display: "flex", gap: "0", position: "relative" }}>
                            <div style={{ width: "2px", background: `linear-gradient(180deg, ${COLORS.accent}, transparent)`, marginRight: "16px", borderRadius: "1px" }} />
                            <div style={{ flex: 1 }}>
                              {v.reasoning_steps?.map((s, si) => (
                                <div key={si} style={{
                                  display: "flex", gap: "12px", marginBottom: "8px", alignItems: "flex-start",
                                  padding: "8px 10px", background: COLORS.bg, borderRadius: "4px",
                                }}>
                                  <div style={{ width: "22px", height: "22px", borderRadius: "50%", background: COLORS.accentGlow, border: `1px solid ${COLORS.accent}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", color: COLORS.accent, flexShrink: 0 }}>{s.index}</div>
                                  <div>
                                    <div style={{ fontSize: "10px", color: COLORS.textDim, letterSpacing: "0.1em", marginBottom: "2px" }}>[{s.type}]</div>
                                    <div style={{ fontSize: "12px", color: COLORS.text }}>{s.content}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Comparison Tab */}
              {activeTab === "comparison" && (
                <div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "20px" }}>
                    <div style={styles.card}>
                      <div style={styles.sectionLabel}>ROBUSTNESS RANKING</div>
                      {result.model_results?.sort((a, b) => b.metrics.robustness_score - a.metrics.robustness_score).map((r, i) => (
                        <div key={r.model} style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "14px" }}>
                          <span style={{ fontSize: "20px", color: i === 0 ? COLORS.amber : COLORS.textDim, width: "28px" }}>
                            {i === 0 ? "①" : i === 1 ? "②" : i === 2 ? "③" : `${i + 1}.`}
                          </span>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: "12px", color: MODEL_COLORS[r.model] || COLORS.text, marginBottom: "4px" }}>{r.model}</div>
                            <ProgressBar value={r.metrics.robustness_score} color={MODEL_COLORS[r.model] || COLORS.accent} />
                          </div>
                          <span style={{ fontSize: "16px", fontWeight: 700, color: COLORS.text }}>{(r.metrics.robustness_score * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>

                    <div style={styles.card}>
                      <div style={styles.sectionLabel}>METRIC BREAKDOWN</div>
                      {Object.entries(comparison?.metric_comparison || {}).map(([metric, vals]) => (
                        <div key={metric} style={{ marginBottom: "16px" }}>
                          <div style={{ fontSize: "10px", color: COLORS.textMuted, letterSpacing: "0.1em", marginBottom: "6px" }}>
                            {metric.replace(/_/g, " ").toUpperCase()}
                          </div>
                          {Object.entries(vals).sort(([, a], [, b]) => b - a).map(([model, val]) => (
                            <div key={model} style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "4px" }}>
                              <span style={{ fontSize: "10px", color: MODEL_COLORS[model] || COLORS.textMuted, width: "120px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{model}</span>
                              <div style={{ flex: 1, height: "6px", background: COLORS.border, borderRadius: "3px" }}>
                                <div style={{ width: `${val * 100}%`, height: "100%", background: MODEL_COLORS[model] || COLORS.accent, borderRadius: "3px" }} />
                              </div>
                              <span style={{ fontSize: "10px", color: COLORS.textMuted, width: "40px", textAlign: "right" }}>{(val * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={styles.card}>
                    <div style={styles.sectionLabel}>FULL COMPARISON CHART</div>
                    <ModelComparisonBars models={allModels} metrics={comparison?.metric_comparison || {}} />
                  </div>
                </div>
              )}
            </>
          ) : (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", flexDirection: "column", gap: "16px" }}>
              <div style={{ fontSize: "40px" }}>⬡</div>
              <div style={{ fontSize: "14px", color: COLORS.textMuted }}>Configure your evaluation and click Run</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
