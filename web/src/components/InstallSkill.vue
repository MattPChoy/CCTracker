<script setup lang="ts">
import { computed, ref } from "vue";

// When signed in we can prefill the real token; otherwise a placeholder.
const props = defineProps<{ token?: string | null }>();

const apiBase = window.location.origin;
const tokenText = computed(() => props.token || "<your token>");

const prompt = computed(
  () => `Download the CCTracker install guide from ${apiBase}/install and follow the
instructions to install the "update-leaderboard" Claude Code skill for my OS.

Use these values:
  api_base = ${apiBase}
  token = ${tokenText.value}

When it's done, run /update-leaderboard to confirm my usage pushed.`,
);

const copied = ref(false);
async function copyPrompt() {
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
    <h2 style="margin:0">Install the skill</h2>
    <p class="muted" style="margin:4px 0 12px">
      Paste this prompt into Claude Code. It reads the install guide and sets up the
      <code>/update-leaderboard</code> skill for your OS.
    </p>

    <div class="cmd">
      <pre>{{ prompt }}</pre>
      <button class="ghost" @click="copyPrompt">{{ copied ? "Copied ✓" : "Copy prompt" }}</button>
    </div>
    <p class="muted" style="font-size:12.5px;margin:6px 0 0">
      Full install guide:
      <a :href="`${apiBase}/install`" target="_blank">{{ apiBase }}/install</a>.
    </p>

    <details v-if="token" style="margin-top:12px">
      <summary>Reveal raw token</summary>
      <p class="muted" style="font-size:13px">
        For manual setup. Treat it like a password — it's your only credential.
      </p>
      <div class="token-box">{{ token }}</div>
    </details>

    <p v-if="!token" class="muted" style="font-size:13px;margin-top:12px">
      Click <strong>Get started</strong> above to fill this prompt in with your token.
    </p>
  </div>
</template>

<style scoped>
.cmd { position: relative; margin-top: 10px; }
.cmd pre {
  background: #000; color: #cfd3dc; border-radius: 8px; padding: 14px 130px 14px 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px;
  line-height: 1.5; white-space: pre-wrap; word-break: break-word; overflow-x: auto; margin: 0;
}
.cmd button { position: absolute; top: 8px; right: 8px; padding: 5px 10px; font-size: 12px; }
details summary { cursor: pointer; color: var(--accent); font-size: 14px; }
</style>
