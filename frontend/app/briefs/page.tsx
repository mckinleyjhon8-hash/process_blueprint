import { redirect } from "next/navigation";

// /briefs moved to /runs in the IA redesign — keep old links working.
export default function BriefsRedirect() {
  redirect("/runs");
}
