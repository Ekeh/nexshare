import {
  CartIcon,
  HotelIcon,
  GraduationCapIcon,
  HomeIcon,
  ShieldIcon,
  HeartIcon,
  AppsIcon,
  TicketIcon,
  CarIcon,
  UtensilsIcon,
  BriefcaseIcon,
} from "@/components/icons";
import { Reveal } from "@/components/motion/Reveal";

const industries = [
  { label: "E-commerce Products", icon: CartIcon, bg: "bg-orange-50", fg: "text-orange-500" },
  { label: "Hotels & Travel", icon: HotelIcon, bg: "bg-sky-50", fg: "text-sky-500" },
  { label: "Education & Courses", icon: GraduationCapIcon, bg: "bg-emerald-50", fg: "text-emerald-500" },
  { label: "Real Estate", icon: HomeIcon, bg: "bg-rose-50", fg: "text-rose-500" },
  { label: "Insurance & Finance", icon: ShieldIcon, bg: "bg-cyan-50", fg: "text-cyan-500" },
  { label: "Health & Wellness", icon: HeartIcon, bg: "bg-amber-50", fg: "text-amber-500" },
  { label: "Software & Apps", icon: AppsIcon, bg: "bg-indigo-50", fg: "text-indigo-500" },
  { label: "Events & Tickets", icon: TicketIcon, bg: "bg-purple-50", fg: "text-purple-500" },
  { label: "Automotive", icon: CarIcon, bg: "bg-fuchsia-50", fg: "text-fuchsia-500" },
  { label: "Food & Restaurants", icon: UtensilsIcon, bg: "bg-red-50", fg: "text-red-500" },
  { label: "Professional Services", icon: BriefcaseIcon, bg: "bg-blue-50", fg: "text-blue-500" },
];

export function Industries() {
  return (
    <section className="bg-white pb-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <Reveal className="text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-navy-900 sm:text-4xl">
            Works for Every Industry
          </h2>
          <p className="mt-2 text-sm font-medium text-navy-400">
            Promote anything — products, services, bookings, subscriptions,
            leads and more.
          </p>
        </Reveal>

        <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {industries.map((ind, i) => (
            <Reveal key={ind.label} delay={i * 0.05} y={12}>
              <div
                className={`flex flex-col items-center justify-center gap-2 rounded-xl ${ind.bg} px-4 py-6 text-center transition hover:-translate-y-0.5 hover:shadow-card active:scale-95`}
              >
                <ind.icon className={`h-6 w-6 ${ind.fg}`} />
                <span className="text-xs font-semibold text-navy-800">
                  {ind.label}
                </span>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
