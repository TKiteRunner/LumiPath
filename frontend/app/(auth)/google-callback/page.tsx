"use client";
import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/store/authStore";
import { SunIcon } from "lucide-react";

function GoogleCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      toast.error("Google 登录失败：缺少授权码");
      router.push("/login");
      return;
    }

    authApi
      .googleCallback(code)
      .then((data) => {
        setAuth(data.user, data.access_token, data.refresh_token);
        toast.success("Google 登录成功！");
        router.push("/");
      })
      .catch(() => {
        toast.error("Google 登录失败，请重试");
        router.push("/login");
      });
  }, [searchParams, setAuth, router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-surface gap-4">
      <SunIcon className="w-8 h-8 text-macaron-pink animate-pulse" strokeWidth={1.5} />
      <p className="text-text-muted text-sm">Google 登录中，请稍候…</p>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col items-center justify-center bg-surface gap-4">
          <SunIcon className="w-8 h-8 text-macaron-pink animate-pulse" strokeWidth={1.5} />
          <p className="text-text-muted text-sm">Google 登录中，请稍候…</p>
        </div>
      }
    >
      <GoogleCallbackInner />
    </Suspense>
  );
}
