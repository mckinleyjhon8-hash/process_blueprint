"use client";

import { useEffect, useState } from "react";

export type Provider = "anthropic" | "openai" | "openrouter";

export interface LlmConfig {
  provider: Provider;
  model: string; // empty string = use the backend/provider default
}

const KEY = "pb.llm.config";
const DEFAULT: LlmConfig = { provider: "anthropic", model: "" };

export function loadLlm(): LlmConfig {
  if (typeof window === "undefined") return DEFAULT;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw) return { ...DEFAULT, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return DEFAULT;
}

export function saveLlm(cfg: LlmConfig): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(cfg));
  } catch {
    /* ignore */
  }
}

/** React hook: reads the saved LLM config (client-side) and persists updates. */
export function useLlm(): [LlmConfig, (c: LlmConfig) => void] {
  const [cfg, setCfg] = useState<LlmConfig>(DEFAULT);
  useEffect(() => setCfg(loadLlm()), []);
  const update = (c: LlmConfig) => {
    setCfg(c);
    saveLlm(c);
  };
  return [cfg, update];
}
