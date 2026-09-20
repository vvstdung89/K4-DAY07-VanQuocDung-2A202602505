# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Văn Quốc Dũng

**Nhóm:** Studo.h (T114)

**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

**Chiến lược của tôi:** `FixedSizeChunker(chunk_size=500, overlap=50)` — phương án cơ sở để nhóm so sánh với các cách chia văn bản khác.

**Embedding khi chạy benchmark:** `text-embedding-3-small` (OpenAI).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Theo tôi hiểu, độ tương tự cosine cao cho biết hai vector có hướng gần nhau. Khi dùng embedding để biểu diễn văn bản, điều này thường có nghĩa là hai đoạn có nội dung hoặc chủ đề gần nhau, dù cách dùng từ khác nhau. Tuy nhiên, điểm cao chưa đủ để kết luận rằng hai câu có ý nghĩa hoàn toàn giống nhau, nhất là khi câu có điều kiện hoặc từ phủ định.

**Ví dụ có độ tương tự CAO:**

- Câu A: Khách được đổi hàng trong 7 ngày nếu sản phẩm còn nguyên tem.
- Câu B: Người mua có 7 ngày để hoàn trả hàng chưa bóc seal.
- Giải thích: Cả hai câu đều đề cập đến việc đổi hoặc trả hàng trong vòng 7 ngày, với điều kiện sản phẩm còn nguyên tem hoặc seal. Dù “đổi hàng” và “hoàn trả” không hoàn toàn giống nhau, hai câu vẫn có nội dung khá gần nhau nên tôi dự đoán điểm tương tự sẽ cao.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Thời hạn đổi trả là 7 ngày kể từ khi nhận hàng.
- Câu B: Người bán phải nộp thuế GTGT theo quý.
- Giải thích: Câu A nói về thời hạn đổi trả của người mua, còn câu B nói về nghĩa vụ thuế của người bán. Hai câu cùng thuộc bối cảnh kinh doanh nhưng đề cập đến hai vấn đề khác nhau, vì vậy tôi dự đoán độ tương tự sẽ thấp.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

> Cosine tập trung vào hướng của hai vector và không phụ thuộc vào độ lớn của chúng. Điều này phù hợp khi tôi muốn so sánh mức độ gần nhau về nội dung mà mô hình embedding biểu diễn. Trong khi đó, khoảng cách Euclid chịu ảnh hưởng của cả hướng lẫn độ lớn vector, nên sự chênh lệch về độ lớn có thể tác động đến kết quả so sánh.
>
> Tuy vậy, không thể suy ra rằng câu dài hơn luôn có vector lớn hơn. Nếu các vector đã được chuẩn hóa về độ dài bằng 1, cosine và khoảng cách Euclid sẽ cho cùng thứ tự xếp hạng mức độ tương đồng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Với mỗi chunk dài tối đa 500 ký tự và phần chồng lặp là 50 ký tự, vị trí bắt đầu của hai chunk liên tiếp cách nhau 450 ký tự. Áp dụng công thức của bài tập:
>
> `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23`
>
> Như vậy, tài liệu được chia thành **23 chunk**, trong đó chunk cuối chứa phần văn bản còn lại và có thể ngắn hơn 500 ký tự. Kết quả này cũng phù hợp với cách hoạt động của `FixedSizeChunker(500, 50)` trong mã nguồn.

**Nếu overlap tăng lên 100, số chunk đổi thế nào? Vì sao muốn overlap lớn hơn?**

> Khi tăng overlap lên 100, mỗi bước chỉ dịch chuyển 400 ký tự. Số chunk lúc này là `ceil((10000 - 100) / (500 - 100)) = ceil(24.75) = 25`, tức tăng thêm 2 chunk so với ban đầu.
>
> Phần chồng lặp lớn hơn giúp giữ lại nhiều ngữ cảnh ở ranh giới giữa hai chunk. Chẳng hạn, nếu một câu bị cắt ở cuối chunk trước, chunk sau có thể chứa lại phần đầu của câu đó và giúp thông tin dễ hiểu hơn khi được truy xuất. Đổi lại, hệ thống phải tạo embedding và lưu trữ nhiều nội dung trùng lặp hơn. Vì vậy, tôi cần cân nhắc giữa việc giữ đủ ngữ cảnh và chi phí xử lý, thay vì mặc định overlap càng lớn càng tốt.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Khi triển khai các phần trong gói `src`, tôi tập trung vào luồng xử lý từ chia văn bản, lưu embedding đến truy xuất và tạo câu trả lời. Với mỗi phần, tôi chú ý cả trường hợp thông thường lẫn các tình huống như văn bản rỗng, không có kết quả tìm kiếm hoặc cần lọc tài liệu theo metadata.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng biểu thức chính quy `(?<=[.!?])[ \n]+` để nhận diện ranh giới câu tại dấu chấm, chấm than hoặc chấm hỏi có khoảng trắng hay xuống dòng theo sau. Cách tách này giữ lại dấu câu ở cuối mỗi câu, giúp nội dung sau khi chia vẫn dễ đọc. Sau đó, tôi loại bỏ khoảng trắng thừa và gom tối đa `max_sentences_per_chunk` câu vào một chunk. Nếu đầu vào rỗng hoặc chỉ có khoảng trắng, hàm trả về danh sách rỗng.
>
> Ưu điểm của cách làm này là đơn giản và giữ được ranh giới câu trong những trường hợp thông thường. Tuy nhiên, các từ viết tắt như “TS.” hoặc “v.v.” vẫn có thể bị nhận nhầm là kết thúc câu nếu phía sau có khoảng trắng. Đây là hạn chế tôi cần lưu ý khi áp dụng cho văn bản thực tế.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Với `RecursiveChunker`, tôi ưu tiên chia theo cấu trúc lớn của văn bản trước, rồi mới chuyển sang ranh giới nhỏ hơn nếu đoạn vẫn quá dài. Thứ tự dấu phân cách là `"\n\n"`, `"\n"`, `". "`, `" "` và cuối cùng là chuỗi rỗng để chuyển sang cắt theo số ký tự.
>
> Hàm `_split` giữ nguyên những đoạn đã có độ dài không vượt quá `chunk_size`. Nếu dấu phân cách hiện tại không tách được văn bản, hàm thử dấu phân cách tiếp theo; nếu vẫn còn đoạn quá dài, hàm tiếp tục xử lý đệ quy. Khi hết dấu phân cách, tôi dùng `_hard_split` để bảo đảm giới hạn kích thước.
>
> Sau bước chia, `_merge` gom các mảnh liền kề lại miễn là tổng độ dài vẫn nằm trong giới hạn. Bước này giúp tránh tạo ra quá nhiều chunk ngắn, đồng thời giữ thêm ngữ cảnh trong mỗi kết quả truy xuất.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Trong phiên bản cá nhân, tôi lưu các bản ghi trực tiếp trong bộ nhớ và đặt `_use_chroma = False`. Cách triển khai này đáp ứng các thao tác cần có của bài thực hành và giúp tôi theo dõi rõ quá trình thêm, tìm kiếm và xóa tài liệu.
>
> Khi thêm tài liệu, `_make_record` sao chép metadata để tránh làm thay đổi dữ liệu của bên gọi. Tôi dùng `setdefault("doc_id", doc.id)` để bổ sung mã tài liệu nếu chưa có, đồng thời giữ nguyên `doc_id` đã được gán cho các chunk thuộc cùng một tài liệu gốc. Nội dung sau đó được chuyển thành embedding và lưu cùng mã định danh, văn bản và metadata.
>
> Khi tìm kiếm, tôi tạo embedding cho câu hỏi, dùng `compute_similarity` để tính cosine với từng bản ghi, rồi sắp xếp điểm từ cao xuống thấp và lấy tối đa `top_k` kết quả. Hai hàm `search` và `search_with_filter` dùng chung `_search_records` để thống nhất cách xếp hạng. Kết quả trả về gồm nội dung, mã định danh, metadata và điểm tương tự; vector embedding được giữ trong kho lưu trữ.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Tôi thực hiện lọc metadata trước khi tính điểm và chọn top-k. Lý do là nếu lấy top-k trên toàn bộ kho rồi mới lọc, các tài liệu không đúng đối tượng có thể chiếm hết vị trí, khiến kết quả còn lại quá ít dù trong kho vẫn có tài liệu phù hợp. Với bộ dữ liệu của nhóm, trường `audience` giúp giới hạn tìm kiếm vào tài liệu dành cho người mua hoặc người bán.
>
> Đối với `delete_document`, tôi xóa tất cả bản ghi có `metadata['doc_id']` trùng với mã được truyền vào. Nhờ vậy, khi xóa một tài liệu gốc, các chunk thuộc tài liệu đó cũng được xóa cùng lúc. Hàm trả về `True` nếu có bản ghi bị xóa và `False` nếu không tìm thấy tài liệu tương ứng.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Tôi triển khai `answer` theo ba bước: truy xuất các chunk liên quan nhất, ghép chúng thành ngữ cảnh trong prompt, rồi gọi `llm_fn` để tạo câu trả lời. Nếu không có kết quả truy xuất, hàm trả về thông báo ngay để tránh gọi mô hình khi không có tài liệu làm căn cứ.
>
> Trong prompt, mỗi chunk được đánh số như `[1]`, `[2]`, `[3]` và kèm nguồn tài liệu để có thể đối chiếu câu trả lời. Tôi yêu cầu mô hình chỉ sử dụng thông tin trong ngữ cảnh, trích dẫn số đoạn đã dùng và nói rõ khi tài liệu chưa đủ để trả lời. Các hướng dẫn này giúp định hướng câu trả lời, nhưng chất lượng cuối cùng vẫn phụ thuộc vào việc truy xuất đúng và đủ thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- .venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\vvstd\vinai\K4-DAY07-VanQuocDung-2A202602505
plugins: anyio-4.15.1
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.11s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

Theo kết quả kiểm thử đã ghi lại ở trên, mã nguồn vượt qua toàn bộ 42 bài test. Kết quả này cho thấy các chức năng đáp ứng những trường hợp được kiểm tra trong bộ test của lab. Tuy nhiên, việc vượt qua test chưa đồng nghĩa với truy xuất tốt trên mọi câu hỏi thực tế, nên tôi tiếp tục đánh giá trên bộ tài liệu và câu hỏi chung của nhóm ở phần 5.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Điểm cosine đo bằng `compute_similarity()` trên vector `text-embedding-3-small`.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
| --- | ----- | ----- | ------- | ------------ | ----- |
| 1 | Khách được đổi hàng trong 7 ngày nếu sản phẩm còn nguyên tem. | Người mua có 7 ngày để hoàn trả hàng chưa bóc seal. | cao | 0.68 | Có |
| 2 | Ảnh bằng chứng tối đa 5MB. | Video bằng chứng tối đa 100MB. | cao | 0.72 | Có |
| 3 | Thời hạn đổi trả là 7 ngày kể từ khi nhận hàng. | Hôm nay trời mưa to, tôi ở nhà đọc sách. | thấp | 0.21 | Có |
| 4 | Thực phẩm đông lạnh không áp dụng lý do trả hàng đổi ý. | Đơn thanh toán thẻ tín dụng nhận tiền hoàn sau 7 - 14 ngày làm việc. | thấp | 0.29 | Có |
| 5 | Shopee hoàn voucher Shopee cho người mua. | Shop Voucher của người bán không được hoàn. | thấp | 0.64 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Tôi bất ngờ nhất với cặp 5 vì ban đầu dự đoán điểm thấp, nhưng kết quả thực tế là **0.64**, khá gần mức **0.68** của cặp 1. Khi đọc theo mục đích trả lời câu hỏi, tôi chú ý đến sự khác nhau giữa “được hoàn” và “không được hoàn”. Tuy nhiên, cả hai câu đều nói về việc hoàn voucher nên vẫn có sự gần nhau về chủ đề.
>
> Nhìn kỹ hơn, hai câu cũng không hoàn toàn mâu thuẫn vì chúng nói về hai loại voucher khác nhau: voucher của Shopee và Shop Voucher do người bán phát hành. Kết quả này giúp tôi nhận ra rằng điểm cosine cao không bảo đảm hai đoạn có thể thay thế cho nhau khi trả lời một câu hỏi cụ thể. Tôi cũng chưa có đủ cơ sở để kết luận mô hình không hiểu phủ định chỉ từ một cặp câu.
>
> Với dữ liệu chính sách, tôi cần kiểm tra cả đối tượng áp dụng, loại voucher và điều kiện đi kèm. Lọc theo `audience` là một cách thu hẹp phạm vi tìm kiếm khi câu hỏi đã xác định rõ phía người mua hoặc người bán; sau đó vẫn phải đọc đúng nội dung của các chunk được trả về.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi sử dụng `FixedSizeChunker(chunk_size=500, overlap=50)` để chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân. Bộ dữ liệu gồm 12 tài liệu, sau khi chia tạo thành **98 chunk**. Với embedding `text-embedding-3-small`, kết quả truy xuất đạt **4/10 điểm** theo cách chấm `must_contain`. Log đầy đủ được lưu trong `ket_qua_benchmark.txt`.

Benchmark kiểm tra sự xuất hiện của các cụm từ bắt buộc trong ngữ cảnh top-3 và vị trí của tài liệu chuẩn (`gold_docs`). Lần chạy này chưa gọi LLM để sinh câu trả lời, vì vậy cột cuối của bảng là nhận xét của tôi về thông tin có thể dùng để trả lời từ ngữ cảnh, không phải đầu ra thực tế của Agent.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Khả năng trả lời từ ngữ cảnh top-3 |
| --- | --- | --- | --- | --- | --- |
| 1 | Đơn hàng thực phẩm đông lạnh đã giao thành công 2 ngày trước, tôi đổi ý không muốn dùng nữa thì trả hàng được không? | `doi-y-khong-con-nhu-cau#14` đề cập đến điều kiện còn nguyên seal đối với một số sản phẩm vệ sinh và ăn uống. | 0.56 | Liên quan một phần. Tài liệu chuẩn dành cho người mua xuất hiện ở vị trí thứ 3 và có mốc 24 giờ, nhưng ngữ cảnh thiếu quy định hạn chế trả hàng do đổi ý. | Có thể nêu mốc 24 giờ, nhưng chưa đủ căn cứ để giải thích đầy đủ điều kiện trả hàng do đổi ý đối với thực phẩm đông lạnh. **0/2** |
| 2 | Shop Voucher do Người bán phát hành có được hoàn lại khi yêu cầu Trả hàng/Hoàn tiền được chấp nhận không? | `quy-dinh-chung-tra-hang-hoan-tien-seller#1` chứa quy định về việc không hoàn Shop Voucher và mã Freeship. Truy vấn có lọc `audience=seller`. | 0.62 | Có liên quan. Cả ba kết quả đều thuộc tài liệu dành cho người bán. | Ngữ cảnh đủ để trả lời rằng Shop Voucher không được hoàn lại trong bất cứ trường hợp nào; người mua có thể chủ động liên hệ shop để được hỗ trợ. **2/2** |
| 3 | Tôi trả hàng bằng hình thức “Tự sắp xếp”, đơn không thuộc Shopee Mall, địa chỉ của tôi khác tỉnh với Người bán — được hỗ trợ phí trả hàng bao nhiêu và trong bao lâu? | `phuong-thuc-phi-gui-hang-hoan-tra#10` nêu mức hỗ trợ 40.000 Shopee Xu nếu khác tỉnh và 25.000 Xu nếu cùng tỉnh. | 0.72 | Có liên quan. Cả ba kết quả đều đúng tài liệu cần tìm; thời gian “3 - 5 ngày làm việc” nằm ở kết quả thứ 2. | Ngữ cảnh cung cấp được cả mức hỗ trợ 40.000 Shopee Xu và thời gian 3–5 ngày làm việc cho trường hợp được hỏi. **2/2** |
| 4 | Khi gửi bằng chứng cho yêu cầu Trả hàng/Hoàn tiền, ảnh và video được phép dung lượng tối đa bao nhiêu, và nếu Shopee yêu cầu bổ sung thì tôi có bao lâu? | `quy-dinh-chung-tra-hang-hoan-tien-buyer#1` nói về thời hạn gửi yêu cầu, thay vì yêu cầu đối với bằng chứng. | 0.71 | Chưa đáp ứng câu hỏi. Top-3 gồm quy định chung và hướng dẫn gửi yêu cầu, thiếu các cụm `5mb`, `100 mb` và `1 phút`. | Ngữ cảnh chưa đủ để trả lời giới hạn dung lượng ảnh và video. Cần truy xuất thêm tài liệu về bằng chứng trước khi đưa ra câu trả lời đầy đủ. **0/2** |
| 5 | Đơn hàng thanh toán bằng thẻ tín dụng thì bao lâu nhận được tiền hoàn, so với Ví ShopeePay? | `thoi-gian-nhan-tien-hoan#1` chứa một phần bảng thời gian hoàn tiền, nhưng bị cắt trước khi có đủ thông tin về thẻ tín dụng. | 0.75 | Liên quan một phần. Đã tìm đúng tài liệu chuẩn, nhưng ngữ cảnh top-3 thiếu mốc “7 - 14 ngày làm việc”. | Có thông tin về thời gian hoàn tiền qua ShopeePay khoảng 24 giờ, nhưng chưa đủ dữ liệu để so sánh với thẻ tín dụng. **0/2** |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?**

Có **4/5 câu hỏi** tìm được ít nhất một chunk thuộc tài liệu chuẩn trong top-3. Tuy nhiên, chỉ câu 2 và câu 3 có đủ các cụm thông tin bắt buộc theo benchmark. Câu 1 và câu 5 cho thấy việc tìm đúng tài liệu chưa chắc đã đủ: chunk được lấy ra vẫn có thể thiếu phần nội dung quyết định câu trả lời. Riêng câu 4 chưa truy xuất được tài liệu về bằng chứng trong top-3.

**A/B filter — câu 2:**

Khi dùng `metadata_filter={"audience": "seller"}`, tài liệu chuẩn dành cho người bán đứng ở vị trí đầu tiên và câu hỏi đạt **2/2 điểm**. Khi bỏ bộ lọc, kết quả đầu tiên chuyển sang tài liệu dành cho người mua có nội dung về voucher Shopee được hoàn; tài liệu chuẩn lùi xuống vị trí thứ 2 nên điểm còn **1/2**.

Thử nghiệm này cho thấy bộ lọc giúp ưu tiên đúng phạm vi tài liệu đối với câu hỏi về Shop Voucher. Dù lần chạy không lọc vẫn có tài liệu chuẩn trong top-3, việc đưa thêm nội dung về loại voucher khác vào ngữ cảnh có thể gây nhầm lẫn khi tổng hợp câu trả lời. Kết quả A/B ở đây chứng minh sự thay đổi về thứ hạng truy xuất, chưa đánh giá trực tiếp câu trả lời của LLM.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Theo số liệu nhóm đã ghi nhận, Thịnh dùng `SentenceChunker` đạt **8/10 điểm** trên bộ 5 câu hỏi; kết quả này chưa được đối chiếu lại với bộ `must_contain` hiện tại. Điều tôi thấy đáng học hỏi là cách chia theo câu có thể giữ thông tin liền mạch hơn, đặc biệt với các nội dung chứa thời hạn, mức phí hoặc điều kiện áp dụng.
>
> Trong kết quả của tôi, câu 5 là ví dụ rõ nhất: hệ thống tìm đúng tài liệu về thời gian hoàn tiền nhưng chunk được lấy ra chỉ chứa một phần bảng, còn mốc “7 - 14 ngày làm việc” không xuất hiện trong ngữ cảnh top-3. Phần overlap 50 ký tự chưa đủ để bảo đảm thông tin cần thiết được truy xuất cùng nhau. Với câu 4, vấn đề lại nằm ở việc chưa tìm được đúng tài liệu về bằng chứng, nên tôi không thể quy toàn bộ lỗi cho ranh giới chunk.
>
> Qua đó, tôi rút ra rằng cần xem cụ thể từng kết quả thiếu gì trước khi điều chỉnh chiến lược. Nếu làm lại, tôi sẽ thử giữ nguyên các hàng trong bảng thời gian hoàn tiền và gắn tiêu đề mục vào chunk để làm rõ ngữ cảnh. Sau đó, tôi sẽ chạy lại cùng bộ câu hỏi để kiểm tra liệu những thay đổi này có cải thiện các trường hợp thất bại hay không.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
| --- | --- |
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
