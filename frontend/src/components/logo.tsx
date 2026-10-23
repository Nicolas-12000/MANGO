export function Logo({ className = "size-16" }: { className?: string }) {
  return (
    <svg viewBox="0 0 72 72" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="mango-skin" x1="18%" y1="8%" x2="82%" y2="96%">
          <stop offset="0%" stopColor="#F8D36B" />
          <stop offset="38%" stopColor="#F08A24" />
          <stop offset="100%" stopColor="#C2410C" />
        </linearGradient>
        <linearGradient id="mango-leaf" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#8FBF55" />
          <stop offset="100%" stopColor="#2F6B2A" />
        </linearGradient>
      </defs>
      <path
        d="M40 20c9-13 24-13 30-3-11 0-20 6-24 15-2-5-4-9-6-12Z"
        fill="url(#mango-leaf)"
      />
      <path
        d="M44 16c8-5 16-4 20-1"
        fill="none"
        stroke="#245422"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
      <path
        d="M39 24c1.2-7 5-12 10-14"
        fill="none"
        stroke="#6B3A1F"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path
        d="M34 22c-14 2-24 14-24 28 0 14 12 24 28 22 16-2 28-16 26-32-2-14-16-22-30-18Z"
        fill="url(#mango-skin)"
      />
      <path
        d="M46 34c6 6 8 16 4 26"
        fill="none"
        stroke="#9A3412"
        strokeWidth="7"
        strokeLinecap="round"
        opacity="0.28"
      />
      <path
        d="M26 34c1 9 0 18-3 26"
        fill="none"
        stroke="#FFF6EE"
        strokeWidth="3.2"
        strokeLinecap="round"
        opacity="0.7"
      />
      <circle cx="24" cy="32" r="2.2" fill="#FFF6EE" opacity="0.85" />
    </svg>
  );
}
