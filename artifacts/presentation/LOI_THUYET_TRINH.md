# Lời thuyết trình theo từng slide

Có thể đọc phần “Lời trình bày” ngay trên mỗi slide hoặc dùng bản này.

## Slide 1: Xây dựng kho tri thức từ tài liệu PDF

Em là Trần Minh Tân. Trong bài lab này, em xây dựng một pipeline để biến giáo trình PDF thành kho tri thức có thể tìm kiếm theo ý nghĩa. Khi nhập câu hỏi, hệ thống trả về các đoạn liên quan cùng trang nguồn để đối chiếu. Sau đây em trình bày dữ liệu đầu vào, từng bước xử lý, cách đánh giá và demo giao diện.

Điểm cần nhớ: Bài này tập trung vào chuẩn bị dữ liệu và tìm bằng chứng.

Giao diện hiện trả về đoạn tài liệu, chưa sinh câu trả lời bằng LLM.

## Slide 2: 1. Khảo sát và chọn dữ liệu đầu vào

Trước khi viết pipeline, em khảo sát PDF để biết có lấy được chữ hay không và trang nào có nội dung hữu ích. File có 71 trang nhưng em chỉ sử dụng 62 trang từ 9 đến 70. Em ghi các quyết định này trong manifest để người khác biết nguồn dữ liệu và có thể kiểm tra lại cách tính trang.

Điểm cần nhớ: PDF do học viên cung cấp; bìa ghi năm 2019.

Chưa có URL tải gốc. Trang 2 đề cập mục đích đào tạo/tham khảo; không tự gán giấy phép mở.

## Slide 3: 2. Toàn bộ quy trình hoạt động

Quy trình gồm sáu bước. Đầu tiên em đọc chữ từ PDF, sau đó chuẩn hóa text và gắn nguồn, số trang. Tiếp theo em chia text thành các đoạn nhỏ, tạo embedding cho từng đoạn và lưu vào Qdrant. Khi người dùng hỏi, câu hỏi được tạo vector bằng cùng model để tìm ba đoạn liên quan nhất.

Điểm cần nhớ: Lúc chuẩn bị: tài liệu → vector → kho lưu trữ.

Lúc truy vấn: câu hỏi → vector → tìm 3 đoạn gần nhất trong kho đã tạo.

## Slide 4: 3. Đọc PDF và chuẩn hóa text

Em dùng pypdf để đọc riêng từng trang, thay vì gộp cả tài liệu thành một chuỗi. Sau đó em chuẩn hóa Unicode và khoảng trắng nhưng vẫn giữ cấu trúc dòng. Một số từ trong PDF bị tách chữ, em ghi nhận hạn chế này và chưa tự sửa vì có thể làm sai nội dung. Mỗi bản ghi luôn giữ nguồn và số trang.

Điểm cần nhớ: Số trang luôn là trang vật lý trong PDF để đối chiếu.

Nếu đọc lỗi hoặc thiếu trang đã khai báo, pipeline ghi log và dừng.

## Slide 5: 4. Chunk là gì? Vì sao phải chia nhỏ?

Chunk có thể hiểu là một mẩu nhỏ của tài liệu. Việc chia nhỏ giúp hệ thống trả về bằng chứng cụ thể. Tuy nhiên, nếu chia quá ngắn thì dễ mất ý; chia quá dài thì có nhiều thông tin không liên quan. Vì vậy em thử hai công thức chia và đo xem công thức nào hỗ trợ truy xuất tốt hơn.

Điểm cần nhớ: Ví dụ: một đoạn giải thích vai trò của gia vị có thể là một chunk.

Mục tiêu là đoạn đủ ngữ cảnh nhưng vẫn tập trung vào một nhóm ý.

## Slide 6: 5. Embedding biến văn bản thành vector

Embedding là bước chuyển đoạn văn thành một dãy số để so sánh ý nghĩa. Em sử dụng MiniLM đa ngữ chạy local và mỗi vector có 384 chiều. Câu hỏi cũng được xử lý bằng cùng model. Hệ thống dựa vào độ tương đồng cosine để xếp hạng, nhưng điểm cao không bảo đảm đoạn đó chứa đúng bằng chứng cần tìm.

Điểm cần nhớ: Cosine cao hơn nghĩa là gần hơn theo model.

Điểm tương đồng không phải xác suất câu trả lời đúng. Model vẫn có thể nhầm các đối tượng gần nghĩa.

## Slide 7: 6. Qdrant lưu những gì?

Qdrant là kho vector của bài. Em không chỉ lưu vector mà còn lưu text và metadata để hiển thị bằng chứng. Database nằm trên ổ đĩa nên dữ liệu vẫn còn sau khi tắt chương trình. Khi nạp lại, ID ổn định giúp không sinh bản ghi trùng; khi nguồn thay đổi, em refresh dữ liệu để loại các chunk cũ.

Điểm cần nhớ: Một chunk có thể mang metadata:

page: 67
content_group: trinh_bay

Đóng rồi mở lại database vẫn truy xuất được.

## Slide 8: 7. Ba cấu hình A, B và C khác nhau thế nào?

Ở A, em chia theo số ký tự và dùng overlap để giữ một phần ngữ cảnh giữa hai đoạn. Ở B, em ưu tiên điểm kết thúc câu hoặc đoạn để giữ trọn ý hơn. C dùng cùng dữ liệu như B nhưng thêm bộ lọc nhóm. Việc giữ các yếu tố khác giống nhau giúp em phân tích ảnh hưởng của chiến lược dữ liệu.

Điểm cần nhớ: A–B so sánh toàn bộ công thức chia: cả ranh giới và overlap.

B–C chỉ khác bộ lọc. Nếu không chọn nhóm, C cho kết quả như B.

## Slide 9: 8. Bộ lọc metadata hoạt động ra sao?

Ví dụ khi em muốn tìm yêu cầu trình bày món ăn, em chọn nhóm trình bày. Qdrant chỉ xét các chunk thuộc nhóm đó, thay vì tìm cả tài liệu. Điều này giúp giảm nhiễu ngoài phạm vi. Tuy nhiên, lọc đúng nhóm chưa đủ, vì model vẫn phải tìm đúng đoạn trong nhóm đã chọn.

Điểm cần nhớ: Bộ lọc giúp giảm kết quả ngoài phạm vi.

Nhưng trong một nhóm vẫn có nhiều đoạn khác nhau, nên hệ thống vẫn có thể chọn sai bằng chứng.

## Slide 10: 9. Benchmark, dev, test và Hit@3

Để đánh giá, em xây 20 câu hỏi kèm đáp án và bằng chứng. Em dùng 15 câu dev để chọn cấu hình, sau đó dùng 5 câu test để kiểm tra. Với Hit@3, một câu được tính đúng khi ít nhất một trong ba chunk đầu đúng nguồn, đúng trang và chứa đủ bằng chứng. Chỉ trả về đúng trang nhưng thiếu ý vẫn chưa được tính hit.

Điểm cần nhớ: Có 3 câu dùng filter, trong đó 1 câu thuộc test.

Chốt hash câu hỏi/cấu hình trước thử nghiệm. Không sửa chiến lược dựa trên kết quả test.

## Slide 11: 10. Kết quả thực nghiệm và lựa chọn

Trên tập dev, C đạt 7 trên 15 câu, cao nhất trong ba cấu hình nên được chọn. Sau khi chốt, C đạt 1 trên 5 câu test, trong khi A đạt 2 trên 5. Em vẫn giữ lựa chọn C theo dev. Tập test chỉ có năm câu, mỗi câu tương đương 20 điểm phần trăm nên chưa thể kết luận cấu hình nào tốt nhất một cách tổng quát.

Điểm cần nhớ: Chọn C vì dev tốt nhất: 7/15.

Test của C chỉ 1/5, thấp hơn A 2/5. Giữ kết quả này để phân tích, không chọn lại theo test.

## Slide 12: 11. Audit: xem chất lượng ngoài điểm Hit@3

Ngoài retrieval, em xem chunk có trọn ý không, metadata có đúng không và bằng chứng có đủ để trả lời không. Phần này gọi là audit. Ví dụ một đoạn tìm đúng chủ đề nhưng thiếu điều kiện cần thiết thì grounding vẫn chưa tốt. Các nhận xét định tính hiện do AI hỗ trợ, em chưa xác nhận chấm thủ công nên báo cáo ghi rõ trạng thái này.

Điểm cần nhớ: Audit định tính hiện do AI hỗ trợ và còn chờ học viên xác nhận.

Không gọi nhãn AI là chấm tay của học viên; không coi grounding là độ chính xác câu trả lời LLM.

## Slide 13: 12. Một trường hợp thất bại để giải thích

Một lỗi cụ thể là câu hỏi về cỏ xạ hương. Đáp án nằm ở trang 40, nhưng cấu hình C trả về trang 39 và 38, nói về các loại gia vị khác. Bộ lọc đã làm đúng nhiệm vụ giới hạn nhóm, nhưng model vẫn nhầm đối tượng. Đây là lý do cần đọc trace, thay vì chỉ nhìn thấy đúng chủ đề rồi kết luận truy xuất thành công.

Điểm cần nhớ: Không sửa mô hình hoặc bộ câu hỏi hiện tại để tăng điểm sau khi đã xem test.

Nếu thử cải tiến, chọn trên dev và cần tập test phù hợp cho vòng đánh giá mới.

## Slide 14: 13. Demo giao diện và kết luận

Cuối cùng em demo một câu hỏi trên giao diện, đọc ba đoạn truy xuất và mở trang PDF để kiểm tra. Sau đó em so sánh A, B, C với cùng câu hỏi. Qua bài này, em thực hành cách tổ chức pipeline, giữ liên kết về nguồn và kiểm chứng kết quả. Hạn chế còn lại là lỗi text PDF, model nhỏ, test ít câu và phần nhãn thủ công chưa xác nhận. Em xin kết thúc phần trình bày.

Điểm cần nhớ: Đã có pipeline chạy thật, index lưu bền vững và 6 kiểm thử kỹ thuật đạt.

Điều học được: giữ lineage, kiểm soát chất lượng, nạp lại không trùng và đánh giá bằng bằng chứng.
