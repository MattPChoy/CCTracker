<script setup lang="ts">
import { computed, ref } from "vue";

// When signed in we can prefill the real token; otherwise a placeholder.
const props = defineProps<{ token?: string | null }>();

const apiBase = window.location.origin;
const tokenText = computed(() => props.token || "<your token>");

type OS = "nix" | "win";
const os = ref<OS>(/Windows/i.test(navigator.userAgent) ? "win" : "nix");

const nixCmd = computed(
  () => `curl -fsSL ${apiBase}/install.sh | CCLB_API_BASE=${apiBase} CCLB_TOKEN=${tokenText.value} bash`,
);
const winCmd = computed(
  () => `$env:CCLB_API_BASE='${apiBase}'; $env:CCLB_TOKEN='${tokenText.value}'; irm ${apiBase}/install.ps1 | iex`,
);
const command = computed(() => (os.value === "win" ? winCmd.value : nixCmd.value));

const copied = ref("");
async function copy(what: string, text: string) {
  try {
    await navigator.clipboard.writeText(text);
    copied.value = what;
    setTimeout(() => (copied.value = ""), 1500);
  } catch {
    copied.value = "";
  }
}
</script>

<template>
  <div class="card">
    <div class="row" style="justify-content:space-between;align-items:flex-start">
      <div>
        <h2 style="margin:0">Install the skill</h2>
        <p class="muted" style="margin:4px 0 0">
          Run this in your terminal. It's a normal installer — open
          <a :href="`${apiBase}/install.sh`" target="_blank">{{ os === "win" ? "install.ps1" : "install.sh" }}</a>
          first if you'd like to read exactly what it does.
        </p>
      </div>
      <div class="ostabs">
        <button :class="{ active: os === 'nix' }" @click="os = 'nix'">macOS · Linux</button>
        <button :class="{ active: os === 'win' }" @click="os = 'win'">Windows</button>
      </div>
    </div>

    <div class="cmd">
      <pre>{{ command }}</pre>
      <button class="ghost" @click="copy('cmd', command)">{{ copied === "cmd" ? "Copied ✓" : "Copy" }}</button>
    </div>
    <p class="muted" style="font-size:12.5px;margin:8px 0 0">
      It writes just two things — your config at <code>~/.cc-leaderboard/config.json</code> and the
      skill at <code>~/.claude/skills/update-leaderboard/</code> — then pushes your usage once.
      The token is your own key for this leaderboard.
    </p>

    <details v-if="token" style="margin-top:8px">
      <summary>Reveal raw token</summary>
      <p class="muted" style="font-size:13px">
        For manual setup. Treat it like a password — it's your only credential.
      </p>
      <div class="token-box">{{ token }}</div>
    </details>

    <p class="muted" style="font-size:12.5px;margin:10px 0 0">
      Full install guide:
      <a :href="`${apiBase}/install`" target="_blank">{{ apiBase }}/install</a>.
    </p>

    <p v-if="!token" class="muted" style="font-size:13px;margin-top:8px">
      Click <strong>Get started</strong> above to fill this in with your token.
    </p>
  </div>
</template>

<style scoped>
.ostabs { display: flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.ostabs button { background: var(--panel-2); color: var(--muted); border: none; border-radius: 0; padding: 6px 12px; font-size: 13px; }
.ostabs button.active { background: var(--accent); color: #1a1205; font-weight: 600; }
.cmd { position: relative; margin-top: 10px; }
.cmd pre {
  background: #000; color: #cfd3dc; border-radius: 8px; padding: 14px 70px 14px 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px;
  line-height: 1.5; white-space: pre-wrap; word-break: break-word; overflow-x: auto; margin: 0;
}
.cmd button { position: absolute; top: 8px; right: 8px; padding: 5px 10px; font-size: 12px; }
details summary { cursor: pointer; color: var(--accent); font-size: 14px; }
</style>
