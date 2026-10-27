import { useState } from "react";
import { motion } from "motion/react";

interface Props {
  fileName?: string;
  onSearch: (query: string) => void;
}

export default function SearchBar({ fileName, onSearch }: Props) {
  const [value, setValue] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = value.trim();
    if (q) onSearch(q);
  };

  return (
    <motion.div
      className="search-wrap"
      // rises from below
      initial={{ y: "60vh", opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: "-30vh", opacity: 0 }}
      transition={{ type: "spring", stiffness: 90, damping: 16 }}
    >
      {fileName && (
        <motion.div
          className="file-chip"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          📄 {fileName}
        </motion.div>
      )}

      <form onSubmit={submit} className="search-form">
        <input
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about your file…"
        />
        <motion.button type="submit" whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.92 }} disabled={!value.trim()}>
          Search
        </motion.button>
      </form>
    </motion.div>
  );
}