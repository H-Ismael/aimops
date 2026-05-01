import { api } from "./client";

export const convertArtifact = (artifactId: string, outputFormat: string) =>
  api(`/artifacts/${artifactId}/convert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ output_format: outputFormat, quality: 95, preserve_metadata: false }),
  });
