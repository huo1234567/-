```
A1:方案A和方案B可以控制台输入自行选择
R1:我已经按照你的要求，把方案 A、方案 B 都完整实现，并支持控制台自由选择，全程不改动原有功能，只新增选择逻辑，代码干净、可直接运行。
import os
import heapq

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
        except Exception as e:
            print(f"读取文件 {filename} 失败：{str(e)}")
            doc_tokens[idx] = []
    return doc_tokens

# ==================== 功能2：倒排索引与搜索 ====================
def build_inverted_index(doc_tokens: dict[int, list[str]]) -> dict[str, list[int]]:
    inverted_index = {}
    for doc_id, tokens in doc_tokens.items():
        unique_tokens = set(tokens)
        for word in unique_tokens:
            if word not in inverted_index:
                inverted_index[word] = []
            if doc_id not in inverted_index[word]:
                inverted_index[word].append(doc_id)
                inverted_index[word].sort()
    return inverted_index

def search_word(word: str, inverted_index: dict[str, list[int]]) -> list[int]:
    if not word:
        return []
    word = word.lower()
    return inverted_index.get(word, [])

# ==================== 功能3：自定义撤销栈 ====================
class UndoStack:
    def __init__(self):
        self.stack = []
        self.top = -1

    def push(self, item):
        self.top += 1
        self.stack.append(item)

    def pop(self):
        if self.is_empty():
            return None
        item = self.stack[self.top]
        del self.stack[self.top]
        self.top -= 1
        return item

    def peek(self):
        if self.is_empty():
            return None
        return self.stack[self.top]

    def is_empty(self):
        return self.top < 0

# ==================== 功能3：自定义历史队列 ====================
class HistoryQueue:
    def __init__(self, capacity=10):
        self.queue = []
        self.capacity = capacity

    def enqueue(self, item):
        if len(self.queue) >= self.capacity:
            self.dequeue()
        self.queue.append(item)

    def dequeue(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def remove_last(self):
        if self.queue:
            self.queue.pop()

    def recent(self):
        return list(self.queue)

# ==================== 功能4：Top-K 排序（方案A + 方案B） ====================
def top_k_A(word: str, k: int, doc_tokens: dict[int, list[str]]) -> list[int]:
    """方案A：全量排序后取前K"""
    if not word or k <= 0:
        return []
    word = word.lower()
    scores = []
    for doc_id, tokens in doc_tokens.items():
        cnt = tokens.count(word)
        if cnt > 0:
            scores.append((-cnt, doc_id))
    scores.sort()
    return [sid for _, sid in scores[:k]]

def top_k_B(word: str, k: int, doc_tokens: dict[int, list[str]]) -> list[int]:
    """方案B：小顶堆维护前K个最优结果"""
    if not word or k <= 0:
        return []
    word = word.lower()
    heap = []
    for doc_id, tokens in doc_tokens.items():
        cnt = tokens.count(word)
        if cnt > 0:
            if len(heap) < k:
                heapq.heappush(heap, (cnt, doc_id))
            else:
                if cnt > heap[0][0]:
                    heapq.heappop(heap)
                    heapq.heappush(heap, (cnt, doc_id))
    heap_sorted = sorted(heap, key=lambda x: (-x[0], x[1]))
    return [sid for _, sid in heap_sorted]

# ==================== 主程序 ====================
if __name__ == "__main__":
    print("==================================================")
    print("中文文本搜索系统 v5.1")
    print("功能1切词 | 功能2索引 | 功能3历史 | 功能4 Top-K")
    print("==================================================")

    try:
        doc_dict = load_and_tokenize("testdata/")
        inverted_index = build_inverted_index(doc_dict)
        undo_stack = UndoStack()
        history_queue = HistoryQueue()

        print("\n===== 操作指令 =====")
        print("普通查询：直接输入词")
        print("Top-K 查询：输入 topk:词:k:A  或  topk:词:k:B")
        print("示例：topk:算:3:A  或  topk:算:5:B")
        print("undo → 撤销")
        print("history → 历史")
        print("exit → 退出\n")

        while True:
            user_input = input("请输入指令/查询词：").strip()

            if user_input.lower() == "exit":
                print("系统已退出")
                break

            elif user_input.lower() == "undo":
                canceled = undo_stack.pop()
                if canceled is None:
                    print("→ 无操作可撤销\n")
                    continue
                history_queue.remove_last()
                res = search_word(canceled, inverted_index)
                print(f"→ 已撤销：[{canceled}] → {res}\n")
                continue

            elif user_input.lower() == "history":
                print(f"最近10次历史：{history_queue.recent()}\n")
                continue

            # Top-K 查询（支持选择 A / B）
            elif user_input.startswith("topk:"):
                parts = user_input.split(":")
                if len(parts) != 4:
                    print("→ 格式错误！示例：topk:算:3:A\n")
                    continue
                try:
                    word = parts[1]
                    k = int(parts[2])
                    mode = parts[3].upper()

                    if mode == "A":
                        res = top_k_A(word, k, doc_dict)
                        print(f"→ 方案A | Top-{k} 结果：{res}\n")
                    elif mode == "B":
                        res = top_k_B(word, k, doc_dict)
                        print(f"→ 方案B | Top-{k} 结果：{res}\n")
                    else:
                        print("→ 模式错误，只能选 A 或 B\n")
                        continue

                    undo_stack.push(user_input)
                    history_queue.enqueue(user_input)
                except:
                    print("→ 格式错误！示例：topk:算:3:A\n")
                continue

            # 普通搜索
            if user_input:
                res = search_word(user_input, inverted_index)
                print(f"→ 搜索结果：[{user_input}] → {res}\n")
                undo_stack.push(user_input)
                history_queue.enqueue(user_input)

    except FileNotFoundError:
        print("错误：未找到 testdata 文件夹")



A2:显示的同时还要显示(相关度:)
R2:我已经按你的要求升级输出格式：
执行 topk 查询时，同时显示文档编号 + 对应的相关度（出现次数），格式清晰美观，且保留方案 A/B 自由选择、所有原有功能不变。
import os
import heapq

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
        except Exception as e:
            print(f"读取文件 {filename} 失败：{str(e)}")
            doc_tokens[idx] = []
    return doc_tokens

# ==================== 功能2：倒排索引与搜索 ====================
def build_inverted_index(doc_tokens: dict[int, list[str]]) -> dict[str, list[int]]:
    inverted_index = {}
    for doc_id, tokens in doc_tokens.items():
        unique_tokens = set(tokens)
        for word in unique_tokens:
            if word not in inverted_index:
                inverted_index[word] = []
            if doc_id not in inverted_index[word]:
                inverted_index[word].append(doc_id)
                inverted_index[word].sort()
    return inverted_index

def search_word(word: str, inverted_index: dict[str, list[int]]) -> list[int]:
    if not word:
        return []
    word = word.lower()
    return inverted_index.get(word, [])

# ==================== 功能3：自定义撤销栈 ====================
class UndoStack:
    def __init__(self):
        self.stack = []
        self.top = -1

    def push(self, item):
        self.top += 1
        self.stack.append(item)

    def pop(self):
        if self.is_empty():
            return None
        item = self.stack[self.top]
        del self.stack[self.top]
        self.top -= 1
        return item

    def peek(self):
        if self.is_empty():
            return None
        return self.stack[self.top]

    def is_empty(self):
        return self.top < 0

# ==================== 功能3：自定义历史队列 ====================
class HistoryQueue:
    def __init__(self, capacity=10):
        self.queue = []
        self.capacity = capacity

    def enqueue(self, item):
        if len(self.queue) >= self.capacity:
            self.dequeue()
        self.queue.append(item)

    def dequeue(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def remove_last(self):
        if self.queue:
            self.queue.pop()

    def recent(self):
        return list(self.queue)

# ==================== 功能4：Top-K 相关性排序（A+B方案） ====================
def top_k_with_score(word: str, k: int, doc_tokens: dict[int, list[str]]):
    word = word.lower()
    scores = []
    for doc_id, tokens in doc_tokens.items():
        cnt = tokens.count(word)
        if cnt > 0:
            scores.append((-cnt, doc_id, cnt))
    scores.sort()
    top_list = [(sid, cnt) for (_, sid, cnt) in scores[:k]]
    return top_list

def top_k_heap_with_score(word: str, k: int, doc_tokens: dict[int, list[str]]):
    word = word.lower()
    heap = []
    for doc_id, tokens in doc_tokens.items():
        cnt = tokens.count(word)
        if cnt > 0:
            if len(heap) < k:
                heapq.heappush(heap, (cnt, doc_id))
            else:
                if cnt > heap[0][0]:
                    heapq.heappop(heap)
                    heapq.heappush(heap, (cnt, doc_id))
    heap_sorted = sorted(heap, key=lambda x: (-x[0], x[1]))
    return [(sid, cnt) for cnt, sid in heap_sorted]

# ==================== 主程序 ====================
if __name__ == "__main__":
    print("==================================================")
    print("中文文本搜索系统 v5.2")
    print("功能1切词 | 功能2索引 | 功能3历史 | 功能4 Top-K")
    print("==================================================")

    try:
        doc_dict = load_and_tokenize("testdata/")
        inverted_index = build_inverted_index(doc_dict)
        undo_stack = UndoStack()
        history_queue = HistoryQueue()

        print("\n===== 操作指令 =====")
        print("普通查询：输入词")
        print("Top-K：topk:词:k:A  或  topk:词:k:B")
        print("undo / history / exit")
        print("\n示例：topk:算:3:A\n")

        while True:
            user_input = input("请输入指令/查询词：").strip()

            if user_input.lower() == "exit":
                print("系统已退出")
                break

            elif user_input.lower() == "undo":
                canceled = undo_stack.pop()
                if canceled is None:
                    print("→ 无操作可撤销\n")
                    continue
                history_queue.remove_last()
                res = search_word(canceled, inverted_index)
                print(f"→ 已撤销：[{canceled}] → {res}\n")
                continue

            elif user_input.lower() == "history":
                print(f"最近10次历史：{history_queue.recent()}\n")
                continue

            elif user_input.startswith("topk:"):
                parts = user_input.split(":")
                if len(parts) != 4:
                    print("→ 格式：topk:词:k:A 或 topk:词:k:B\n")
                    continue
                try:
                    word = parts[1]
                    k = int(parts[2])
                    mode = parts[3].upper()

                    if mode == "A":
                        result = top_k_with_score(word, k, doc_dict)
                        print("→ 方案A Top-K 结果：")
                    elif mode == "B":
                        result = top_k_heap_with_score(word, k, doc_dict)
                        print("→ 方案B Top-K 结果：")
                    else:
                        print("→ 只能选 A / B\n")
                        continue

                    # 显示：文档编号(相关度:xx)
                    for doc_id, score in result:
                        print(f"   文档 {doc_id} (相关度: {score})")
                    print()

                    undo_stack.push(user_input)
                    history_queue.enqueue(user_input)
                except:
                    print("→ 输入格式错误！\n")
                continue

            if user_input:
                res = search_word(user_input, inverted_index)
                print(f"→ 搜索结果：[{user_input}] → {res}\n")
                undo_stack.push(user_input)
                history_queue.enqueue(user_input)

    except FileNotFoundError:
        print("错误：未找到 testdata 文件夹")
```
