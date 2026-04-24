import { BriefcaseIcon, TargetIcon, BookOpenIcon, SparklesIcon } from "lucide-react";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import Link from "next/link";

const quickLinks = [
  {
    href: "/interviews",
    icon: BriefcaseIcon,
    label: "面试看板",
    desc: "追踪每一轮面试进度",
    accent: "pink" as const,
  },
  {
    href: "/okr",
    icon: TargetIcon,
    label: "OKR 规划",
    desc: "拆解目标，量化成长",
    accent: "mint" as const,
  },
  {
    href: "/notes",
    icon: BookOpenIcon,
    label: "学习笔记",
    desc: "记录每日思考与复盘",
    accent: "lilac" as const,
  },
  {
    href: "/agent",
    icon: SparklesIcon,
    label: "AI 助手",
    desc: "多智能体协作支持",
    accent: "sky" as const,
  },
];

export default function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-text-main mb-2">
        欢迎回到 LumiPath ✨
      </h1>
      <p className="text-text-muted mb-8 text-sm">
        照亮你的求职与成长路径
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
        {quickLinks.map(({ href, icon: Icon, label, desc, accent }) => (
          <Link key={href} href={href}>
            <MacaronCard
              accent={accent}
              className="cursor-pointer h-full"
            >
              <div className="flex items-start gap-3">
                <Icon className="w-5 h-5 mt-0.5 text-text-muted flex-shrink-0" strokeWidth={1.5} />
                <div>
                  <p className="font-semibold text-text-main text-sm">{label}</p>
                  <p className="text-text-muted text-xs mt-0.5">{desc}</p>
                </div>
              </div>
            </MacaronCard>
          </Link>
        ))}
      </div>
    </div>
  );
}
