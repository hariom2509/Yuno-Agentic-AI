import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { Bot, GitBranch, Activity, LayoutTemplate, BarChart3, Workflow, Wrench } from "lucide-react";

import "./styles/global.css";
import Dashboard from "./pages/Dashboard";
import Agents from "./pages/Agents";
import Workflows from "./pages/Workflows";
import Builder from "./pages/Builder";
import Monitoring from "./pages/Monitoring";
import Templates from "./pages/Templates";
import Skills from "./pages/Skills";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🤖</div>
        <div>
          <div className="sidebar-logo-text">Yuno AI</div>
          <div className="sidebar-logo-badge">PLATFORM</div>
        </div>
      </div>

      <div className="nav-section-label">Workspace</div>
      <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <BarChart3 size={16} /> Dashboard
      </NavLink>
      <NavLink to="/agents" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <Bot size={16} /> Agents
      </NavLink>
      <NavLink to="/skills" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <Wrench size={16} /> Skills
      </NavLink>

      <div className="nav-section-label">Orchestration</div>
      <NavLink to="/workflows" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <Workflow size={16} /> Workflows
      </NavLink>
      <NavLink to="/builder" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <GitBranch size={16} /> Builder
      </NavLink>
      <NavLink to="/templates" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <LayoutTemplate size={16} /> Templates
      </NavLink>

      <div className="nav-section-label">Observability</div>
      <NavLink to="/monitoring" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <Activity size={16} /> Monitoring
      </NavLink>
    </aside>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/builder" element={<Builder />} />
            <Route path="/builder/:workflowId" element={<Builder />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/skills" element={<Skills />} />
          </Routes>
        </main>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1a1d26",
            color: "#f1f5f9",
            border: "1px solid #1e2235",
            fontFamily: "Inter, sans-serif",
            fontSize: "13px",
          },
        }}
      />
    </BrowserRouter>
  );
}