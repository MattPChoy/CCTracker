<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { getToken, setToken } from "./api";

const router = useRouter();
const loggedIn = ref(!!getToken());

// Re-check on navigation so the nav reflects login/logout.
router.afterEach(() => {
  loggedIn.value = !!getToken();
});

function logout() {
  setToken(null);
  loggedIn.value = false;
  router.push("/");
}
</script>

<template>
  <nav class="top">
    <router-link class="brand" to="/">CC<span>Tracker</span></router-link>
    <router-link v-if="loggedIn" to="/boards" class="muted">Boards</router-link>
    <div class="spacer"></div>
    <button v-if="loggedIn" class="ghost" @click="logout">Sign out</button>
  </nav>
  <div class="wrap">
    <router-view />
  </div>
</template>
