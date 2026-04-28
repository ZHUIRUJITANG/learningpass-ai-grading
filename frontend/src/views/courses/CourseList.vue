<template>
  <div class="course-page">
    <div class="page-header">
      <h1 class="page-title">&#35838;&#31243;&#31649;&#29702;</h1>
      <el-button type="primary" @click="openCreateDialog">
        &#26032;&#22686;&#35838;&#31243;
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="courses" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column
          prop="name"
          :label="'\u540d\u79f0'"
          min-width="220"
        />
        <el-table-column
          prop="code"
          :label="'\u4ee3\u7801'"
          min-width="180"
        />
        <el-table-column
          :label="'\u64cd\u4f5c'"
          width="180"
          fixed="right"
        >
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
      :title="
        isEditMode ? '\u7f16\u8f91\u8bfe\u7a0b' : '\u65b0\u589e\u8bfe\u7a0b'
      "
      width="480px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item :label="'\u540d\u79f0'" prop="name">
          <el-input
            v-model="form.name"
            :placeholder="'\u8bf7\u8f93\u5165\u8bfe\u7a0b\u540d\u79f0'"
          />
        </el-form-item>
        <el-form-item :label="'\u4ee3\u7801'" prop="code">
          <el-input
            v-model="form.code"
            :placeholder="'\u8bf7\u8f93\u5165\u8bfe\u7a0b\u4ee3\u7801'"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">
          &#21462;&#28040;
        </el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          &#20445;&#23384;
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import type { Course } from "@/types";
import {
  createCourse,
  deleteCourse,
  getCourses,
  updateCourse,
} from "@/api/courses";

interface CourseFormData {
  name: string;
  code: string;
}

const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const isEditMode = ref(false);
const editingCourseId = ref<number | null>(null);
const courses = ref<Course[]>([]);
const formRef = ref<FormInstance>();

const form = reactive<CourseFormData>({
  name: "",
  code: "",
});

const rules: FormRules<CourseFormData> = {
  name: [
    {
      required: true,
      message: "\u8bf7\u8f93\u5165\u8bfe\u7a0b\u540d\u79f0",
      trigger: "blur",
    },
  ],
  code: [
    {
      required: true,
      message: "\u8bf7\u8f93\u5165\u8bfe\u7a0b\u4ee3\u7801",
      trigger: "blur",
    },
  ],
};

async function loadCourses() {
  loading.value = true;
  try {
    courses.value = await getCourses();
  } finally {
    loading.value = false;
  }
}

function resetForm() {
  editingCourseId.value = null;
  isEditMode.value = false;
  form.name = "";
  form.code = "";
  formRef.value?.clearValidate();
}

function openCreateDialog() {
  resetForm();
  dialogVisible.value = true;
  nextTick(() => {
    formRef.value?.clearValidate();
  });
}

function openEditDialog(course: Course) {
  resetForm();
  isEditMode.value = true;
  editingCourseId.value = course.id;
  form.name = course.name;
  form.code = course.code;
  dialogVisible.value = true;
  nextTick(() => {
    formRef.value?.clearValidate();
  });
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    if (isEditMode.value && editingCourseId.value !== null) {
      await updateCourse(editingCourseId.value, {
        name: form.name,
        code: form.code,
      });
      ElMessage.success("\u8bfe\u7a0b\u66f4\u65b0\u6210\u529f");
    } else {
      await createCourse({
        name: form.name,
        code: form.code,
      });
      ElMessage.success("\u8bfe\u7a0b\u521b\u5efa\u6210\u529f");
    }

    dialogVisible.value = false;
    await loadCourses();
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(course: Course) {
  try {
    await ElMessageBox.confirm(
      `\u786e\u5b9a\u5220\u9664\u8bfe\u7a0b\u201c${course.name}\u201d\u5417\uff1f`,
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

  await deleteCourse(course.id);
  ElMessage.success("\u8bfe\u7a0b\u5220\u9664\u6210\u529f");
  await loadCourses();
}

onMounted(() => {
  loadCourses();
});
</script>

<style scoped>
.course-page {
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}
</style>
