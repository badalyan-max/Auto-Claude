import { useState } from 'react';
import { X, MessageSquare, Plus } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import type { InsightsTab } from '../stores/insights-store';

interface InsightsTabBarProps {
  tabs: InsightsTab[];
  activeTabId: string | null;
  onTabSelect: (sessionId: string) => void;
  onTabClose: (sessionId: string) => void;
  onNewTab: () => void;
}

export function InsightsTabBar({
  tabs,
  activeTabId,
  onTabSelect,
  onTabClose,
  onNewTab
}: InsightsTabBarProps) {
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);

  if (tabs.length === 0) {
    return null;
  }

  const handleTabClose = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    onTabClose(sessionId);
  };

  const truncateTitle = (title: string, maxLength: number = 25) => {
    if (title.length <= maxLength) return title;
    return title.substring(0, maxLength - 3) + '...';
  };

  return (
    <div className="flex items-center gap-1 border-b border-border bg-muted/30 px-2 py-1 overflow-x-auto">
      {tabs.map((tab) => {
        const isActive = tab.sessionId === activeTabId;
        const isHovered = tab.sessionId === hoveredTab;

        return (
          <div
            key={tab.sessionId}
            className={cn(
              'group relative flex items-center gap-2 rounded-md px-3 py-1.5 text-sm cursor-pointer transition-colors min-w-[120px] max-w-[200px]',
              isActive
                ? 'bg-background text-foreground shadow-sm border border-border'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
            onClick={() => onTabSelect(tab.sessionId)}
            onMouseEnter={() => setHoveredTab(tab.sessionId)}
            onMouseLeave={() => setHoveredTab(null)}
            title={tab.title}
          >
            <MessageSquare className={cn(
              'h-3.5 w-3.5 shrink-0',
              isActive ? 'text-primary' : 'text-muted-foreground'
            )} />
            <span className="truncate flex-1">{truncateTitle(tab.title)}</span>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                'h-4 w-4 p-0 shrink-0 transition-opacity',
                isActive || isHovered ? 'opacity-100' : 'opacity-0'
              )}
              onClick={(e) => handleTabClose(e, tab.sessionId)}
              title="Close tab"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        );
      })}

      {/* New Tab Button */}
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0 text-muted-foreground hover:text-foreground"
        onClick={onNewTab}
        title="New chat tab"
      >
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  );
}
