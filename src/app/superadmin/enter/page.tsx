import { redirect } from "next/navigation";

export default function LegacyAdminEntry() {
  redirect("/login");
}
