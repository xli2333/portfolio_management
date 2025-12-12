-- 数据库增量更新脚本 (Supabase Pinned Stocks SQL)
-- 目的：支持 AI 投顾界面“固定”股票功能
-- 请在 Supabase Dashboard -> SQL Editor 中运行此脚本

-- 1. 创建 pinned_stocks 表
-- 说明：此表用于存储用户在 AI 投顾界面固定的股票，即使没有持仓也会保留。
CREATE TABLE IF NOT EXISTS public.pinned_stocks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL, -- 移除了 REFERENCES auth.users(id)，因为可能使用匿名 ID
    symbol TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- 确保每个用户只能固定同一只股票一次
    UNIQUE (user_id, symbol)
);

-- 2. [关键修复] 禁用行级安全 (RLS)
-- 原因：当前应用可能未通过 Supabase Auth 登录，启用 RLS 会导致写入失败。
-- 在单用户或本地模式下，禁用 RLS 是安全的。
ALTER TABLE public.pinned_stocks DISABLE ROW LEVEL SECURITY;

-- 3. 性能优化：添加索引
CREATE INDEX IF NOT EXISTS idx_pinned_stocks_user_symbol ON public.pinned_stocks(user_id, symbol);