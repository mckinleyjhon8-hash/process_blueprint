import { DashboardClient } from "@/components/dashboard/DashboardClient";
import { SEED_FACTS, SEED_BRIEF_CLIENT } from "@/lib/seed";

export default function DashboardPage() {
  return <DashboardClient initialFacts={SEED_FACTS} seedBrief={SEED_BRIEF_CLIENT} />;
}
