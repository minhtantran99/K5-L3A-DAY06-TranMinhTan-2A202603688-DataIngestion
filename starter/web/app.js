const $ = (selector) => document.querySelector(selector);
const form = $('#search-form');
const question = $('#question');
const submit = $('#submit');
const group = $('#group');
const compare = $('#compare');
const list = $('#result-list');
const error = $('#error');
let status = null;
let busy = false;
const labels = {A: 'Chunk cố định', B: 'Gom đoạn & câu', C: 'Gom đoạn & câu + bộ lọc'};

function selectedStrategy() { return form.elements.strategy.value; }
function updateFilter() {
  group.disabled = selectedStrategy() !== 'C' && !compare.checked;
  $('#filter-note').textContent = compare.checked
    ? 'Khi so sánh, bộ lọc chỉ áp dụng cho C. A và B tìm trên toàn bộ giáo trình.'
    : group.disabled ? 'Chọn C để giới hạn theo nhóm nội dung.' : 'Bộ lọc áp dụng cho cấu hình C.';
}
function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function render(data) {
  list.replaceChildren();
  let hitCount = 0;
  data.results.forEach(result => {
    const section = node('section', 'result-group');
    const heading = node('div', 'group-heading');
    heading.append(node('h3', '', `Cấu hình ${result.strategy}`), node('span', '', labels[result.strategy]));
    section.append(heading);
    if (!result.hits.length) section.append(node('p', 'hint', 'Không có đoạn nào trong phạm vi đã chọn.'));
    result.hits.forEach((hit, index) => {
      hitCount++;
      const card = node('article', 'hit');
      card.append(node('span', 'rank', String(index + 1)));
      const content = node('div');
      const top = node('div', 'hit-top');
      const source = node('div', 'hit-source');
      const link = node('a', '', `Trang ${hit.page} ↗`);
      link.href = `/source.pdf#page=${Number(hit.page)}`;
      link.target = '_blank'; link.rel = 'noopener';
      source.append(link, node('span', 'tag', status.groups[hit.metadata.content_group] || hit.metadata.content_group));
      const score = node('span', 'score', `Cosine ${Number(hit.score).toFixed(3)}`);
      score.title = 'Độ tương đồng vector, không phải xác suất câu trả lời đúng.';
      top.append(source, score);
      content.append(top, node('p', 'hit-text', hit.text));
      const details = node('details');
      details.append(node('summary', '', 'Chi tiết truy vết'));
      details.append(node('p', '', `Nguồn: ${hit.source}`));
      details.append(node('p', '', `Vị trí ký tự: ${hit.metadata.start_char}–${hit.metadata.end_char}`));
      details.append(node('p', 'chunk-id', `Chunk ID: ${hit.chunk_id}`));
      content.append(details); card.append(content); section.append(card);
    });
    list.append(section);
  });
  $('#empty').hidden = true;
  $('#result-query').hidden = false;
  $('#result-query').textContent = `Câu hỏi: ${data.question}`;
  $('#result-meta').textContent = `${hitCount} đoạn · ${data.elapsed_ms.toLocaleString('vi-VN')} ms`;
  $('#live-status').textContent = `Đã tìm thấy ${hitCount} đoạn bằng chứng.`;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (busy || !status) return;
  if (!question.value.trim()) { question.focus(); return; }
  busy = true; submit.disabled = true; submit.textContent = 'Đang tìm…';
  $('.results').setAttribute('aria-busy', 'true');
  $('#live-status').textContent = 'Đang tìm bằng chứng trong giáo trình.';
  error.hidden = true;
  try {
    const response = await fetch('/api/search', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: question.value, strategy: selectedStrategy(),
        group: group.disabled ? '' : group.value, compare: compare.checked})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Không thể truy xuất.');
    render(data);
  } catch (exception) {
    error.textContent = exception.message || 'Không kết nối được máy chủ. Kiểm tra terminal rồi thử lại.';
    error.hidden = false;
    $('#live-status').textContent = 'Truy xuất chưa thành công.';
  } finally {
    busy = false; submit.disabled = false;
    submit.textContent = 'Tìm bằng chứng →';
    $('.results').setAttribute('aria-busy', 'false');
  }
});

document.querySelectorAll('input[name=strategy]').forEach(input => input.addEventListener('change', updateFilter));
compare.addEventListener('change', updateFilter);
document.querySelectorAll('.example').forEach(button => button.addEventListener('click', () => {
  question.value = button.dataset.question; question.focus();
}));
question.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); form.requestSubmit(); }
});
updateFilter();
(async () => {
  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw new Error('Không đọc được trạng thái kho tài liệu.');
    status = await response.json();
    $('#connection').classList.add('ready');
    $('#connection-text').textContent = 'Sẵn sàng · Local';
    $('#system-info').textContent = `MiniLM đa ngữ · ${status.dimensions} chiều · ${status.store}`;
    submit.disabled = false;
  } catch (exception) {
    $('#connection-text').textContent = 'Chưa kết nối';
    error.textContent = `${exception.message} Hãy chạy giao diện bằng run_ui.ps1.`;
    error.hidden = false;
  }
})();
