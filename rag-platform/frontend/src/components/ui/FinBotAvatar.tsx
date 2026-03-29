/** FinBot SVG Avatar — used in NavBar and AnswerCard */
export function FinBotAvatar({ size = 28, className = '' }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer hexagon */}
      <path
        d="M16 2L28 9V23L16 30L4 23V9L16 2Z"
        fill="url(#finbot-grad)"
        opacity="0.15"
      />
      <path
        d="M16 2L28 9V23L16 30L4 23V9L16 2Z"
        stroke="url(#finbot-grad)"
        strokeWidth="1.2"
        fill="none"
      />
      {/* Inner spark */}
      <path
        d="M16 8L19 14H25L20 18L22 24L16 20L10 24L12 18L7 14H13L16 8Z"
        fill="url(#finbot-grad)"
        opacity="0.9"
      />
      <defs>
        <linearGradient id="finbot-grad" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#E0CC8E" />
          <stop offset="50%" stopColor="#C9A84C" />
          <stop offset="100%" stopColor="#D4B86A" />
        </linearGradient>
      </defs>
    </svg>
  )
}
