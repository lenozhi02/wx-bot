import { cn } from '../lib/utils';

interface PixelBadgeProps {
  children: React.ReactNode;
  color?: 'gold' | 'green' | 'red' | 'blue' | 'amber' | 'purple' | 'slate';
  className?: string;
}

const colorMap: Record<string, string> = {
  gold: 'bg-[#ffd700]/10 text-[#ffd700] border-[#ffd700]/30',
  green: 'bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]/30',
  red: 'bg-[#e94560]/10 text-[#e94560] border-[#e94560]/30',
  blue: 'bg-[#3b82f6]/10 text-[#3b82f6] border-[#3b82f6]/30',
  amber: 'bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30',
  purple: 'bg-[#a855f7]/10 text-[#a855f7] border-[#a855f7]/30',
  slate: 'bg-[#1f2937] text-[#94a3b8] border-[#334155]',
};

export function PixelBadge({ children, color = 'slate', className }: PixelBadgeProps) {
  return (
    <span
      className={cn(
        'inline-block px-2 py-0.5 text-[11px] font-bold border-[2px] tracking-wide',
        colorMap[color],
        className
      )}
    >
      {children}
    </span>
  );
}
