<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api, getToken, setToken, type Leaderboard } from "../api";
import InstallSkill from "../components/InstallSkill.vue";
import LeaderboardTable from "../components/LeaderboardTable.vue";

const router = useRouter();
const existingToken = ref("");
const newToken = ref<string | null>(null);
const newHandle = ref<string | null>(null);
const err = ref("");
const busy = ref(false);
const alreadyIn = ref(!!getToken());

// Public leaderboard — the first thing everyone sees.
const lb = ref<Leaderboard | null>(null);
const window = ref("7d");
const metric = ref("total_tokens");
const WINDOWS = [
  { v: "today", label: "Today" },
  { v: "7d", label: "7 days" },
  { v: "30d", label: "30 days" },
  { v: "all_time", label: "All time" },
];
const METRICS = [
  { v: "total_tokens", label: "Tokens" },
  { v: "cost_usd", label: "Cost 💸" },
];

async function loadPublic() {
  try {
    lb.value = await api.publicLeaderboard(metric.value, window.value);
  } catch (e: any) {
    err.value = e.message;
  }
}

function setWindow(w: string) {
  window.value = w;
  loadPublic();
}

function setMetric(m: string) {
  metric.value = m;
  loadPublic();
}

async function getStarted() {
  err.value = "";
  busy.value = true;
  try {
    // No handle needed — the server auto-assigns a friendly one you can change later.
    const res = await api.register();
    newToken.value = res.token;
    newHandle.value = res.handle;
    setToken(res.token);
    alreadyIn.value = true;
  } catch (e: any) {
    err.value = e.message;
  } finally {
    busy.value = false;
  }
}

function useExistingToken() {
  err.value = "";
  setToken(existingToken.value.trim());
  router.push("/boards");
}

function continueIn() {
  router.push("/boards");
}

onMounted(loadPublic);
</script>

<template>
  <!-- CTA banner -->
  <div class="banner">
    <div>
      <strong>CCTracker</strong> · the Claude Code usage leaderboard.
      <span class="muted">See where you'd rank — set up in one command.</span>
    </div>
    <div class="row" style="gap:8px">
      <button v-if="!alreadyIn" :disabled="busy" @click="getStarted">
        {{ busy ? "…" : "Get started" }}
      </button>
      <button v-else class="ghost" @click="continueIn">Your boards →</button>
    </div>
  </div>
  <p v-if="err" class="err">{{ err }}</p>

  <!-- Public leaderboard: first thing you see -->
  <div class="card">
    <div class="row" style="justify-content:space-between;align-items:center;gap:8px">
      <h1 style="margin:0">🏆 Global leaderboard</h1>
      <div class="row" style="gap:8px">
        <div class="ostabs">
          <button
            v-for="m in METRICS"
            :key="m.v"
            :class="{ active: metric === m.v }"
            @click="setMetric(m.v)"
          >{{ m.label }}</button>
        </div>
        <div class="ostabs">
          <button
            v-for="w in WINDOWS"
            :key="w.v"
            :class="{ active: window === w.v }"
            @click="setWindow(w.v)"
          >{{ w.label }}</button>
        </div>
      </div>
    </div>
    <p class="muted" style="margin-top:4px">
      Everyone pushing usage, ranked by {{ metric === "cost_usd" ? "cold hard spend 💸" : "total tokens" }}.
      Flip to see who's burning the most.
    </p>
    <template v-if="lb && lb.entries.length">
      <LeaderboardTable :entries="lb.entries" :metric="lb.metric" />
    </template>
    <p v-else class="muted">No usage pushed yet — be the first on the board.</p>
  </div>

  <!-- Onboarding / install -->
  <template v-if="newToken">
    <div class="card">
      <h2>You're in{{ newHandle ? ` as @${newHandle}` : "" }} 🎉</h2>
      <p class="muted">
        Account created and you're signed in — no token to copy. Paste the prompt
        below into Claude Code to start pushing usage, then head to your boards.
        You can change your handle anytime.
      </p>
      <button @click="continueIn">Go to boards →</button>
    </div>
    <InstallSkill :token="newToken" />
  </template>

  <template v-else-if="!alreadyIn">
    <div class="card">
      <h2>Get on the board</h2>
      <p class="muted" style="margin-top:0">
        No signup form — we'll assign you a handle (changeable later) and set you up instantly.
      </p>
      <div class="row">
        <button :disabled="busy" @click="getStarted">{{ busy ? "…" : "Get started" }}</button>
      </div>
    </div>

    <div class="card">
      <h2>Already have a token?</h2>
      <div class="row">
        <input v-model="existingToken" placeholder="cclb_live_…" style="flex:1" />
        <button class="ghost" :disabled="!existingToken" @click="useExistingToken">Sign in</button>
      </div>
    </div>
  </template>

  <template v-else>
    <InstallSkill :token="getToken()" />
  </template>
</template>

<style scoped>
.banner {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  background: linear-gradient(90deg, rgba(217,119,87,0.14), rgba(217,119,87,0.03));
  border: 1px solid var(--border); border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
}
.banner .muted { display: block; font-size: 13px; margin-top: 2px; }
.ostabs { display: flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.ostabs button { background: var(--panel-2); color: var(--muted); border: none; border-radius: 0; padding: 5px 10px; font-size: 12.5px; }
.ostabs button.active { background: var(--accent); color: #1a1205; font-weight: 600; }
</style>
