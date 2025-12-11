-- 创建股票元数据表
-- 用于存储 A 股名称映射，作为 CSV 文件的云端替代方案
CREATE TABLE IF NOT EXISTS public.stock_metadata (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market TEXT DEFAULT 'CN', -- CN for A-share
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 启用 RLS
ALTER TABLE public.stock_metadata ENABLE ROW LEVEL SECURITY;

-- 允许所有认证用户读取（用于查询名称）
CREATE POLICY "Allow public read stock metadata"
    ON public.stock_metadata FOR SELECT
    USING (true);

-- 允许服务角色或特定用户写入（为了安全，暂时设为仅认证用户可写，或者您可以手动在 Dashboard 导入）
-- 这里为了方便脚本上传，允许认证用户插入。
CREATE POLICY "Allow authenticated insert stock metadata"
    ON public.stock_metadata FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');
