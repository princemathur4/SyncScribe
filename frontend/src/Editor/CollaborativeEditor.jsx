import { useEffect, useRef, useState } from "react";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { basicSetup } from "codemirror";
import { markdown } from "@codemirror/lang-markdown";
import { yCollab } from "y-codemirror.next";
import "./CollaborativeEditor.css";
import Toolbar from "../Toolbar";


const WS_BASE_URL = "ws://localhost:8000/ws";

function CollaborativeEditor({ pageSlug, username }) {
  const editorContainerRef = useRef(null);
  // Add this ref alongside editorContainerRef
  const editorViewRef = useRef(null);

  const [connectedUsers, setConnectedUsers] = useState(0);
  const [status, setStatus] = useState("connecting");
  const [activeUsers, setActiveUsers] = useState([]);

  useEffect(() => {
    // Guard: do not mount if the ref is not ready
    if (!editorContainerRef.current) return;

    // 1. Yjs document
    const ydoc = new Y.Doc();

    // 2. Connect to FastAPI WebSocket relay
    const provider = new WebsocketProvider(WS_BASE_URL, pageSlug, ydoc);

    const generateColor = () => "#" + Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, "0");
    // 3. Set presence info for this user
    provider.awareness.setLocalStateField("user", {
      name: username,
      color: generateColor(),
    });

    // Tell Yjs to consider a peer offline after 5 seconds of silence
    provider.awareness.outdatedTimeout = 5000; // ms

    // 4. Track connection status
    provider.on("status", (event) => {
      setStatus(event.status);
    });

    // 5. Track how many users are in the room
    provider.awareness.on("change", () => {
      const states = provider.awareness.getStates();
      const users = [];
      states.forEach((state, clientId) => {
        if (state.user) {
          users.push({
            clientId,
            name: state.user.name,
            color: state.user.color,
          });
        }
      });
      setActiveUsers(users);
      setConnectedUsers(states.size);
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
    editorViewRef.current = view; // add this line

    
    // 9. Cleanup on unmount
    return () => {
      ytext.unobserve(onYtextChange);
      clearTimeout(saveTimeout);
      window.removeEventListener("beforeunload", handleBeforeUnload);
      editorViewRef.current = null;
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
        {/* User avatars bar */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
          {activeUsers.map((user) => (
            <div
              key={user.clientId}
              style={{
                backgroundColor: user.color,
                color: "#fff",
                padding: "2px 10px",
                borderRadius: "12px",
                fontSize: "12px",
                fontWeight: "bold",
              }}
            >
              {user.name}
            </div>
          ))}
        </div>
      </div>
      <Toolbar editorViewRef={editorViewRef} />
      <div ref={editorContainerRef} />
    </div>
  );
}

export default CollaborativeEditor;
