from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    NO_CONTEXT = "Khong tim thay tai lieu nao trong kho de tra loi cau hoi nay."

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        # Store rong / khong co ket qua: tra thong bao, khong goi LLM vo ich.
        if not results:
            return self.NO_CONTEXT

        blocks = []
        for position, result in enumerate(results, start=1):
            source = result["metadata"].get("doc_id") or result["metadata"].get("source") or result["id"]
            blocks.append(f"[{position}] (nguon: {source})\n{result['content']}")
        context = "\n\n".join(blocks)

        prompt = (
            "Ban la tro ly tra loi dua tren tai lieu duoc cung cap.\n"
            "Quy tac:\n"
            "- Chi dung thong tin trong phan NGU CANH duoi day, khong bia them.\n"
            "- Trich dan so hieu doan da dung, vi du [1], [2].\n"
            "- Neu ngu canh khong du de tra loi, noi ro la khong tim thay trong tai lieu.\n\n"
            f"NGU CANH:\n{context}\n\n"
            f"CAU HOI: {question}\n\n"
            "TRA LOI:"
        )
        return self.llm_fn(prompt)
