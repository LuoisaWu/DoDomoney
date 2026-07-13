import type { AssistantTone } from "../types";

const toneOptions: Array<{ value: AssistantTone; label: string }> = [
  { value: "cute", label: "可爱陪伴型" },
  { value: "snarky", label: "毒舌吐槽型" },
  { value: "gentle", label: "温柔鼓励型" },
  { value: "advisor", label: "理性顾问型" },
  { value: "minimal", label: "极简冷淡型" }
];

interface SettingsPageProps {
  assistantTone: AssistantTone;
  onToneChange: (tone: AssistantTone) => void;
}

export function SettingsPage({ assistantTone, onToneChange }: SettingsPageProps) {
  return (
    <section className="work-area">
      <header className="page-header">
        <div>
          <p className="eyebrow">助手设置</p>
          <h1>账小喵人格</h1>
        </div>
      </header>

      <div className="settings-panel">
        <label>
          回复风格
          <select
            value={assistantTone}
            onChange={(event) => onToneChange(event.target.value as AssistantTone)}
          >
            {toneOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
