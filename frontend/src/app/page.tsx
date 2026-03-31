"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { KanbanBoard } from "@/components/KanbanBoard";
import { clearToken, getToken, verifyToken } from "@/lib/auth";

export default function Home() {
  const [authenticated, setAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    verifyToken(token).then((valid) => {
      if (valid) {
        setAuthenticated(true);
      } else {
        clearToken();
        router.replace("/login");
      }
    });
  }, []);

  const handleLogout = () => {
    clearToken();
    router.replace("/login");
  };

  if (!authenticated) return null;

  return <KanbanBoard onLogout={handleLogout} />;
}
