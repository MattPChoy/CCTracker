<script setup lang="ts">
import { computed } from "vue";
import type { PerModel } from "../api";

// Copied from LeaderboardTable.vue's local color mapping (kept in sync by hand,
// not imported, per the "self-contained component" contract).
const MODEL_COLORS: Record<string, string> = {
  opus: "var(--opus)",
  sonnet: "var(--sonnet)",
  haiku: "var(--haiku)",
};
function color(model: string): string {
  return MODEL_COLORS[model] || "#7a8296";
}

const props = withDefaults(
  defineProps<{
    perModel: PerModel[];
    /** Donut diameter in px. Defaults to a compact inline size. */
    size?: number;
    /** Show the dot+label+% legend beside the donut. */
    legend?: boolean;
  }>(),
  { size: 56, legend: true }
);

interface Segment {
  model: string;
  label: string;
  color: string;
  pct: number; // rounded share, for display only
  start: number; // cumulative percent, 0-100
  end: number; // cumulative percent, 0-100
}

// Largest share first, matching the stacked bar in LeaderboardTable.vue.
// Zero-share entries are dropped so they don't leave a degenerate 0-width
// wedge (and a spurious seam) in the gradient.
const segments = computed<Segment[]>(() => {
  const entries = (props.perModel || []).filter((pm) => pm.share > 0);
  if (!entries.length) return [];
  const sorted = [...entries].sort((a, b) => b.share - a.share);

  let cursor = 0;
  const list = sorted.map((pm): Segment => {
    const start = cursor;
    const end = cursor + pm.share * 100;
    cursor = end;
    return { model: pm.model, label: pm.label, color: color(pm.model), pct: Math.round(pm.share * 100), start, end };
  });
  // Shares may not sum to exactly 100 due to floating point / upstream
  // rounding; pin the last boundary to 100% so the ring closes with no gap.
  list[list.length - 1].end = 100;
  return list;
});

// Hard-edged conic-gradient: each stop repeats its color at both the start
// and end percentage of its wedge, so wedges abut with no blended seam.
// A single segment collapses to a plain color (no gradient function at all)
// so a 100%-share model renders as a clean solid ring, never a seam artifact.
const gradient = computed(() => {
  const segs = segments.value;
  if (!segs.length) return "var(--panel-2)";
  if (segs.length === 1) return segs[0].color;
  const stops = segs.map((s) => `${s.color} ${s.start}% ${s.end}%`).join(", ");
  return `conic-gradient(${stops})`;
});

const tooltip = computed(() => segments.value.map((s) => `${s.label}: ${s.pct}%`).join(" · "));
</script>

<template>
  <div v-if="segments.length" class="model-mix">
    <div
      class="model-mix-donut"
      role="img"
      :aria-label="tooltip"
      :title="tooltip"
      :style="{ width: size + 'px', height: size + 'px', background: gradient }"
    >
      <div class="model-mix-hole"></div>
    </div>
    <div v-if="legend" class="legend model-mix-legend">
      <span v-for="seg in segments" :key="seg.model">
        <span class="dot" :style="{ background: seg.color }"></span>
        {{ seg.label }} {{ seg.pct }}%
      </span>
    </div>
  </div>
  <div v-else class="model-mix-empty muted">No data</div>
</template>

<style scoped>
.model-mix {
  display: flex;
  align-items: center;
  gap: 10px;
}
.model-mix-donut {
  position: relative;
  flex: 0 0 auto;
  border-radius: 50%;
}
.model-mix-hole {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 58%;
  height: 58%;
  border-radius: 50%;
  background: var(--panel);
  transform: translate(-50%, -50%);
}
.model-mix-legend {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  margin-top: 0;
}
.model-mix-empty {
  font-size: 12px;
}
</style>
