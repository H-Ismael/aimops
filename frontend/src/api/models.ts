import { api } from "./client";

export const listModels = () => api<any[]>("/models");
export const classifyArtifact = (artifactId: string, modelIds: string[]) =>
  api(`/artifacts/${artifactId}/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_ids: modelIds, top_k: 5 }),
  });
