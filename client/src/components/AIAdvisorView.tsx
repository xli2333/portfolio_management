import { Pin } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface AIAdvisorProps {
    holdings: any[];
    onNavigate: (symbol: string) => void;
    onRefresh: () => void;
    onUpdatePinStatus: (symbol: string, isPinned: boolean) => void;
    userId: string;
}

export function AIAdvisorView({ holdings, onNavigate, onRefresh, onUpdatePinStatus, userId }: AIAdvisorProps) {
    const [pinning, setPinning] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000';

    const handleTogglePin = async (symbol: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (pinning) return;

        setPinning(symbol);
        setErrorMessage(null);

        // Create an AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 seconds timeout

        try {
            const res = await fetch(`${apiBase}/api/portfolio/toggle_pin`, {
                method: 'POST',
                headers: {
                    'User-ID': userId,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbol }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Parse response body
            const data = await res.json();

            // Check for errors in response
            if (!res.ok || data.error || data.status === 'error') {
                const errorMsg = data.error || data.msg || `操作失败 (${res.status})`;
                setErrorMessage(errorMsg);
                console.error("Pin toggle failed:", errorMsg);
                return;
            }

            // Success - update local state instead of full refresh
            if (data.status === 'success' && data.is_pinned !== undefined) {
                onUpdatePinStatus(symbol, data.is_pinned);
            } else {
                // Fallback to full refresh if response format is unexpected
                onRefresh();
            }

        } catch (err: any) {
            clearTimeout(timeoutId);

            if (err.name === 'AbortError') {
                setErrorMessage('请求超时，请检查网络连接');
            } else {
                setErrorMessage('网络错误，请稍后重试');
            }
            console.error("Pin toggle failed:", err);
        } finally {
            setPinning(null);
        }
    };

    // Sort: Pinned first, then by Value (desc)
    const sortedHoldings = [...holdings].sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        return (b.market_value || 0) - (a.market_value || 0);
    });

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="mb-12 border-b-4 border-black pb-6">
                <h2 className="text-3xl font-black font-serif tracking-tighter">AI 投顾中心 (Knowledge Base)</h2>
                <p className="text-gray-500 font-mono mt-2">智能分析 / 研报生成 / 深度问答</p>
            </div>

            {/* Error Message Display */}
            {errorMessage && (
                <div className="mb-6 p-4 bg-red-50 border-2 border-red-600 text-red-600 font-mono text-sm flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-300">
                    <span>⚠️ {errorMessage}</span>
                    <button
                        onClick={() => setErrorMessage(null)}
                        className="ml-4 text-red-600 hover:text-red-800 font-bold"
                    >
                        ✕
                    </button>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Fixed Card: Macro View */}
                <div 
                    onClick={() => onNavigate('MACRO')}
                    className="border-2 border-black p-6 bg-gray-50 hover:bg-black hover:text-white transition-all cursor-pointer group relative overflow-hidden"
                >
                    <div className="relative z-10">
                        <div className="text-2xl font-black font-serif mb-2">宏观视野 (Macro)</div>
                        <div className="text-sm font-mono opacity-70 mb-4 group-hover:opacity-100">全球经济 / 政策解读 / 宏观趋势</div>
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-t border-current pt-4 opacity-50 group-hover:opacity-100">
                            进入分析室 <span>→</span>
                        </div>
                    </div>
                    <div className="absolute -bottom-4 -right-4 text-9xl font-black opacity-5 group-hover:opacity-10 select-none">
                        M
                    </div>
                </div>

                {/* Fixed Card: Strategy View */}
                <div 
                    onClick={() => onNavigate('STRATEGY')}
                    className="border-2 border-black p-6 bg-gray-50 hover:bg-black hover:text-white transition-all cursor-pointer group relative overflow-hidden"
                >
                    <div className="relative z-10">
                        <div className="text-2xl font-black font-serif mb-2">策略精选 (Strategy)</div>
                        <div className="text-sm font-mono opacity-70 mb-4 group-hover:opacity-100">资产配置 / 仓位管理 / 投资方法论</div>
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-t border-current pt-4 opacity-50 group-hover:opacity-100">
                            进入决策室 <span>→</span>
                        </div>
                    </div>
                    <div className="absolute -bottom-4 -right-4 text-9xl font-black opacity-5 group-hover:opacity-10 select-none">
                        S
                    </div>
                </div>

                {/* Individual Holdings */}
                {sortedHoldings.map(h => (
                    <div 
                        key={h.symbol}
                        onClick={() => onNavigate(h.symbol)}
                        className={cn(
                            "border-2 border-black p-6 transition-all cursor-pointer group relative overflow-hidden",
                            h.is_pinned ? "bg-white ring-4 ring-gray-100 ring-offset-2" : "bg-white hover:bg-black hover:text-white"
                        )}
                    >
                        {/* Pin Button */}
                        <button
                            onClick={(e) => handleTogglePin(h.symbol, e)}
                            disabled={pinning === h.symbol}
                            className={cn(
                                "absolute top-4 right-4 z-20 p-2 rounded-full transition-all hover:scale-110 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50",
                                h.is_pinned ? "text-black bg-neon shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "text-gray-300 hover:text-black hover:bg-gray-100",
                                pinning === h.symbol && "animate-pulse"
                            )}
                            title={pinning === h.symbol ? "处理中..." : (h.is_pinned ? "取消固定" : "固定至前排")}
                        >
                            <Pin size={16} className={cn(h.is_pinned && "fill-current")} />
                        </button>

                        <div className="relative z-10">
                            <div className="flex items-baseline gap-2 mb-2">
                                <div className="text-2xl font-black font-mono">{h.symbol}</div>
                                {h.shares === 0 && h.is_pinned && (
                                    <span className="text-[10px] bg-gray-200 text-gray-500 px-1 py-0.5 rounded font-bold">
                                        已清仓
                                    </span>
                                )}
                            </div>
                            <div className={cn("text-sm font-serif opacity-70 mb-4 group-hover:opacity-100", h.is_pinned ? "text-black" : "")}>
                                {h.name}
                            </div>
                            <div className={cn("flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-t border-current pt-4 opacity-50 group-hover:opacity-100", h.is_pinned ? "text-black" : "")}>
                                进入知识库 <span>→</span>
                            </div>
                        </div>
                        {/* Decorative background element */}
                        <div className="absolute -bottom-4 -right-4 text-9xl font-black opacity-5 group-hover:opacity-10 select-none">
                            AI
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
