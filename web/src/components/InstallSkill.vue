<script setup lang="ts">
import { computed, ref } from "vue";

// When signed in we can prefill the real token; otherwise a placeholder.
const props = defineProps<{ token?: string | null }>();

const apiBase = window.location.origin;
const tokenText = computed(() => props.token || "<my token>");

const prompt = computed(
  () => `Install the CCTracker usage-push skill from https://github.com/MattPChoy/CCTracker.

1. Download these two files:
   - https://raw.githubusercontent.com/MattPChoy/CCTracker/main/skill/SKILL.md
   - https://raw.githubusercontent.com/MattPChoy/CCTracker/main/skill/push.sh
2. Save them to ~/.claude/skills/cc-leaderboard-push/ (create the dir) and chmod +x the push.sh.
3. Create ~/.cc-leaderboard/config.json (chmod 600) with:
   { "api_base": "${apiBase}", "token": "${tokenText.value}" }
4. Confirm ccusage, jq, and curl are available, then run push.sh once to push my usage.`,
);

const copied = ref(false);
async function copy() {
  try {
    await navigator.clipboard.writeText(prompt.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch {
    copied.value = false;
  }
}
</script>

<template>
  <div class="card">
    <div class="row" style="justify-content:space-between">
      <h2 style="margin:0">Install the push skill</h2>
      <button class="ghost" @click="copy">{{ copied ? "Copied ✓" : "Copy prompt" }}</button>
    </div>
    <p class="muted">
      Paste this into <strong>Claude Code</strong> and it will download and install the
      skill from GitHub, then push your usage.
    </p>
    <pre class="prompt">{{ prompt }}</pre>
    <p v-if="!token" class="muted" style="font-size:13px">
      Register above to get your token — it drops straight into this prompt.
    </p>
  </div>
</template>

<style scoped>
.prompt {
  background: #000;
  color: #cfd3dc;
  border-radius: 8px;
  padding: 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  margin: 8px 0 4px;
}
</style>
