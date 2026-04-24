"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/lib/store/authStore";
import { authApi } from "@/lib/api/auth";
import { cn } from "@/lib/utils";
import {
  BriefcaseIcon,
  TargetIcon,
  BookOpenIcon,
  SparklesIcon,
  SettingsIcon,
  LogOutIcon,
  SunIcon,
} from "lucide-react";

const navItems = [
  { href: "/interviews", icon: BriefcaseIcon, key: "interviews" as const },
  { href: "/okr", icon: TargetIcon, key: "okr" as const },
  { href: "/notes", icon: BookOpenIcon, key: "notes" as const },
  { href: "/agent", icon: SparklesIcon, key: "agent" as const },
  { href: "/settings", icon: SettingsIcon, key: "settings" as const },
];

export function Sidebar() {
  const pathname = usePathname();
  const t = useTranslations("nav");
  const { user, clearAuth } = useAuthStore();

  const handleLogout = async () => {
    await authApi.logout().catch(() => {});
    clearAuth();
    window.location.href = "/login";
  };

  return (
    <aside
      className="flex flex-col w-56 min-h-screen border-r border-border bg-white"
      style={{ boxShadow: "var(--shadow-sidebar)" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5 border-b border-border">
        <SunIcon className="w-7 h-7 text-macaron-pink" strokeWidth={1.5} />
        <span className="font-bold text-lg text-text-main tracking-tight">
          LumiPath
        </span>
      </div>

      {/* 导航 */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, icon: Icon, key }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                active
                  ? "bg-macaron-pink/30 text-text-main"
                  : "text-text-muted hover:bg-macaron-pink/10 hover:text-text-main"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
              {t(key)}
            </Link>
          );
        })}
      </nav>

      {/* 用户 */}
      <div className="px-3 py-4 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2 rounded-md mb-1">
          <div className="w-7 h-7 rounded-full bg-macaron-lilac flex items-center justify-center text-xs font-bold text-text-main">
            {user?.display_name?.[0]?.toUpperCase() ?? "U"}
          </div>
          <span className="text-sm text-text-main truncate flex-1">
            {user?.display_name ?? "用户"}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-text-muted hover:text-text-main hover:bg-macaron-pink/10 transition-colors"
        >
          <LogOutIcon className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
          退出登录
        </button>
      </div>
    </aside>
  );
}
