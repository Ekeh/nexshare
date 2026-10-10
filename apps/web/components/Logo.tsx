export function LogoMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} fill="none">
      <rect width="40" height="40" rx="10" fill="url(#nexshare-mark-grad)" />
      <path
        d="M11 28V13.6a1.2 1.2 0 0 1 2.05-.85L26 25.5"
        stroke="white"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M26 13v9.5"
        stroke="#F5C518"
        strokeWidth="3.2"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M21.5 17 26 12.5 30.5 17"
        stroke="#F5C518"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <defs>
        <linearGradient
          id="nexshare-mark-grad"
          x1="0"
          y1="0"
          x2="40"
          y2="40"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#3B62F5" />
          <stop offset="1" stopColor="#101a4d" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export function Logo({
  tagline = true,
  dark = false,
  className,
}: {
  tagline?: boolean;
  dark?: boolean;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2.5 ${className ?? ""}`}>
      <LogoMark />
      <div className="leading-tight">
        <div className="text-lg font-extrabold tracking-tight">
          <span className={dark ? "text-navy-900" : "text-white"}>Nex</span>
          <span className="text-gold-500">Share</span>
        </div>
        {tagline && (
          <div
            className={`text-[10px] font-medium tracking-wide ${
              dark ? "text-navy-600" : "text-white/60"
            }`}
          >
            Promote Anything. Earn From Results.
          </div>
        )}
      </div>
    </div>
  );
}
