<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api, getToken, type Membership } from "../api";
import InstallSkill from "../components/InstallSkill.vue";

const router = useRouter();
const storedToken = getToken();
const memberships = ref<Membership[]>([]);
const handle = ref("");
const err = ref("");
const editingName = ref(false);
const editHandle = ref("");
const savingName = ref(false);
const newBoardName = ref("");
const joinId = ref("");
const joinCode = ref("");

async function load() {
  err.value = "";
  try {
    const me = await api.me();
    handle.value = me.handle;
    memberships.value = me.memberships;
  } catch (e: any) {
    err.value = e.message;
    if (e.message.includes("401") || e.message.toLowerCase().includes("token")) {
      router.push("/");
    }
  }
}

function startEditName() {
  editHandle.value = handle.value;
  editingName.value = true;
}

async function saveName() {
  err.value = "";
  savingName.value = true;
  try {
    await api.updateMe({ handle: editHandle.value.trim() });
    editingName.value = false;
    await load();
  } catch (e: any) {
    err.value = e.message;
  } finally {
    savingName.value = false;
  }
}

async function create() {
  err.value = "";
  try {
    const b = await api.createBoard(newBoardName.value.trim());
    newBoardName.value = "";
    router.push(`/boards/${b.id}`);
  } catch (e: any) {
    err.value = e.message;
  }
}

async function join() {
  err.value = "";
  try {
    const b = await api.joinBoard(joinId.value.trim(), joinCode.value.trim());
    router.push(`/boards/${b.id}`);
  } catch (e: any) {
    err.value = e.message;
  }
}

onMounted(load);
</script>

<template>
  <div class="card">
    <h1>Your boards</h1>
    <div v-if="!editingName" class="row" style="gap:8px">
      <p class="muted" style="margin:0">Signed in as @{{ handle }}</p>
      <button class="ghost" style="padding:2px 8px;font-size:12px" @click="startEditName">Change handle</button>
    </div>
    <div v-else style="margin:8px 0">
      <div class="row">
        <input v-model="editHandle" placeholder="handle" />
        <button :disabled="savingName || !editHandle.trim()" @click="saveName">Save</button>
        <button class="ghost" @click="editingName = false">Cancel</button>
      </div>
      <p class="muted" style="font-size:12px;margin:6px 0 0">
        Your handle is your public @name on every board.
      </p>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <div v-if="memberships.length === 0" class="muted">
      You're not on any boards yet. Create one or join with an invite code.
    </div>
    <div v-for="m in memberships" :key="m.board_id" class="entry">
      <div class="who-col">
        <div class="name">{{ m.name }}</div>
        <div class="handle">{{ m.role }} · {{ m.slug }}</div>
      </div>
      <router-link :to="`/boards/${m.board_id}`"><button class="ghost">View →</button></router-link>
    </div>
  </div>

  <div class="card">
    <h2>Create a board</h2>
    <div class="row">
      <input v-model="newBoardName" placeholder="board name" style="flex:1" />
      <button :disabled="!newBoardName" @click="create">Create</button>
    </div>
  </div>

  <div class="card">
    <h2>Join a board</h2>
    <div class="row">
      <input v-model="joinId" placeholder="board id or slug" />
      <input v-model="joinCode" placeholder="invite code" />
      <button class="ghost" :disabled="!joinId || !joinCode" @click="join">Join</button>
    </div>
  </div>

  <InstallSkill :token="storedToken" />
</template>
