import { useEffect, useRef, useState } from "react";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { basicSetup } from "codemirror";
import { markdown } from "@codemirror/lang-markdown";
import { yCollab } from "y-codemirror.next";

const WS_BASE_URL = "ws://localhost:8000/ws";

function CollaborativeEditor({ pageSlug, username }) {
  const editorContainerRef = useRef(null);
  const [connectedUsers, setConnectedUsers] = useState(0);
  const [status, setStatus] = useState("connecting");

  useEffect(() => {
    // Guard: do not mount if the ref is not ready
    if (!editorContainerRef.current) return;

    // 1. Yjs document
    const ydoc = new Y.Doc();

    // 2. Connect to FastAPI WebSocket relay
    const provider = new WebsocketProvider(WS_BASE_URL, pageSlug, ydoc);

    // 3. Set presence info for this user
    provider.awareness.setLocalStateField("user", {
      name: username,
      color: "#" + Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, "0"),
    });

    // 4. Track connection status
    provider.on("status", (event) => {
      setStatus(event.status);
    });

    // 5. Track how many users are in the room
    provider.awareness.on("change", () => {
      setConnectedUsers(provider.awareness.getStates().size);
    });

    // 6. The shared text field inside the Yjs doc
    const ytext = ydoc.getText("codemirror");

    // 7. Build CodeMirror editor
    const state = EditorState.create({
      extensions: [
        basicSetup,
        markdown(),
        yCollab(ytext, provider.awareness),
        EditorView.theme({
          "&": {
            height: "400px",
            border: "1px solid #ccc",
            borderRadius: "4px",
            fontSize: "14px",
          },
          ".cm-scroller": { overflow: "auto" },
        }),
      ],
    });

    // 8. Mount into the DOM
    const view = new EditorView({
      state,
      parent: editorContainerRef.current,
    });

    // 9. Cleanup on unmount
    return () => {
      view.destroy();
      provider.destroy();
      ydoc.destroy();
    };
  }, [pageSlug, username]);

  return (
    <div>
      <div style={{
        display: "flex",
        gap: "1rem",
        marginBottom: "0.5rem",
        fontSize: "13px",
        color: "#555",
      }}>
        <span>
          Status:{" "}
          <strong style={{ color: status === "connected" ? "green" : "orange" }}>
            {status}
          </strong>
        </span>
        <span>Users editing: <strong>{connectedUsers}</strong></span>
      </div>

      <div ref={editorContainerRef} />
    </div>
  );
}

export default CollaborativeEditor;