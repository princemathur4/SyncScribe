import CollaborativeEditor from "./Editor.jsx";

function App() {
  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>WikiSync</h1>
      <p style={{ color: "#666", marginBottom: "1rem" }}>
        Open this page in two tabs to test real-time collaboration.
      </p>
      <CollaborativeEditor pageSlug="test-page" username="guest" />
    </div>
  );
}

export default App;