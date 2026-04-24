"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/store/authStore";
import { SunIcon } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [form, setForm] = useState({
    email: "",
    password: "",
    display_name: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await authApi.register(form);
      setAuth(data.user, data.access_token, data.refresh_token);
      toast.success("注册成功，欢迎加入 LumiPath！");
      router.push("/");
    } catch {
      toast.error("注册失败，该邮箱可能已被使用");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-full bg-macaron-pink flex items-center justify-center mb-3">
            <SunIcon className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          <h1 className="text-2xl font-bold text-text-main">LumiPath</h1>
          <p className="text-text-muted text-sm mt-1">开始你的成长旅程</p>
        </div>

        <div className="macaron-card p-6">
          <h2 className="text-lg font-semibold text-text-main mb-5">注册账号</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                昵称
              </label>
              <input
                type="text"
                required
                value={form.display_name}
                onChange={(e) =>
                  setForm({ ...form, display_name: e.target.value })
                }
                className="w-full px-3 py-2 rounded-md border border-border bg-white text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-macaron-pink/50"
                placeholder="你的名字"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                邮箱
              </label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-white text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-macaron-pink/50"
                placeholder="your@email.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                密码
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-white text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-macaron-pink/50"
                placeholder="至少 8 位"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-md bg-macaron-pink text-text-main text-sm font-medium hover:bg-[--color-primary-dark] transition-colors disabled:opacity-60"
            >
              {loading ? "注册中…" : "注册"}
            </button>
          </form>
          <p className="text-center text-sm text-text-muted mt-4">
            已有账号？{" "}
            <Link href="/login" className="text-text-main font-medium underline">
              立即登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
