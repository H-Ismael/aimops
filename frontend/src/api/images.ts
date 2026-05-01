import { api } from "./client";

export async function uploadImage(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return api<{ image_id: string; artifact_id: string; preview_url: string }>("/images/upload", {
    method: "POST",
    body: fd,
  });
}

export async function listImages() {
  return api<any[]>("/images");
}

export async function getImage(imageId: string) {
  return api<{ image: any; artifacts: any[] }>(`/images/${imageId}`);
}
