/* AI assistance: written with OpenAI Codex from the author's task
   descriptions; reviewed and modified by the author. See AI_USE.md. */
// @vitest-environment node
import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

const tokens = readFileSync(new URL("./tokens.css", import.meta.url), "utf8");

function linearChannel(hex: string): number {
  const srgb = Number.parseInt(hex, 16) / 255;
  return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(token: string): number {
  const hex = tokens.match(new RegExp(`^\\s*${token}:\\s*#([0-9a-f]{6})\\s*;`, "im"))?.[1];
  if (!hex) throw new Error(`Missing hex value for ${token}`);

  const red = linearChannel(hex.slice(0, 2));
  const green = linearChannel(hex.slice(2, 4));
  const blue = linearChannel(hex.slice(4, 6));
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

it.each([
  ["--ok", "--ok-bg"],
  ["--running", "--running-bg"],
  ["--queued", "--queued-bg"],
  ["--warn", "--warn-bg"],
  ["--danger", "--danger-bg"],
  ["--text", "--ok-bg"],
  ["--ok", "--surface"],
  ["--ok", "--bg"],
  ["--text", "--bg"],
  ["--text-muted", "--bg"],
  ["--text", "--surface"],
  ["--text-muted", "--surface"],
])("meets WCAG 2.2 AA contrast for %s on %s", (foreground, background) => {
  const text = relativeLuminance(foreground);
  const fill = relativeLuminance(background);
  const ratio = (Math.max(text, fill) + 0.05) / (Math.min(text, fill) + 0.05);
  const message = `${foreground} on ${background} = ${ratio.toFixed(2)}:1`;
  console.info(message);
  expect(ratio, message).toBeGreaterThanOrEqual(4.5);
});
