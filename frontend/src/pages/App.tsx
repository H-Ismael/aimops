import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "../api/client";
import { convertArtifact } from "../api/convert";
import { uploadImage, listImages, getImage } from "../api/images";
import { applyMask } from "../api/mask";
import { classifyArtifact, listModels } from "../api/models";
import { exportMetadata, extractMetadata, importMetadata, stripMetadata } from "../api/metadata";
import { listOperations } from "../api/operations";

export function App() {
  const [images, setImages] = useState<any[]>([]);
  const [selectedImageId, setSelectedImageId] = useState<string>("");
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string>("");
  const [log, setLog] = useState<string>("Ready");
  const [models, setModels] = useState<any[]>([]);
  const [metaImport, setMetaImport] = useState("{}");

  const selectedArtifact = useMemo(() => artifacts.find((a) => a.id === selectedArtifactId), [artifacts, selectedArtifactId]);

  async function refreshImages() {
    const data = await listImages();
    setImages(data);
  }

  async function refreshImageDetails(imageId: string) {
    const data = await getImage(imageId);
    setArtifacts(data.artifacts);
    if (data.artifacts[0]) setSelectedArtifactId(data.artifacts[0].id);
  }

  useEffect(() => {
    refreshImages();
    listModels().then(setModels).catch(() => setModels([]));
  }, []);

  return (
    <div className="container">
      <h1>aimops</h1>
      <div className="card">
        <h3>Upload / Library</h3>
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp,image/tiff"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            const res = await uploadImage(file);
            setLog(JSON.stringify(res, null, 2));
            await refreshImages();
          }}
        />
        <select
          value={selectedImageId}
          onChange={async (e) => {
            const id = e.target.value;
            setSelectedImageId(id);
            await refreshImageDetails(id);
          }}
        >
          <option value="">Select image</option>
          {images.map((img) => (
            <option key={img.id} value={img.id}>{img.id} - {img.original_filename}</option>
          ))}
        </select>
      </div>

      <div className="row">
        <div className="card">
          <h3>Artifacts</h3>
          <select value={selectedArtifactId} onChange={(e) => setSelectedArtifactId(e.target.value)}>
            <option value="">Select artifact</option>
            {artifacts.map((a) => (
              <option key={a.id} value={a.id}>{a.id} ({a.artifact_type})</option>
            ))}
          </select>
          {selectedArtifactId && <img style={{ width: "100%", borderRadius: 8 }} src={`${API_BASE}/artifacts/${selectedArtifactId}/preview`} />}
          {selectedArtifactId && <p><a href={`${API_BASE}/artifacts/${selectedArtifactId}/download`} target="_blank">Download selected artifact</a></p>}
          <p>Type: {selectedArtifact?.artifact_type ?? "-"}</p>
        </div>

        <div className="card">
          <h3>Metadata + Convert</h3>
          <button onClick={async () => setLog(JSON.stringify(await extractMetadata(selectedArtifactId), null, 2))}>Extract Metadata</button>
          <button onClick={async () => setLog(JSON.stringify(await exportMetadata(selectedArtifactId), null, 2))}>Export Metadata</button>
          <button onClick={async () => { setLog(JSON.stringify(await stripMetadata(selectedArtifactId, "png"), null, 2)); if (selectedImageId) await refreshImageDetails(selectedImageId); }}>Strip Metadata</button>
          <button onClick={async () => { setLog(JSON.stringify(await convertArtifact(selectedArtifactId, "webp"), null, 2)); if (selectedImageId) await refreshImageDetails(selectedImageId); }}>Convert to WEBP</button>
          <textarea rows={5} value={metaImport} onChange={(e) => setMetaImport(e.target.value)} />
          <button onClick={async () => setLog(JSON.stringify(await importMetadata(selectedArtifactId, JSON.parse(metaImport)), null, 2))}>Import Metadata JSON</button>
        </div>
      </div>

      <div className="row">
        <div className="card">
          <h3>Parametric Transform</h3>
          <button onClick={async () => {
            const payload = { mask_type: "gaussian_noise", strength: 0.01, coverage: 0.15, seed: 42, distribution: "uniform_spatial", per_channel: true, preserve_edges: false, output_format: "png" };
            const res = await applyMask(selectedArtifactId, payload);
            setLog(JSON.stringify(res, null, 2));
            if (selectedImageId) await refreshImageDetails(selectedImageId);
          }}>Apply Gaussian Mask</button>
        </div>

        <div className="card">
          <h3>Classification</h3>
          <button onClick={async () => {
            const ids = models.map((m) => m.id);
            const res = await classifyArtifact(selectedArtifactId, ids);
            setLog(JSON.stringify(res, null, 2));
          }}>Run All Models</button>
          <p>Models: {models.map((m) => m.id).join(", ") || "none"}</p>
        </div>
      </div>

      <div className="card">
        <h3>Operation History</h3>
        <button onClick={async () => setLog(JSON.stringify(await listOperations(selectedArtifactId), null, 2))}>Load Operations</button>
      </div>

      <div className="card">
        <h3>Logs / Results</h3>
        <pre>{log}</pre>
      </div>
    </div>
  );
}
