import { useState } from "react";
import ChatPage from "./pages/ChatPage";
import DatabasePage from "./pages/DatabasePage";
import StatsPage from "./pages/StatsPage";
import Sidebar from "./components/Sidebar";
import "./styles/globals.css";

export default function App() {
  const [page, setPage] = useState("chat");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="app-shell">
      <Sidebar 
        currentPage={page} 
        onNavigate={setPage}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <main className={`main-content ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
        {page === "chat" && <ChatPage />}
        {page === "database" && <DatabasePage />}
        {page === "stats" && <StatsPage />}
      </main>
    </div>
  );
}
