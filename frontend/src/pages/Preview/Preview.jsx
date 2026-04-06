import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import DOMPurify from "dompurify";
import "highlight.js/styles/github.css";
import "./Preview.css";

function Preview({ content }) {
  const sanitized = DOMPurify.sanitize(content);

  return (
    <div className="preview">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
      >
        {sanitized}
      </ReactMarkdown>
    </div>
  );
}

export default Preview;
