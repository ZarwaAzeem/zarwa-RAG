const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

function Icon({ children, size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...stroke}>
      {children}
    </svg>
  )
}

export const BackIcon = () => (
  <Icon>
    <path d="M14.5 5.5 8 12l6.5 6.5" />
  </Icon>
)

export const NewChatIcon = () => (
  <Icon>
    <path d="M12 5v14M5 12h14" />
  </Icon>
)

export const SendIcon = () => (
  <Icon>
    <path d="M12 19V5M5.5 11.5 12 5l6.5 6.5" />
  </Icon>
)

export const MicIcon = () => (
  <Icon>
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" />
  </Icon>
)

export const ChatIcon = () => (
  <Icon>
    <path d="M20 11.5a7.5 7.5 0 0 1-11 6.6L4 19.5l1.4-4.3A7.5 7.5 0 1 1 20 11.5Z" />
  </Icon>
)

export const UploadIcon = () => (
  <Icon size={30}>
    <path d="M12 16V5M7.5 9.5 12 5l4.5 4.5M5 19h14" />
  </Icon>
)

/* Four-point sparkle used on the hero card, drawn with a champagne-to-rose sheen. */
export function Sparkle({ className }) {
  return (
    <svg className={className} viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <linearGradient id="sparkle-fill" x1="0.15" y1="0.1" x2="0.85" y2="0.9">
          <stop offset="0" stopColor="#f8dcc0" />
          <stop offset="0.5" stopColor="#e08a9d" />
          <stop offset="1" stopColor="#a8324f" />
        </linearGradient>
      </defs>
      <path
        fill="url(#sparkle-fill)"
        d="M50 2C54 30 70 46 98 50 70 54 54 70 50 98 46 70 30 54 2 50 30 46 46 30 50 2Z"
      />
    </svg>
  )
}
