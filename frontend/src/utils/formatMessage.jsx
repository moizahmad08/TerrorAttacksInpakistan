/**
 * Lightweight markdown → React renderer for assistant messages.
 * Supports headings, lists, bold, paragraphs, and horizontal rules.
 */

function parseInline(text) {
  const parts = [];
  const re = /\*\*(.+?)\*\*|`([^`]+)`/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ type: "text", value: text.slice(last, m.index) });
    if (m[1]) parts.push({ type: "strong", value: m[1] });
    else parts.push({ type: "code", value: m[2] });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ type: "text", value: text.slice(last) });
  return parts.length ? parts : [{ type: "text", value: text }];
}

function Inline({ text }) {
  return (
    <>
      {parseInline(text).map((p, i) => {
        if (p.type === "strong") return <strong key={i}>{p.value}</strong>;
        if (p.type === "code") return <code key={i}>{p.value}</code>;
        return <span key={i}>{p.value}</span>;
      })}
    </>
  );
}

function parseBlocks(content) {
  const lines = (content || "").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (/^---+$/.test(line.trim())) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      blocks.push({ type: `h${heading[1].length}`, text: heading[2] });
      i++;
      continue;
    }

    if (/^[-*•]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^[-*•]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*•]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    const para = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^(#{1,3})\s/.test(lines[i]) && !/^[-*•]\s+/.test(lines[i]) && !/^\d+\.\s+/.test(lines[i]) && !/^---+$/.test(lines[i].trim())) {
      para.push(lines[i]);
      i++;
    }
    blocks.push({ type: "p", text: para.join("\n") });
  }

  return blocks;
}

export function FormattedMessage({ content }) {
  const blocks = parseBlocks(content);

  return (
    <div className="msg-prose">
      {blocks.map((block, idx) => {
        switch (block.type) {
          case "h1":
            return <h3 key={idx} className="msg-h1"><Inline text={block.text} /></h3>;
          case "h2":
            return <h4 key={idx} className="msg-h2"><Inline text={block.text} /></h4>;
          case "h3":
            return <h5 key={idx} className="msg-h3"><Inline text={block.text} /></h5>;
          case "ul":
            return (
              <ul key={idx} className="msg-list">
                {block.items.map((item, j) => (
                  <li key={j}><Inline text={item} /></li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={idx} className="msg-list msg-list-ol">
                {block.items.map((item, j) => (
                  <li key={j}><Inline text={item} /></li>
                ))}
              </ol>
            );
          case "hr":
            return <hr key={idx} className="msg-hr" />;
          case "p":
          default:
            return (
              <p key={idx} className="msg-p">
                <Inline text={block.text} />
              </p>
            );
        }
      })}
    </div>
  );
}
