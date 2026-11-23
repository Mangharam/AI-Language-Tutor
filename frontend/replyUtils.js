// Turns a tutor reply (which may contain **bold** and newlines) into text a
// TTS engine can read naturally, and caps its length at a sentence boundary.
export function toSpeechText(text, max = 1200) {
  let t = String(text || "")
    .replace(/\*\*/g, "")
    .replace(/:\s*\n+/g, ": ")
    .replace(/\bQuestion (\d+):/g, "Question $1.")
    .replace(/\s*\n+\s*/g, ". ")
    .replace(/([.!?])\s*\./g, "$1")
    .replace(/\s+/g, " ")
    .trim();
  if (t.length > max) {
    const cut = t.slice(0, max);
    const end = Math.max(cut.lastIndexOf(". "), cut.lastIndexOf("? "), cut.lastIndexOf("! "));
    t = end > 200 ? cut.slice(0, end + 1) : cut;
  }
  return t;
}
