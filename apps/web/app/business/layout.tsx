import { AccountProvider } from "@/components/dashboard/AccountContext";
import { BusinessChrome } from "@/components/business/BusinessChrome";

export default function BusinessLayout({ children }: { children: React.ReactNode }) {
  return (
    <AccountProvider role="business">
      <BusinessChrome>{children}</BusinessChrome>
    </AccountProvider>
  );
}
