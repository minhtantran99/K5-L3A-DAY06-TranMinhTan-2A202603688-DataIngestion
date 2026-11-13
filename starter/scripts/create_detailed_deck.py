"""Editable Vietnamese presentation with visible speaking text on every slide."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cache/presentation-tools"))
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt
from PIL import Image, ImageDraw, ImageFont

OUT = ROOT / "artifacts/presentation"
OUT.mkdir(parents=True, exist_ok=True)
METRICS = json.loads((ROOT / "results/metrics.json").read_text(encoding="utf-8"))

PAGES = [
    {
        "title": "Xây dựng kho tri thức từ tài liệu PDF",
        "subtitle": "Trần Minh Tân · MSSV 2A202603688 · Day 06 Data Ingestion Engineering",
        "rows": [
            ("Mục tiêu", "Tìm các đoạn tài liệu liên quan đến câu hỏi và truy ngược được về trang gốc."),
            ("Dữ liệu", "Giáo trình Kỹ thuật chế biến món ăn · dùng 62 trang nội dung."),
            ("Sản phẩm", "Pipeline Python, kho vector Qdrant, giao diện test và bộ đánh giá 20 câu hỏi.")],
        "remember": "Bài này tập trung vào chuẩn bị dữ liệu và tìm bằng chứng.\n\nGiao diện hiện trả về đoạn tài liệu, chưa sinh câu trả lời bằng LLM.",
        "speech": "Em là Trần Minh Tân. Trong bài lab này, em xây dựng một pipeline để biến giáo trình PDF thành kho tri thức có thể tìm kiếm theo ý nghĩa. Khi nhập câu hỏi, hệ thống trả về các đoạn liên quan cùng trang nguồn để đối chiếu. Sau đây em trình bày dữ liệu đầu vào, từng bước xử lý, cách đánh giá và demo giao diện."
    },
    {
        "title": "1. Khảo sát và chọn dữ liệu đầu vào",
        "subtitle": "Đọc được file chưa có nghĩa mọi trang đều là dữ liệu hữu ích.",
        "rows": [
            ("71 trang vật lý → 62 trang nội dung", "Dùng trang 9–70; loại phần đầu 1–8 và trang 71 chỉ còn số trang."),
            ("4 nhóm nội dung", "Tổng luận/sơ chế; phối hợp nguyên liệu/gia vị; làm chín; trình bày món ăn."),
            ("Lưu thông tin nguồn trong manifest", "Tên tài liệu, quyền sử dụng, hash PDF, các trang được tính và số ký tự.")],
        "remember": "PDF do học viên cung cấp; bìa ghi năm 2019.\n\nChưa có URL tải gốc. Trang 2 đề cập mục đích đào tạo/tham khảo; không tự gán giấy phép mở.",
        "speech": "Trước khi viết pipeline, em khảo sát PDF để biết có lấy được chữ hay không và trang nào có nội dung hữu ích. File có 71 trang nhưng em chỉ sử dụng 62 trang từ 9 đến 70. Em ghi các quyết định này trong manifest để người khác biết nguồn dữ liệu và có thể kiểm tra lại cách tính trang."
    },
    {
        "title": "2. Toàn bộ quy trình hoạt động",
        "subtitle": "Pipeline là chuỗi bước biến đổi dữ liệu, đầu ra bước trước trở thành đầu vào bước sau.",
        "kind": "pipeline",
        "remember": "Lúc chuẩn bị: tài liệu → vector → kho lưu trữ.\n\nLúc truy vấn: câu hỏi → vector → tìm 3 đoạn gần nhất trong kho đã tạo.",
        "speech": "Quy trình gồm sáu bước. Đầu tiên em đọc chữ từ PDF, sau đó chuẩn hóa text và gắn nguồn, số trang. Tiếp theo em chia text thành các đoạn nhỏ, tạo embedding cho từng đoạn và lưu vào Qdrant. Khi người dùng hỏi, câu hỏi được tạo vector bằng cùng model để tìm ba đoạn liên quan nhất."
    },
    {
        "title": "3. Đọc PDF và chuẩn hóa text",
        "subtitle": "Giữ được nội dung và dấu nguồn quan trọng hơn việc làm text nhìn đẹp.",
        "rows": [
            ("Đọc từng trang bằng pypdf", "Mỗi bản ghi có document_id, source, page, text và metadata."),
            ("Chuẩn hóa có kiểm soát", "Unicode NFC; gộp khoảng trắng ngang; thống nhất xuống dòng; bỏ dòng số trang đầu."),
            ("Ghi nhận lỗi trích xuất", "Một số từ bị tách như “nguyên li ệu”. Giữ nguyên, chưa sửa tự động bằng suy đoán.")],
        "remember": "Số trang luôn là trang vật lý trong PDF để đối chiếu.\n\nNếu đọc lỗi hoặc thiếu trang đã khai báo, pipeline ghi log và dừng.",
        "speech": "Em dùng pypdf để đọc riêng từng trang, thay vì gộp cả tài liệu thành một chuỗi. Sau đó em chuẩn hóa Unicode và khoảng trắng nhưng vẫn giữ cấu trúc dòng. Một số từ trong PDF bị tách chữ, em ghi nhận hạn chế này và chưa tự sửa vì có thể làm sai nội dung. Mỗi bản ghi luôn giữ nguồn và số trang."
    },
    {
        "title": "4. Chunk là gì? Vì sao phải chia nhỏ?",
        "subtitle": "Chunk là một đoạn nội dung dùng làm đơn vị tạo vector và truy xuất.",
        "rows": [
            ("Không dùng cả PDF làm một kết quả", "Người hỏi cần một đoạn có bằng chứng cụ thể, không phải toàn bộ 62 trang."),
            ("Chunk quá nhỏ / quá lớn", "Quá nhỏ dễ mất chủ thể và điều kiện; quá lớn chứa nhiều ý, khó tập trung vào câu hỏi."),
            ("Giữ liên kết về nguồn", "Mỗi chunk có ID ổn định, trang và vị trí ký tự; không chia vượt qua ranh giới trang.")],
        "remember": "Ví dụ: một đoạn giải thích vai trò của gia vị có thể là một chunk.\n\nMục tiêu là đoạn đủ ngữ cảnh nhưng vẫn tập trung vào một nhóm ý.",
        "speech": "Chunk có thể hiểu là một mẩu nhỏ của tài liệu. Việc chia nhỏ giúp hệ thống trả về bằng chứng cụ thể. Tuy nhiên, nếu chia quá ngắn thì dễ mất ý; chia quá dài thì có nhiều thông tin không liên quan. Vì vậy em thử hai công thức chia và đo xem công thức nào hỗ trợ truy xuất tốt hơn."
    },
    {
        "title": "5. Embedding biến văn bản thành vector",
        "subtitle": "Vector là một dãy số giúp hệ thống so sánh độ gần nhau về ý nghĩa.",
        "rows": [
            ("Model thật, chạy trên máy", "paraphrase-multilingual-MiniLM-L12-v2 qua FastEmbed, bản ONNX quantized."),
            ("Mỗi chunk → vector 384 chiều", "Model nhận text và trả về một dãy gồm 384 số; không dùng vector ngẫu nhiên."),
            ("Câu hỏi dùng cùng model", "So sánh vector câu hỏi với vector chunk bằng cosine similarity.")],
        "remember": "Cosine cao hơn nghĩa là gần hơn theo model.\n\nĐiểm tương đồng không phải xác suất câu trả lời đúng. Model vẫn có thể nhầm các đối tượng gần nghĩa.",
        "speech": "Embedding là bước chuyển đoạn văn thành một dãy số để so sánh ý nghĩa. Em sử dụng MiniLM đa ngữ chạy local và mỗi vector có 384 chiều. Câu hỏi cũng được xử lý bằng cùng model. Hệ thống dựa vào độ tương đồng cosine để xếp hạng, nhưng điểm cao không bảo đảm đoạn đó chứa đúng bằng chứng cần tìm."
    },
    {
        "title": "6. Qdrant lưu những gì?",
        "subtitle": "Vector giúp tìm kiếm; text và metadata giúp đọc kết quả và kiểm tra nguồn.",
        "rows": [
            ("Vector + text + metadata", "Lưu vector, nội dung chunk, document_id, source, page, content_group và offset."),
            ("Lưu bền vững trên ổ đĩa", "Database ở .local/qdrant; có ba collection day06_A, day06_B và day06_C."),
            ("Nạp lại và cập nhật", "Upsert theo stable ID chống trùng; refresh xóa điểm cũ rồi nạp lại để không giữ chunk lỗi thời.")],
        "remember": "Một chunk có thể mang metadata:\n\npage: 67\ncontent_group: trinh_bay\n\nĐóng rồi mở lại database vẫn truy xuất được.",
        "speech": "Qdrant là kho vector của bài. Em không chỉ lưu vector mà còn lưu text và metadata để hiển thị bằng chứng. Database nằm trên ổ đĩa nên dữ liệu vẫn còn sau khi tắt chương trình. Khi nạp lại, ID ổn định giúp không sinh bản ghi trùng; khi nguồn thay đổi, em refresh dữ liệu để loại các chunk cũ."
    },
    {
        "title": "7. Ba cấu hình A, B và C khác nhau thế nào?",
        "subtitle": "Cùng corpus, model và benchmark; thay đổi cách chia hoặc cách lọc để so sánh.",
        "rows": [
            ("A — Chia cố định", "Tối đa 700 ký tự; hai chunk liền nhau trùng 100 ký tự. Dễ cắt giữa từ hoặc câu."),
            ("B — Ưu tiên đoạn và câu", "Tối đa 700 ký tự, không overlap. Gom đơn vị theo ranh giới cấu trúc khi có thể."),
            ("C — Như B, thêm bộ lọc", "Dùng cùng chunk và vector B; chỉ lọc nhóm nội dung khi được cung cấp trước truy xuất.")],
        "remember": "A–B so sánh toàn bộ công thức chia: cả ranh giới và overlap.\n\nB–C chỉ khác bộ lọc. Nếu không chọn nhóm, C cho kết quả như B.",
        "speech": "Ở A, em chia theo số ký tự và dùng overlap để giữ một phần ngữ cảnh giữa hai đoạn. Ở B, em ưu tiên điểm kết thúc câu hoặc đoạn để giữ trọn ý hơn. C dùng cùng dữ liệu như B nhưng thêm bộ lọc nhóm. Việc giữ các yếu tố khác giống nhau giúp em phân tích ảnh hưởng của chiến lược dữ liệu."
    },
    {
        "title": "8. Bộ lọc metadata hoạt động ra sao?",
        "subtitle": "Lọc là giới hạn phạm vi ứng viên trước khi trả về các đoạn gần câu hỏi nhất.",
        "rows": [
            ("Không lọc: toàn bộ 62 trang", "Hỏi “Có những yêu cầu nào?” có thể gặp yêu cầu sơ chế, làm chín hoặc trình bày."),
            ("Lọc nhóm trình bày: trang 65–70", "C chỉ xét các chunk có content_group = trinh_bay, rồi xếp hạng theo độ tương đồng."),
            ("Phạm vi phải có trước", "Người dùng chọn nhóm theo nhu cầu; không lấy trang đáp án trong benchmark để lọc.")],
        "remember": "Bộ lọc giúp giảm kết quả ngoài phạm vi.\n\nNhưng trong một nhóm vẫn có nhiều đoạn khác nhau, nên hệ thống vẫn có thể chọn sai bằng chứng.",
        "speech": "Ví dụ khi em muốn tìm yêu cầu trình bày món ăn, em chọn nhóm trình bày. Qdrant chỉ xét các chunk thuộc nhóm đó, thay vì tìm cả tài liệu. Điều này giúp giảm nhiễu ngoài phạm vi. Tuy nhiên, lọc đúng nhóm chưa đủ, vì model vẫn phải tìm đúng đoạn trong nhóm đã chọn."
    },
    {
        "title": "9. Benchmark, dev, test và Hit@3",
        "subtitle": "Benchmark là bộ câu hỏi có bằng chứng chuẩn để đo chất lượng một cách nhất quán.",
        "rows": [
            ("20 câu hỏi có gold evidence", "Mỗi câu có đáp án kỳ vọng, trang nguồn và đoạn bằng chứng đã kiểm tra trong text."),
            ("15 dev → chọn; 5 test → kiểm tra", "Chọn cấu hình bằng dev, cố định lựa chọn rồi mới đánh giá test. Không huấn luyện lại model."),
            ("Hit@1 và Evidence Hit@3", "Hit@1 xét đoạn đầu. Hit@3 xét có ít nhất một đoạn trong top-3 đúng nguồn/trang và đủ evidence.")],
        "remember": "Có 3 câu dùng filter, trong đó 1 câu thuộc test.\n\nChốt hash câu hỏi/cấu hình trước thử nghiệm. Không sửa chiến lược dựa trên kết quả test.",
        "speech": "Để đánh giá, em xây 20 câu hỏi kèm đáp án và bằng chứng. Em dùng 15 câu dev để chọn cấu hình, sau đó dùng 5 câu test để kiểm tra. Với Hit@3, một câu được tính đúng khi ít nhất một trong ba chunk đầu đúng nguồn, đúng trang và chứa đủ bằng chứng. Chỉ trả về đúng trang nhưng thiếu ý vẫn chưa được tính hit."
    },
    {
        "title": "10. Kết quả thực nghiệm và lựa chọn",
        "subtitle": "Bảng dưới là Evidence Hit@3 từ lần chạy thật; không thay lựa chọn sau khi xem test.",
        "kind": "results",
        "remember": "Chọn C vì dev tốt nhất: 7/15.\n\nTest của C chỉ 1/5, thấp hơn A 2/5. Giữ kết quả này để phân tích, không chọn lại theo test.",
        "speech": "Trên tập dev, C đạt 7 trên 15 câu, cao nhất trong ba cấu hình nên được chọn. Sau khi chốt, C đạt 1 trên 5 câu test, trong khi A đạt 2 trên 5. Em vẫn giữ lựa chọn C theo dev. Tập test chỉ có năm câu, mỗi câu tương đương 20 điểm phần trăm nên chưa thể kết luận cấu hình nào tốt nhất một cách tổng quát."
    },
    {
        "title": "11. Audit: xem chất lượng ngoài điểm Hit@3",
        "subtitle": "Điểm số cho biết kết quả; audit giúp hiểu vì sao hệ thống đúng hoặc sai.",
        "rows": [
            ("Coherence — chunk có trọn ý không?", "10 vị trí nguồn × 3 cấu hình = 30 mẫu, xem có cắt câu hoặc thiếu chủ thể không."),
            ("Metadata — nguồn và nhóm có đúng không?", "5 câu test × top-3 × 3 cấu hình = 45 bản ghi đối chiếu với dữ liệu nguồn trích xuất."),
            ("Grounding — đủ bằng chứng để trả lời chưa?", "5 câu test × 3 cấu hình = 15 trường hợp xem top-3; chấm 0, 1 hoặc 2 và ghi lý do.")],
        "remember": "Audit định tính hiện do AI hỗ trợ và còn chờ học viên xác nhận.\n\nKhông gọi nhãn AI là chấm tay của học viên; không coi grounding là độ chính xác câu trả lời LLM.",
        "speech": "Ngoài retrieval, em xem chunk có trọn ý không, metadata có đúng không và bằng chứng có đủ để trả lời không. Phần này gọi là audit. Ví dụ một đoạn tìm đúng chủ đề nhưng thiếu điều kiện cần thiết thì grounding vẫn chưa tốt. Các nhận xét định tính hiện do AI hỗ trợ, em chưa xác nhận chấm thủ công nên báo cáo ghi rõ trạng thái này."
    },
    {
        "title": "12. Một trường hợp thất bại để giải thích",
        "subtitle": "Câu q17: trong phần gia vị, cỏ xạ hương được dùng cho những nhóm món nào?",
        "rows": [
            ("Bằng chứng cần tìm: trang 40", "Nêu cách dùng cỏ xạ hương cho nước dùng, món có mùi hôi và món chế biến nhiệt dài."),
            ("Kết quả C: trang 39, 39 và 38", "Đúng nhóm gia vị, nhưng các đoạn nói về mùi tây, hương thảo và những gia vị khác."),
            ("Kết luận từ lỗi", "Filter tuân thủ phạm vi nhưng retrieval vẫn nhầm thực thể. Có thể nghiên cứu hybrid/reranker ở vòng mới.")],
        "remember": "Không sửa mô hình hoặc bộ câu hỏi hiện tại để tăng điểm sau khi đã xem test.\n\nNếu thử cải tiến, chọn trên dev và cần tập test phù hợp cho vòng đánh giá mới.",
        "speech": "Một lỗi cụ thể là câu hỏi về cỏ xạ hương. Đáp án nằm ở trang 40, nhưng cấu hình C trả về trang 39 và 38, nói về các loại gia vị khác. Bộ lọc đã làm đúng nhiệm vụ giới hạn nhóm, nhưng model vẫn nhầm đối tượng. Đây là lý do cần đọc trace, thay vì chỉ nhìn thấy đúng chủ đề rồi kết luận truy xuất thành công."
    },
    {
        "title": "13. Demo giao diện và kết luận",
        "subtitle": "Chạy: .\\.venv\\Scripts\\python.exe -m starter.src.webapp --open",
        "rows": [
            ("Bước 1 — Tìm một câu hỏi", "Chọn B; nhập “Gia vị có vai trò gì trong món ăn?”; bấm Tìm bằng chứng."),
            ("Bước 2 — Kiểm tra nguồn", "Đọc top-3, xem điểm cosine, bấm số trang để đối chiếu PDF; điểm cao chưa chắc đủ ý."),
            ("Bước 3 — So sánh", "Chọn nhóm phối hợp nguyên liệu/gia vị và bật so sánh A/B/C. Bộ lọc chỉ áp dụng cho C.")],
        "remember": "Đã có pipeline chạy thật, index lưu bền vững và 6 kiểm thử kỹ thuật đạt.\n\nĐiều học được: giữ lineage, kiểm soát chất lượng, nạp lại không trùng và đánh giá bằng bằng chứng.",
        "speech": "Cuối cùng em demo một câu hỏi trên giao diện, đọc ba đoạn truy xuất và mở trang PDF để kiểm tra. Sau đó em so sánh A, B, C với cùng câu hỏi. Qua bài này, em thực hành cách tổ chức pipeline, giữ liên kết về nguồn và kiểm chứng kết quả. Hạn chế còn lại là lỗi text PDF, model nhỏ, test ít câu và phần nhãn thủ công chưa xác nhận. Em xin kết thúc phần trình bày."
    },
]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
SCALE = 144
BG, DARK, GREEN, MUTED, LINE = "F5F5EF", "203D34", "2E6550", "69796C", "DEE5D9"
images = []
fonts = {}


def box(x, y, w, h, fill, border=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = .1
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if border:
        shape.line.color.rgb = RGBColor.from_string(border)
    else:
        shape.line.fill.background()
    draw.rounded_rectangle((int(x*SCALE), int(y*SCALE), int((x+w)*SCALE), int((y+h)*SCALE)),
                           radius=12, fill="#"+fill, outline="#"+border if border else None, width=2)


def text(x, y, w, h, value, size=16, color=DARK, bold=False):
    key = (size, bold)
    if key not in fonts:
        fonts[key] = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", int(size*2))
    font = fonts[key]
    lines = []
    for paragraph in value.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = (current+" "+word).strip()
            if current and draw.textlength(candidate, font=font) > w*SCALE-4:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    line_height = size*2*1.24
    assert len(lines)*line_height <= h*SCALE+4, (page['title'], value, len(lines), h)
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.word_wrap = False
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i==0 else frame.add_paragraph()
        p.text = line
        p.font.name, p.font.size, p.font.bold = "Segoe UI", Pt(size), bold
        p.font.color.rgb = RGBColor.from_string(color)
        p.line_spacing = Pt(size*1.24)
        p.space_before = p.space_after = Pt(0)
        draw.text((x*SCALE, y*SCALE+i*line_height), line, fill="#"+color, font=font)


for index, page in enumerate(PAGES, 1):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(BG)
    image = Image.new("RGB", (1920, 1080), "#"+BG)
    draw = ImageDraw.Draw(image)
    text(.55,.20,11.8,.23,"DATA INGESTION ENGINEERING  /  TRẦN MINH TÂN · 2A202603688",10,GREEN,True)
    text(.55,.66,12.2,.56,page['title'],26,DARK,True)
    text(.55,1.29,12.1,.43,page['subtitle'],12,MUTED)
    box(.55,1.98,7.65,3.18,"FFFFFF",LINE)
    kind = page.get('kind')
    if kind == 'pipeline':
        for i,(title,body) in enumerate([
            ('01 · Đọc PDF','Text từng trang'),('02 · Chuẩn hóa','Giữ nội dung & nguồn'),('03 · Chia chunk','Đoạn nhỏ có ID'),
            ('04 · Embedding','Vector 384 chiều'),('05 · Qdrant','Lưu vector + metadata'),('06 · Truy xuất','Câu hỏi → top-3')]):
            x = .80+(i%3)*2.44
            y = 2.26+(i//3)*1.28
            box(x,y,2.22,.94,'EAF0E5')
            text(x+.13,y+.11,1.97,.33,title,15,GREEN,True)
            text(x+.13,y+.55,1.97,.28,body,10,MUTED)
    elif kind == 'results':
        text(.84,2.22,2.0,.32,'Cấu hình',13,MUTED,True)
        text(3.10,2.22,2.02,.32,'Dev Hit@3',13,MUTED,True)
        text(5.52,2.22,2.02,.32,'Test Hit@3',13,MUTED,True)
        for i,s in enumerate('ABC'):
            y = 2.91+i*.65
            if s=='C':
                box(.75,y-.07,7.22,.53,'EAF0E5')
            dev = next(r for r in METRICS if r['strategy']==s and r['split']=='dev')
            test = next(r for r in METRICS if r['strategy']==s and r['split']=='test')
            text(.90,y,1.9,.34,s+' · chọn' if s=='C' else s,17,GREEN if s=='C' else DARK,True)
            text(3.10,y,2.1,.34,f"{dev['hit3_n']}/{dev['n']} · {dev['hit3']:.1%}",17,DARK,s=='C')
            text(5.52,y,2.1,.34,f"{test['hit3_n']}/{test['n']} · {test['hit3']:.0%}",17,DARK,s=='C')
        text(.90,4.82,6.9,.23,'Tập test nhỏ: một câu = 20 điểm phần trăm.',10,MUTED)
    else:
        for i,(title,body) in enumerate(page['rows']):
            y = 2.20+i*.96
            text(.85,y,7.03,.35,title,16,GREEN,True)
            text(.85,y+.39,7.03,.51,body,12,DARK)
    box(8.43,1.98,4.35,3.18,'E8EDDF')
    text(8.70,2.21,3.8,.30,'ĐIỂM CẦN NHỚ',11,GREEN,True)
    text(8.70,2.78,3.78,2.12,page['remember'],14,DARK)
    box(.55,5.43,12.23,1.38,'FFFFFF',LINE)
    text(.80,5.58,11.7,.25,'LỜI TRÌNH BÀY',10,GREEN,True)
    text(.80,5.95,11.7,.76,page['speech'],12,DARK)
    text(.55,7.12,10,.23,'PDF → text → chunk → embedding → Qdrant → bằng chứng có nguồn',10,MUTED)
    text(11.88,7.10,.92,.27,f'{index:02} / {len(PAGES):02}',11,GREEN,True)
    slide.notes_slide.notes_text_frame.text = page['speech']+'\n\nĐiểm cần nhớ:\n'+page['remember']
    image.save(OUT / f'detailed_slide_{index:02}.png')
    images.append(image)

base = OUT / '2A202603688_TranMinhTan_ThuyetTrinh_ChiTiet'
prs.save(base.with_suffix('.pptx'))
images[0].save(base.with_suffix('.pdf'), 'PDF', resolution=144, save_all=True, append_images=images[1:])
contact = Image.new('RGB',(1200, int((len(images)+1)//2)*338), '#DEE5D9')
for i,im in enumerate(images):
    thumb = im.resize((592,333))
    contact.paste(thumb,((i%2)*600,(i//2)*338))
contact.save(OUT/'ThuyetTrinh_ChiTiet_preview.jpg',quality=90)
script = '# Lời thuyết trình theo từng slide\n\nCó thể đọc phần “Lời trình bày” ngay trên mỗi slide hoặc dùng bản này.\n\n'
for i,p in enumerate(PAGES,1):
    script += f"## Slide {i}: {p['title']}\n\n{p['speech']}\n\nĐiểm cần nhớ: {p['remember']}\n\n"
(OUT/'LOI_THUYET_TRINH.md').write_text(script.rstrip()+'\n',encoding='utf-8')
check = Presentation(base.with_suffix('.pptx'))
assert len(check.slides)==len(PAGES)
for s in check.slides:
    assert any('LỜI TRÌNH BÀY' in sh.text for sh in s.shapes if sh.has_text_frame)
    for sh in s.shapes:
        assert sh.left >=0 and sh.top >=0
        assert sh.left+sh.width <= prs.slide_width+Inches(.01)
        assert sh.top+sh.height <= prs.slide_height+Inches(.01)
print(f'Created {len(PAGES)} editable slides with visible speaking text, PDF, previews and script.')
print(base.with_suffix('.pptx'))
