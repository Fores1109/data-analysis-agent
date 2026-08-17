"""分层记忆端到端验证（真实 LLM，需要 .env 配置 DEEPSEEK_API_KEY）。

验证：多轮对话触发滚动摘要 + 长期记忆检索让 Agent 跨轮引用历史结论。
运行：python tests/test_agent_memory_e2e.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import build_agent
from app.data_source import load_file


def show_ctx(tag, agent):
    ctx = agent._memory.build_context("（查看当前记忆状态）")
    print(f"--- [{tag}] 记忆上下文 ---")
    print(ctx if ctx else "（空）")
    print(f"--- 长期记忆文档数: {len(agent._memory.vector)} / 工作记忆轮数: {agent._memory.summary.working_rounds_count} / 摘要: {'有' if agent._memory.summary.summary else '无'} ---")


def main():
    df = load_file("data/sample_sales.csv")
    # 小阈值：3 轮即触发摘要，方便验证
    agent = build_agent(df, memory_kwargs={"working_rounds": 2, "summarize_at": 3, "top_k": 2})

    questions = [
        "哪个月销售额最高？给出具体数值。",
        "上海的总销售额是多少？",
        "广州卖得最好的品类是什么？",
        "北京和广州谁销售额更高？",
        "我之前问过的，销售额最高的那个月具体是多少钱？",   # 验证跨轮检索引用
    ]
    for i, q in enumerate(questions, 1):
        print(f"\n===== 第 {i} 轮：{q} =====", flush=True)
        r = agent.invoke({"input": q})
        print(r["output"], flush=True)
        if i in (3, 4):
            show_ctx(f"第 {i} 轮后", agent)

    print("\n===== 记忆验证完成 =====")


if __name__ == "__main__":
    main()
