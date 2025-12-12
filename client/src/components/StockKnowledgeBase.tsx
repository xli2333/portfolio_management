import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Upload, FileText, Bot, Trash2, Send, Paperclip, CheckSquare, Square, Download, Sparkles, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';

interface StockKnowledgeBaseProps {
    symbol: string;
    userId: string;
    onBack: () => void;
}

interface Document {
    id: string;
    filename: string;
    created_at: string;
    file_size: number;
    type: string;
    is_pinned?: boolean; // Added for pinning feature
}

interface Message {
    role: 'user' | 'model';
    text: string;
}

export function StockKnowledgeBase({ symbol, userId, onBack }: StockKnowledgeBaseProps) {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [model, setModel] = useState('gemini-2.5-flash');
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [generatingReport, setGeneratingReport] = useState(false);
    const [selectedMessageIndices, setSelectedMessageIndices] = useState<Set<number>>(new Set());

    // Ultra Deep Report states
    const [showUltraDeepModal, setShowUltraDeepModal] = useState(false);
    const [geminiApiKey, setGeminiApiKey] = useState('');
    const [customPrompt, setCustomPrompt] = useState('');
    const [ultraDeepLoading, setUltraDeepLoading] = useState(false);
    const [ultraDeepProgress, setUltraDeepProgress] = useState('');
    
    const fileInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    
    const STORAGE_KEY = `kb_chat_${symbol}`;
    const EXPIRY_KEY = `kb_chat_expiry_${symbol}`;

    useEffect(() => {
        fetchDocuments();
        loadHistory();
    }, [symbol]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadHistory = () => {
        const storedHistory = localStorage.getItem(STORAGE_KEY);
        const storedExpiry = localStorage.getItem(EXPIRY_KEY);

        if (storedHistory && storedExpiry) {
            const now = new Date().getTime();
            if (now > parseInt(storedExpiry)) {
                localStorage.removeItem(STORAGE_KEY);
                localStorage.removeItem(EXPIRY_KEY);
                setMessages([]);
            } else {
                setMessages(JSON.parse(storedHistory));
            }
        } else {
            setMessages([]);
        }
    };

    const saveHistory = (newMessages: Message[]) => {
        const now = new Date().getTime();
        const oneDay = 24 * 60 * 60 * 1000;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newMessages));
        if (!localStorage.getItem(EXPIRY_KEY)) {
             localStorage.setItem(EXPIRY_KEY, (now + oneDay).toString());
        }
    };

    const handleDownload = (docId: string, filename: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const link = document.createElement('a');
        link.href = `${apiBase}/api/knowledge/download?doc_id=${docId}`;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleTogglePin = async (docId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const res = await fetch(`${apiBase}/api/knowledge/toggle_pin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-ID': userId
                },
                body: JSON.stringify({ doc_id: docId })
            });
            if (!res.ok) throw new Error('Failed to toggle pin status');
            const data = await res.json();
            setDocuments(prevDocs =>
                prevDocs.map(doc =>
                    doc.id === docId ? { ...doc, is_pinned: data.is_pinned } : doc
                )
            );
        } catch (err) {
            console.error('Error toggling pin status:', err);
            alert('切换置顶状态失败');
        }
    };

    const fetchDocuments = async () => {
        try {
            const res = await fetch(`${apiBase}/api/knowledge/list?symbol=${symbol}`, {
                headers: { 'User-ID': userId }
            });
            const data = await res.json();
            if (Array.isArray(data)) {
                setDocuments(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        
        setUploading(true);
        const formData = new FormData();
        formData.append('file', e.target.files[0]);
        formData.append('symbol', symbol);

        try {
            const res = await fetch(`${apiBase}/api/knowledge/upload`, {
                method: 'POST',
                headers: { 'User-ID': userId },
                body: formData,
            });
            if (!res.ok) throw new Error('Upload failed');
            fetchDocuments();
        } catch (err) {
            alert('上传失败，请重试');
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async (docId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm('确定删除此文档吗？')) return;
        try {
            await fetch(`${apiBase}/api/knowledge/delete?doc_id=${docId}`, { 
                method: 'DELETE',
                headers: { 'User-ID': userId }
            });
            fetchDocuments();
            const newSelected = new Set(selectedIds);
            newSelected.delete(docId);
            setSelectedIds(newSelected);
        } catch (err) {
            console.error(err);
        }
    };

    const toggleSelection = (docId: string) => {
        const newSet = new Set(selectedIds);
        if (newSet.has(docId)) newSet.delete(docId);
        else newSet.add(docId);
        setSelectedIds(newSet);
    };

    const toggleMessageSelection = (index: number) => {
        const newSet = new Set(selectedMessageIndices);
        if (newSet.has(index)) newSet.delete(index);
        else newSet.add(index);
        setSelectedMessageIndices(newSet);
    };

    const handleSaveChat = async () => {
        if (selectedMessageIndices.size === 0) return;
        
        const selectedMsgs = messages.filter((_, idx) => selectedMessageIndices.has(idx));
        const formattedMsgs = selectedMsgs.map(m => `[${m.role.toUpperCase()}]: ${m.text}`);
        
        try {
            const res = await fetch(`${apiBase}/api/knowledge/save_chat`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'User-ID': userId
                },
                body: JSON.stringify({
                    symbol,
                    messages: formattedMsgs
                })
            });
            if (res.ok) {
                alert('对话已保存到知识库');
                setSelectedMessageIndices(new Set());
                fetchDocuments();
            } else {
                throw new Error('Save failed');
            }
        } catch (e) {
            alert('保存失败');
        }
    };

    const handleGenerateReport = async () => {
        if (generatingReport) return;
        setGeneratingReport(true);

        // Add a temporary system message to show status
        const loadingMsg: Message = { role: 'model', text: '正在进行深度研究并生成报告，请稍候（可能需要1-2分钟）...' };
        const tempMessages = [...messages, loadingMsg];
        setMessages(tempMessages);

        try {
            const res = await fetch(`${apiBase}/api/agent/generate_report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-ID': userId
                },
                body: JSON.stringify({
                    symbol: symbol,
                    model: model,
                    selected_file_ids: Array.from(selectedIds)
                })
            });

            if (!res.ok) throw new Error('Generation failed');
            const data = await res.json();

            // Replace loading message with success
            let successText = `**深度研究报告已生成**\n\n已自动保存至左侧文档列表：\
${data.file_record.filename}\
`;

            successText += `\n\n您现在可以勾选这些报告并针对其内容进行提问。`;

            const successMsg: Message = {
                role: 'model',
                text: successText
            };

            // Remove the last loading message and add success message
            const finalMessages = [...messages, successMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
            fetchDocuments(); // Refresh list to show new report

        } catch (e) {
            const errorMsg: Message = { role: 'model', text: '报告生成失败，请稍后重试。' };
            setMessages([...messages, errorMsg]);
        } finally {
            setGeneratingReport(false);
        }
    };

    const handleOpenUltraDeepModal = () => {
        // Set default prompt based on symbol type
        let defaultPrompt = '';
        if (symbol === 'MACRO') {
            defaultPrompt = '请分析2025年全球宏观经济形势，重点关注美联储货币政策、中国经济增长、地缘政治风险，并给出大类资产配置建议。';
        } else if (symbol === 'STRATEGY') {
            defaultPrompt = '请设计一个适合2025年市场环境的量化投资策略，包括因子选择、回测结果、风险管理方案。';
        } else {
            defaultPrompt = `请对${symbol}进行全面深度分析，包括公司基本面、竞争优势、财务质量、估值水平，并给出投资建议。`;
        }
        setCustomPrompt(defaultPrompt);
        setShowUltraDeepModal(true);
    };

    const handleGenerateUltraDeepReport = async () => {
        if (!geminiApiKey.trim()) {
            alert('请输入您的 Gemini API Key');
            return;
        }
        if (!customPrompt.trim()) {
            alert('请输入研究主题');
            return;
        }

        setUltraDeepLoading(true);
        setShowUltraDeepModal(false);
        setUltraDeepProgress('正在提交任务到 Google Deep Research...');

        // Add initial loading message
        const loadingMsg: Message = {
            role: 'model',
            text: '🚀 **顶级深度报告任务已提交**\n\n正在后台运行 Deep Research Agent。\n\n• 预计耗时：10-20 分钟\n• 您可以继续使用其他功能，报告生成后会自动出现。'
        };
        const tempMessages = [...messages, loadingMsg];
        setMessages(tempMessages);

        try {
            // Determine mode
            let mode = 'STOCK';
            if (symbol === 'MACRO') mode = 'MACRO';
            else if (symbol === 'STRATEGY') mode = 'STRATEGY';

            // 1. Start Task
            const res = await fetch(`${apiBase}/api/agent/generate_ultra_deep_report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-ID': userId
                },
                body: JSON.stringify({
                    symbol: symbol,
                    mode: mode,
                    custom_prompt: customPrompt,
                    gemini_api_key: geminiApiKey
                })
            });

            const startData = await res.json();
            if (!res.ok || startData.error) {
                throw new Error(startData.error || 'Failed to start task');
            }

            const taskId = startData.task_id;
            
            // 2. Poll Status
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`${apiBase}/api/agent/task_status/${taskId}`);
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === 'completed') {
                        clearInterval(pollInterval);
                        setUltraDeepLoading(false);
                        
                        // Success Message
                        const result = statusData.result;
                        let successText = `**✓ 顶级深度报告已完成**\n\n已自动保存至左侧文档列表：\
${result.file_record.filename}\
\n\n报告长度：${Math.round(result.report_length / 1000)}K 字符\
\n\n这是使用 Google 官方 Deep Research API 生成的超级深度报告。`;

                        const successMsg: Message = {
                            role: 'model',
                            text: successText
                        };

                        setMessages(prev => [...prev, successMsg]);
                        fetchDocuments(); // Refresh list

                    } else if (statusData.status === 'failed') {
                        clearInterval(pollInterval);
                        setUltraDeepLoading(false);
                        throw new Error(statusData.error || 'Unknown error');
                        
                    } else {
                        // Still processing
                        setUltraDeepProgress(statusData.progress || '正在进行深度研究...');
                    }
                } catch (err: any) {
                    // Handle polling errors (maybe retry or stop)
                    console.error("Polling error:", err);
                    // Don't clear interval immediately on network blip, but if error persists...
                    // For simplicity, we keep polling unless fatal
                    if (err.message.includes('Task not found')) {
                         clearInterval(pollInterval);
                         setUltraDeepLoading(false);
                         alert('任务丢失，请重试');
                    }
                }
            }, 5000); // Poll every 5 seconds

        } catch (e: any) {
            setUltraDeepLoading(false);
            const errorMsg: Message = {
                role: 'model',
                text: `❌ **任务启动失败**\n\n错误：${e.message}`
            };
            setMessages(prev => [...prev, errorMsg]);
        }
    };

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg: Message = { role: 'user', text: input };
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        saveHistory(updatedMessages);
        setInput('');
        setLoading(true);

        try {
            // Standard Chat History format
            const historyForApi = updatedMessages.slice(0, -1).map(m => ({
                role: m.role,
                parts: [m.text]
            }));

            const res = await fetch(`${apiBase}/api/chat`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'User-ID': userId
                },
                body: JSON.stringify({
                    symbol: symbol,
                    message: userMsg.text,
                    history: historyForApi,
                    // Extra params for RAG/Context
                    selected_file_ids: Array.from(selectedIds),
                    model: model
                })
            });

            if (!res.ok) throw new Error('Failed to send message');
            const data = await res.json();
            
            const aiMsg: Message = { role: 'model', text: data.reply };
            const finalMessages = [...updatedMessages, aiMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
        } catch (error) {
            const errorMsg: Message = { role: 'model', text: 'Error: Connection failed.' };
            const finalMessages = [...updatedMessages, errorMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
        } finally {
            setLoading(false);
        }
    };

    const formatSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    return (
        <div className="animate-in slide-in-from-right-8 duration-500 flex flex-col h-[calc(100vh-200px)]">
            {/* Top Bar */}
            <div className="flex justify-between items-center mb-6">
                <button 
                    onClick={onBack}
                    className="flex items-center gap-2 text-sm font-bold font-serif tracking-widest text-gray-400 hover:text-black transition-colors"
                >
                    <ArrowLeft size={16} /> 返回 AI 投顾中心
                </button>
                <div className="text-right">
                    <div className="text-4xl font-black font-mono tracking-tighter leading-none">{symbol}</div>
                    <div className="text-xs font-serif font-bold text-gray-400">KNOWLEDGE BASE</div>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
                {/* Left: Upload & Files */}
                <div className="col-span-4 flex flex-col gap-4 min-h-0">
                    {/* Upload Box */}
                    <div 
                        onClick={() => fileInputRef.current?.click()}
                        className={cn(
                            "bg-gray-50 border-2 border-dashed border-gray-300 rounded-none p-6 flex flex-col items-center justify-center text-gray-400 hover:bg-gray-100 hover:border-black hover:text-black transition-all cursor-pointer group shrink-0",
                            uploading && "opacity-50 pointer-events-none"
                        )}
                    >
                        <input 
                            type="file" 
                            ref={fileInputRef} 
                            onChange={handleUpload} 
                            accept=".pdf" 
                            className="hidden" 
                        />
                        <Upload size={32} className={cn("mb-2 group-hover:scale-110 transition-transform", uploading && "animate-bounce")} />
                        <div className="font-bold font-serif text-sm">{uploading ? '上传中...' : '上传 PDF 资料'}</div>
                    </div>

                    {/* File List */}
                    <div className="flex-1 border-2 border-black p-0 overflow-hidden flex flex-col bg-white">
                        <div className="p-3 border-b-2 border-gray-100 bg-gray-50 flex justify-between items-center">
                            <h3 className="font-bold font-serif text-sm flex items-center gap-2">
                                <FileText size={14} /> 文档列表 ({documents.length})
                            </h3>
                            <span className="text-[10px] text-neon-dark font-mono font-bold">
                                已选 {selectedIds.size}
                            </span>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto p-2 space-y-2">
                            {documents.length === 0 && (
                                <div className="text-center text-gray-300 text-xs mt-10">暂无文档</div>
                            )}
                            {documents.map(doc => {
                                const isSelected = selectedIds.has(doc.id);
                                return (
                                    <div 
                                        key={doc.id}
                                        onClick={() => toggleSelection(doc.id)}
                                        className={cn(
                                            "p-3 border flex items-start gap-3 cursor-pointer transition-all hover:shadow-md",
                                            isSelected ? "border-black bg-black text-white" : "border-gray-200 bg-white hover:border-gray-400"
                                        )}
                                    >
                                        <div className="mt-0.5">
                                            {isSelected ? <CheckSquare size={16} className="text-neon" /> : <Square size={16} className="text-gray-300" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className={cn("font-bold text-sm truncate", isSelected ? "text-white" : "text-black")}>
                                                {doc.filename}
                                            </div>
                                            <div className={cn("text-[10px] font-mono mt-1 flex justify-between", isSelected ? "text-gray-400" : "text-gray-400")}>
                                                <span>{formatSize(doc.file_size)}</span>
                                                <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-1">
                                            <button 
                                                onClick={(e) => handleTogglePin(doc.id, e)}
                                                className={cn("p-1 hover:text-black transition-colors", isSelected ? (doc.is_pinned ? "text-neon-dark hover:text-white" : "text-gray-400 hover:text-neon-dark") : (doc.is_pinned ? "text-neon-dark hover:text-black" : "text-gray-300"))}
                                                title={doc.is_pinned ? "取消置顶" : "置顶文档"}
                                            >
                                                {doc.is_pinned ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="lucide lucide-pin"><path d="M12 17v5"/><path d="M15 9.4L18.35 6.65a1 1 0 0 0 0-1.41l-2.19-2.19a1 1 0 0 0-1.41 0L12 4.6 8.65 1.25a1 1 0 0 0-1.41 0L5.05 3.44a1 1 0 0 0 0 1.41L8 8l-2 3-3 1v3h3l2 3h3z"/></svg> : <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="lucide lucide-pin"><path d="M12 17v5"/><path d="M15 9.4L18.35 6.65a1 1 0 0 0 0-1.41l-2.19-2.19a1 1 0 0 0-1.41 0L12 4.6 8.65 1.25a1 1 0 0 0-1.41 0L5.05 3.44a1 1 0 0 0 0 1.41L8 8l-2 3-3 1v3h3l2 3h3z"/></svg>}
                                            </button>
                                            <button 
                                                onClick={(e) => handleDownload(doc.id, doc.filename, e)}
                                                className={cn("p-1 hover:text-black transition-colors", isSelected ? "text-gray-400 hover:text-white" : "text-gray-300")}
                                                title="下载文档"
                                            >
                                                <Download size={14} />
                                            </button>
                                            <button 
                                                onClick={(e) => handleDelete(doc.id, e)}
                                                className={cn("p-1 hover:text-red-500 transition-colors", isSelected ? "text-gray-600" : "text-gray-300")}
                                                title="删除文档"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Right: Embedded AI Chat */}
                <div className="col-span-8 border-2 border-black flex flex-col bg-white relative shadow-lg h-full overflow-hidden">
                    {/* Chat Header / Controls */}
                    <div className="p-3 border-b-2 border-black bg-gray-50 flex justify-between items-center shrink-0">
                        <div className="flex items-center gap-2">
                            <Bot size={20} className="text-black" />
                            <span className="font-bold font-serif text-sm">AI 分析师</span>
                        </div>
                        <div className="flex gap-2 items-center">
                            {selectedMessageIndices.size > 0 && (
                                <button 
                                    onClick={handleSaveChat}
                                    className="bg-black text-white text-xs font-bold px-3 py-1 hover:bg-neon hover:text-black transition-colors flex items-center gap-1"
                                >
                                    <Paperclip size={12} /> 保存 ({selectedMessageIndices.size})
                                </button>
                            )}

                            <button
                                onClick={() => handleGenerateReport()}
                                disabled={generatingReport}
                                className={cn(
                                    "text-xs font-black uppercase tracking-wider px-3 py-1 transition-colors flex items-center gap-1",
                                    generatingReport ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-neon text-black hover:bg-neon-dim"
                                )}
                            >
                                {generatingReport ? "生成中..." : "生成深度研报"}
                            </button>

                            <button
                                onClick={handleOpenUltraDeepModal}
                                disabled={ultraDeepLoading}
                                className={cn(
                                    "text-xs font-black uppercase tracking-wider px-3 py-1 transition-colors flex items-center gap-1",
                                    ultraDeepLoading ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-black text-white hover:bg-gray-800 border-2 border-black"
                                )}
                                title="使用 Google 官方 Deep Research API 生成超级深度报告（10-20分钟）"
                            >
                                <Sparkles size={12} />
                                {ultraDeepLoading ? "生成中..." : "顶级深度报告"}
                            </button>

                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="bg-white border-2 border-gray-200 text-xs font-bold px-2 py-1 outline-none cursor-pointer hover:border-black transition-colors"
                            >
                                <option value="gemini-2.5-flash">Gemini 2.5 Flash (快速)</option>
                                <option value="gemini-2.5-pro">Gemini 2.5 Pro (深度)</option>
                            </select>
                        </div>
                    </div>
                    
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white">
                        {messages.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-gray-300 opacity-50">
                                <div className="text-6xl font-black font-serif mb-4">AI</div>
                                <p className="text-sm font-mono">选择左侧文档，开始深度分析...</p>
                            </div>
                        )}
                        {messages.map((msg, idx) => {
                            const isSelected = selectedMessageIndices.has(idx);
                            return (
                                <div key={idx} className={cn("flex w-full items-start gap-2", msg.role === 'user' ? "flex-row-reverse" : "")}>
                                    {/* Selection Checkbox */}
                                    <button 
                                        onClick={() => toggleMessageSelection(idx)}
                                        className="mt-2 text-gray-300 hover:text-black transition-colors"
                                    >
                                        {isSelected ? <CheckSquare size={16} className="text-neon-dark" /> : <Square size={16} />}
                                    </button>

                                    <div className={cn(
                                        "max-w-[85%] p-4 text-sm font-medium leading-relaxed shadow-sm overflow-hidden",
                                        msg.role === 'user' 
                                            ? "bg-black text-white" 
                                            : "bg-gray-50 border border-gray-100 text-gray-800"
                                    )}>
                                        <div className={cn(
                                            "prose prose-sm max-w-none break-words font-serif",
                                            msg.role === 'user' 
                                                ? "prose-invert prose-p:text-white prose-headings:text-white prose-strong:text-white" 
                                                : "prose-headings:font-black prose-headings:font-sans prose-strong:font-black prose-strong:text-black prose-li:marker:text-black"
                                        )}>
                                            <ReactMarkdown 
                                                components={{
                                                    strong: ({node, ...props}) => <span className="font-black bg-neon/20 px-1 rounded-sm" {...props} />,
                                                    h3: ({node, ...props}) => <h3 className="text-lg font-black mt-4 mb-2 border-l-4 border-neon pl-2" {...props} />,
                                                    h4: ({node, ...props}) => <h4 className="text-base font-bold mt-3 mb-1 uppercase tracking-wider" {...props} />,
                                                    li: ({node, ...props}) => <li className="my-1" {...props} />
                                                }}
                                            >
                                                {msg.text}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                        {loading && (
                            <div className="flex justify-start ml-6">
                                <div className="bg-gray-50 p-4 text-xs font-mono text-gray-500 animate-pulse border border-gray-100">
                                    {selectedIds.size > 0 ? `正在阅读 ${selectedIds.size} 份文档并思考...` : 'AI 正在思考...'}
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 border-t-2 border-black bg-white shrink-0">
                        {selectedIds.size > 0 && (
                            <div className="mb-2 flex items-center gap-1 text-[10px] font-bold text-neon-dark uppercase tracking-wider">
                                <Paperclip size={10} />
                                已附加 {selectedIds.size} 份资料作为上下文
                            </div>
                        )}
                        <div className="flex gap-2 relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                placeholder={selectedIds.size > 0 ? "基于选定资料提问..." : "输入问题..."}
                                className="flex-1 bg-gray-50 border-2 border-gray-200 px-4 py-3 text-sm focus:border-black focus:ring-0 outline-none transition-colors font-medium placeholder:text-gray-400"
                                autoFocus
                            />
                            <button 
                                onClick={sendMessage}
                                disabled={loading || !input.trim()}
                                className="bg-black text-white px-6 hover:bg-neon hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Ultra Deep Report Modal */}
            {showUltraDeepModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white border-4 border-black max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
                        {/* Header */}
                        <div className="bg-black text-white p-6 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Sparkles size={24} />
                                <h2 className="text-2xl font-black font-serif">顶级深度报告</h2>
                            </div>
                            <button
                                onClick={() => setShowUltraDeepModal(false)}
                                className="hover:bg-white hover:text-black transition-colors p-2 rounded"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 space-y-6">
                            {/* Info Banner */}
                            <div className="bg-neon border-2 border-black p-4">
                                <p className="text-sm font-bold font-mono">
                                    ⚡ 使用 Google 官方 Deep Research API 生成超级深度报告
                                </p>
                                <ul className="mt-2 text-xs font-mono space-y-1 opacity-80">
                                    <li>• 预计耗时：10-20 分钟</li>
                                    <li>• 报告长度：5000+ 字，包含大量数据引用</li>
                                    <li>• 需要您提供自己的 Gemini API Key</li>
                                </ul>
                            </div>

                            {/* API Key Input */}
                            <div className="space-y-2">
                                <label className="block text-sm font-bold font-mono">
                                    Gemini API Key *
                                </label>
                                <input
                                    type="password"
                                    value={geminiApiKey}
                                    onChange={(e) => setGeminiApiKey(e.target.value)}
                                    placeholder="AIzaSy..."
                                    className="w-full bg-gray-50 border-2 border-gray-300 px-4 py-3 text-sm focus:border-black focus:ring-0 outline-none transition-colors font-mono"
                                />
                                <p className="text-xs text-gray-500 font-mono">
                                    在 <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer" className="underline hover:text-black">Google AI Studio</a> 获取 API Key
                                </p>
                            </div>

                            {/* Custom Prompt Input */}
                            <div className="space-y-2">
                                <label className="block text-sm font-bold font-mono">
                                    研究主题 *
                                </label>
                                <textarea
                                    value={customPrompt}
                                    onChange={(e) => setCustomPrompt(e.target.value)}
                                    rows={8}
                                    placeholder="请输入您想深度研究的主题和关注点..."
                                    className="w-full bg-gray-50 border-2 border-gray-300 px-4 py-3 text-sm focus:border-black focus:ring-0 outline-none transition-colors font-medium resize-none"
                                />
                                <p className="text-xs text-gray-500 font-mono">
                                    提示：越详细的研究问题，生成的报告质量越高
                                </p>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={handleGenerateUltraDeepReport}
                                    className="flex-1 bg-black text-white py-3 px-6 font-black uppercase tracking-wider hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                                >
                                    <Sparkles size={16} />
                                    开始生成
                                </button>
                                <button
                                    onClick={() => setShowUltraDeepModal(false)}
                                    className="px-6 py-3 border-2 border-black font-black uppercase tracking-wider hover:bg-gray-100 transition-colors"
                                >
                                    取消
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Ultra Deep Loading Overlay */}
            {ultraDeepLoading && (
                <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
                    <div className="bg-white border-4 border-neon p-8 max-w-md shadow-[8px_8px_0px_0px_rgba(255,242,0,1)] animate-pulse">
                        <div className="flex items-center gap-4 mb-4">
                            <Sparkles size={32} className="text-black animate-spin" />
                            <h3 className="text-xl font-black font-serif">Deep Research 进行中...</h3>
                        </div>
                        <p className="text-sm font-mono text-gray-600 mb-4">
                            {ultraDeepProgress || '正在与 Google AI 通信...'}
                        </p>
                        <div className="bg-gray-200 h-2 overflow-hidden">
                            <div className="bg-black h-full w-1/2 animate-pulse"></div>
                        </div>
                        <p className="text-xs text-gray-500 font-mono mt-4 text-center">
                            预计需要 10-20 分钟，请耐心等待
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
