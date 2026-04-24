import { ApiKeyForm } from "./components/ApiKeyForm";
import { AgentSkillsForm } from "./components/AgentSkillsForm";
import { LanguageToggle } from "./components/LanguageToggle";
import { MacaronCard } from "@/components/macaron/MacaronCard";

export default function SettingsPage() {
  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-bold text-text-main mb-6">设置</h1>

      <div className="space-y-5">
        {/* LLM 配置 */}
        <MacaronCard accent="lilac">
          <h2 className="font-semibold text-text-main text-sm mb-4">
            🤖 LLM 配置
          </h2>
          <ApiKeyForm />
        </MacaronCard>

        {/* Agent Skills */}
        <MacaronCard accent="peach">
          <h2 className="font-semibold text-text-main text-sm mb-4">
            ✨ Agent Skills
          </h2>
          <AgentSkillsForm />
        </MacaronCard>

        {/* 语言 */}
        <MacaronCard accent="sky">
          <h2 className="font-semibold text-text-main text-sm mb-4">
            🌐 语言 / Language
          </h2>
          <LanguageToggle />
        </MacaronCard>
      </div>
    </div>
  );
}
