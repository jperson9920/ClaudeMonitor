import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

function App() {
  const [greeting, setGreeting] = useState("");
  const [version, setVersion] = useState("");

  useEffect(() => {
    // Test IPC communication
    async function loadData() {
      const greetMsg = await invoke<string>("greet", { name: "User" });
      setGreeting(greetMsg);

      const appVersion = await invoke<string>("get_version");
      setVersion(appVersion);
    }

    loadData();

    // Listen for force refresh events from system tray
    const unlistenPromise = listen("force-refresh", () => {
      console.log("Force refresh triggered from system tray");
      loadData();
    });

    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  }, []);

  return (
    <div className="app">
      <header>
        <h1>Claude Usage Monitor</h1>
        <p className="version">v{version}</p>
      </header>

      <div className="content">
        <div className="placeholder">
          <h2>🚀 Tauri Application Ready!</h2>
          <p className="greeting">{greeting}</p>

          <div className="info-box">
            <h3>Setup Complete</h3>
            <ul>
              <li>✓ Tauri backend initialized</li>
              <li>✓ React frontend running</li>
              <li>✓ System tray integrated</li>
              <li>✓ IPC communication working</li>
            </ul>
          </div>

          <div className="next-steps">
            <h3>Next Steps</h3>
            <p>
              EPIC-03 will integrate the Python scraper with this Tauri
              application to display real-time usage data.
            </p>
          </div>
        </div>
      </div>

      <footer>
        <p>Try the system tray menu →</p>
      </footer>
    </div>
  );
}

export default App;
