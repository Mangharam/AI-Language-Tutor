// Renders **bold** and line breaks from tutor replies. Uses React text nodes
// only (no innerHTML), so model output cannot inject markup.
function renderBold(line) {
  return line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.length > 4 && part.startsWith("**") && part.endsWith("**")
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  );
}

export default function FormattedReply({ text }) {
  return (
    <div className="formatted-reply">
      {String(text || "").split("\n").map((line, i) =>
        line.trim() === ""
          ? <div key={i} className="reply-gap" />
          : <p key={i}>{renderBold(line)}</p>
      )}
    </div>
  );
}
