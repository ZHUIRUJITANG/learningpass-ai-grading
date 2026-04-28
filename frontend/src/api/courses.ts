import request from "./request";
import type { Course } from "@/types";

export async function getCourses(): Promise<Course[]> {
  const response = await request.get<Course[]>("/api/v1/courses/");
  return response.data;
}

export async function getCourse(id: number): Promise<Course> {
  const response = await request.get<Course>(`/api/v1/courses/${id}`);
  return response.data;
}

export async function createCourse(data: {
  name: string;
  code: string;
}): Promise<Course> {
  const response = await request.post<Course>("/api/v1/courses/", data);
  return response.data;
}

export async function updateCourse(
  id: number,
  data: {
    name?: string;
    code?: string;
  }
): Promise<Course> {
  const response = await request.put<Course>(`/api/v1/courses/${id}`, data);
  return response.data;
}

export async function deleteCourse(id: number): Promise<{ message: string }> {
  const response = await request.delete<{ message: string }>(
    `/api/v1/courses/${id}`
  );
  return response.data;
}
