<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { api, type Board, type Leaderboard } from "../api";

const props = defineProps<{ id: string }>();

const board = ref<Board | null>(null);
const lb = ref<Leaderboard | null>(null);
const metric = ref("total_tokens");
const window = ref("7d");
const err = ref("");

const METRICS = [
  { v: "total_tokens", label: "Total tokens" },
  { v: "output_tokens", label: "Output tokens" },
  { v: "cost_usd", label: "Cost (USD)" },
  { v: "active_days", label: "Active days" },
];
const WINDOWS = [
  { v: "today", label: "Today" },
  { v: "7d", label: "7 days" },
  { v: "30d", label: "30 days" },
  { v: "all_time", label: "All time" },
];

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

async function load() {
  err.value = "";
  try {
    board.value = await api.getBoard(props.id);
    metric.value = board.value.default_metric;
    window.value = board.value.default_window;
    await refresh();
  } catch (e: any) {
    err.value = e.message;
  }
}

async function refresh() {
  try {
    lb.value = await api.leaderboard(props.id, metric.value, window.value);
  } catch (e: any) {
    err.value = e.message;
  }
}

watch([metric, window], refresh);
onMounted(load);
</script>

<template>
  <div v-if="board" class="card">
    <h1>{{ board.name }}</h1>
    <p class="muted">{{ board.slug }} · {{ board.visibility }}</p>
    <p v-if="board.invite_code">
      <span class="muted">Invite code:</span>
      <code class="token-box" style="display:inline-block;padding:4px 8px">{{ board.invite_code }}</code>
    </p>
    <div class="row" style="margin-top:8px">
      <select v-model="metric">
        <option v-for="m in METRICS" :key="m.v" :value="m.v">{{ m.label }}</option>
      </select>
      <select v-model="window">
        <option v-for="w in WINDOWS" :key="w.v" :value="w.v">{{ w.label }}</option>
      </select>
    </div>
  </div>

  <p v-if="err" class="err">{{ err }}</p>

  <div v-if="lb" class="card">
    <h2>Ranking · {{ lb.metric }} · {{ lb.window }}</h2>
    <p v-if="lb.entries.length === 0" class="muted">
      No usage yet. Members need to push with the skill.
    </p>
    <div v-for="e in lb.entries" :key="e.handle" class="entry" style="display:block">
      <div style="display:flex;align-items:center;gap:14px">
        <div class="rank" :class="{ top: e.rank === 1 }">{{ e.rank }}</div>
        <div class="who-col">
          <div class="name">{{ e.alias || e.handle }}</div>
          <div class="handle">{{ e.handle }}</div>
        </div>
        <div class="value">
          {{ fmt(e.value, lb.metric) }}<span class="unit">{{ unit(lb.metric) }}</span>
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
  </div>
</template>
