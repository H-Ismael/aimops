import { api } from "./client";

export const applyMask = (artifactId: string, payload: object) =>
  api(`/artifacts/${artifactId}/mask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
