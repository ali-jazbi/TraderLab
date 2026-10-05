import Dashboard from "@/components/dashboard";
import fixture from "@/data/canonical.json";
import type { Dataset } from "@/lib/types";

export default function Page() {
  return <Dashboard fixture={fixture as Dataset} />;
}
