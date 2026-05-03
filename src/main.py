import os
import heapq
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ==================== 功能1：文档读取与切词 ====================
def tokenize_text(text: str) -> list[str]:
    tokens = []
    current_buffer = []
    text = text.lower()
    for char in text:
        is_chinese = '\u4e00' <= char <= '\u9fff'
        is_letter = char.isalpha()
        is_digit = char.isdigit()
        if is_chinese:
            if current_buffer:
                tokens.append(''.join(current_buffer))
                current_buffer.clear()
            tokens.append(char)
        elif is_letter or is_digit:
            current_buffer.append(char)
        else:
            if current_buffer:
                tokens.append(''.join(current_buffer))
                current_buffer.clear()
    if current_buffer:
        tokens.append(''.join(current_buffer))
    return tokens

def load_and_tokenize(folder_path: str) -> dict[int, list[str]]:
    txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    txt_files.sort()
    doc_tokens = {}
    for idx, filename in enumerate(txt_files):
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tokens = tokenize_text(content)
            doc_tokens[idx] = tokens
        except:
            doc_tokens[idx] = []
    return doc_tokens

# ==================== 功能2：分块索引（分治 3块+） ====================
def split_into_blocks(doc_dict: dict, block_num=3):
    docs = list(doc_dict.items())
    total = len(docs)
    block_size = (total + block_num - 1) // block_num
    blocks = []
    for i in range(block_num):
        start = i * block_size
        end = start + block_size
        block = dict(docs[start:end])
        if block:
            blocks.append(block)
    return blocks

def build_sub_index(block: dict):
    sub_idx = {}
    for doc_id, tokens in block.items():
        unique_terms = set(tokens)
        for term in unique_terms:
            if term not in sub_idx:
                sub_idx[term] = []
            sub_idx[term].append(doc_id)
            sub_idx[term].sort()
    return sub_idx

def merge_sub_indexes(sub_indexes: list):
    global_idx = {}
    for sub in sub_indexes:
        for term, doc_ids in sub.items():
            if term not in global_idx:
                global_idx[term] = []
            global_idx[term].extend(doc_ids)
            global_idx[term] = sorted(list(set(global_idx[term])))
    return global_idx

def build_block_index(doc_dict: dict, block_num=3):
    blocks = split_into_blocks(doc_dict, block_num)
    sub_indexes = [build_sub_index(b) for b in blocks]
    return merge_sub_indexes(sub_indexes)

def search_word(word: str, inverted_index):
    if not word:
        return []
    return inverted_index.get(word.lower(), [])

# ==================== 功能3：撤销栈 + 历史队列 ====================
class UndoStack:
    def __init__(self):
        self.stack = []
    def push(self, data):
        self.stack.append(data)
    def pop(self):
        return self.stack.pop() if self.stack else None

class HistoryQueue:
    def __init__(self, capacity=10):
        self.queue = []
        self.cap = capacity
    def enqueue(self, x):
        if len(self.queue) >= self.cap:
            self.queue.pop(0)
        self.queue.append(x)
    def remove_last(self):
        if self.queue:
            self.queue.pop()
    def get(self):
        return self.queue.copy()

# ==================== 功能4：Top-K ====================
def top_k_A(word, k, doc_tokens):
    word = word.lower()
    lst = []
    for did, tks in doc_tokens.items():
        cnt = tks.count(word)
        if cnt>0:
            lst.append((-cnt, did))
    lst.sort()
    return [(did, -cnt) for (cnt, did) in lst[:k]]

def top_k_B(word, k, doc_tokens):
    word = word.lower()
    heap = []
    for did, tks in doc_tokens.items():
        cnt = tks.count(word)
        if cnt>0:
            if len(heap)<k:
                heapq.heappush(heap,(cnt,did))
            else:
                if cnt>heap[0][0]:
                    heapq.heappop(heap)
                    heapq.heappush(heap,(cnt,did))
    heap.sort(key=lambda x:(-x[0],x[1]))
    return [(d,c) for c,d in heap]

# ==================== 功能5：拼写纠错 ====================
def edit_distance(a,b):
    m,n=len(a),len(b)
    dp=[[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0]=i
    for j in range(n+1): dp[0][j]=j
    for i in range(1,m+1):
        for j in range(1,n+1):
            dp[i][j] = dp[i-1][j-1] if a[i-1]==b[j-1] else 1+min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])
    return dp[m][n]

def correct(word, vocab):
    word=word.lower()
    if not word.isalpha() or any('\u4e00'<=c<='\u9fff' for c in word):
        return None
    best, md = None, 999
    for w in vocab:
        if w.isalpha():
            d = edit_distance(word,w)
            if d < md:
                md = d
                best = w
    return best

# ==================== 功能6：字典树 Trie 前缀补全 ====================
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    def insert(self, word):
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_end = True
    def get_prefix_list(self, prefix):
        node = self.root
        for c in prefix:
            if c not in node.children:
                return []
            node = node.children[c]
        res = []
        def dfs(n, path):
            if n.is_end:
                res.append(path)
            for char, child in n.children.items():
                dfs(child, path+char)
        dfs(node, prefix)
        return res

# ==================== GUI图形化界面 + 融合前缀逻辑 ====================
class SearchGUI:
    def __init__(self, root, doc_dict, inv_idx, vocab, trie):
        self.root = root
        self.root.title("文本搜索系统 | 前缀融合版")
        self.root.geometry("850x650")

        self.doc_dict = doc_dict
        self.inv_idx = inv_idx
        self.vocab = vocab
        self.trie = trie

        self.undo = UndoStack()
        self.hist = HistoryQueue()

        # 顶部输入
        top = ttk.Frame(root)
        top.pack(pady=10, fill=tk.X, padx=20)
        ttk.Label(top, text="查询词：").pack(side=tk.LEFT)
        self.entry = ttk.Entry(top, width=40, font=("Arial",12))
        self.entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(top, text="普通搜索", command=self.do_search).pack(side=tk.LEFT, padx=3)

        # 功能按钮区
        f = ttk.LabelFrame(root, text="功能区")
        f.pack(pady=5, fill=tk.X, padx=20)
        ttk.Button(f, text="撤销上一次", command=self.do_undo).grid(row=0,column=0,padx=5)
        ttk.Button(f, text="查看历史", command=self.show_hist).grid(row=0,column=1,padx=5)
        ttk.Button(f, text="显示全部切词", command=self.show_all_tokens).grid(row=0,column=2,padx=5)
        ttk.Label(f, text="K值:").grid(row=0,column=3)
        self.k_entry = ttk.Entry(f, width=4)
        self.k_entry.insert(0,"3")
        self.k_entry.grid(row=0,column=4)
        ttk.Button(f, text="TopK-A", command=self.do_topA).grid(row=0,column=5,padx=3)
        ttk.Button(f, text="TopK-B", command=self.do_topB).grid(row=0,column=6,padx=3)

        # 日志输出（只追加不清空）
        ttk.Label(root, text="运行日志：").pack(anchor=tk.W, padx=20)
        self.result = scrolledtext.ScrolledText(root, height=28, font=("SimHei",10))
        self.result.pack(padx=20, fill=tk.BOTH, expand=True)
        self.log("========== 系统初始化完成 ==========\n")

    def log(self, msg):
        self.result.insert(tk.END, msg+"\n")
        self.result.see(tk.END)

    # 统一：查询无结果时自动触发前缀补全提示
    def auto_prefix_tip(self, word):
        prefix_res = self.trie.get_prefix_list(word.lower())
        if prefix_res:
            self.log(f"💡 前缀补全提示：以「{word}」开头的词 → {prefix_res}")

    # 1.普通查询
    def do_search(self):
        w = self.entry.get().strip()
        if not w:
            messagebox.showwarning("提示","请输入查询词")
            return
        self.log("----------------------------------------")
        res = search_word(w, self.inv_idx)
        if res:
            self.log(f"→ 普通查询：[{w}]")
            self.log(f"→ 查询结果：{res}")
            self.undo.push({"type":"search","word":w})
            self.hist.enqueue(f"普通查询:{w}")
        else:
            self.log(f"→ 未找到精准词汇 [{w}]")
            # 自动前缀提示
            self.auto_prefix_tip(w)
            # 拼写纠错
            sugg = correct(w, self.vocab)
            if sugg:
                self.log(f"💡 拼写纠错建议：{sugg}")

    # 2.TopK A
    def do_topA(self):
        w = self.entry.get().strip()
        try:
            k = int(self.k_entry.get())
        except:
            k = 3
        if not w:
            return
        self.log("----------------------------------------")
        res = top_k_A(w, k, self.doc_dict)
        if res:
            self.log(f"→ Top-K(A) 全排序 | 关键词：{w}  K={k}")
            for did,sc in res:
                self.log(f"   文档 {did} (相关度: {sc})")
            self.undo.push({"type":"topA","word":w,"k":k})
            self.hist.enqueue(f"TopKA:{w}")
        else:
            self.log(f"→ TopK查询无精准匹配词汇 [{w}]")
            self.auto_prefix_tip(w)

    # 3.TopK B
    def do_topB(self):
        w = self.entry.get().strip()
        try:
            k = int(self.k_entry.get())
        except:
            k = 3
        if not w:
            return
        self.log("----------------------------------------")
        res = top_k_B(w, k, self.doc_dict)
        if res:
            self.log(f"→ Top-K(B) 小顶堆 | 关键词：{w}  K={k}")
            for did,sc in res:
                self.log(f"   文档 {did} (相关度: {sc})")
            self.undo.push({"type":"topB","word":w,"k":k})
            self.hist.enqueue(f"TopKB:{w}")
        else:
            self.log(f"→ TopK查询无精准匹配词汇 [{w}]")
            self.auto_prefix_tip(w)

    # 5.撤销
    def do_undo(self):
        self.log("----------------------------------------")
        data = self.undo.pop()
        if not data:
            self.log("→ 无操作可撤销")
            return
        self.hist.remove_last()

        t = data["type"]
        w = data["word"]

        if t == "search":
            res = search_word(w, self.inv_idx)
            self.log(f"→ 已撤销【普通查询】：[{w}]")
            self.log(f"→ 原查询结果：{res}")
        elif t == "topA":
            k = data["k"]
            res = top_k_A(w, k, self.doc_dict)
            self.log(f"→ 已撤销【Top-K(A)】：[{w}] K={k}")
            for did,sc in res:
                self.log(f"   文档 {did} (相关度: {sc})")
        elif t == "topB":
            k = data["k"]
            res = top_k_B(w, k, self.doc_dict)
            self.log(f"→ 已撤销【Top-K(B)】：[{w}] K={k}")
            for did,sc in res:
                self.log(f"   文档 {did} (相关度: {sc})")

    # 查看历史
    def show_hist(self):
        self.log("----------------------------------------")
        h = self.hist.get()
        self.log("→ 最近查询历史：")
        for idx,item in enumerate(h,1):
            self.log(f"   {idx}. {item}")

    # 全部切词
    def show_all_tokens(self):
        self.log("----------------------------------------")
        self.log("→ 全部文档切词结果：")
        for did, tokens in self.doc_dict.items():
            self.log(f"   文档{did}：{tokens}")

# ========== 程序入口 ==========
if __name__ == "__main__":
    try:
        doc_data = load_and_tokenize("testdata")
        inv_index = build_block_index(doc_data, 3)
        vocab_set = set(inv_index.keys())

        trie_tree = Trie()
        for word in vocab_set:
            trie_tree.insert(word)

        root = tk.Tk()
        app = SearchGUI(root, doc_data, inv_index, vocab_set, trie_tree)
        root.mainloop()
    except FileNotFoundError:
        messagebox.showerror("路径错误","请在程序同级目录创建 testdata 文件夹并放入txt文件")
