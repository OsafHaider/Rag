import { useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";

type Status = "idle" | "uploading" | "success" | "error";

interface Props {
  uploadUrl?: string;
  onSuccess: (fileName: string) => void;
}

// Only text files are allowed
const ALLOWED_EXT = [".txt", ".md", ".csv", ".json", ".log","pdf"];

export default function FileUploader({ uploadUrl = "/api/upload", onSuccess }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState("");

  const isTextFile = (file: File) =>
    file.type.startsWith("text/") ||
    file.type === "application/json" ||
    ALLOWED_EXT.some((ext) => file.name.toLowerCase().endsWith(ext));

  const upload = (file: File) => {
    if (!isTextFile(file)) {
      setStatus("error");
      setError("Only text files are allowed (.txt, .md, .csv, .json, .log)");
      return;
    }

    setFileName(file.name);
    setStatus("uploading");
    setProgress(0);
    setError("");

    const form = new FormData();
    form.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", uploadUrl);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100));
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        setStatus("success");
        // Show the success animation briefly before moving to the next step
        setTimeout(() => onSuccess(file.name), 900);
      } else {
        setStatus("error");
        setError(`Upload failed (${xhr.status})`);
      }
    };

    xhr.onerror = () => {
      setStatus("error");
      setError("Network error. Please try again.");
    };

    xhr.send(form);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) upload(file);
  };

  return (
    <motion.div
      className={`uploader ${dragging ? "dragging" : ""} ${status}`}
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, y: -60, scale: 0.9 }}
      transition={{ type: "spring", stiffness: 160, damping: 18 }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => status !== "uploading" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        hidden
        accept={ALLOWED_EXT.join(",") + ",text/*,application/json"}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) upload(f);
          e.target.value = "";
        }}
      />

      <AnimatePresence mode="wait">
        {status === "idle" && (
          <motion.div key="idle" className="uploader-body" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div animate={{ y: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 2 }} className="uploader-icon">
              ⬆
            </motion.div>
            <h3>Drop a text file here</h3>
            <p>or click to select one (.txt, .md, .csv, .json)</p>
          </motion.div>
        )}

        {status === "uploading" && (
          <motion.div key="up" className="uploader-body" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <h3>{fileName}</h3>
            <div className="progress-track">
              <motion.div className="progress-bar" animate={{ width: `${progress}%` }} transition={{ ease: "easeOut" }} />
            </div>
            <p>Uploading… {progress}%</p>
          </motion.div>
        )}

        {status === "success" && (
          <motion.div key="ok" className="uploader-body" initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }}>
            <motion.div
              className="uploader-icon success-icon"
              initial={{ scale: 0 }}
              animate={{ scale: [0, 1.3, 1] }}
              transition={{ duration: 0.5 }}
            >
              ✓
            </motion.div>
            <h3>Upload complete!</h3>
            <p>{fileName}</p>
          </motion.div>
        )}

        {status === "error" && (
          <motion.div
            key="err"
            className="uploader-body"
            initial={{ x: 0 }}
            animate={{ x: [0, -10, 10, -6, 6, 0] }}
            transition={{ duration: 0.4 }}
          >
            <div className="uploader-icon error-icon">✕</div>
            <h3>{error}</h3>
            <p>Click again to try</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}