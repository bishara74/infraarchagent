// AI assistance: written with OpenAI Codex from the author's task
// descriptions; reviewed and modified by the author. See AI_USE.md.
import { render } from "@testing-library/react";
import { expect, it } from "vitest";
import { Icon } from "./Icon";
it("FR-UI-01 decorative Codicons do not duplicate accessible labels", () => {
  const { container } = render(
    <button>
      <Icon name="zap" />
      Generate
    </button>,
  );
  expect(container.querySelector(".codicon-zap")).toHaveAttribute("aria-hidden", "true");
  expect(container.querySelector("button")).toHaveAccessibleName("Generate");
});
