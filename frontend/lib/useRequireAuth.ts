"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

/**
 * 客户端守卫：未登录直接跳 /login。
 * dashboard 段下的页面统一用这个简化逻辑（页面里调 API 时如果 401 也会再次跳走）。
 */
export function useRequireAuth() {
  const router = useRouter();
  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    }
  }, [router]);
}
