import { cn } from '../lib/utils';

interface PixelCardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  titleIcon?: React.ReactNode;
  noCorners?: boolean;
}

export function PixelCard({ children, className, title, titleIcon, noCorners }: PixelCardProps) {
  return (
    <div
      className={cn(
        'bg-[#141722] border-[3px] border-[#0e1119] relative',
        !noCorners && 'pixel-corners',
        className
      )}
      style={{
        boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.03), 4px 4px 0 rgba(0,0,0,0.3)',
      }}
    >
      {title && (
        <div className="px-4 py-3 border-b-2 border-[#0e1119] flex items-center gap-2">
          {titleIcon && <span className="text-[#ffd700]">{titleIcon}</span>}
          <h3 className="text-sm font-bold text-[#ffd700] tracking-wide pixel-title">
            {title}
          </h3>
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
