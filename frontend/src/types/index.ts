export type ImageRow = { id: string; original_filename: string; created_at: string };
export type ArtifactRow = {
  id: string;
  image_id: string;
  parent_artifact_id: string | null;
  artifact_type: string;
  format: string | null;
  width: number | null;
  height: number | null;
};
