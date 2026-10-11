import { useEffect, useRef, useState } from "react";

type Recipe = {
  name: string;
  description: string;
  variables: Record<string, { default: any }>;
};

export default function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [workspaces, setWorkspaces] = useState<string[]>([]);
  const [projectName, setProjectName] = useState("");
  const [selected, setSelected] = useState<string>("");
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const logRef = useRef<HTMLPreElement>(null);

  const refresh = async () => {
    const r = await fetch("http://localhost:8000/api/recipes").then(r => r.json());
    const w = await fetch("http://localhost:8000/api/workspaces").then(r => r.json());
    setRecipes(r);
    setWorkspaces(w);
    if (r.length && !selected) setSelected(r[0].name);
  };

  useEffect(() => { refresh(); }, []);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const create = () => {
    if (!selected || !projectName) return;
    const safeName = projectName.trim().replace(/[^a-zA-Z0-9_-]/g, "-");
    if (safeName !== projectName) {
      setLogs([`[devlab] Invalid characters in name. Using: ${safeName}`]);
    }
    setLogs([]);
    setRunning(true);
    const ws = new WebSocket("ws://localhost:8000/ws/create");
    ws.onopen = () => ws.send(JSON.stringify({ recipe: selected, project_name: projectName }));
    ws.onmessage = (e) => {
      const msg = e.data;
      if (msg === "__DONE__") {
        setRunning(false);
        setProjectName("");
        refresh();
        ws.close();
        return;
      }
      if (msg.startsWith("__ERROR__")) {
        setLogs(l => [...l, msg]);
        setRunning(false);
        ws.close();
        return;
      }
      setLogs(l => [...l, msg]);
    };
    ws.onerror = () => { setRunning(false); };
  };

  return (
    <div style={{ fontFamily: "monospace", padding: 24, background: "#111", color: "#eee", minHeight: "100vh" }}>
      <h1>DevLab</h1>

      <section style={{ marginBottom: 24 }}>
        <h2>New project</h2>
        <select value={selected} onChange={e => setSelected(e.target.value)} style={{ padding: 8 }}>
          {recipes.map(r => <option key={r.name} value={r.name}>{r.name} — {r.description}</option>)}
        </select>
        <input
          placeholder="project name (letters, numbers, - _ only)"
          value={projectName}
          onChange={e => setProjectName(e.target.value)}
          style={{ padding: 8, marginLeft: 8 }}
        />
        <button onClick={create} disabled={running} style={{ padding: 8, marginLeft: 8 }}>
          {running ? "Creating..." : "Create"}
        </button>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2>Terminal</h2>
        <pre ref={logRef} style={{ background: "#000", padding: 12, height: 300, overflow: "auto", fontSize: 12 }}>
          {logs.join("\n") || "—"}
        </pre>
      </section>

      <section>
        <h2>Workspaces</h2>
        <ul>{workspaces.map(w => <li key={w}>{w}</li>)}</ul>
      </section>
    </div>
  );
}