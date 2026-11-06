import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Landing } from "../index";

const renderLanding = () =>
  render(
    <MemoryRouter>
      <Landing />
    </MemoryRouter>,
  );

describe("Landing", () => {
  it("shows the headline and links to sign in", () => {
    renderLanding();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Check every claim.");
    expect(screen.getAllByRole("link", { name: "Sign in" })[0].getAttribute("href")).toBe("/auth");
  });

  it("does not link out to GitHub or list made-up customers", () => {
    const { container } = renderLanding();
    expect(container.innerHTML).not.toMatch(/github\.com/i);
    expect(container.textContent).not.toMatch(/trusted by/i);
  });

  it("updates verdicts when the evidence changes", () => {
    renderLanding();
    expect(screen.getByText("3 of 5")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Transfers, 24 h"), { target: { value: "11" } });
    expect(screen.getByText("4 of 5")).toBeTruthy();
  });

  it("shows where the sealed chain breaks", () => {
    renderLanding();
    fireEvent.change(screen.getByLabelText("Evidence entry"), { target: { value: "Wire of 9,400 from acc_corp_88" } });
    expect(screen.getByText(/Chain breaks at/).textContent).toContain("evidence ingested");
  });

  it("filters the command list", () => {
    renderLanding();
    fireEvent.change(screen.getByLabelText("Find a command"), { target: { value: "legal" } });
    expect(within(screen.getByRole("listbox", { name: "Commands" })).getAllByRole("option")).toHaveLength(1);
    expect(screen.getByText("Apply a legal hold")).toBeTruthy();
  });

  it("asks for a name and email before sending the demo request", () => {
    renderLanding();
    fireEvent.submit(document.getElementById("demo-form")!);
    expect(screen.getByText(/Add your name and a work email/)).toBeTruthy();
  });
});
