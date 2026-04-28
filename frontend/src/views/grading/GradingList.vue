<template>
  <div class="grading-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">作业批改</h1>
        <p class="page-subtitle">作业 ID：{{ assignmentId ?? "-" }}</p>
      </div>
      <div class="page-actions">
        <el-button type="success" @click="exportExcel">导出 Excel</el-button>
        <el-button type="primary" :loading="loading" @click="loadSubmissions">
          刷新列表
        </el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
        empty-text="暂无提交记录"
      >
        <el-table-column prop="student_id" label="学号" min-width="120" />
        <el-table-column prop="student_name" label="姓名" min-width="120" />
        <el-table-column label="文件名" min-width="220">
          <template #default="{ row }">
            <a
              v-if="row.file_url"
              :href="row.file_url"
              class="file-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ row.file_name }}
            </a>
            <span v-else>{{ row.file_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.submit_time) }}
          </template>
        </el-table-column>
        <el-table-column label="解析状态" min-width="120">
          <template #default="{ row }">
            <el-tag :type="getParseStatusMeta(row.parse_status).type" effect="light">
              {{ getParseStatusMeta(row.parse_status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="解析内容" min-width="260">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.extractedContentText"
              placement="top-start"
              effect="dark"
              :show-after="150"
            >
              <template #content>
                <div class="content-tooltip">
                  {{ row.extractedContentText }}
                </div>
              </template>
              <span class="content-preview">
                {{ truncateText(row.extractedContentText, 30) }}
              </span>
            </el-tooltip>
            <span v-else class="content-empty">-</span>
          </template>
        </el-table-column>
        <el-table-column label="AI建议分" min-width="100">
          <template #default="{ row }">
            {{ formatScore(row.ai_score) }}
          </template>
        </el-table-column>
        <el-table-column label="AI评语预览" min-width="200">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.aiCommentText"
              placement="top-start"
              effect="dark"
              :show-after="150"
            >
              <template #content>
                <div class="content-tooltip">
                  {{ row.aiCommentText }}
                </div>
              </template>
              <span class="content-preview">
                {{ truncateText(row.aiCommentText, 20) }}
              </span>
            </el-tooltip>
            <span v-else class="content-empty">-</span>
          </template>
        </el-table-column>
        <el-table-column label="最终评分" min-width="100">
          <template #default="{ row }">
            {{ formatScore(row.final_score) }}
          </template>
        </el-table-column>
        <el-table-column label="复核状态" min-width="120">
          <template #default="{ row }">
            {{ row.review_status || "-" }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openReviewDialog(row)">
              复核
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="reviewDialogVisible"
      title="教师复核"
      width="760px"
      destroy-on-close
    >
      <div v-if="selectedSubmission" class="review-dialog">
        <div class="review-section">
          <div class="review-grid">
            <div class="review-item">
              <span class="review-label">学号</span>
              <span>{{ selectedSubmission.student_id }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">姓名</span>
              <span>{{ selectedSubmission.student_name }}</span>
            </div>
            <div class="review-item review-item-wide">
              <span class="review-label">提交时间</span>
              <span>{{ formatDateTime(selectedSubmission.submit_time) }}</span>
            </div>
          </div>
        </div>

        <div class="review-section">
          <div class="review-label">文件下载</div>
          <a
            v-if="selectedSubmission.file_url"
            :href="selectedSubmission.file_url"
            class="file-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ selectedSubmission.file_name }}
          </a>
          <span v-else class="content-empty">暂无下载链接</span>
        </div>

        <div class="review-section">
          <div class="review-label">AI 建议分</div>
          <div class="review-text">{{ formatScore(selectedSubmission.ai_score) }}</div>
        </div>

        <div class="review-section">
          <div class="review-label">AI 评语</div>
          <div class="review-text">
            {{ selectedSubmission.ai_comment || "暂无 AI 评语" }}
          </div>
        </div>

        <div class="review-section">
          <div class="review-label">扣分原因</div>
          <div class="review-text">
            {{ selectedSubmission.ai_score_reason || "暂无扣分原因" }}
          </div>
        </div>

        <div class="review-section">
          <div class="review-label">提取文字内容</div>
          <el-input
            :model-value="selectedSubmission.extractedContentText"
            type="textarea"
            :rows="8"
            readonly
          />
        </div>

        <div class="review-section">
          <div class="review-label">教师评分</div>
          <el-input
            v-model.number="reviewForm.final_score"
            type="number"
            placeholder="请输入最终分数"
          />
        </div>

        <div class="review-section">
          <div class="review-label">教师评语</div>
          <el-input
            v-model="reviewForm.teacher_comment"
            type="textarea"
            :rows="4"
            placeholder="请输入教师评语"
          />
        </div>

        <div class="review-section">
          <div class="review-label">复核状态</div>
          <el-select v-model="reviewForm.review_status" class="status-select">
            <el-option label="pending" value="pending" />
            <el-option label="reviewed" value="reviewed" />
            <el-option label="confirmed" value="confirmed" />
          </el-select>
        </div>
      </div>

      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveReview">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import type { TagProps } from "element-plus";
import request from "@/api/request";
import {
  getSubmissions,
  updateSubmission,
  type Submission,
} from "@/api/submissions";

type ReviewStatus = "pending" | "reviewed" | "confirmed";

interface ParseStatusMeta {
  label: string;
  type: TagProps["type"];
}

interface SubmissionRow extends Submission {
  extractedContentText: string;
  aiCommentText: string;
}

interface ReviewFormState {
  final_score: number | null;
  teacher_comment: string;
  review_status: ReviewStatus;
}

const route = useRoute();
const loading = ref(false);
const saving = ref(false);
const submissions = ref<Submission[]>([]);
const reviewDialogVisible = ref(false);
const selectedSubmission = ref<SubmissionRow | null>(null);

const reviewForm = reactive<ReviewFormState>({
  final_score: null,
  teacher_comment: "",
  review_status: "pending",
});

const assignmentId = computed<number | null>(() => {
  const rawValue = Array.isArray(route.params.assignmentId)
    ? route.params.assignmentId[0]
    : route.params.assignmentId;
  const parsedValue = Number(rawValue);
  return Number.isInteger(parsedValue) && parsedValue > 0 ? parsedValue : null;
});

const tableData = computed<SubmissionRow[]>(() =>
  submissions.value.map((submission) => ({
    ...submission,
    extractedContentText: toPlainExtractedText(submission.extracted_content),
    aiCommentText: normalizeText(submission.ai_comment || ""),
  }))
);

function formatDateTime(value?: string): string {
  if (!value) {
    return "-";
  }

  return value.replace("T", " ").slice(0, 19);
}

function formatScore(score: number | null | undefined): string {
  return score == null ? "-" : String(score);
}

function truncateText(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

function normalizeText(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

function extractTextCandidate(value: unknown): string {
  if (typeof value === "string") {
    return normalizeText(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => extractTextCandidate(item))
      .filter(Boolean)
      .join(" ");
  }

  if (!value || typeof value !== "object") {
    return "";
  }

  const record = value as Record<string, unknown>;
  const prioritizedKeys = [
    "extracted_content",
    "extracted_text",
    "content",
    "text",
    "ocr_text",
  ];

  for (const key of prioritizedKeys) {
    const candidate = extractTextCandidate(record[key]);
    if (candidate) {
      return candidate;
    }
  }

  for (const [key, item] of Object.entries(record)) {
    if (!/(text|content)/i.test(key)) {
      continue;
    }

    const candidate = extractTextCandidate(item);
    if (candidate) {
      return candidate;
    }
  }

  return "";
}

function toPlainExtractedText(content?: string | null): string {
  const normalized = normalizeText(content || "");
  if (!normalized) {
    return "";
  }

  try {
    const parsed = JSON.parse(normalized);
    const extractedText = extractTextCandidate(parsed);
    return extractedText || normalized;
  } catch {
    return normalized;
  }
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

function openReviewDialog(submission: SubmissionRow) {
  selectedSubmission.value = submission;
  reviewForm.final_score = submission.final_score ?? null;
  reviewForm.teacher_comment = submission.teacher_comment || "";
  reviewForm.review_status = (
    submission.review_status || "pending"
  ) as ReviewStatus;
  reviewDialogVisible.value = true;
}

function exportExcel() {
  if (assignmentId.value === null) {
    ElMessage.warning("无效的作业 ID");
    return;
  }

  const baseURL = String(request.defaults.baseURL || window.location.origin);
  const exportUrl = new URL(
    `/api/v1/export/${assignmentId.value}`,
    baseURL.endsWith("/") ? baseURL : `${baseURL}/`
  ).toString();
  window.open(exportUrl, "_blank");
}

async function loadSubmissions() {
  if (assignmentId.value === null) {
    submissions.value = [];
    ElMessage.warning("无效的作业 ID");
    return;
  }

  loading.value = true;
  try {
    submissions.value = await getSubmissions(assignmentId.value);
  } catch (error) {
    console.error(error);
    ElMessage.error("加载批改列表失败");
  } finally {
    loading.value = false;
  }
}

async function saveReview() {
  if (!selectedSubmission.value) {
    return;
  }

  saving.value = true;
  try {
    await updateSubmission(selectedSubmission.value.id, {
      final_score: reviewForm.final_score,
      teacher_comment: reviewForm.teacher_comment || null,
      review_status: reviewForm.review_status,
    });
    ElMessage.success("复核结果已保存");
    reviewDialogVisible.value = false;
    await loadSubmissions();
  } catch (error) {
    console.error(error);
    ElMessage.error("保存复核结果失败");
  } finally {
    saving.value = false;
  }
}

watch(
  assignmentId,
  async () => {
    await loadSubmissions();
  }
);

onMounted(async () => {
  await loadSubmissions();
});
</script>

<style scoped>
.grading-page {
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.page-subtitle {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.file-link {
  color: #2563eb;
  text-decoration: none;
}

.file-link:hover {
  text-decoration: underline;
}

.content-preview {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  color: #374151;
  line-height: 1.5;
  cursor: pointer;
  word-break: break-word;
}

.content-empty {
  color: #9ca3af;
}

.content-tooltip {
  max-width: 420px;
  max-height: 240px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.review-dialog {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.review-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 16px;
}

.review-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.review-item-wide {
  grid-column: 1 / -1;
}

.review-label {
  font-weight: 600;
  color: #111827;
}

.review-text {
  white-space: pre-wrap;
  word-break: break-word;
  color: #374151;
  line-height: 1.6;
}

.status-select {
  width: 100%;
}

@media (max-width: 768px) {
  .grading-page {
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

  .page-title {
    font-size: 24px;
  }

  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
