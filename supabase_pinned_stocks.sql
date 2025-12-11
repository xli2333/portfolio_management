-- 数据库增量更新脚本 (Supabase Pinned Stocks SQL)
-- 目的：支持 AI 投顾界面“固定”股票功能
-- 请在 Supabase Dashboard -> SQL Editor 中运行此脚本

-- 1. 创建 pinned_stocks 表
-- 说明：此表用于存储用户在 AI 投顾界面固定的股票，即使没有持仓也会保留。
CREATE TABLE IF NOT EXISTS public.pinned_stocks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- 确保每个用户只能固定同一只股票一次
    UNIQUE (user_id, symbol)
);

-- 2. 启用行级安全 (RLS)
ALTER TABLE public.pinned_stocks ENABLE ROW LEVEL SECURITY;

-- 3. 定义行级安全策略
-- 允许用户查看和插入自己的固定股票
BEGIN;
  DROP POLICY IF EXISTS "Users can view own pinned stocks" ON public.pinned_stocks;
  DROP POLICY IF EXISTS "Users can insert own pinned stocks" ON public.pinned_stocks;
  DROP POLICY IF EXISTS "Users can delete own pinned stocks" ON public.pinned_stocks;
  
  CREATE POLICY "Users can view own pinned stocks" 
      ON public.pinned_stocks FOR SELECT 
      USING (auth.uid() = user_id);

  CREATE POLICY "Users can insert own pinned stocks" 
      ON public.pinned_stocks FOR INSERT 
      WITH CHECK (auth.uid() = user_id);

  CREATE POLICY "Users can delete own pinned stocks" 
      ON public.pinned_stocks FOR DELETE 
      USING (auth.uid() = user_id);
COMMIT;

-- 4. 性能优化：添加索引
CREATE INDEX IF NOT EXISTS idx_pinned_stocks_user_symbol ON public.pinned_stocks(user_id, symbol);
