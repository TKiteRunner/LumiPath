"use client";
import { useSettingsStore } from "@/lib/store/settingsStore";
import { GlobeIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const LOCALES = [
  { value: "zh-CN" as const, label: "中文" },
  { value: "en-US" as const, label: "English" },
];

export function LanguageToggle() {
  const { locale, setLocale } = useSettingsStore();

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <GlobeIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
        <span className="text-sm font-medium text-text-main">语言 / Language</span>
      </div>
      <div className="flex gap-2">
        {LOCALES.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setLocale(value)}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium border transition-colors",
              locale === value
                ? "bg-macaron-lilac border-macaron-lilac text-text-main"
                : "bg-white border-border text-text-muted hover:bg-macaron-lilac/20"
            )}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
