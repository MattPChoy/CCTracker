<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api, getToken, setToken } from "../api";
import InstallSkill from "../components/InstallSkill.vue";

const router = useRouter();
const handle = ref("");
const displayName = ref("");
const existingToken = ref("");
const newToken = ref<string | null>(null);
const err = ref("");
const busy = ref(false);
const alreadyIn = ref(!!getToken());
const storedToken = getToken();

async function register() {
  err.value = "";
  busy.value = true;
  try {
    const res = await api.register(handle.value.trim(), displayName.value.trim() || undefined);
    newToken.value = res.token;
    setToken(res.token);
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
</script>

<template>
  <template v-if="alreadyIn">
    <div class="card">
      <h1>You're signed in</h1>
      <p class="muted">Head to your boards to see rankings.</p>
      <button @click="continueIn">Go to boards →</button>
    </div>
    <InstallSkill :token="storedToken" />
  </template>

  <template v-else>
    <div class="card">
      <h1>Claude Code Usage Leaderboard</h1>
      <p class="muted">
        Compare your Claude Code usage with friends and teammates. Register a handle,
        install the push skill, and your daily per-model usage appears on any board you join.
      </p>
    </div>

    <div class="card">
      <h2>Register</h2>
      <div class="row">
        <input v-model="handle" placeholder="handle (e.g. alex)" />
        <input v-model="displayName" placeholder="display name (optional)" />
        <button :disabled="busy || !handle" @click="register">Create account</button>
      </div>
      <p v-if="err" class="err">{{ err }}</p>

      <template v-if="newToken">
        <p style="margin-top:16px">
          <strong>Your secret token — copy it now, it's shown only once:</strong>
        </p>
        <div class="token-box">{{ newToken }}</div>
        <p class="muted" style="margin-top:8px">
          Put this in <code>~/.cc-leaderboard/config.json</code> for the push skill.
        </p>
        <button style="margin-top:8px" @click="continueIn">Continue →</button>
      </template>
    </div>

    <div class="card">
      <h2>Already have a token?</h2>
      <div class="row">
        <input v-model="existingToken" placeholder="cclb_live_…" style="flex:1" />
        <button class="ghost" :disabled="!existingToken" @click="useExistingToken">Sign in</button>
      </div>
    </div>

    <InstallSkill :token="newToken" />
  </template>
</template>
