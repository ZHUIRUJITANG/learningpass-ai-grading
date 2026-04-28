import request from "./request";
import type { Assignment } from "@/types";

export async function getAssignments(
  courseId?: number
): Promise<Assignment[]> {
  const response = await request.get<Assignment[]>("/api/v1/assignments/", {
    params: courseId !== undefined ? { course_id: courseId } : undefined,
  });
  return response.data;
}

export async function getAssignment(id: number): Promise<Assignment> {
  const response = await request.get<Assignment>(`/api/v1/assignments/${id}`);
  return response.data;
}

export async function createAssignment(data: {
  course_id: number;
  name: string;
  description?: string;
  grading_rubric?: Record<string, unknown>;
  due_date?: string;
  total_points?: number;
}): Promise<Assignment> {
  const response = await request.post<Assignment>("/api/v1/assignments/", data);
  return response.data;
}

export async function updateAssignment(
  id: number,
  data: Partial<Assignment>
): Promise<Assignment> {
  const response = await request.put<Assignment>(
    `/api/v1/assignments/${id}`,
    data
  );
  return response.data;
}

export async function deleteAssignment(
  id: number
): Promise<{ message: string }> {
  const response = await request.delete<{ message: string }>(
    `/api/v1/assignments/${id}`
  );
  return response.data;
}
