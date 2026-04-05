function Toolbar({ editorViewRef }) {

  // Wraps the currently selected text with a prefix and suffix
  // e.g. prefix="**" suffix="**" turns "hello" into "**hello**"
  const wrapSelection = (prefix, suffix) => {
    const view = editorViewRef.current;
    if (!view) return;

    const { from, to } = view.state.selection.main;
    const selectedText = view.state.sliceDoc(from, to);

    view.dispatch({
      changes: {
        from,
        to,
        insert: `${prefix}${selectedText}${suffix}`,
      },
      // Move cursor to end of inserted text
      selection: { anchor: from + prefix.length + selectedText.length + suffix.length },
    });

    view.focus();
  };

  // Inserts a prefix at the start of the current line
  const insertLinePrefix = (prefix) => {
    const view = editorViewRef.current;
    if (!view) return;

    const { from } = view.state.selection.main;
    const line = view.state.doc.lineAt(from);

    view.dispatch({
      changes: {
        from: line.from,
        to: line.from,
        insert: prefix,
      },
    });

    view.focus();
  };

  const buttons = [
    { label: "B",      title: "Bold",          action: () => wrapSelection("**", "**"),  style: { fontWeight: "bold" } },
    { label: "I",      title: "Italic",         action: () => wrapSelection("*", "*"),    style: { fontStyle: "italic" } },
    { label: "~~S~~",  title: "Strikethrough",  action: () => wrapSelection("~~", "~~"), style: {} },
    { label: "H1",     title: "Heading 1",      action: () => insertLinePrefix("# "),     style: {} },
    { label: "H2",     title: "Heading 2",      action: () => insertLinePrefix("## "),    style: {} },
    { label: "H3",     title: "Heading 3",      action: () => insertLinePrefix("### "),   style: {} },
    { label: "• List", title: "Bullet List",    action: () => insertLinePrefix("- "),     style: {} },
    { label: "1. List",title: "Numbered List",  action: () => insertLinePrefix("1. "),   style: {} },
    { label: "> Quote",title: "Blockquote",     action: () => insertLinePrefix("> "),     style: {} },
    { label: "</>",    title: "Inline Code",    action: () => wrapSelection("`", "`"),    style: { fontFamily: "monospace" } },
    { label: "```",    title: "Code Block",     action: () => wrapSelection("```\n", "\n```"), style: { fontFamily: "monospace" } },
  ];

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      gap: "4px",
      padding: "6px",
      backgroundColor: "#f5f5f5",
      border: "1px solid #ccc",
      borderBottom: "none",
      borderRadius: "4px 4px 0 0",
    }}>
      {buttons.map((btn) => (
        <button
          key={btn.title}
          title={btn.title}
          onClick={btn.action}
          style={{
            padding: "3px 8px",
            fontSize: "18px",
            cursor: "pointer",
            border: "1px solid #ccc",
            borderRadius: "3px",
            backgroundColor: "#fff",
            ...btn.style,
          }}
        >
          {btn.label}
        </button>
      ))}
    </div>
  );
}

export default Toolbar;
