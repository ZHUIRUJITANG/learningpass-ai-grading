import request from "./request";

export interface Submission {
  id: number;
  student_id: string;
  student_name: string;
  assignment_id: number;
  file_name: string;
  file_type?: string;
  file_size?: number | null;
  submit_time: string;
  parse_status?: string;
  extracted_content?: string | null;
  ai_score: number | null;
  ai_comment?: string | null;
  ai_score_reason?: string | null;
  parse_confidence?: number | null;
  final_score: number | null;
  teacher_comment?: string | null;
  review_status: string;
  file_url?: string;
}

export async function getSubmissions(
  assignmentId?: number
): Promise<Submission[]> {
  const response = await request.get<Submission[]>("/api/v1/submissions/", {
    params:
      assignmentId !== undefined ? { assignment_id: assignmentId } : undefined,
  });
  return response.data;
}

export async function getSubmission(id: number): Promise<Submission> {
  const response = await request.get<Submission>(`/api/v1/submissions/${id}`);
  return response.data;
}

export async function createSubmission(data: FormData): Promise<Submission> {
  const response = await request.post<Submission>("/api/v1/submissions/", data);
  return response.data;
}

export async function updateSubmission(
  id: number,
  data: Partial<Submission>
): Promise<Submission> {
  const response = await request.put<Submission>(`/api/v1/submissions/${id}`, data);
  return response.data;
}

export async function deleteSubmission(
  id: number
): Promise<{ message: string }> {
  const response = await request.delete<{ message: string }>(
    `/api/v1/submissions/${id}`
  );
  return response.data;
}
