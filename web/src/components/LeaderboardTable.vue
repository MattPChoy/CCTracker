<script setup lang="ts">
import type { Entry } from "../api";

defineProps<{ entries: Entry[]; metric: string }>();

const MODEL_COLORS: Record<string, string> = {
  opus: "var(--opus)",
  sonnet: "var(--sonnet)",
  haiku: "var(--haiku)",
};
function color(model: string): string {
  return MODEL_COLORS[model] || "#7a8296";
}

function fmt(n: number, m: string): string {
  if (m === "cost_usd") return "$" + n.toFixed(2);
  if (m === "active_days") return String(n);
  return n >= 1000 ? (n / 1000).toFixed(1) + "k" : String(n);
}
function unit(m: string): string {
  if (m === "cost_usd") return "";
  if (m === "active_days") return "days";
  return "tokens";
}
</script>

<template>
  <div v-for="e in entries" :key="e.handle" class="entry" style="display:block">
    <div style="display:flex;align-items:center;gap:14px">
      <div class="rank" :class="{ top: e.rank === 1 }">{{ e.rank }}</div>
      <div class="who-col">
        <div class="name">{{ e.handle }}</div>
      </div>
      <div class="value">
        {{ fmt(e.value, metric) }}<span class="unit">{{ unit(metric) }}</span>
      </div>
    </div>
    <div v-if="e.per_model.length" style="margin-left:42px">
      <div class="bar">
        <span
          v-for="pm in e.per_model"
          :key="pm.model"
          :style="{ width: (pm.share * 100).toFixed(1) + '%', background: color(pm.model) }"
          :title="`${pm.label}: ${(pm.share * 100).toFixed(0)}%`"
        ></span>
      </div>
      <div class="legend">
        <span v-for="pm in e.per_model" :key="pm.model">
          <span class="dot" :style="{ background: color(pm.model) }"></span>
          {{ pm.label }} {{ (pm.share * 100).toFixed(0) }}%<template v-if="pm.cost_usd != null"> · ${{ pm.cost_usd.toFixed(2) }}</template>
        </span>
      </div>
    </div>
  </div>
</template>
