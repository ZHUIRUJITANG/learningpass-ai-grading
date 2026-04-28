<template>
  <el-form ref="innerFormRef" :model="model" :rules="rules" label-width="88px">
    <el-form-item label="课程" prop="course_id">
      <el-select
        v-model="model.course_id"
        class="form-select"
        placeholder="请选择课程"
      >
        <el-option
          v-for="course in courses"
          :key="course.id"
          :label="course.name"
          :value="course.id"
        />
      </el-select>
    </el-form-item>
    <el-form-item label="作业名称" prop="name">
      <el-input v-model="model.name" placeholder="请输入作业名称" />
    </el-form-item>
    <el-form-item label="描述" prop="description">
      <el-input
        v-model="model.description"
        type="textarea"
        :rows="4"
        placeholder="请输入作业描述"
      />
    </el-form-item>
    <el-form-item label="评分标准" prop="grading_rubric">
      <el-input
        v-model="model.grading_rubric"
        type="textarea"
        :rows="4"
        placeholder='例如：{"正确性": 40, "完整性": 30} 或直接写打分细则'
      />
    </el-form-item>
    <el-form-item label="总分" prop="total_points">
      <el-input-number
        v-model="model.total_points"
        :min="0"
        :precision="1"
        :step="10"
        controls-position="right"
      />
    </el-form-item>
    <el-form-item label="截止日期" prop="due_date">
      <el-date-picker
        v-model="model.due_date"
        type="datetime"
        value-format="YYYY-MM-DDTHH:mm:ss"
        format="YYYY-MM-DD HH:mm"
        placeholder="请选择截止日期"
        style="width: 100%"
      />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import type { Course } from "@/types";

export interface AssignmentFormModel {
  course_id: number | null;
  name: string;
  description: string;
  grading_rubric: string;
  total_points: number;
  due_date: string;
}

const props = defineProps<{
  model: AssignmentFormModel;
  courses: Course[];
  rules?: FormRules<AssignmentFormModel>;
}>();

const innerFormRef = ref<FormInstance>();

function validate() {
  return innerFormRef.value?.validate();
}

function clearValidate() {
  innerFormRef.value?.clearValidate();
}

defineExpose({
  validate,
  clearValidate,
});
</script>

<style scoped>
.form-select {
  width: 100%;
}
</style>
