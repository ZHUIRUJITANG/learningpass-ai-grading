<template>
  <div class="assignment-submit-page">
    <div class="page-header">
      <h1 class="page-title">提交作业</h1>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="form-card">
          <template #header>
            <span>提交信息</span>
          </template>

          <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
            <el-form-item label="学号" prop="student_id">
              <el-input
                v-model="form.student_id"
                placeholder="请输入学号"
                clearable
              />
            </el-form-item>

            <el-form-item label="姓名" prop="student_name">
              <el-input
                v-model="form.student_name"
                placeholder="请输入姓名"
                clearable
              />
            </el-form-item>

            <el-form-item label="作业" prop="assignment_id">
              <el-select
                v-model="form.assignment_id"
                class="full-width"
                placeholder="请选择作业"
                :loading="assignmentsLoading"
                filterable
                clearable
              >
                <el-option
                  v-for="assignment in assignments"
                  :key="assignment.id"
                  :label="assignment.name"
                  :value="assignment.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="文件" required>
              <el-upload
                ref="uploadRef"
                class="full-width"
                drag
                action="#"
                :auto-upload="false"
                :limit="1"
                :file-list="fileList"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                :on-exceed="handleFileExceed"
              >
                <el-icon class="upload-icon">
                  <UploadFilled />
                </el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="upload-tip">
                    手动上传模式，点击“提交作业”后才会真正提交
                  </div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="submitting"
                :disabled="assignments.length === 0"
                @click="handleSubmit"
              >
                提交作业
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="table-card">
          <template #header>
            <div class="card-header">
              <span>提交记录</span>
              <el-button
                text
                type="primary"
                :disabled="form.assignment_id === null"
                @click="loadSubmissions"
              >
                刷新
              </el-button>
            </div>
          </template>

          <el-table
            v-loading="submissionsLoading"
            :data="submissions"
            stripe
            style="width: 100%"
            empty-text="当前作业暂无提交记录"
          >
            <el-table-column prop="student_id" label="学号" min-width="120" />
            <el-table-column prop="student_name" label="姓名" min-width="120" />
            <el-table-column
              prop="file_name"
              label="文件名"
              min-width="220"
              show-overflow-tooltip
            />
            <el-table-column label="提交时间" min-width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.submit_time) }}
              </template>
            </el-table-column>
            <el-table-column label="解析状态" min-width="180">
              <template #default="{ row }">
                <div class="status-cell">
                  <el-tag
                    :type="getParseStatusMeta(row.parse_status).type"
                    effect="light"
                  >
                    {{ getParseStatusMeta(row.parse_status).label }}
                  </el-tag>

                  <el-popover
                    v-if="
                      row.parse_status === 'completed' &&
                      (row.extracted_content || '').trim()
                    "
                    placement="top-start"
                    :width="360"
                    trigger="hover"
                  >
                    <template #reference>
                      <el-button link type="primary">查看内容</el-button>
                    </template>
                    <div class="preview-title">提取文本摘要</div>
                    <div class="preview-text">
                      {{ getExtractedPreview(row.extracted_content) }}
                    </div>
                  </el-popover>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="AI评分" min-width="100">
              <template #default="{ row }">
                {{ formatScore(row.ai_score) }}
              </template>
            </el-table-column>
            <el-table-column label="AI 反馈" min-width="120">
              <template #default="{ row }">
                <el-button
                  text
                  type="primary"
                  :disabled="!hasAiFeedback(row)"
                  @click="openAiFeedbackDialog(row)"
                >
                  {{ hasAiFeedback(row) ? "查看评语" : "暂无评语" }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column label="最终评分" min-width="100">
              <template #default="{ row }">
                {{ formatScore(row.final_score) }}
              </template>
            </el-table-column>
            <el-table-column label="审核状态" min-width="110">
              <template #default="{ row }">
                {{ row.review_status || "-" }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="feedbackDialogVisible"
      title="AI 反馈"
      width="520px"
      destroy-on-close
    >
      <div v-if="feedbackTarget" class="feedback-dialog">
        <div class="feedback-item">
          <div class="feedback-label">AI 评分</div>
          <div class="feedback-value">
            {{ formatScore(feedbackTarget.ai_score) }}
          </div>
        </div>
        <div class="feedback-item">
          <div class="feedback-label">评语</div>
          <div class="feedback-value feedback-text">
            {{ feedbackTarget.ai_comment || "暂无评语" }}
          </div>
        </div>
        <div v-if="feedbackTarget.ai_score_reason" class="feedback-item">
          <div class="feedback-label">扣分原因</div>
          <div class="feedback-value feedback-text">
            {{ feedbackTarget.ai_score_reason }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import type {
  FormInstance,
  FormRules,
  TagProps,
  UploadFile,
  UploadFiles,
  UploadInstance,
  UploadProps,
  UploadRawFile,
  UploadUserFile,
} from "element-plus";
import type { Assignment } from "@/types";
import { getAssignments } from "@/api/assignments";
import {
  createSubmission,
  getSubmissions,
  type Submission,
} from "@/api/submissions";

interface SubmissionFormData {
  student_id: string;
  student_name: string;
  assignment_id: number | null;
}

interface ParseStatusMeta {
  label: string;
  type: TagProps["type"];
}

const formRef = ref<FormInstance>();
const uploadRef = ref<UploadInstance>();

const assignmentsLoading = ref(false);
const submissionsLoading = ref(false);
const submitting = ref(false);

const assignments = ref<Assignment[]>([]);
const submissions = ref<Submission[]>([]);
const fileList = ref<UploadUserFile[]>([]);
const selectedFile = ref<File | null>(null);
const feedbackDialogVisible = ref(false);
const feedbackTarget = ref<Submission | null>(null);

const form = reactive<SubmissionFormData>({
  student_id: "",
  student_name: "",
  assignment_id: null,
});

const rules: FormRules<SubmissionFormData> = {
  student_id: [
    {
      required: true,
      message: "请输入学号",
      trigger: "blur",
    },
  ],
  student_name: [
    {
      required: true,
      message: "请输入姓名",
      trigger: "blur",
    },
  ],
  assignment_id: [
    {
      required: true,
      message: "请选择作业",
      trigger: "change",
    },
  ],
};

function formatDateTime(value?: string): string {
  if (!value) {
    return "-";
  }

  return value.replace("T", " ").slice(0, 19);
}

function formatScore(score: number | null): string {
  return score === null ? "-" : String(score);
}

function hasAiFeedback(submission: Submission): boolean {
  return submission.parse_status === "completed" && submission.ai_score != null;
}

function openAiFeedbackDialog(submission: Submission) {
  if (!hasAiFeedback(submission)) {
    return;
  }

  feedbackTarget.value = submission;
  feedbackDialogVisible.value = true;
}

function getParseStatusMeta(status?: string | null): ParseStatusMeta {
  switch (status) {
    case "completed":
      return { label: "已完成", type: "success" };
    case "processing":
      return { label: "解析中", type: "warning" };
    case "failed":
      return { label: "失败", type: "danger" };
    case "pending":
      return { label: "待处理", type: "info" };
    default:
      return { label: "未知", type: "info" };
  }
}

function getExtractedPreview(content?: string | null): string {
  const normalized = (content || "").trim().replace(/\s+/g, " ");
  if (!normalized) {
    return "暂无提取内容";
  }

  return normalized.length > 180
    ? `${normalized.slice(0, 180)}...`
    : normalized;
}

const handleFileChange: UploadProps["onChange"] = (
  uploadFile: UploadFile,
  uploadFiles: UploadFiles
) => {
  if (!uploadFile.raw) {
    return;
  }

  selectedFile.value = uploadFile.raw;
  fileList.value = uploadFiles.slice(-1).map((item) => ({
    name: item.name,
    size: item.size,
    status: item.status,
    uid: item.uid,
    raw: item.raw,
    url: item.url,
  }));
};

const handleFileRemove: UploadProps["onRemove"] = () => {
  selectedFile.value = null;
  fileList.value = [];
};

const handleFileExceed: UploadProps["onExceed"] = (files) => {
  const latestFile = files[0] as UploadRawFile | undefined;
  if (!latestFile) {
    return;
  }

  uploadRef.value?.clearFiles();
  selectedFile.value = latestFile;
  fileList.value = [
    {
      name: latestFile.name,
      size: latestFile.size,
      status: "ready",
      uid: latestFile.uid,
      raw: latestFile,
    },
  ];
};

async function loadAssignments() {
  assignmentsLoading.value = true;
  try {
    assignments.value = await getAssignments();
    if (form.assignment_id === null && assignments.value.length > 0) {
      form.assignment_id = assignments.value[0].id;
    }
  } finally {
    assignmentsLoading.value = false;
  }
}

async function loadSubmissions() {
  if (form.assignment_id === null) {
    submissions.value = [];
    return;
  }

  submissionsLoading.value = true;
  try {
    submissions.value = await getSubmissions(form.assignment_id);
  } finally {
    submissionsLoading.value = false;
  }
}

async function handleSubmit() {
  if (!formRef.value || form.assignment_id === null) {
    return;
  }

  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  if (!selectedFile.value) {
    ElMessage.warning("请先选择要上传的文件");
    return;
  }

  const data = new FormData();
  data.append("student_id", form.student_id.trim());
  data.append("student_name", form.student_name.trim());
  data.append("assignment_id", String(form.assignment_id));
  data.append("file", selectedFile.value);

  submitting.value = true;
  try {
    await createSubmission(data);
    ElMessage.success("作业提交成功");
    uploadRef.value?.clearFiles();
    selectedFile.value = null;
    fileList.value = [];
    await loadSubmissions();
  } finally {
    submitting.value = false;
  }
}

watch(
  () => form.assignment_id,
  async () => {
    await loadSubmissions();
  }
);

onMounted(async () => {
  await loadAssignments();
});
</script>

<style scoped>
.assignment-submit-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.form-card,
.table-card {
  height: 100%;
}

.full-width {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.upload-icon {
  margin-bottom: 8px;
  font-size: 32px;
}

.upload-tip {
  color: #6b7280;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-title {
  margin-bottom: 8px;
  font-weight: 600;
  color: #111827;
}

.preview-text {
  max-height: 180px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: #4b5563;
  line-height: 1.6;
}

.feedback-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.feedback-label {
  font-weight: 600;
  color: #111827;
}

.feedback-value {
  color: #374151;
}

.feedback-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

@media (max-width: 992px) {
  .table-card {
    margin-top: 20px;
  }
}

@media (max-width: 768px) {
  .assignment-submit-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }
}
</style>
