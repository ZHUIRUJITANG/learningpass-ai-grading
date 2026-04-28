export interface Course {
  id: number;
  name: string;
  code: string;
}

export interface Assignment {
  id: number;
  course_id: number;
  name: string;
  description?: string;
  due_date?: string;
  grading_rubric?: any;
  total_points: number;
}
