-- 数据库增量更新脚本 (Supabase Update SQL)
-- 目的：支持“宏观/策略”顾问功能，确保知识库表结构兼容
-- 请在 Supabase Dashboard -> SQL Editor 中运行此脚本

-- 1. [核心表检查] 创建 knowledge_documents 表
-- 说明：如果表已存在，此命令会被忽略。
-- 新的“宏观(MACRO)”和“策略(STRATEGY)”研报将复用此表，存储在 symbol 字段中。
CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    file_type TEXT
);

-- 2. [关键兼容性] 调整 symbol 字段类型
-- 说明：确保 symbol 字段是 TEXT 类型。
-- 如果之前的表结构将 symbol 限制为 VARCHAR(6)（仅够存股票代码），
-- 这一步将扩展它以支持 "STRATEGY"（8个字符）等长标签，防止报错。
ALTER TABLE public.knowledge_documents ALTER COLUMN symbol TYPE TEXT;

-- 3. [安全设置] 启用行级安全 (RLS)
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;

-- 4. [权限刷新] 重置并应用访问策略
-- 说明：先删除旧策略再重建，确保权限逻辑是最新的。
-- 效果：保证用户只能看到自己上传的宏观/策略报告，保护隐私。
BEGIN;
  DROP POLICY IF EXISTS "Users can view own documents" ON public.knowledge_documents;
  DROP POLICY IF EXISTS "Users can insert own documents" ON public.knowledge_documents;
  DROP POLICY IF EXISTS "Users can delete own documents" ON public.knowledge_documents;
  
  CREATE POLICY "Users can view own documents" 
      ON public.knowledge_documents FOR SELECT 
      USING (auth.uid() = user_id);

  CREATE POLICY "Users can insert own documents" 
      ON public.knowledge_documents FOR INSERT 
      WITH CHECK (auth.uid() = user_id);

  CREATE POLICY "Users can delete own documents" 
      ON public.knowledge_documents FOR DELETE 
      USING (auth.uid() = user_id);
COMMIT;

-- 5. [性能优化] 补充索引
-- 说明：加快对 MACRO/STRATEGY 标签的检索速度。
CREATE INDEX IF NOT EXISTS idx_knowledge_symbol ON public.knowledge_documents(symbol);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON public.knowledge_documents(user_id);
