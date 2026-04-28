<template>
  <el-tag :type="tagType" size="small">
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  confidence: number
}>()

const tagType = computed(() => {
  if (props.confidence >= 0.8) return 'success'
  if (props.confidence >= 0.5) return 'warning'
  return 'danger'
})

const label = computed(() => {
  if (props.confidence >= 0.8) return '高置信度'
  if (props.confidence >= 0.5) return '中置信度'
  return '低置信度'
})
</script>