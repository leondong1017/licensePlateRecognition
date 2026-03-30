<template>
  <div class="page-card">
    <HistoryTable />
  </div>
</template>

<script setup lang="ts">
import HistoryTable from '../components/HistoryTable.vue'
</script>

<style scoped>
.page-card { background: #fff; border-radius: 8px; border: 1px solid #e8e8e8; padding: 24px; }
</style>
