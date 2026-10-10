import {
  FacebookIcon,
  InstagramIcon,
  MailIcon,
  MessageCircleIcon,
  TelegramIcon,
  TikTokIcon,
  WhatsAppIcon,
  XIcon,
} from "@/components/icons";
import { buildShareUrls, linkForChannel } from "@/lib/shareLinks";

const LINK_CHANNELS = [
  { key: "whatsapp", label: "WhatsApp", icon: WhatsAppIcon, bg: "bg-[#25D366]" },
  { key: "facebook", label: "Facebook", icon: FacebookIcon, bg: "bg-[#1877F2]" },
  { key: "x", label: "X", icon: XIcon, bg: "bg-navy-950" },
  { key: "telegram", label: "Telegram", icon: TelegramIcon, bg: "bg-[#229ED9]" },
  { key: "sms", label: "SMS", icon: MessageCircleIcon, bg: "bg-navy-600" },
  { key: "email", label: "Email", icon: MailIcon, bg: "bg-navy-600" },
] as const;

// Instagram and TikTok have no web share-by-URL scheme — the real-world
// pattern is to copy the link/caption and hand off to the app instead.
const COPY_ONLY_CHANNELS = [
  { key: "instagram", label: "Instagram", icon: InstagramIcon, bg: "bg-gradient-to-br from-fuchsia-500 to-amber-400" },
  { key: "tiktok", label: "TikTok", icon: TikTokIcon, bg: "bg-navy-950" },
] as const;

export function ShareChannels({
  link,
  message,
  onCopyOnly,
}: {
  link: string;
  message: string;
  onCopyOnly: (channelLabel: string) => void;
}) {
  const urls = buildShareUrls(link, message);

  return (
    <div className="grid grid-cols-4 gap-3">
      {LINK_CHANNELS.map((c) => (
        <a
          key={c.key}
          href={urls[c.key]}
          target="_blank"
          rel="noopener noreferrer"
          className={`flex flex-col items-center gap-1.5 rounded-2xl ${c.bg} py-3 text-white shadow-card transition hover:brightness-105`}
        >
          <c.icon className="h-5 w-5" />
          <span className="text-[11px] font-semibold">{c.label}</span>
        </a>
      ))}
      {COPY_ONLY_CHANNELS.map((c) => (
        <button
          key={c.key}
          type="button"
          onClick={() => {
            navigator.clipboard.writeText(`${message}\n\n${linkForChannel(link, c.key)}`);
            onCopyOnly(c.label);
          }}
          className={`flex flex-col items-center gap-1.5 rounded-2xl ${c.bg} py-3 text-white shadow-card transition hover:brightness-105`}
        >
          <c.icon className="h-5 w-5" />
          <span className="text-[11px] font-semibold">{c.label}</span>
        </button>
      ))}
    </div>
  );
}
