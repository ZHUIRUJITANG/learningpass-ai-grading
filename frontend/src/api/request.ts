import axios from "axios";
import { ElMessage } from "element-plus";

const request = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 60000,
});

request.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Request failed";

    ElMessage.error(message);
    return Promise.reject(error);
  }
);

export default request;
