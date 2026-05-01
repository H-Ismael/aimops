import { api } from "./client";

export const extractMetadata = (artifactId: string) => api(`/artifacts/${artifactId}/metadata/extract`, { method: "POST" });
export const importMetadata = (artifactId: string, content: object) =>
  api(`/artifacts/${artifactId}/metadata/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, source_format: "json" }),
  });
export const exportMetadata = (artifactId: string) =>
  api(`/artifacts/${artifactId}/metadata/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: "extracted" }),
  });
export const stripMetadata = (artifactId: string, outputFormat: string) =>
  api(`/artifacts/${artifactId}/metadata/strip`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "strip_all", output_format: outputFormat, export_removed_metadata: true }),
  });
