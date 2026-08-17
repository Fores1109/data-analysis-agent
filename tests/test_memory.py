"""分层记忆单元测试（不调真实 LLM）：长期检索 / 工作记忆 / 滚动摘要（FakeLLM）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory import AgentMemory, SummaryMemory, VectorMemory


class _Resp:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """最小 fake：invoke 返回固定内容，用于测试摘要路径。"""

    def __init__(self, content="（测试摘要：本月销售额最高为 1 月 124,048 元）"):
        self._content = content

    def invoke(self, prompt):
        return _Resp(self._content)


def main():
    ok = []

    # ---- 1. 长期记忆：中文语义检索 ----
    vm = VectorMemory(top_k=2)
    vm.add("问：哪个月销售额最高？\n答：1 月最高，销售额 124,048 元。")
    vm.add("问：哪个城市贡献最大？\n答：上海 91,340 元。")
    vm.add("问：哪个品类销量最好？\n答：食品饮料。")
    hits = vm.search("销售额最高的月份是几月？")
    ok.append(("中文检索命中相关结论", len(hits) > 0 and "1 月" in hits[0]["text"]))
    ok.append(("检索按相似度排序", len(hits) >= 2 and hits[0]["score"] >= hits[1]["score"]))
    ok.append(("检索带分数", all("score" in h for h in hits)))
    empty = VectorMemory().search("任意")
    ok.append(("空库检索安全返回", empty == []))

    # ---- 2. 工作记忆：保留最近 N 轮 ----
    sm = SummaryMemory(llm=FakeLLM(), summarize_at=8, working_rounds=6)
    for i in range(8):
        sm.add(f"问题{i}", f"回答{i}")
    ok.append(("工作记忆保留 8 轮（未触发摘要，8 不 > 8）", sm.working_rounds_count == 8))
    sm.add("问题8", "回答8")  # 第 9 轮触发滚动摘要
    ok.append(("触发摘要后工作记忆裁剪到 6 轮", sm.working_rounds_count == 6))
    ok.append(("滚动摘要已生成", "测试摘要" in sm.summary))

    # ---- 3. 滚动摘要内容：旧摘要 + 溢出对话 ----
    sm2 = SummaryMemory(llm=FakeLLM(content="NEW_SUMMARY"), summarize_at=3, working_rounds=2)
    sm2.add("q1", "a1")
    sm2.add("q2", "a2")
    sm2.add("q3", "a3")
    ok.append(("3 轮未触发（3 不 > 3）", sm2.summary == ""))
    sm2.add("q4", "a4")  # 第 4 轮触发第一次摘要
    ok.append(("第一次摘要生成", sm2.summary == "NEW_SUMMARY"))
    ok.append(("溢出轮次被裁剪（保留最近 2 轮）", sm2.working_rounds_count == 2))
    sm2.add("q5", "a5")
    sm2.add("q6", "a6")
    sm2.add("q7", "a7")  # 第 7 轮触发第二次（旧摘要并入后再压缩）
    ok.append(("摘要滚动更新（旧摘要并入后再次压缩）", sm2.summary == "NEW_SUMMARY"))

    # ---- 4. AgentMemory 组合上下文 ----
    mem = AgentMemory(llm=FakeLLM(), working_rounds=6, summarize_at=3, top_k=2)
    mem.remember("哪个月销售额最高？", "1 月最高 124,048 元")
    mem.remember("哪个城市贡献最大？", "上海 91,340 元")
    mem.remember("销量最好的品类？", "食品饮料")
    mem.remember("复购率是多少？", "复购率 12%")
    ctx = mem.build_context("销售额最高的月份？")
    ok.append(("上下文包含检索结论", "124,048" in ctx))
    ok.append(("上下文包含历史摘要", "历史对话摘要" in ctx))
    ok.append(("上下文包含最近对话", "最近对话" in ctx))
    ctx_irrelevant = mem.build_context("画一个柱状图")
    ok.append(("无关查询也返回上下文（含摘要）", "历史对话摘要" in ctx_irrelevant))

    # ---- 5. 关闭记忆 ----
    mem_off = AgentMemory(llm=FakeLLM(), enabled=False)
    mem_off.remember("q", "a")
    ok.append(("enabled=False 不产生上下文", mem_off.build_context("q") == ""))

    # ---- 6. 记忆上限 ----
    vm2 = VectorMemory(max_docs=3)
    for i in range(5):
        vm2.add(f"结论{i}")
    ok.append(("长期记忆上限截断（保留最新 3 条）", len(vm2) == 3))

    print("===== 分层记忆测试 =====")
    fails = 0
    for name, passed in ok:
        print(f"{'✓' if passed else '❌'} {name}")
        if not passed:
            fails += 1
    print(f"\n结果：{len(ok) - fails}/{len(ok)} 通过")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
