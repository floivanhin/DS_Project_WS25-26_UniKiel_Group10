<template>
  <header class="bg-slate-900 text-white shadow-md">
    <nav class="mx-auto flex max-w-7xl flex-wrap gap-3 px-6 py-4">
      <RouterLink
        v-for="item in links"
        :key="item.path"
        :to="item.path"
        class="rounded-lg px-4 py-2 transition hover:bg-slate-700"
        active-class="bg-slate-700"
      >
        {{ item.label }}
      </RouterLink>
    </nav>
  </header>
</template>

<script setup lang="ts">
const links = [
  { label: "Main", path: "/" },
  { label: "RQ1", path: "/rq1" },
  { label: "RQ2", path: "/rq2" },
  { label: "RQ3", path: "/rq3" },
  { label: "RQ4", path: "/rq4" },
  { label: "RQ5", path: "/rq5" },
  { label: "RQ6", path: "/rq6" },
  { label: "RQ7", path: "/rq7" },
  { label: "RQ8", path: "/rq8" },
];
</script>
