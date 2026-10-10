import {
  UserPlusIcon,
  SearchIcon,
  ShareIcon,
  ActionIcon,
  CoinIcon,
  ArrowRightIcon,
} from "@/components/icons";
import { Reveal } from "@/components/motion/Reveal";

const steps = [
  {
    icon: UserPlusIcon,
    title: "1. Join",
    body: "Sign up for free as a Promoter or Business.",
  },
  {
    icon: SearchIcon,
    title: "2. Find Offers",
    body: "Choose from thousands of offers to promote.",
  },
  {
    icon: ShareIcon,
    title: "3. Share",
    body: "Share on your social media, website or anywhere.",
  },
  {
    icon: ActionIcon,
    title: "4. People Take Action",
    body: "They buy, book, sign up or submit a lead.",
  },
  {
    icon: CoinIcon,
    title: "5. Earn Real Money",
    body: "Get paid when results are confirmed.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-white py-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <Reveal className="text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-navy-900 sm:text-4xl">
            How NexShare Works
          </h2>
          <p className="mt-2 text-sm font-medium text-navy-400">
            Simple. Powerful. Profitable.
          </p>
        </Reveal>

        <div className="mt-12 flex flex-col items-stretch gap-4 lg:flex-row lg:items-center lg:justify-between">
          {steps.map((step, i) => (
            <div key={step.title} className="flex items-center lg:contents">
              <Reveal delay={i * 0.08} className="flex flex-1">
                <div className="flex flex-1 flex-col items-center gap-3 rounded-2xl bg-slate-50 px-5 py-7 text-center">
                  <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#3B62F5] to-navy-900 text-white shadow-card">
                    <step.icon className="h-6 w-6" />
                  </span>
                  <h3 className="text-sm font-bold text-navy-900">{step.title}</h3>
                  <p className="text-xs leading-relaxed text-navy-400">{step.body}</p>
                </div>
              </Reveal>
              {i < steps.length - 1 && (
                <ArrowRightIcon className="mx-2 hidden h-5 w-5 shrink-0 text-navy-200 lg:block" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
