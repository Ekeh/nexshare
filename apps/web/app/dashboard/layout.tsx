import { AccountProvider } from "@/components/dashboard/AccountContext";
import { DashboardChrome } from "@/components/dashboard/DashboardChrome";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AccountProvider role="promoter">
      <DashboardChrome>{children}</DashboardChrome>
    </AccountProvider>
  );
}
