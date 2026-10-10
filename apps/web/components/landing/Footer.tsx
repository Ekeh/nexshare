import Link from "next/link";
import { Logo } from "@/components/Logo";
import {
  FacebookIcon,
  XIcon,
  InstagramIcon,
  TikTokIcon,
  YoutubeIcon,
} from "@/components/icons";
import { Reveal } from "@/components/motion/Reveal";

const columns = [
  {
    title: "Company",
    links: ["About Us", "Our Mission", "Careers", "Contact"],
  },
  {
    title: "Opportunities",
    links: ["For Promoters", "For Businesses", "Referral Program", "Success Stories"],
  },
  {
    title: "Resources",
    links: ["Blog", "Help Center", "Training", "API Docs"],
  },
  {
    title: "Support",
    links: ["Live Chat", "Email Us", "Community", "Report Fraud"],
  },
];

export function Footer() {
  return (
    <footer className="bg-navy-950 pt-14">
      <div className="mx-auto max-w-7xl px-6 pb-8 lg:px-10">
        <Reveal className="grid grid-cols-2 gap-10 pb-10 sm:grid-cols-3 lg:grid-cols-6">
          <div className="col-span-2 sm:col-span-3 lg:col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm text-white/50">
              A universal performance-commerce network connecting businesses,
              promoters and customers across Africa.
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-bold text-white">{col.title}</h4>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((l) => (
                  <li key={l}>
                    <Link
                      href="#"
                      className="text-sm text-white/50 transition hover:text-white"
                    >
                      {l}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </Reveal>

        <div className="flex flex-col gap-6 border-t border-white/10 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4 text-white/70">
            {[FacebookIcon, XIcon, InstagramIcon, TikTokIcon, YoutubeIcon].map(
              (Icon, i) => (
                <Link
                  key={i}
                  href="#"
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20 active:scale-90"
                >
                  <Icon className="h-4 w-4" />
                </Link>
              ),
            )}
          </div>
          <form className="flex items-center gap-3">
            <label htmlFor="newsletter" className="text-xs text-white/50">
              Subscribe to our newsletter
            </label>
            <input
              id="newsletter"
              type="email"
              placeholder="Your email"
              className="w-44 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs text-white placeholder:text-white/40 focus:outline-none focus:ring-1 focus:ring-gold-500"
            />
            <button
              type="submit"
              className="rounded-full bg-cta-gradient px-4 py-2 text-xs font-bold text-navy-900"
            >
              Subscribe
            </button>
          </form>
        </div>

        <p className="border-t border-white/10 pt-6 text-center text-xs text-white/40">
          © 2026 NexShare. All rights reserved. | Privacy | Terms | Compliance
        </p>
      </div>
    </footer>
  );
}
