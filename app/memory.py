"""分层记忆系统：工作记忆 + 滚动摘要 + 长期记忆（向量检索）。

设计（对应 Agent 记忆管理高频考点）：
  - 工作记忆（working memory）：保留最近 N 轮原始对话，注入上下文供直接引用；
  - 摘要记忆（summary memory）：超过阈值后，用 LLM 把早期对话**滚动压缩**成要点摘要
    （recursive summarization：旧摘要 + 新溢出对话 → 新摘要），防止上下文无限膨胀；
  - 长期记忆（long-term memory）：每轮问答的 (问题, 回答) 作为结论文档入库，
    用「字符级 n-gram TF-IDF 稀疏向量 + cosine 相似度」做本地语义检索——
    零外部依赖（不依赖 embedding API、不联网），对中文友好；
    每轮把最相关的历史结论注入上下文，实现"跨轮引用"。

用法（一般通过 app.agent 的 build_agent 自动接入）：
    mem = AgentMemory(llm=llm)
    mem.remember("问题", "回答")
    ctx = mem.build_context("新问题")   # 摘要 + 检索结论 + 最近对话
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# 长期记忆：字符级 n-gram TF-IDF + cosine 检索
# ---------------------------------------------------------------------------

class VectorMemory:
    """结论文档的本地语义检索（字符级 n-gram TF-IDF 稀疏向量 + cosine 相似度）。

    零外部依赖：不调用 embedding API，纯本地计算；字符级 n-gram 对中文友好。
    """

    def __init__(self, top_k: int = 3, max_docs: int = 500):
        self.top_k = top_k
        self.max_docs = max_docs
        self.docs: list[dict] = []          # [{"text": str, "meta": dict}]
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4), max_features=20000,
        )
        self._matrix = None
        self._dirty = True

    def add(self, text: str, meta: dict | None = None):
        self.docs.append({"text": text, "meta": meta or {}})
        if len(self.docs) > self.max_docs:
            self.docs = self.docs[-self.max_docs:]  # 只保留最新，防止无限膨胀
        self._dirty = True

    def _rebuild(self):
        if not self.docs:
            self._matrix = None
            return
        self._matrix = self._vectorizer.fit_transform([d["text"] for d in self.docs])
        self._dirty = False

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """检索与 query 最相似的结论文档，按相似度降序返回 [{text, score}]。"""
        if not self.docs or not (query or "").strip():
            return []
        if self._dirty or self._matrix is None:
            self._rebuild()
        k = top_k or self.top_k
        qv = self._vectorizer.transform([query])
        sims = cosine_similarity(qv, self._matrix)[0]
        order = sims.argsort()[::-1]
        hits = []
        for i in order:
            score = float(sims[i])
            if score <= 0:
                break
            hits.append({"text": self.docs[i]["text"], "score": round(score, 4)})
            if len(hits) >= k:
                break
        return hits

    def __len__(self):
        return len(self.docs)


# ---------------------------------------------------------------------------
# 摘要记忆：LLM 滚动压缩早期对话
# ---------------------------------------------------------------------------

_SUMMARIZE_PROMPT = """你是对话记忆管理员。请把下面的历史对话压缩成简洁的要点摘要：
- 保留：用户问过的关键问题、分析得到的**具体数字结论**、业务结论与建议；
- 丢弃：寒暄、重复内容、工具调用细节；
- 输出为编号要点列表，控制在中文字符 400 字以内。

旧摘要（若为空表示第一次压缩）：
{old_summary}

新增对话：
{conversation}

新的完整摘要："""


class SummaryMemory:
    """滚动摘要：对话超过阈值时，用 LLM 把溢出部分并入旧摘要压缩。"""

    def __init__(self, llm, summarize_at: int = 8, working_rounds: int = 6):
        self._llm = llm
        self.summary = ""
        self.working: list[tuple[str, str]] = []   # [(question, answer), ...]
        self.summarize_at = summarize_at
        self.working_rounds = working_rounds

    def add(self, question: str, answer: str):
        self.working.append((question, answer))
        if len(self.working) > self.summarize_at:
            self._rollup()

    def _rollup(self):
        overflow = self.working[: len(self.working) - self.working_rounds]
        self.working = self.working[len(self.working) - self.working_rounds:]
        convo = "\n\n".join(f"问：{q}\n答：{a}" for q, a in overflow)
        prompt = _SUMMARIZE_PROMPT.format(old_summary=self.summary or "（无）", conversation=convo)
        resp = self._llm.invoke(prompt)
        self.summary = (resp.content if hasattr(resp, "content") else str(resp)).strip()

    @property
    def working_rounds_count(self) -> int:
        return len(self.working)


# ---------------------------------------------------------------------------
# 组合：分层记忆管理器
# ---------------------------------------------------------------------------

class AgentMemory:
    """三层记忆的组合管理器：工作记忆 + 滚动摘要 + 长期向量检索。"""

    def __init__(self, llm=None, working_rounds: int = 6, summarize_at: int = 8,
                 top_k: int = 3, max_docs: int = 500, enabled: bool = True):
        self.enabled = enabled
        self.summary = SummaryMemory(llm, summarize_at=summarize_at,
                                     working_rounds=working_rounds)
        self.vector = VectorMemory(top_k=top_k, max_docs=max_docs)

    def remember(self, question: str, answer: str):
        """对话结束后调用：结论文档入库 + 工作记忆更新（可能触发滚动摘要）。"""
        if not self.enabled or not (answer or "").strip():
            return
        self.vector.add(f"问：{question}\n答：{answer}")
        self.summary.add(question, answer)

    def build_context(self, question: str) -> str:
        """组装记忆上下文（注入 system prompt）：摘要 + 检索结论 + 最近对话。"""
        if not self.enabled:
            return ""
        parts = []
        if self.summary.summary:
            parts.append(f"【历史对话摘要】\n{self.summary.summary}")
        hits = self.vector.search(question)
        if hits:
            lines = "\n".join(f"- {h['text']}" for h in hits)
            parts.append(f"【相关历史结论（自动检索）】\n{lines}")
        if self.summary.working:
            lines = "\n".join(f"问：{q}\n答：{a[:300]}" for q, a in self.summary.working[-3:])
            parts.append(f"【最近对话】\n{lines}")
        return "\n\n".join(parts)

    def clear(self):
        self.summary.summary = ""
        self.summary.working = []
        self.vector.docs = []
        self.vector._matrix = None
        self.vector._dirty = True
