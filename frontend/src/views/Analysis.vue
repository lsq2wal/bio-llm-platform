<template>
  <div class="analysis-page">
    <AnalysisTask />
  </div>
</template>

<script>
import AnalysisTask from '@/components/AnalysisTask.vue'

export default {
  name: 'Analysis',
  components: {
    AnalysisTask
  }
}
</script>

<style scoped>
.analysis-page {
  padding: 20px;
}
</style> 