<template>
  <div class="assignment-page">
    <div class="page-header">
      <h1 class="page-title">&#20316;&#19994;&#31649;&#29702;</h1>
      <div class="page-actions">
        <el-select
          v-model="selectedCourseId"
          class="course-filter"
          :placeholder="'\u5168\u90e8\u8bfe\u7a0b'"
          @change="handleFilterChange"
        >
          <el-option :label="'\u5168\u90e8\u8bfe\u7a0b'" value="all" />
          <el-option
            v-for="course in courses"
            :key="course.id"
            :label="course.name"
            :value="course.id"
          />
        </el-select>
        <el-button type="primary" @click="openCreateDialog">
          &#26032;&#22686;&#20316;&#19994;
        </el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="assignments" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="name" :label="'\u4f5c\u4e1a\u540d\u79f0'" min-width="220" />
        <el-table-column :label="'\u6240\u5c5e\u8bfe\u7a0b'" min-width="180">
          <template #default="{ row }">
            {{ getCourseName(row.course_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_points" :label="'\u603b\u5206'" width="120" />
        <el-table-column :label="'\u622a\u6b62\u65e5\u671f'" min-width="180">
          <template #default="{ row }">
            {{ formatDueDate(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="'\u64cd\u4f5c'" width="180" fixed="right">
          <template #default="{ row }">
            <el-space>
              <el-button type="primary" link @click="openEditDialog(row)">
                &#32534;&#36753;
              </el-button>
              <el-button type="danger" link @click="handleDelete(row)">
                &#21024;&#38500;
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '\u7f16\u8f91\u4f5c\u4e1a' : '\u65b0\u589e\u4f5c\u4e1a'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-form-item :label="'\u8bfe\u7a0b'" prop="course_id">
          <el-select
            v-model="form.course_id"
            class="form-select"
            :placeholder="'\u8bf7\u9009\u62e9\u8bfe\u7a0b'"
          >
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="'\u4f5c\u4e1a\u540d\u79f0'" prop="name">
          <el-input
            v-model="form.name"
            :placeholder="'\u8bf7\u8f93\u5165\u4f5c\u4e1a\u540d\u79f0'"
          />
        </el-form-item>
        <el-form-item :label="'\u63cf\u8ff0'" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            :placeholder="'\u8bf7\u8f93\u5165\u4f5c\u4e1a\u63cf\u8ff0'"
          />
        </el-form-item>
        <el-form-item :label="'\u8bc4\u5206\u6807\u51c6'" prop="grading_rubric">
          <el-input
            v-model="form.grading_rubric"
            type="textarea"
            :rows="4"
            placeholder='例如：{"正确性": 40, "完整性": 30} 或直接写打分细则'
          />
        </el-form-item>
        <el-form-item :label="'\u603b\u5206'" prop="total_points">
          <el-input-number
            v-model="form.total_points"
            :min="0"
            :precision="1"
            :step="10"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item :label="'\u622a\u6b62\u65e5\u671f'" prop="due_date">
          <el-date-picker
            v-model="form.due_date"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            format="YYYY-MM-DD HH:mm"
            :placeholder="'\u8bf7\u9009\u62e9\u622a\u6b62\u65e5\u671f'"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">&#21462;&#28040;</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          &#20445;&#23384;
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import type { Assignment, Course } from "@/types";
import {
  createAssignment,
  deleteAssignment,
  getAssignments,
  updateAssignment,
} from "@/api/assignments";
import { getCourses } from "@/api/courses";

interface AssignmentFormData {
  course_id: number | null;
  name: string;
  description: string;
  grading_rubric: string;
  total_points: number;
  due_date: string;
}

const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const isEditMode = ref(false);
const editingAssignmentId = ref<number | null>(null);
const selectedCourseId = ref<number | "all">("all");
const assignments = ref<Assignment[]>([]);
const courses = ref<Course[]>([]);
const formRef = ref<FormInstance>();

const form = reactive<AssignmentFormData>({
  course_id: null,
  name: "",
  description: "",
  grading_rubric: "",
  total_points: 100,
  due_date: "",
});

const courseMap = computed(() => {
  return new Map(courses.value.map((course) => [course.id, course.name]));
});

const rules: FormRules<AssignmentFormData> = {
  course_id: [
    {
      required: true,
      message: "\u8bf7\u9009\u62e9\u8bfe\u7a0b",
      trigger: "change",
    },
  ],
  name: [
    {
      required: true,
      message: "\u8bf7\u8f93\u5165\u4f5c\u4e1a\u540d\u79f0",
      trigger: "blur",
    },
  ],
  total_points: [
    {
      required: true,
      message: "\u8bf7\u8f93\u5165\u603b\u5206",
      trigger: "change",
    },
  ],
};

function getCourseName(courseId: number): string {
  return courseMap.value.get(courseId) ?? `#${courseId}`;
}

function formatDueDate(value?: string): string {
  if (!value) {
    return "-";
  }

  return value.replace("T", " ");
}

function formatGradingRubricValue(
  gradingRubric: Assignment["grading_rubric"]
): string {
  if (gradingRubric === null || gradingRubric === undefined) {
    return "";
  }

  if (typeof gradingRubric === "string") {
    return gradingRubric;
  }

  try {
    return JSON.stringify(gradingRubric, null, 2);
  } catch {
    return String(gradingRubric);
  }
}

function buildGradingRubricPayload(
  gradingRubricText: string
): Record<string, unknown> | undefined {
  const trimmed = gradingRubricText.trim();
  if (!trimmed) {
    return undefined;
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    // Fallback to plain text wrapper below.
  }

  return { text: trimmed };
}

function resetForm() {
  editingAssignmentId.value = null;
  isEditMode.value = false;
  form.course_id = null;
  form.name = "";
  form.description = "";
  form.grading_rubric = "";
  form.total_points = 100;
  form.due_date = "";
  formRef.value?.clearValidate();
}

async function loadCourses() {
  courses.value = await getCourses();
}

async function loadAssignments() {
  loading.value = true;
  try {
    assignments.value = await getAssignments(
      selectedCourseId.value === "all" ? undefined : selectedCourseId.value
    );
  } finally {
    loading.value = false;
  }
}

async function refreshList() {
  await loadAssignments();
}

function openCreateDialog() {
  resetForm();
  dialogVisible.value = true;
  nextTick(() => {
    formRef.value?.clearValidate();
  });
}

function openEditDialog(assignment: Assignment) {
  resetForm();
  isEditMode.value = true;
  editingAssignmentId.value = assignment.id;
  form.course_id = assignment.course_id;
  form.name = assignment.name;
  form.description = assignment.description ?? "";
  form.grading_rubric = formatGradingRubricValue(assignment.grading_rubric);
  form.total_points = assignment.total_points;
  form.due_date = assignment.due_date ?? "";
  dialogVisible.value = true;
  nextTick(() => {
    formRef.value?.clearValidate();
  });
}

async function handleSubmit() {
  if (!formRef.value || form.course_id === null) {
    return;
  }

  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  const payload = {
    course_id: form.course_id,
    name: form.name,
    description: form.description || undefined,
    grading_rubric: buildGradingRubricPayload(form.grading_rubric),
    due_date: form.due_date || undefined,
    total_points: form.total_points,
  };

  submitting.value = true;
  try {
    if (isEditMode.value && editingAssignmentId.value !== null) {
      await updateAssignment(editingAssignmentId.value, payload);
      ElMessage.success("\u4f5c\u4e1a\u66f4\u65b0\u6210\u529f");
    } else {
      await createAssignment(payload);
      ElMessage.success("\u4f5c\u4e1a\u521b\u5efa\u6210\u529f");
    }

    dialogVisible.value = false;
    await refreshList();
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(assignment: Assignment) {
  try {
    await ElMessageBox.confirm(
      `\u786e\u5b9a\u5220\u9664\u4f5c\u4e1a\u201c${assignment.name}\u201d\u5417\uff1f`,
      "\u5220\u9664\u786e\u8ba4",
      {
        type: "warning",
        confirmButtonText: "\u786e\u5b9a",
        cancelButtonText: "\u53d6\u6d88",
      }
    );
  } catch {
    return;
  }

  await deleteAssignment(assignment.id);
  ElMessage.success("\u4f5c\u4e1a\u5220\u9664\u6210\u529f");
  await refreshList();
}

async function handleFilterChange() {
  await loadAssignments();
}

onMounted(async () => {
  await loadCourses();
  await loadAssignments();
});
</script>

<style scoped>
.assignment-page {
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.course-filter {
  width: 240px;
}

.form-select {
  width: 100%;
}

@media (max-width: 768px) {
  .assignment-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .course-filter {
    width: 100%;
  }
}
</style>
