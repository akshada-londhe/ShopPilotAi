"use client";

import {
  Brain,
  Search,
  ShieldCheck,
  PackageCheck,
  Scale,
  Award,
  Sparkles,
  RotateCcw,
  CheckCircle2,
  Database,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Stage descriptions & metadata ──────────────────────────────────────────
const STAGE_DESCRIPTIONS: Record<
  string,
  { title: string; desc: string; icon: React.ElementType }
> = {
  normalizing: {
    title: "1. Query Normalizer",
    desc: "Extracting category, hard budget range, and soft preference attributes.",
    icon: Brain,
  },
  generating: {
    title: "2. Query Generator",
    desc: "Formulating targeted multi-variation search keywords for e-commerce search.",
    icon: Search,
  },
  cache_check: {
    title: "3. Vector Memory Cache Check",
    desc: "Querying ChromaDB vector store for existing matching embeddings.",
    icon: Database,
  },
  searching: {
    title: "4. Tavily Web Retrieval",
    desc: "Querying live web engines for real-time merchant product pages.",
    icon: Search,
  },
  sanitizing: {
    title: "5. Content Sanitization",
    desc: "Cleaning scraped HTML and stripping malicious prompt injections.",
    icon: ShieldCheck,
  },
  extracting: {
    title: "6. Structured Product Extractor",
    desc: "Extracting verified product titles, literal prices, and specification fields.",
    icon: PackageCheck,
  },
  matching: {
    title: "7. Constraint & Preference Matching",
    desc: "Applying deterministic hard budget filters and scoring soft quality preferences.",
    icon: Scale,
  },
  critiquing: {
    title: "8. Critic (LLM-as-a-Judge)",
    desc: "Scoring evidence quality, completeness, and checking contradiction rubric.",
    icon: Award,
  },
  retrying: {
    title: "Self-Correction Retry Loop",
    desc: "Refining queries using critic feedback for a higher-confidence second pass.",
    icon: RotateCcw,
  },
  synthesizing: {
    title: "9. Recommendation Synthesizer",
    desc: "Generating human-readable summary with direct clickable source citations.",
    icon: Sparkles,
  },
  done: {
    title: "Search Complete",
    desc: "All products verified against constraints and ready for review.",
    icon: CheckCircle2,
  },
};

interface PipelineDiagramProps {
  activeStage: string | null;
  completedStages: string[];
  isBestAvailable?: boolean;
  fromCache?: boolean;
  className?: string;
}

// ─── Node layout in 980×340 coordinate space ────────────────────────────────
const NODES: Array<{
  id: string;
  label: string;
  sublabel: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color: "teal" | "blue" | "cyan" | "orange" | "yellow" | "emerald";
}> = [
  { id: "normalizing",  label: "Query Normalizer",   sublabel: "Extract intent & budget",  x: 95,  y: 60,  w: 145, h: 50, color: "teal"    },
  { id: "generating",   label: "Query Generator",    sublabel: "Targeted search terms",    x: 95,  y: 180, w: 145, h: 50, color: "blue"    },
  { id: "cache_check",  label: "ChromaDB Cache",     sublabel: "Vector similarity check",  x: 310, y: 180, w: 145, h: 50, color: "cyan"    },
  { id: "searching",    label: "Tavily Search",      sublabel: "Live web retrieval",       x: 310, y: 280, w: 145, h: 50, color: "orange"  },
  { id: "sanitizing",   label: "Sanitization",       sublabel: "Prompt injection defense", x: 530, y: 280, w: 145, h: 50, color: "yellow"  },
  { id: "extracting",   label: "Product Extractor",  sublabel: "Extract price & specs",    x: 530, y: 180, w: 145, h: 50, color: "blue"    },
  { id: "matching",     label: "Constraint Match",   sublabel: "Hard + soft filters",      x: 530, y: 60,  w: 145, h: 50, color: "teal"    },
  { id: "critiquing",   label: "Critic Agent",       sublabel: "Rubric scoring judge",     x: 740, y: 60,  w: 135, h: 50, color: "orange"  },
  { id: "retrying",     label: "Retry Loop",         sublabel: "Self-correction",          x: 740, y: 180, w: 135, h: 50, color: "yellow"  },
  { id: "synthesizing", label: "Synthesizer",        sublabel: "Source-grounded summary",  x: 900, y: 60,  w: 125, h: 50, color: "emerald" },
  { id: "done",         label: "Verified Result",    sublabel: "Ranked recommendations",   x: 900, y: 180, w: 125, h: 50, color: "emerald" },
];

const EDGES: Array<{
  from: string;
  to: string;
  label?: string;
  dashed?: boolean;
  curved?: boolean;
}> = [
  { from: "normalizing",  to: "generating"  },
  { from: "generating",   to: "cache_check" },
  { from: "cache_check",  to: "searching",   label: "miss / stale", dashed: true },
  { from: "cache_check",  to: "matching",    label: "cache hit",    dashed: true },
  { from: "searching",    to: "sanitizing"  },
  { from: "sanitizing",   to: "extracting"  },
  { from: "extracting",   to: "matching"    },
  { from: "matching",     to: "critiquing"  },
  { from: "critiquing",   to: "synthesizing", label: "pass (≥7.0)" },
  { from: "critiquing",   to: "retrying",     label: "fail (<7.0)", dashed: true },
  { from: "retrying",     to: "generating",   label: "retry with feedback", dashed: true, curved: true },
  { from: "synthesizing", to: "done"        },
  { from: "retrying",     to: "done",         label: "exhausted", dashed: true },
];

const PALETTE = {
  teal:    { bg: "#0d9488" },
  blue:    { bg: "#2563eb" },
  cyan:    { bg: "#0891b2" },
  orange:  { bg: "#ea580c" },
  yellow:  { bg: "#d97706" },
  emerald: { bg: "#059669" },
};

// Active/primary signal color (matches the --primary token in globals.css).
const ACTIVE_COLOR = "#14b8a6";
const ACTIVE_COLOR_LIGHT = "#f0fdfa";

function getNodeState(
  id: string,
  activeStage: string | null,
  completedStages: string[]
): "idle" | "active" | "done" {
  if (id === activeStage) return "active";
  if (completedStages.includes(id)) return "done";
  return "idle";
}

function getEdgePoints(from: (typeof NODES)[0], to: (typeof NODES)[0]) {
  return { fx: from.x, fy: from.y, tx: to.x, ty: to.y };
}

function nodeById(id: string) {
  return NODES.find((n) => n.id === id)!;
}

export function PipelineDiagram({
  activeStage,
  completedStages,
  isBestAvailable = false,
  fromCache = false,
  className,
}: PipelineDiagramProps) {
  const isRetrying = activeStage === "retrying" || completedStages.includes("retrying");
  const currentStageInfo = activeStage ? STAGE_DESCRIPTIONS[activeStage] : null;
  const ActiveIcon = fromCache ? Database : currentStageInfo ? currentStageInfo.icon : Sparkles;

  return (
    <div
      className={cn(
        "flex h-full w-full flex-col justify-between overflow-hidden rounded-xl border bg-gradient-to-b from-card/90 via-card to-background/90 p-3 shadow-md backdrop-blur-md transition-all sm:p-4",
        fromCache ? "border-cyan-500/40 shadow-cyan-500/10" : "border-primary/20",
        className
      )}
    >
      {/* ── Top Header Bar ── */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-border/40 pb-2.5">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-6 w-6 items-center justify-center rounded-md shadow-xs",
              fromCache ? "bg-cyan-500/20 text-cyan-400" : "bg-primary/20 text-primary"
            )}
          >
            <ActiveIcon className={cn("h-3.5 w-3.5", activeStage && activeStage !== "done" && "animate-spin")} />
          </div>
          <div>
            <h2 className="flex items-center gap-1.5 text-xs font-bold tracking-tight text-foreground">
              Live Agentic RAG Engine
              {fromCache ? (
                <span className="py-0.2 flex items-center gap-1 rounded-full border border-cyan-500/30 bg-cyan-500/15 px-2 text-[9.5px] font-bold text-cyan-300 shadow-[0_0_8px_#06b6d4]">
                  <Database className="h-2.5 w-2.5" />
                  SAVED IN MEMORY (CHROMADB)
                </span>
              ) : activeStage && activeStage !== "done" ? (
                <span className="py-0.2 flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-1.5 text-[9.5px] font-semibold text-primary animate-pulse">
                  <span className="h-1 w-1 rounded-full bg-primary"></span>
                  EXECUTING
                </span>
              ) : activeStage === "done" ? (
                <span className="py-0.2 rounded-full border border-blue-500/20 bg-blue-500/10 px-1.5 text-[9.5px] font-semibold text-blue-400">
                  COMPLETED
                </span>
              ) : (
                <span className="text-[10px] font-normal text-muted-foreground">Ready</span>
              )}
            </h2>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2.5 text-[10.5px] text-muted-foreground">
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee]"></span>
            <span className="text-[10px] font-medium text-cyan-300">Memory Hit</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary shadow-[0_0_6px_hsl(var(--glow-active))]"></span>
            <span className="text-[10px] font-medium text-foreground">Active</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
            <span className="text-[10px]">Done</span>
          </div>
          {isBestAvailable && (
            <span className="py-0.2 rounded-full border border-amber-500/20 bg-amber-500/10 px-1.5 text-[9.5px] font-semibold text-amber-400">
              Partial
            </span>
          )}
        </div>
      </div>

      {/* ── Interactive SVG Flowchart Container ── */}
      <div className="my-1 flex min-h-0 w-full flex-1 items-center justify-center">
        <svg
          viewBox="0 0 980 340"
          className="max-h-[calc(100vh-310px)] h-full w-full select-none object-contain"
          aria-label="Interactive Pipeline Architecture"
        >
          <defs>
            <filter id="neon-active" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="5" result="blur1" />
              <feGaussianBlur stdDeviation="12" result="blur2" />
              <feMerge>
                <feMergeNode in="blur2" />
                <feMergeNode in="blur1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="laser-glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="2.5" result="glow" />
              <feMerge>
                <feMergeNode in="glow" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <marker id="arrow-neutral" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#475569" />
            </marker>
            <marker id="arrow-memory-laser" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#06b6d4" />
            </marker>
            <marker id="arrow-active-laser" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill={ACTIVE_COLOR} />
            </marker>
            <marker id="arrow-done" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#10b981" />
            </marker>
            <marker id="arrow-retry-laser" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#f59e0b" />
            </marker>
          </defs>

          {/* ── Draw Edges (Laser Beams & Connecting Lines) ── */}
          {EDGES.map((edge, i) => {
            const fromNode = nodeById(edge.from);
            const toNode = nodeById(edge.to);
            if (!fromNode || !toNode) return null;

            const { fx, fy, tx, ty } = getEdgePoints(fromNode, toNode);
            const isCacheHitEdge = fromCache && edge.from === "cache_check" && edge.to === "matching";
            const isBypassedEdge =
              fromCache &&
              ((edge.from === "cache_check" && edge.to === "searching") ||
                edge.from === "searching" ||
                edge.from === "sanitizing" ||
                edge.from === "extracting");
            const isEdgeActive = isCacheHitEdge || activeStage === edge.to;
            const isEdgeTraversed =
              isCacheHitEdge || (completedStages.includes(edge.from) && completedStages.includes(edge.to));
            const isRetryEdge = edge.from === "retrying" && edge.to === "generating";

            const edgeColor = isCacheHitEdge
              ? "#06b6d4"
              : isRetryEdge
              ? "#f59e0b"
              : isBypassedEdge
              ? "#1e293b"
              : isEdgeActive
              ? ACTIVE_COLOR
              : isEdgeTraversed
              ? "#10b981"
              : "#334155";

            const marker = isCacheHitEdge
              ? "url(#arrow-memory-laser)"
              : isRetryEdge
              ? "url(#arrow-retry-laser)"
              : isEdgeActive
              ? "url(#arrow-active-laser)"
              : isEdgeTraversed
              ? "url(#arrow-done)"
              : "url(#arrow-neutral)";

            if (edge.curved) {
              const midX = (fx + tx) / 2;
              const midY = Math.max(fy, ty) + 80;
              const pathD = `M${fx},${fy} Q${midX},${midY} ${tx},${ty}`;

              return (
                <g key={i}>
                  <path
                    d={pathD}
                    fill="none"
                    stroke={isRetrying ? "#f59e0b" : "#334155"}
                    strokeWidth={isRetrying ? 2.5 : 1.2}
                    strokeDasharray={isRetrying ? "8 5" : "5 5"}
                    markerEnd={marker}
                    filter={isRetrying ? "url(#laser-glow)" : undefined}
                    style={isRetrying ? { animation: "laser-flow 0.8s linear infinite" } : undefined}
                  />
                  {edge.label && (
                    <text
                      x={midX}
                      y={midY + 12}
                      textAnchor="middle"
                      fontSize="8.5"
                      fontWeight="bold"
                      fill={isRetrying ? "#f59e0b" : "#64748b"}
                    >
                      {edge.label}
                    </text>
                  )}
                </g>
              );
            }

            const dx = tx - fx;
            const dy = ty - fy;
            let startX = fx;
            let startY = fy;
            let endX = tx;
            let endY = ty;

            if (Math.abs(dx) > Math.abs(dy)) {
              startX = dx > 0 ? fx + fromNode.w / 2 : fx - fromNode.w / 2;
              endX = dx > 0 ? tx - toNode.w / 2 : tx + toNode.w / 2;
            } else {
              startY = dy > 0 ? fy + fromNode.h / 2 : fy - fromNode.h / 2;
              endY = dy > 0 ? ty - toNode.h / 2 : ty + toNode.h / 2;
            }

            return (
              <g key={i}>
                <line
                  x1={startX}
                  y1={startY}
                  x2={endX}
                  y2={endY}
                  stroke={edgeColor}
                  strokeWidth={isEdgeActive || isCacheHitEdge ? 2 : 1.2}
                  strokeDasharray={isCacheHitEdge ? "6 3" : edge.dashed ? "4 4" : undefined}
                  markerEnd={marker}
                  filter={isEdgeActive || isCacheHitEdge ? "url(#laser-glow)" : undefined}
                  style={isEdgeActive || isCacheHitEdge ? { animation: "laser-flow 0.5s linear infinite" } : undefined}
                />

                {(isEdgeActive || isCacheHitEdge) && (
                  <circle r="3" fill={ACTIVE_COLOR_LIGHT} filter="url(#laser-glow)">
                    <animateMotion path={`M${startX},${startY} L${endX},${endY}`} dur="0.8s" repeatCount="indefinite" />
                  </circle>
                )}

                {edge.label && (
                  <text
                    x={(startX + endX) / 2 + (dx === 0 ? 8 : 0)}
                    y={(startY + endY) / 2 - 4}
                    textAnchor={dx === 0 ? "start" : "middle"}
                    fontSize="8.5"
                    fontWeight="500"
                    fill={isEdgeActive ? "#5eead4" : isEdgeTraversed ? "#34d399" : "#64748b"}
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* ── Draw Nodes ── */}
          {NODES.map((node) => {
            const state = getNodeState(node.id, activeStage, completedStages);
            const p = PALETTE[node.color];
            const isBypassedNode = fromCache && (node.id === "searching" || node.id === "sanitizing" || node.id === "extracting");
            const isMemoryNode = fromCache && node.id === "cache_check";
            const isActive = isMemoryNode || state === "active";
            const isDone = !isBypassedNode && state === "done";

            const rx = node.x - node.w / 2;
            const ry = node.y - node.h / 2;

            const nodeSublabel = isBypassedNode
              ? "Bypassed (0s memory)"
              : isMemoryNode
              ? "Found Embeddings (0s)"
              : node.sublabel;

            return (
              <g
                key={node.id}
                role="img"
                aria-label={`${node.label}: ${state}`}
                className={cn("transition-all duration-300", isBypassedNode && "opacity-35")}
              >
                {isActive && (
                  <rect
                    x={rx - 5}
                    y={ry - 5}
                    width={node.w + 10}
                    height={node.h + 10}
                    rx="12"
                    fill={isMemoryNode ? "#06b6d4" : p.bg}
                    opacity="0.4"
                    filter="url(#neon-active)"
                    style={{ animation: "pipeline-glow 1.2s ease-in-out infinite" }}
                  />
                )}

                <rect
                  x={rx}
                  y={ry}
                  width={node.w}
                  height={node.h}
                  rx="9"
                  fill={isMemoryNode ? "#0891b2" : isActive ? p.bg : isDone ? "#1e293b" : "#0f172a"}
                  stroke={isMemoryNode ? "#22d3ee" : isActive ? "#ffffff" : isDone ? "#10b981" : "#334155"}
                  strokeWidth={isActive || isMemoryNode ? 2 : isDone ? 1.2 : 1}
                  className="transition-colors duration-300"
                />

                {isDone && (
                  <g transform={`translate(${rx + node.w - 16}, ${ry + 7})`}>
                    <circle cx="5" cy="5" r="6" fill="#10b981" />
                    <text x="5" y="8" fontSize="8" fontWeight="bold" fill="#ffffff" textAnchor="middle">
                      ✓
                    </text>
                  </g>
                )}

                {isMemoryNode && (
                  <g transform={`translate(${rx + node.w - 18}, ${ry + 7})`}>
                    <circle cx="5" cy="5" r="6" fill="#22d3ee" />
                    <text x="5" y="8" fontSize="8" fontWeight="bold" fill="#0f172a" textAnchor="middle">
                      ⚡
                    </text>
                  </g>
                )}

                {isActive && !isMemoryNode && (
                  <g transform={`translate(${rx + node.w - 18}, ${ry + 7})`}>
                    <circle cx="5" cy="5" r="5" fill="#ffffff" className="animate-ping opacity-75" />
                    <circle cx="5" cy="5" r="3.5" fill="#ffffff" />
                  </g>
                )}

                <text
                  x={node.x}
                  y={node.y - 3}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight={isActive ? "700" : "600"}
                  fill={isActive ? "#ffffff" : isDone ? "#f8fafc" : "#94a3b8"}
                  className="tracking-tight"
                >
                  {node.label}
                </text>

                <text
                  x={node.x}
                  y={node.y + 11}
                  textAnchor="middle"
                  fontSize="8.5"
                  fontWeight="500"
                  fill={isMemoryNode ? "#cffafe" : isActive ? "#f0fdfa" : isDone ? "#34d399" : "#64748b"}
                >
                  {nodeSublabel}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* ── Live Stage Telemetry Banner ── */}
      {fromCache ? (
        <div className="flex shrink-0 items-center gap-2.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 p-2.5 shadow-[0_0_10px_rgba(6,182,212,0.12)] animate-[fade-in-up_0.2s_ease-out_both]">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-cyan-500 font-bold text-slate-950">
            <Database className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <p className="truncate text-[11.5px] font-bold text-cyan-300">
                ⚡ Vector Memory Hit: Embeddings Loaded from ChromaDB!
              </p>
              <span className="py-0.2 rounded border border-cyan-500/30 bg-cyan-950/60 px-1.5 font-mono text-[9px] font-bold uppercase text-cyan-400">
                0s CACHE HIT
              </span>
            </div>
            <p className="truncate text-[10px] text-cyan-200/80">
              Matching product embeddings were already saved in local memory — served instantly!
            </p>
          </div>
        </div>
      ) : currentStageInfo && activeStage !== "done" ? (
        <div className="flex shrink-0 items-center gap-2.5 rounded-lg border border-primary/30 bg-primary/10 p-2.5 animate-[fade-in-up_0.2s_ease-out_both]">
          <div className="relative flex h-6 w-6 shrink-0 items-center justify-center rounded bg-primary text-primary-foreground shadow-xs">
            <ActiveIcon className="h-3.5 w-3.5 animate-bounce" />
            <span className="absolute -right-0.5 -top-0.5 flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <p className="truncate text-[11.5px] font-bold text-foreground">{currentStageInfo.title}</p>
              <span className="text-[9px] font-mono font-medium uppercase text-primary">IN PROGRESS</span>
            </div>
            <p className="truncate text-[10px] text-muted-foreground">{currentStageInfo.desc}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}