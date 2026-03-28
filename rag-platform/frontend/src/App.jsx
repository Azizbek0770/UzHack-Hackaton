import { useEffect, useMemo, useState } from "react";
import DataHub from "./pages/DataHub.jsx";
import Home from "./pages/Home.jsx";
import OpsCenter from "./pages/OpsCenter.jsx";

const routes = [
  { key: "home", label: "Assistant" },
  { key: "data", label: "Data Hub" },
  { key: "ops", label: "Ops Center" }
];

function getRouteFromHash() {
  const hash = window.location.hash.replace("#", "");
  if (routes.some((route) => route.key === hash)) {
    return hash;
  }
  return "home";
}

export default function App() {
  const [route, setRoute] = useState(getRouteFromHash());

  useEffect(() => {
    const onHashChange = () => setRoute(getRouteFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const page = useMemo(() => {
    if (route === "data") {
      return <DataHub />;
    }
    if (route === "ops") {
      return <OpsCenter />;
    }
    return <Home />;
  }, [route]);

  return (
    <div>
      <div className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <p className="text-sm font-semibold text-slate-200">RAG Financial Platform</p>
          <div className="flex items-center gap-2">
            {routes.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  window.location.hash = item.key;
                  setRoute(item.key);
                }}
                className={`rounded-lg px-3 py-2 text-xs transition ${
                  route === item.key
                    ? "bg-cyan-500 text-slate-950"
                    : "border border-slate-700 text-slate-300 hover:border-cyan-500/60"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      {page}
    </div>
  );
}
