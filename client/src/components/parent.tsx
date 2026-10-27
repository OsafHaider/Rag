import { useState } from "react";
import { AnimatePresence } from "motion/react";
import FileUploader from "./file-uploader";
import SearchBar from "./searchbar";
import ChatScreen from "./chat-screen";

type Stage = "upload" | "search" | "chat";

export default function DocumentChatFlow() {
  const [stage, setStage] = useState<Stage>("upload");
  const [fileName, setFileName] = useState("");
  const [query, setQuery] = useState("");

  return (
    <div className="flow-root">
      <AnimatePresence mode="wait">
        {stage === "upload" && (
          <FileUploader
            key="upload"
            uploadUrl="http://localhost:8000/api/upload"
            onSuccess={(name) => {
              setFileName(name);
              setStage("search");
            }}
          />
        )}

        {stage === "search" && (
          <SearchBar
            key="search"
            fileName={fileName}
            onSearch={(q) => {
              setQuery(q);
              setStage("chat");
            }}
          />
        )}

        {stage === "chat" && <ChatScreen key="chat" initialQuery={query} chatUrl="http://localhost:8000/api/chat" />}
      </AnimatePresence>
    </div>
  );
}