import { api } from "./client";

export const listOperations = (artifactId: string) => api<any[]>(`/artifacts/${artifactId}/operations`);
