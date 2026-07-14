<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "../api";

const props = defineProps<{ handle: string }>();

interface DayCell {
  date: string; // yyyy-mm-dd
  total_tokens: number;
  level: 0 | 1 | 2 | 3 | 4;
  inRange: boolean;
}

const loading = ref(true);
const errored = ref(false);
const weeks = ref<DayCell[][]>([]); // weeks[w][d], d = 0 (Sun) .. 6 (Sat)

function toKey(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function levelFor(tokens: number, max: number): 0 | 1 | 2 | 3 | 4 {
  if (tokens <= 0 || max <= 0) return 0;
  const frac = tokens / max;
  if (frac > 0.75) return 4;
  if (frac > 0.5) return 3;
  if (frac > 0.25) return 2;
  return 1;
}

async function load() {
  loading.value = true;
  errored.value = false;
  try {
    const res = await api.userDaily(props.handle, 371);
    const byDate = new Map<string, number>();
    for (const d of res.days) byDate.set(d.date, d.total_tokens);

    const today = new Date();
    today.setUTCHours(0, 0, 0, 0);
    const rangeStart = new Date(today);
    rangeStart.setUTCDate(rangeStart.getUTCDate() - 370); // ~53 weeks back
    // Align the grid start back to the most recent Sunday on/before rangeStart.
    const gridStart = new Date(rangeStart);
    gridStart.setUTCDate(gridStart.getUTCDate() - gridStart.getUTCDay());

    const max = res.days.length ? Math.max(...res.days.map((d) => d.total_tokens)) : 0;

    const cells: DayCell[] = [];
    const cursor = new Date(gridStart);
    while (cursor <= today) {
      const key = toKey(cursor);
      const tokens = byDate.get(key) || 0;
      cells.push({
        date: key,
        total_tokens: tokens,
        level: levelFor(tokens, max),
        inRange: cursor >= rangeStart,
      });
      cursor.setUTCDate(cursor.getUTCDate() + 1);
    }

    const built: DayCell[][] = [];
    for (let i = 0; i < cells.length; i += 7) {
      built.push(cells.slice(i, i + 7));
    }
    weeks.value = built;
  } catch {
    errored.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(load);

const hasData = computed(() => weeks.value.some((w) => w.some((c) => c.total_tokens > 0)));

function tooltip(cell: DayCell): string {
  return `${cell.date}: ${cell.total_tokens.toLocaleString()} tokens`;
}
</script>

<template>
  <div class="heatmap" v-if="!loading && !errored">
    <div class="grid">
      <div v-for="(week, wi) in weeks" :key="wi" class="week">
        <div
          v-for="(cell, di) in week"
          :key="di"
          class="cell"
          :class="`lvl-${cell.level}`"
          :style="{ visibility: cell.inRange ? 'visible' : 'hidden' }"
          :title="tooltip(cell)"
        ></div>
      </div>
    </div>
    <div class="legend-row" v-if="hasData">
      <span class="muted">Less</span>
      <span class="swatch lvl-0"></span>
      <span class="swatch lvl-1"></span>
      <span class="swatch lvl-2"></span>
      <span class="swatch lvl-3"></span>
      <span class="swatch lvl-4"></span>
      <span class="muted">More</span>
    </div>
    <div v-else class="muted no-data">No usage yet</div>
  </div>
</template>

<style scoped>
.heatmap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.grid {
  display: flex;
  gap: 2px;
  overflow-x: auto;
}
.week {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cell {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--panel-2);
}
.cell.lvl-0 {
  background: var(--panel-2);
}
.cell.lvl-1 {
  background: color-mix(in srgb, var(--accent) 25%, var(--panel-2));
}
.cell.lvl-2 {
  background: color-mix(in srgb, var(--accent) 50%, var(--panel-2));
}
.cell.lvl-3 {
  background: color-mix(in srgb, var(--accent) 75%, var(--panel-2));
}
.cell.lvl-4 {
  background: var(--accent);
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.legend-row .swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}
.legend-row .swatch.lvl-0 {
  background: var(--panel-2);
}
.legend-row .swatch.lvl-1 {
  background: color-mix(in srgb, var(--accent) 25%, var(--panel-2));
}
.legend-row .swatch.lvl-2 {
  background: color-mix(in srgb, var(--accent) 50%, var(--panel-2));
}
.legend-row .swatch.lvl-3 {
  background: color-mix(in srgb, var(--accent) 75%, var(--panel-2));
}
.legend-row .swatch.lvl-4 {
  background: var(--accent);
}
.no-data {
  font-size: 13px;
}
</style>
