---
name: "CNKI Research Toolkit"
description: "Unified CNKI (中国知网) skill for paper search, advanced search, result parsing, pagination/sorting, paper detail extraction, PDF/CAJ download, Zotero/RIS/GB export, journal search, journal indexing query, and journal issue TOC browsing."
argument-hint: "[CNKI task: search/download/export/journal/index/toc + query or URL]"
---

# CNKI Research Toolkit（中国知网综合工具）

This unified skill combines the original CNKI skills into one command/workflow. Use it whenever the user asks for CNKI/知网 literature search, advanced search, result parsing, pagination/sorting, paper details, downloading, citation export/Zotero, journal lookup, journal inclusion/indexing, or journal issue TOC browsing.

## Intent routing

Choose the matching section below based on the user request:

| User intent | Use section |
|---|---|
| Search papers by keyword/topic | CNKI Basic Search |
| Precise search with author/title/journal/year/source filters | CNKI Advanced Search |
| Extract current search result list | CNKI Parse Search Results |
| Next/previous/page N or sort by date/citations/downloads | CNKI Results Pagination and Sorting |
| Extract one paper's full metadata/abstract/keywords | CNKI Paper Detail Extraction |
| Download PDF/CAJ | CNKI Paper Download |
| Export to Zotero/RIS/GB citation | CNKI Export & Zotero Integration |
| Search journals by name/ISSN/CN/sponsor | CNKI Journal Search |
| Check journal inclusion/indexing/impact factors | CNKI Journal Indexing Query |
| Browse journal issues/table of contents/download original TOC | CNKI Journal Table of Contents |

## Global rules

- Prefer direct `navigate_page` to known URLs over clicking result links; CNKI often opens new tabs and wastes tool calls.
- Prefer single `evaluate_script` calls that include waits and extraction; avoid separate `wait_for` unless a section explicitly needs it.
- Captcha detection: check `#tcaptcha_transform_dy` and treat it as active only when `getBoundingClientRect().top >= 0`. Hidden SDK nodes at `top: -1000000px` are not active captchas.
- If an active captcha appears, tell the user to solve it manually in Chrome and continue after confirmation.
- Download/export operations may require CNKI login and permissions. Zotero export requires Zotero desktop running on `127.0.0.1:23119`.

---



<!-- Source skill: cnki-search -->

# CNKI Basic Search

Search CNKI for papers using keyword(s). Returns result count and structured result list (titles, URLs, authors, journal, date) in a single call.

## Arguments

$ARGUMENTS contains the search keyword(s) in Chinese or English.

## Steps

### 1. Navigate

Use `mcp__chrome-devtools__navigate_page` → `https://kns.cnki.net/kns8s/search`

### 2. Search + extract results (single evaluate_script, NO wait_for)

Replace `YOUR_KEYWORDS` with actual search terms:

```javascript
async () => {
  const query = "YOUR_KEYWORDS";

  // Wait for search input (replaces wait_for)
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.querySelector('input.search-input')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // Check captcha (only if visible on screen, not hidden SDK at top:-1000000)
  const outer = document.querySelector('#tcaptcha_transform_dy');
  if (outer && outer.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  // Fill and submit (verified selectors: input.search-input, input.search-btn)
  const input = document.querySelector('input.search-input');
  input.value = query;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  document.querySelector('input.search-btn')?.click();

  // Wait for results
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.body.innerText.includes('条结果')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // Check captcha again
  const outer2 = document.querySelector('#tcaptcha_transform_dy');
  if (outer2 && outer2.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  // Extract current page results (merged parse-results)
  const rows = document.querySelectorAll('.result-table-list tbody tr');
  const checkboxes = document.querySelectorAll('.result-table-list tbody input.cbItem');
  const results = Array.from(rows).map((row, i) => {
    const titleLink = row.querySelector('td.name a.fz14');
    const authors = Array.from(row.querySelectorAll('td.author a.KnowledgeNetLink') || []).map(a => a.innerText?.trim());
    const journal = row.querySelector('td.source a')?.innerText?.trim() || '';
    const date = row.querySelector('td.date')?.innerText?.trim() || '';
    const citations = row.querySelector('td.quote')?.innerText?.trim() || '';
    const downloads = row.querySelector('td.download')?.innerText?.trim() || '';
    return {
      n: i + 1,
      title: titleLink?.innerText?.trim() || '',
      href: titleLink?.href || '',
      exportId: checkboxes[i]?.value || '',
      authors: authors.join('; '),
      journal,
      date,
      citations,
      downloads
    };
  });

  return {
    query,
    total: document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1] || '0',
    page: document.querySelector('.countPageMark')?.innerText || '1/1',
    results
  };
}
```

### 3. Report

Present results as a numbered list:

```
Searched CNKI for "$ARGUMENTS": found {total} results (page {page}).

1. {title}
   Authors: {authors} | Journal: {journal} | Date: {date}
   Citations: {citations} | Downloads: {downloads}

2. ...
```

### 4. Follow-up: navigate to a paper

When the user wants to open or download a specific paper, use `navigate_page` with the result's `href` URL directly — do NOT click the link (clicking opens a new tab and wastes 3 extra tool calls for tab management).

## Captcha detection

Check `#tcaptcha_transform_dy` element's `getBoundingClientRect().top >= 0`.
Tencent captcha SDK preloads DOM at `top: -1000000px` (off-screen, not active).
Only return `error: 'captcha'` when `top >= 0` (actually visible to user).

## Verified selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Search input | `input.search-input` | id=`txt_search`, placeholder "中文文献、外文文献" |
| Search button | `input.search-btn` | type="button" |
| Result count | `.pagerTitleCell` | text "共找到 X 条结果" |
| Page indicator | `.countPageMark` | text "1/300" |
| Result rows | `.result-table-list tbody tr` | Each row = one paper |
| Title link | `td.name a.fz14` | Paper title with href |
| Authors | `td.author a.KnowledgeNetLink` | Author name links |
| Journal | `td.source a` | Journal/source link |
| Date | `td.date` | Publication date text |
| Citations | `td.quote` | Citation count |
| Downloads | `td.download` | Download count |

## Batch export to Zotero

When user wants to save results to Zotero, use batch export directly from the results page — **do NOT navigate to each detail page**. The `exportId` in results equals the detail page's `#export-id`. Call `cnki-export` skill with batch mode (Step 1B). See cnki-export SKILL.md for details.

## Tool calls: 2 (navigate + evaluate_script)


<!-- Source skill: cnki-advanced-search -->

# CNKI Advanced Search (高级检索)

Perform a filtered search on CNKI using the **old-style** advanced search interface (only interface with source category checkboxes).

## Arguments

`$ARGUMENTS` describes the search criteria in natural language. Parse it to identify:
- **Subject keywords** (主题) — default field
- **Title keywords** (篇名)
- **Keywords** (关键词)
- **Author name** (作者) — separate field `#au_1_value1`
- **Journal/source** (文献来源) — separate field `#magazine_value1`
- **Date range** (时间范围) — `#startYear` / `#endYear`
- **Source category** (来源类别：SCI, EI, 北大核心, CSSCI, CSCD)

## Steps

### 1. Navigate

Use `mcp__chrome-devtools__navigate_page` → `https://kns.cnki.net/kns/AdvSearch?classid=7NS01R8M`

### 2. Search + get results (single async evaluate_script)

Replace placeholder values with actual search criteria:

```javascript
async () => {
  // --- Config: fill in actual values ---
  const query = "KEYWORDS";          // row 1 search keywords
  const fieldType = "SU";           // SU=主题, TI=篇名, KY=关键词, TKA=篇关摘, AB=摘要
  const query2 = "";                // row 2 keywords (optional, "" to skip)
  const fieldType2 = "KY";          // row 2 field type
  const rowLogic = "AND";           // AND=并且, OR=或者, NOT=不含 (between row 1 and 2)
  const sourceTypes = ["CSSCI"];    // any of: "SCI", "EI", "hx", "CSSCI", "CSCD" ([] = all)
  const startYear = "";             // e.g. "2020" or "" for no limit
  const endYear = "";               // e.g. "2025" or "" for no limit
  const author = "";                // author name or ""
  const journal = "";               // journal name or ""

  // --- Wait for form ---
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.querySelector('#txt_1_value1')) r(); else if (n++ > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // Captcha check
  const cap = document.querySelector('#tcaptcha_transform_dy');
  if (cap && cap.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  const selects = Array.from(document.querySelectorAll('select')).filter(s => s.offsetParent !== null);

  // --- Source type: uncheck 全部, check targets ---
  if (sourceTypes.length > 0) {
    const gjAll = document.querySelector('#gjAll');
    if (gjAll && gjAll.checked) gjAll.click();
    for (const st of sourceTypes) {
      const cb = document.querySelector('#' + st);
      if (cb && !cb.checked) cb.click();
    }
  }

  // --- Row 1: field type + keyword ---
  selects[0].value = fieldType;
  selects[0].dispatchEvent(new Event('change', { bubbles: true }));
  const input = document.querySelector('#txt_1_value1');
  input.value = query;
  input.dispatchEvent(new Event('input', { bubbles: true }));

  // --- Row 2: field type + keyword (optional) ---
  if (query2) {
    selects[5].value = rowLogic; // row logic: AND/OR/NOT
    selects[5].dispatchEvent(new Event('change', { bubbles: true }));
    selects[6].value = fieldType2;
    selects[6].dispatchEvent(new Event('change', { bubbles: true }));
    const input2 = document.querySelector('#txt_2_value1');
    input2.value = query2;
    input2.dispatchEvent(new Event('input', { bubbles: true }));
  }

  // --- Author (optional) ---
  if (author) {
    const auInput = document.querySelector('#au_1_value1');
    if (auInput) { auInput.value = author; auInput.dispatchEvent(new Event('input', { bubbles: true })); }
  }

  // --- Journal (optional) ---
  if (journal) {
    const magInput = document.querySelector('#magazine_value1');
    if (magInput) { magInput.value = journal; magInput.dispatchEvent(new Event('input', { bubbles: true })); }
  }

  // --- Date range (optional) ---
  if (startYear) { selects[14].value = startYear; selects[14].dispatchEvent(new Event('change', { bubbles: true })); }
  if (endYear) { selects[15].value = endYear; selects[15].dispatchEvent(new Event('change', { bubbles: true })); }

  // --- Submit ---
  document.querySelector('div.search')?.click();

  // Wait for results
  await new Promise((r, j) => {
    let n = 0;
    const c = () => {
      if (document.body.innerText.includes('条结果')) r();
      else if (n++ > 40) j('timeout');
      else setTimeout(c, 500);
    };
    setTimeout(c, 2000);
  });

  // Captcha check again
  const cap2 = document.querySelector('#tcaptcha_transform_dy');
  if (cap2 && cap2.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  return {
    query, fieldType, query2, fieldType2, rowLogic,
    sourceTypes, startYear, endYear, author, journal,
    total: document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1] || '0',
    page: document.querySelector('.countPageMark')?.innerText || '1/1',
    url: location.href
  };
}
```

### 3. Report

> Advanced search: "{query}" ({fieldType}) + source: {sourceTypes} → {total} results.

## Tool calls: 2 (navigate + evaluate_script)

## Verified selectors (old-style interface)

### Form fields

| Element | Selector / Select index | Notes |
|---------|------------------------|-------|
| 行1 字段类型 | `selects[0]` | SU=主题, TI=篇名, KY=关键词, TKA=篇关摘, AB=摘要 |
| 行1 关键词 | `#txt_1_value1` | main keyword input |
| 行1 行内第二词 | `#txt_1_value2` | same-row AND/OR/NOT with first keyword |
| 行1 行内逻辑 | `selects[2]` | AND=并含, OR=或含, NOT=不含 |
| **行间逻辑** | `selects[5]` | **AND=并且, OR=或者, NOT=不含** |
| 行2 字段类型 | `selects[6]` | same options as row 1 |
| 行2 关键词 | `#txt_2_value1` | second row keyword |
| 行2 行内第二词 | `#txt_2_value2` | |
| 作者 | `#au_1_value1` | placeholder "中文名/英文名/拼音" |
| 作者单位 | `#au_1_value2` | placeholder "全称/简称/曾用名" |
| 文献来源 | `#magazine_value1` | placeholder "期刊名称/ISSN/CN" |
| 基金 | `#base_value1` | |
| 起始年 | `selects[14]` / `#startYear` | `<select>` 1915-2026 |
| 结束年 | `selects[15]` / `#endYear` | `<select>` 2026-1915 |
| 检索按钮 | `div.search` | NOT input/button |

### Source type checkboxes (来源类型)

| 来源 | Checkbox ID | Notes |
|------|-------------|-------|
| 全部期刊 | `#gjAll` | 默认勾选，选其他前需取消 |
| SCI来源期刊 | `#SCI` | value="Y" |
| EI来源期刊 | `#EI` | value="Y" |
| 北大核心期刊 | `#hx` | value="Y" |
| CSSCI | `#CSSCI` | value="Y" |
| CSCD | `#CSCD` | value="Y" |

Multiple source types can be checked simultaneously (OR logic).

### Results

| Element | Selector | Notes |
|---------|----------|-------|
| Result count | `.pagerTitleCell` | text "共找到 X 条结果" |
| Page indicator | `.countPageMark` | text "1/300" |

## Captcha detection

Check `#tcaptcha_transform_dy` element's `getBoundingClientRect().top >= 0`.

## Important Notes

- **Must use old-style URL** (`kns.cnki.net/kns/AdvSearch`). New interface (`kns8s/AdvSearch`) has NO source category checkboxes.
- The `classid=7NS01R8M` parameter ensures the correct form layout loads.
- Results page is compatible with `cnki-parse-results` and `cnki-navigate-pages` skills.


<!-- Source skill: cnki-parse-results -->

# CNKI Parse Search Results

Extract structured paper data from the current CNKI search results page.

## Prerequisites

The current Chrome page must be a CNKI search results page (URL contains `kns.cnki.net` and page shows "条结果").

## Steps

### 1. Verify we are on a results page

Use `mcp__chrome-devtools__take_snapshot`. Verify the page contains "条结果". If not, inform the user that no search results page is currently open.

Check for captcha ("拖动下方拼图完成验证") - if found, notify user to solve it manually.

### 2. Extract results via JavaScript

Use `mcp__chrome-devtools__evaluate_script` with this function:

```javascript
() => {
  const rows = document.querySelectorAll('.result-table-list tbody tr');
  const checkboxes = document.querySelectorAll('.result-table-list tbody input.cbItem');
  const results = Array.from(rows).map((row, index) => {
    const nameCell = row.querySelector('td.name');
    const titleLink = nameCell?.querySelector('a.fz14');
    const authorCell = row.querySelector('td.author');
    const sourceCell = row.querySelector('td.source');
    const dateCell = row.querySelector('td.date');
    const dataCell = row.querySelector('td.data');
    const quoteCell = row.querySelector('td.quote');
    const downloadCell = row.querySelector('td.download');
    const isOnlineFirst = !!nameCell?.querySelector('.marktip');

    return {
      number: index + 1,
      title: titleLink?.innerText?.trim() || '',
      url: titleLink?.href || '',
      exportId: checkboxes[index]?.value || '',
      authors: Array.from(authorCell?.querySelectorAll('a.KnowledgeNetLink') || []).map(a => a.innerText?.trim()),
      journal: sourceCell?.querySelector('a')?.innerText?.trim() || '',
      date: dateCell?.innerText?.trim() || '',
      database: dataCell?.innerText?.trim() || '',
      citations: quoteCell?.innerText?.trim() || '',
      downloads: downloadCell?.innerText?.trim() || '',
      isOnlineFirst: isOnlineFirst
    };
  });

  const totalText = document.querySelector('.pagerTitleCell')?.innerText || '';
  const totalMatch = totalText.match(/([\d,]+)/);
  const pageInfo = document.querySelector('.countPageMark')?.innerText || '';

  return {
    papers: results,
    totalCount: totalMatch ? totalMatch[1] : 'unknown',
    pageInfo: pageInfo
  };
}
```

### 3. Present results

Format as a numbered list:

```
CNKI search results ({totalCount} total, page {pageInfo}):

1. {title} {isOnlineFirst ? "[网络首发]" : ""}
   Authors: {authors joined by "; "}
   Journal: {journal} | Date: {date} | Type: {database}
   Citations: {citations} | Downloads: {downloads}
   URL: {url}

2. ...
```

### 4. Fallback: snapshot-based parsing

If JavaScript returns empty (DOM structure changed), use `mcp__chrome-devtools__take_snapshot` and parse the accessibility tree manually:

Look for the repeating pattern:
- `checkbox` → `StaticText` (number) → `link` with URL containing `kcms2/article/abstract` (title) → `link`s with URL containing `kcms2/author/detail` (authors) → `link` with URL containing `navi.cnki.net/knavi/detail` (journal) → `StaticText` (date) → `StaticText` (database type)

## Verified DOM Selectors (CNKI uses jQuery, stable semantic class names)

| Data       | Selector                         | Notes                      |
|------------|----------------------------------|----------------------------|
| Table      | `.result-table-list tbody tr`    | Each row = one paper       |
| Checkbox   | `input.cbItem`                   | value = export encrypted ID |
| Number     | `td.seq`                         | Row sequence number        |
| Title      | `td.name a.fz14`                 | Paper title link           |
| Authors    | `td.author a.KnowledgeNetLink`   | Author name links          |
| Journal    | `td.source a`                    | Journal/source link        |
| Date       | `td.date`                        | Publication date text      |
| DB Type    | `td.data`                        | Database type (期刊/学位论文) |
| Citations  | `td.quote`                       | Citation count             |
| Downloads  | `td.download`                    | Download count             |
| Online 1st | `td.name .marktip`               | "网络首发" label            |
| Total      | `.pagerTitleCell`                 | "共找到 X 条结果"           |
| Page       | `.countPageMark`                  | "1/300" format             |


<!-- Source skill: cnki-navigate-pages -->

# CNKI Results Pagination and Sorting

All operations use a single async `evaluate_script` — no snapshot or wait_for needed.

## Arguments

`$ARGUMENTS` should be one of:
- `next` / `previous` / `page N` — pagination
- `sort by date` / `sort by citations` / `sort by downloads` / `sort by relevance` / `sort by comprehensive` — sorting

## Pagination (single evaluate_script)

Replace `ACTION_HERE` with `"next"`, `"previous"`, or `"page 3"`:

```javascript
async () => {
  const cap = document.querySelector('#tcaptcha_transform_dy');
  if (cap && cap.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  const action = "ACTION_HERE";
  const pageLinks = document.querySelectorAll('.pages a');
  const prevMark = document.querySelector('.countPageMark')?.innerText;

  if (action === 'next') {
    const next = Array.from(pageLinks).find(a => a.innerText.trim() === '下一页');
    if (!next) return { error: 'no_next_page' };
    next.click();
  } else if (action === 'previous') {
    const prev = Array.from(pageLinks).find(a => a.innerText.trim() === '上一页');
    if (!prev) return { error: 'no_previous_page' };
    prev.click();
  } else {
    const num = action.replace(/\D/g, '');
    const target = Array.from(pageLinks).find(a => a.innerText.trim() === num);
    if (!target) return { error: 'page_not_found', available: Array.from(pageLinks).map(a => a.innerText.trim()) };
    target.click();
  }

  // Wait for page change
  await new Promise((r, j) => {
    let n = 0;
    const c = () => {
      const mark = document.querySelector('.countPageMark')?.innerText;
      if (mark && mark !== prevMark) r();
      else if (++n > 30) j('timeout');
      else setTimeout(c, 500);
    };
    setTimeout(c, 1000);
  });

  const cap2 = document.querySelector('#tcaptcha_transform_dy');
  if (cap2 && cap2.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  return {
    action,
    total: document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1] || '0',
    page: document.querySelector('.countPageMark')?.innerText || '?',
    url: location.href
  };
}
```

## Sorting (single evaluate_script)

Replace `SORT_HERE` with `"relevance"`, `"date"`, `"citations"`, `"downloads"`, or `"comprehensive"`:

```javascript
async () => {
  const cap = document.querySelector('#tcaptcha_transform_dy');
  if (cap && cap.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  const sortBy = "SORT_HERE";
  const idMap = {
    'relevance': 'FFD', 'date': 'PT',
    'citations': 'CF', 'downloads': 'DFR', 'comprehensive': 'ZH'
  };

  const liId = idMap[sortBy];
  if (!liId) return { error: 'invalid_sort', valid: Object.keys(idMap) };

  const li = document.querySelector('#orderList li#' + liId);
  if (!li) return { error: 'sort_option_not_found' };

  const prevMark = document.querySelector('.countPageMark')?.innerText;
  li.click();

  // Wait for results to refresh (page resets to 1)
  await new Promise((r, j) => {
    let n = 0;
    const c = () => {
      const mark = document.querySelector('.countPageMark')?.innerText;
      if (mark && mark !== prevMark) r();
      else if (++n > 30) j('timeout');
      else setTimeout(c, 500);
    };
    setTimeout(c, 1000);
  });

  return {
    sortBy,
    total: document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1] || '0',
    page: document.querySelector('.countPageMark')?.innerText || '?',
    activeLi: document.querySelector('#orderList li.cur')?.innerText?.trim(),
    url: location.href
  };
}
```

## Output

> Navigated to page {page}. Total {total} results.
> Results now sorted by {sortBy}.

## Tool calls: 1 (evaluate_script only)

## Verified selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Page links | `.pages a` | numbers + 上一页/下一页 |
| Current page | `.pages a.cur` | |
| Next page | text `下一页`, class `pagesnums` | |
| Page counter | `.countPageMark` | text "1/300" |
| Sort container | `#sortList` (`.order-group`) | |
| Sort options | `#orderList li` | click to sort |
| 相关度 | `li#FFD` | data-sort="FFD" |
| 发表时间 | `li#PT` | data-sort="PT" |
| 被引 | `li#CF` | data-sort="CF" |
| 下载 | `li#DFR` | data-sort="DFR" |
| 综合 | `li#ZH` | data-sort="ZH" |
| Active sort | `#orderList li.cur` | has class `cur` |

## Captcha detection

Check `#tcaptcha_transform_dy` element's `getBoundingClientRect().top >= 0`.
Only active when `top >= 0` (visible). Pre-loaded SDK sits at `top: -1000000px`.


<!-- Source skill: cnki-paper-detail -->

# CNKI Paper Detail Extraction

Extract complete metadata from a CNKI paper detail page.

## Arguments

`$ARGUMENTS` is optionally a CNKI paper detail URL (containing `kcms2/article/abstract`). If not provided, assumes the current page is already a paper detail page.

## Steps

### 1. Navigate to the paper page (if URL provided)

If `$ARGUMENTS` contains a URL:
- Use `mcp__chrome-devtools__navigate_page` with the URL.
- Use `mcp__chrome-devtools__wait_for` with text `["摘要"]` and timeout 15000.

### 2. Check for captcha

Use `mcp__chrome-devtools__take_snapshot`. If "拖动下方拼图完成验证" found, notify user:

> CNKI 正在显示滑块验证码。请在 Chrome 浏览器中手动完成拼图验证，完成后告诉我继续。

### 3. Extract paper metadata via JavaScript

Use `mcp__chrome-devtools__evaluate_script` with this function:

```javascript
() => {
  const brief = document.querySelector('.brief');
  if (!brief) return { error: 'Paper detail section (.brief) not found' };

  // Title
  const title = brief.querySelector('h1')?.innerText?.trim()
    ?.replace(/\s*附视频\s*$/, '')  // remove "附视频" suffix
    ?.replace(/\s*网络首发\s*$/, ''); // remove "网络首发" suffix

  // Authors - first h3.author contains author links with sup tags
  const authorH3s = brief.querySelectorAll('h3.author');
  const authorSection = authorH3s[0];
  const authors = [];
  if (authorSection) {
    const authorLinks = authorSection.querySelectorAll('a');
    authorLinks.forEach(a => {
      const name = a.innerText?.replace(/\d+$/, '').trim();
      const supMatch = a.innerText?.match(/(\d+)$/);
      const affiliationNum = supMatch ? supMatch[1] : '';
      authors.push({ name, affiliationNum });
    });
  }

  // Affiliations - second h3.author contains org links
  const affiliations = [];
  if (authorH3s.length > 1) {
    const orgLinks = authorH3s[1].querySelectorAll('a');
    orgLinks.forEach(a => {
      affiliations.push(a.innerText?.trim());
    });
  }

  // Abstract
  const abstractEl = document.querySelector('.abstract-text');
  const abstract = abstractEl?.innerText?.trim() || '';

  // Keywords
  const keywordsP = document.querySelector('p.keywords');
  const keywords = keywordsP
    ? Array.from(keywordsP.querySelectorAll('a')).map(a => a.innerText?.replace(/;$/, '').trim())
    : [];

  // Fund
  const fundsP = document.querySelector('p.funds');
  const fund = fundsP?.innerText?.trim() || '';

  // Classification code
  const clcCode = document.querySelector('.clc-code');
  const classification = clcCode?.innerText?.trim() || '';

  // Journal/source
  const docTop = document.querySelector('.doc-top');
  const journal = docTop?.querySelector('a')?.innerText?.trim() || '';

  // Online first / publication info
  const headTime = document.querySelector('.head-time');
  const pubInfo = headTime?.innerText?.trim() || '';

  // Is online first?
  const isOnlineFirst = !!brief.querySelector('.icon-shoufa');

  // Article outline/TOC
  const catalogList = document.querySelector('.catalog-list, .catalog-listDiv');
  const toc = catalogList?.innerText?.trim() || '';

  // Citation network counts
  const citationTabs = document.querySelectorAll('ul.module-tab.tpl_lieteratures li');
  const citationInfo = {};
  citationTabs.forEach(li => {
    const id = li.getAttribute('data-id');
    const text = li.innerText?.trim();
    const countMatch = text.match(/(\d+)/);
    if (id) {
      citationInfo[id] = {
        label: text.replace(/\d+/, '').trim(),
        count: countMatch ? parseInt(countMatch[1]) : 0
      };
    }
  });

  return {
    title,
    authors,
    affiliations,
    abstract,
    keywords,
    fund,
    classification,
    journal,
    pubInfo,
    isOnlineFirst,
    toc,
    citationInfo
  };
}
```

### 4. Format and present the output

```
## {title} {isOnlineFirst ? "[网络首发]" : ""}

**Authors:**
{For each author: "- {name} ({affiliation})"}

**Affiliations:**
{For each affiliation: "- {affiliation}"}

**Journal:** {journal}
**Publication Info:** {pubInfo}

**Abstract:**
{abstract}

**Keywords:** {keywords joined by ", "}

**Fund:** {fund}
**Classification:** {classification}

**Citation Network:**
{For each citation type: "- {label}: {count}"}
```

### 5. Fallback: snapshot-based parsing

If JS extraction fails, use `mcp__chrome-devtools__take_snapshot` and parse the accessibility tree:
- **Title**: `heading` level 1 element
- **Authors**: `link` elements whose URLs contain `kcms2/author/detail`
- **Affiliations**: `link` elements whose URLs contain `kcms2/organ/detail`
- **Abstract**: `StaticText` following "摘要："
- **Keywords**: `link` elements whose URLs contain `kcms2/keyword/detail`
- **Fund**: `link` elements following "基金资助："
- **Classification**: `StaticText` following "分类号："

## Verified DOM Selectors

| Data           | Selector                                   | Notes                                    |
|----------------|--------------------------------------------|------------------------------------------|
| Paper section  | `.brief`                                    | Main paper info container                |
| Title          | `.brief h1`                                 | May contain icons, clean text needed     |
| Authors        | `.brief h3.author:first-of-type a`          | Text has superscript numbers (e.g., "张三1") |
| Affiliations   | `.brief h3.author:nth-of-type(2) a`         | Text starts with "N." (e.g., "1.北京大学") |
| Abstract       | `.abstract-text`                            | Full abstract text                       |
| Keywords       | `p.keywords a`                              | Semicolon-separated keyword links        |
| Fund           | `p.funds`                                   | Fund information text                    |
| Classification | `.clc-code`                                 | CLC classification codes                |
| Journal        | `.doc-top a`                                | Source journal link                      |
| Online first   | `.brief .icon-shoufa`                       | Present if paper is online first         |
| Citation tabs  | `ul.module-tab.tpl_lieteratures li`         | data-id attr identifies type             |


<!-- Source skill: cnki-download -->

# CNKI Paper Download (文献下载)

## Prerequisites

User **must be logged in** to CNKI with download permissions.

## Arguments

`$ARGUMENTS` is optionally a paper detail URL. If blank, uses current page.

## Steps

### 1. Navigate (if URL provided)

If URL provided: use `navigate_page` to go to the URL directly (no wait_for needed — Step 2 handles waiting).

**Important**: Always use `navigate_page` instead of clicking links on the search results page. Clicking opens a new tab and wastes 3 extra tool calls (`list_pages` + `select_page` + `take_snapshot`).

### 2. Check status and download (single async evaluate_script)

Replace `FORMAT` with `"pdf"` or `"caj"`:

```javascript
async () => {
  // Wait for page load
  await new Promise((r, j) => {
    let n = 0;
    const c = () => {
      if (document.querySelector('.brief h1')) r();
      else if (++n > 30) j('timeout');
      else setTimeout(c, 500);
    };
    c();
  });

  // Captcha check
  const cap = document.querySelector('#tcaptcha_transform_dy');
  if (cap && cap.getBoundingClientRect().top >= 0) {
    return { error: 'captcha', message: 'CNKI 正在显示滑块验证码。请在 Chrome 中手动完成拼图验证。' };
  }

  const format = "FORMAT"; // "pdf" or "caj"

  // Check download links
  const pdfLink = document.querySelector('#pdfDown') || document.querySelector('.btn-dlpdf a');
  const cajLink = document.querySelector('#cajDown') || document.querySelector('.btn-dlcaj a');

  // Check login status
  const notLogged = document.querySelector('.downloadlink.icon-notlogged')
    || document.querySelector('[class*="notlogged"]');
  if (notLogged) {
    return { error: 'not_logged_in', message: '下载需要登录。请先在 Chrome 中登录知网账号。' };
  }

  const title = document.querySelector('.brief h1')?.innerText?.trim()?.replace(/\s*网络首发\s*$/, '') || '';

  if (format === 'pdf' && pdfLink) {
    pdfLink.click();
    return { status: 'downloading', format: 'PDF', title };
  } else if (format === 'caj' && cajLink) {
    cajLink.click();
    return { status: 'downloading', format: 'CAJ', title };
  } else if (pdfLink) {
    pdfLink.click();
    return { status: 'downloading', format: 'PDF', title };
  } else if (cajLink) {
    cajLink.click();
    return { status: 'downloading', format: 'CAJ', title };
  }

  return { error: 'no_download', message: '未找到下载链接', hasPDF: !!pdfLink, hasCAJ: !!cajLink };
}
```

### 3. Report

Based on JS result:
- `status: downloading` → "PDF 下载已触发：{title}。请在 Chrome 下载管理器中查看。"
- `error: not_logged_in` → tell user to log in
- `error: captcha` → tell user to solve captcha

## Tool calls: 1–2 (navigate_page if URL + evaluate_script)

## Verified selectors

| Element | Selector | Notes |
|---------|----------|-------|
| PDF download | `#pdfDown` | `<a>` inside `li.btn-dlpdf` |
| CAJ download | `#cajDown` | `<a>` inside `li.btn-dlcaj` |
| Download area | `.download-btns` | parent `<div>` |
| Not logged in | `.downloadlink.icon-notlogged` | |
| Title | `.brief h1` | strip trailing "网络首发" |

## Captcha detection

Check `#tcaptcha_transform_dy` element's `getBoundingClientRect().top >= 0`.
Only active when `top >= 0` (visible). Pre-loaded SDK sits at `top: -1000000px`.


<!-- Source skill: cnki-export -->

# CNKI Export & Zotero Integration

Export paper citation data from CNKI and push directly to Zotero, or save as RIS file.

## Arguments

- `zotero` (default) — push to Zotero desktop via local API
- `ris` — save as .ris file
- `gb` — output GB/T 7714 citation text
- Optionally include a paper URL

## Mode Selection

Choose the right mode based on context:

| Context | Mode | Tool calls |
|---------|------|-----------|
| On a paper detail page | Single export (Step 1A) | 1 evaluate + 1 bash = **2** |
| On a search results page, save all/selected | **Batch export (Step 1B)** | 1 evaluate + 1 bash = **2** |
| Need to search then save | Use cnki-search first, then batch export | **4 total** |

**Always prefer batch export (1B) when multiple papers need saving.** It avoids navigating to each detail page (saves ~3 calls per paper).

## Steps

### 1A. Single export: from paper detail page

Use `mcp__chrome-devtools__evaluate_script`:

```javascript
async () => {
  const url = document.querySelector('#export-url')?.value;
  const params = document.querySelector('#export-id')?.value;
  const uniplatform = new URLSearchParams(window.location.search).get('uniplatform') || 'NZKPT';
  if (!url || !params) return { error: 'Not on a paper detail page' };

  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ filename: params, displaymode: 'GBTREFER,elearning,EndNote', uniplatform })
  });
  const data = await resp.json();
  if (data.code !== 1) return { error: data.msg };

  const result = {};
  for (const item of data.data) {
    result[item.mode] = item.value[0];
  }

  const body = document.body.innerText;
  result.pageUrl = window.location.href;
  result.issn = body.match(/ISSN[：:]\s*(\S+)/)?.[1] || '';
  result.dbcode = document.querySelector('#paramdbcode')?.value || '';
  result.dbname = document.querySelector('#paramdbname')?.value || '';
  result.filename = document.querySelector('#paramfilename')?.value || '';

  return result;
}
```

### 1B. Batch export: from search results page (PREFERRED for multiple papers)

On any CNKI search results page, extract checkbox values and call the export API directly — **no need to navigate to detail pages**.

Key discovery: `input.cbItem` checkbox `value` === detail page `#export-id` (same encrypted ID).

Use `mcp__chrome-devtools__evaluate_script`:

```javascript
async () => {
  const API_URL = 'https://kns.cnki.net/dm8/API/GetExport';

  // Get all checkbox values (= export encrypted IDs)
  const checkboxes = document.querySelectorAll('.result-table-list tbody input.cbItem');
  const rows = document.querySelectorAll('.result-table-list tbody tr');

  if (checkboxes.length === 0) return { error: 'No results on page' };

  const allPapers = [];
  for (let i = 0; i < checkboxes.length; i++) {
    const exportId = checkboxes[i].value;
    const paperUrl = rows[i]?.querySelector('td.name a.fz14')?.href || '';

    const resp = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ filename: exportId, displaymode: 'GBTREFER,elearning,EndNote', uniplatform: 'NZKPT' })
    });
    const data = await resp.json();
    if (data.code === 1) {
      const result = {};
      for (const item of data.data) { result[item.mode] = item.value[0]; }
      result.pageUrl = paperUrl;
      // Extract ISSN from ENDNOTE %@ field
      const issnMatch = result.ENDNOTE?.match(/%@\s*([^\s<]+)/);
      result.issn = issnMatch ? issnMatch[1] : '';
      result.dbcode = 'CJFQ';
      result.dbname = '';
      result.filename = '';
      allPapers.push(result);
    }
  }

  return allPapers; // JSON array, directly writable to file for Python script
}
```

**To export only specific papers** (e.g. #1, #3, #5), filter by index:

```javascript
// Replace the for loop condition:
const indices = [0, 2, 4]; // 0-indexed: papers #1, #3, #5
for (let i = 0; i < checkboxes.length; i++) {
  if (!indices.includes(i)) continue;
  // ... rest same
}
```

### 2. Push to Zotero

Save the export data (single object or JSON array) to a temp file, then run the Python script:

```bash
python "e:/cnki/.claude/skills/cnki-export/scripts/push_to_zotero.py" /tmp/papers.json
```

The Python script handles both single paper `{}` and batch `[{}, {}, ...]` JSON input.

- UTF-8 encoding (avoids Windows encoding issues)
- Parsing ELEARNING format into Zotero item fields
- Calling `POST http://127.0.0.1:23119/connector/saveItems`
- Returns: 201 = success, 500 = error, 0 = Zotero not running

### 3. Report result

Single:
```
已将论文添加到 Zotero:
  标题: {title}
  作者: {authors}
  期刊: {journal}

GB/T 7714 引用: {gbt_citation}
```

Batch:
```
已批量添加 {count} 篇论文到 Zotero:
  1. {title1} ({journal1})
  2. {title2} ({journal2})
  ...
```

## Export API Reference

| Parameter | Value | Source |
|-----------|-------|--------|
| API URL | `https://kns.cnki.net/dm8/API/GetExport` | Fixed, works from any page |
| filename | Encrypted ID | Detail page: `#export-id`; Results page: `input.cbItem` value |
| displaymode | `GBTREFER,elearning,EndNote` | Comma-separated modes |
| uniplatform | `NZKPT` | Required |

## Verified selectors

| Element | Selector | Page |
|---------|----------|------|
| Export URL | `#export-url` | Detail page only |
| Export ID | `#export-id` | Detail page only |
| Checkbox (= export ID) | `input.cbItem` | Search results page |
| Result rows | `.result-table-list tbody tr` | Search results page |
| Title link | `td.name a.fz14` | Search results page |

## Zotero API Reference

```
POST http://127.0.0.1:23119/connector/saveItems
Content-Type: application/json
X-Zotero-Connector-API-Version: 3
```

**Response:** 201 = created, 500 = error
**Collection:** Saves to Zotero's currently selected collection.

Query collections:
```bash
python "e:/cnki/.claude/skills/cnki-export/scripts/push_to_zotero.py" --list
```

## Important Notes

- **Windows encoding:** Must use Python script, cannot pass Chinese JSON via bash/curl directly
- **Zotero must be running:** `localhost:23119` requires Zotero desktop in background
- **Chinese authors:** Use `name` field (single field, not split), `creatorType: "author"`
- **Batch export saves ~90% tool calls:** 9 papers: 33 calls → 3 calls
- **CNKI Export API:** `filename` must be encrypted ID (`#export-id` or `input.cbItem` value), NOT `#paramfilename`


<!-- Source skill: cnki-journal-search -->

# CNKI Journal Search (期刊检索)

## Arguments

`$ARGUMENTS` is a journal name, ISSN, CN number, or sponsor name.

## Steps

### 1. Navigate

Use `mcp__chrome-devtools__navigate_page` → `https://navi.cnki.net/knavi`

### 2. Search + extract results (single evaluate_script, NO wait_for)

Use `mcp__chrome-devtools__evaluate_script`. Replace `QUERY_HERE` with actual search term:

```javascript
async () => {
  const query = "QUERY_HERE";

  // Wait for page load
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.querySelector('input.researchbtn')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // Check captcha (visible on screen, not hidden SDK at top:-1000000)
  const outer = document.querySelector('#tcaptcha_transform_dy');
  if (outer && outer.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  // Auto-detect search type and fill
  const select = document.querySelector('select');
  if (select) {
    if (/^\d{4}-\d{3}[\dXx]$/.test(query)) select.value = 'ISSN';
    else if (/^\d{2}-\d{4}/.test(query)) select.value = 'CN';
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }

  const input = document.querySelector('input[placeholder*="检索词"]');
  if (input) input.value = query;

  // Click search button (verified selector: input.researchbtn)
  document.querySelector('input.researchbtn')?.click();

  // Wait for results
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.body.innerText.includes('条结果')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // Click 期刊 tab to filter journals only
  const tabs = document.querySelectorAll('li a');
  for (const a of tabs) { if (a.innerText.trim() === '期刊') { a.click(); break; } }
  await new Promise(r => setTimeout(r, 1500));

  // Extract journal results
  const body = document.body.innerText;
  const countMatch = body.match(/共\s*(\d+)\s*条结果/) || body.match(/找到\s*(\d+)\s*条结果/);
  const count = countMatch ? parseInt(countMatch[1]) : 0;

  const results = [];
  const titleLinks = document.querySelectorAll('a[href*="knavi/detail"]');
  titleLinks.forEach(link => {
    const text = link.innerText?.trim();
    if (!text || text.length < 2) return;
    const parent = link.closest('li, .list-item') || link.parentElement?.parentElement;
    const pt = parent?.innerText || '';
    results.push({
      name: text.split('\n')[0]?.trim(),
      url: link.href,
      issn: pt.match(/ISSN[：:]\s*(\S+)/)?.[1] || '',
      cn: pt.match(/CN[：:]\s*(\S+)/)?.[1] || '',
      cif: pt.match(/复合影响因子[：:]\s*([\d.]+)/)?.[1] || '',
      aif: pt.match(/综合影响因子[：:]\s*([\d.]+)/)?.[1] || '',
      citations: pt.match(/被引次数[：:]\s*([\d,]+)/)?.[1] || '',
      downloads: pt.match(/下载次数[：:]\s*([\d,]+)/)?.[1] || '',
      sponsor: pt.match(/主办单位[：:]\s*(.+?)(?=\n|ISSN)/)?.[1]?.trim() || ''
    });
  });

  return { query, count, results };
}
```

### 3. Present results

```
期刊检索 "$ARGUMENTS"（共 {count} 条）：

1. {name}
   ISSN: {issn} | CN: {cn}
   复合影响因子: {cif} | 综合影响因子: {aif}
   被引: {citations} | 下载: {downloads}
```

## Notes

- Journal detail pages open in **new tab** — use `list_pages` + `select_page`
- If only 1 journal result, can auto-navigate to detail page for `cnki-journal-index`
- Search button selector: `input.researchbtn` (not generic `button`)

## Captcha detection

Check `#tcaptcha_transform_dy` element's `getBoundingClientRect().top >= 0`.
Tencent captcha SDK preloads DOM at `top: -1000000px` (off-screen, not active).
Only return `error: 'captcha'` when `top >= 0` (actually visible to user).

## Tool calls: 2 (navigate + evaluate_script)


<!-- Source skill: cnki-journal-index -->

# CNKI Journal Indexing Query (收录查询)

Check which databases index a journal and extract evaluation metrics from its CNKI detail page.

## Arguments

`$ARGUMENTS` is either:
- A journal name (will search first, then navigate to detail)
- A CNKI journal detail URL (containing `navi.cnki.net/knavi/detail`)

## Steps

### 1. Navigate to the journal detail page

**If URL provided:** Navigate directly.
- Use `mcp__chrome-devtools__navigate_page` with the URL.
- Use `mcp__chrome-devtools__wait_for` with text `["该刊被以下数据库收录"]` and timeout 15000.

**If journal name provided:** Search first.
- Navigate to `https://navi.cnki.net/knavi`
- Search for the journal (same as cnki-journal-search steps 2-4)
- Click the first matching journal title link
- Use `mcp__chrome-devtools__list_pages` to find and select the new detail tab
- Wait for the detail page to load

### 2. Check for captcha

Take snapshot. If "拖动下方拼图完成验证" found, notify user.

### 3. Extract journal info via JavaScript

Use `mcp__chrome-devtools__evaluate_script` with this function:

```javascript
() => {
  const body = document.body.innerText;

  // Journal title
  const titleEl = document.querySelector('h3.titbox, h3.titbox1');
  const titleText = titleEl?.innerText?.trim() || '';
  const titleParts = titleText.split('\n').map(s => s.trim()).filter(Boolean);
  const nameCN = titleParts[0] || '';
  const nameEN = titleParts[1] || '';

  // Indexing tags - extract from text between title and "基本信息"
  const tagText = body.match(/Chinese.*?\n\n([\s\S]*?)\n\n基本信息/)?.[1]
    || body.match(new RegExp(nameCN + '[\\s\\S]*?\\n\\n([\\s\\S]*?)\\n\\n基本信息'))?.[1]
    || '';
  const knownTags = ['北大核心','CSSCI','CSCD','SCI','EI','CAS','JST','WJCI','AMI','Scopus','卓越期刊','网络首发'];
  const indexedIn = knownTags.filter(tag => tagText.includes(tag) || body.includes(tag));

  // Basic info
  const sponsor = body.match(/主办单位[：:]\s*(.+?)(?=\n)/)?.[1] || '';
  const frequency = body.match(/出版周期[：:]\s*(\S+)/)?.[1] || '';
  const issn = body.match(/ISSN[：:]\s*(\S+)/)?.[1] || '';
  const cn = body.match(/CN[：:]\s*(\S+)/)?.[1] || '';

  // Publication info
  const collection = body.match(/专辑名称[：:]\s*(.+?)(?=\n)/)?.[1] || '';
  const paperCount = body.match(/出版文献量[：:]\s*(.+?)(?=\n)/)?.[1] || '';

  // Evaluation info
  const impactComposite = body.match(/复合影响因子[：:]\s*([\d.]+)/)?.[1] || '';
  const impactComprehensive = body.match(/综合影响因子[：:]\s*([\d.]+)/)?.[1] || '';

  // "该刊被以下数据库收录" section - click "更多介绍" first if needed
  const moreBtn = Array.from(document.querySelectorAll('a')).find(a => a.innerText?.includes('更多介绍'));
  const hasMoreIntro = !!moreBtn;

  return {
    nameCN,
    nameEN,
    indexedIn,
    sponsor,
    frequency,
    issn,
    cn,
    collection,
    paperCount,
    impactComposite,
    impactComprehensive,
    hasMoreIntro,
    rawTagText: tagText.substring(0, 200)
  };
}
```

### 4. Get detailed indexing info (optional)

If the extraction shows `hasMoreIntro: true`, click the "更多介绍" link to expand detailed indexing information, then take a new snapshot to capture the expanded content.

The expanded section typically lists specific database inclusions with years, such as:
- 北大核心期刊（2023年版）
- CSCD中国科学引文数据库来源期刊（2023-2024年度）
- EI 工程索引（美）

### 5. Check "统计与评价" tab (for detailed metrics)

If the user wants detailed evaluation data:
- Find and click the "统计与评价" link/tab in the snapshot
- Wait for the statistics section to load
- Extract additional metrics (H-index, citation distribution, etc.)

### 6. Present results

```
## {nameCN} ({nameEN})

**收录数据库：** {indexedIn joined by " | "}

**基本信息：**
- ISSN: {issn}
- CN: {cn}
- 主办单位: {sponsor}
- 出版周期: {frequency}
- 专辑: {collection}
- 出版文献量: {paperCount}

**评价指标：**
- 复合影响因子 (2025版): {impactComposite}
- 综合影响因子 (2025版): {impactComprehensive}

**收录情况：**
{For each tag in indexedIn: "- ✓ {tag}"}
```

## Verified Page Structure

The journal detail page (`navi.cnki.net/knavi/detail`) has:

| Data                  | Location                                    |
|-----------------------|---------------------------------------------|
| Title                 | `h3.titbox.titbox1` — first line CN, second line EN |
| Indexing tags         | Text nodes after title: "北大核心", "EI", "CSCD", etc. |
| "被以下数据库收录"    | `h4` heading, below tags                   |
| Basic info            | Text patterns: "主办单位：", "ISSN：", "CN：", "出版周期：" |
| Publication info      | Text patterns: "专辑名称：", "出版文献量：" |
| Evaluation info       | Text patterns: "复合影响因子：", "综合影响因子：" |
| Detailed indexing     | Expandable via "更多介绍" link              |
| Stats tab             | "统计与评价" tab link                       |
| Detail page opens in  | **New tab** — use list_pages + select_page  |

## Common Indexing Databases

| Tag       | Full Name                                    |
|-----------|----------------------------------------------|
| 北大核心   | 北京大学中文核心期刊                          |
| CSSCI     | 中文社会科学引文索引                          |
| CSCD      | 中国科学引文数据库                            |
| SCI       | Science Citation Index                       |
| EI        | Engineering Index                            |
| CAS       | Chemical Abstracts Service                   |
| JST       | Japan Science and Technology Agency          |
| WJCI      | World Journal Clout Index                    |
| AMI       | 中国人文社会科学期刊 AMI 综合评价             |
| Scopus    | Elsevier Scopus                              |


<!-- Source skill: cnki-journal-toc -->

# CNKI Journal Table of Contents (期刊目录浏览 + 原版目录下载)

Browse journal issues, extract the paper list, and optionally open/download the original TOC PDF (封面+目录扫描版).

## Arguments

`$ARGUMENTS` describes what to browse:
- `{journal name}` — which journal
- `{year}` (optional) — which year, defaults to latest
- `{issue}` (optional) — which issue number
- `download` (optional) — if included, download the original TOC PDF

Examples:
- `计算机学报 2026 01期` — browse 2026 issue 1
- `计算机学报 2026 01期 download` — download original TOC PDF
- `计算机学报` — shows latest (网络首发)

## Steps

### 1. Navigate to journal detail page

If not already on a journal detail page (`navi.cnki.net/knavi/detail`):
- Use `cnki-journal-search` to find the journal
- Use `mcp__chrome-devtools__list_pages` + `mcp__chrome-devtools__select_page` to switch to the journal detail tab (opens in new tab)

### 2. Select issue + extract papers (single async evaluate_script)

Replace `YEAR` and `ISSUE` with actual values (e.g., `"2025"`, `"No.01"`).
The "刊期浏览" tab is the default active view — no need to click it.

```javascript
async () => {
  const year = "YEAR";
  const issue = "ISSUE"; // Format: "No.01", "No.12", etc.

  const dls = document.querySelectorAll('#yearissue0 dl.s-dataList');
  let target = null;
  for (const dl of dls) {
    if (dl.querySelector('dt')?.innerText?.trim() === year) {
      target = Array.from(dl.querySelectorAll('dd a')).find(a => a.innerText.trim() === issue);
      break;
    }
  }
  if (!target) {
    // Return available years and issues for the requested year
    const available = Array.from(dls).map(dl => ({
      year: dl.querySelector('dt')?.innerText?.trim(),
      issues: Array.from(dl.querySelectorAll('dd a')).map(a => a.innerText.trim())
    })).filter(y => y.year);
    return { error: 'issue_not_found', year, issue, available: available.slice(0, 5) };
  }

  target.click();

  // Wait for paper list to load
  await new Promise((r, j) => {
    let n = 0;
    const c = () => {
      const rows = document.querySelectorAll('#CataLogContent dd.row');
      if (rows.length > 0) r();
      else if (++n > 30) j('timeout');
      else setTimeout(c, 500);
    };
    setTimeout(c, 1000);
  });

  // Extract papers
  const rows = document.querySelectorAll('#CataLogContent dd.row');
  const papers = Array.from(rows).map((dd, i) => ({
    no: i + 1,
    title: dd.querySelector('span.name a')?.innerText?.trim(),
    authors: dd.querySelector('span.author')?.innerText?.trim()?.replace(/;$/, ''),
    pages: dd.querySelector('span.company')?.innerText?.trim()
  }));

  // Get 原版目录 URL
  const tocBtn = document.querySelector('a.btn-preview:not(.btn-back)');

  return {
    issueLabel: document.querySelector('span.date-list')?.innerText?.trim(),
    paperCount: papers.length,
    papers,
    tocUrl: tocBtn?.href || null,
    url: location.href
  };
}
```

### 3. Present results

```
## {journal_name} — {issueLabel}

共 {paperCount} 篇论文：

1. {title}  [pp. {pages}]
   作者：{authors}

2. {title}  [pp. {pages}]
   作者：{authors}
...
```

### 4. Download original TOC PDF (if requested)

If user requested download, or asks for "原版目录":

**Method A — Click "原版目录浏览" to open reader, then download:**

1. Find the `link` with text "原版目录浏览" in the snapshot (class `btn-preview`)
2. Click it — this opens a new tab with the reader page (`kns.cnki.net/reader/report`)
3. Use `mcp__chrome-devtools__list_pages` to find the new reader tab
4. Use `mcp__chrome-devtools__select_page` to switch to it
5. Use `mcp__chrome-devtools__wait_for` with text `["下载"]`
6. Take snapshot — find the `link` with text "下载" (the download button in the reader toolbar)
7. Click the download link — triggers PDF download via Chrome

**Method B — Direct download from reader page:**

If already on a reader page (`kns.cnki.net/reader/report`):
1. Take snapshot
2. Find `link` with text "下载"
3. Click it

After clicking, inform the user:
> 原版目录 PDF 下载已触发，请在 Chrome 下载管理器中查看。

## Tool calls

- Browse issue: 1 (evaluate_script only) — after navigating to journal page
- Download TOC: requires snapshot + click + tab switching (new tab)

## Verified selectors

### Journal Detail — 刊期浏览

| Element | Selector | Notes |
|---------|----------|-------|
| 刊期浏览 tab | `a` text "刊期浏览" | default active (`li.on.cur`), no need to click |
| Year area | `#yearissue0` / `.yearissuepage` | |
| Year groups | `dl.s-dataList` | inside `#yearissue0` |
| Year label | `dl.s-dataList dt` | text "2026", "2025" etc. |
| Issue links | `dl.s-dataList dd a` | text "No.01", "No.12" etc. |
| Issue label | `span.date-list` | text "2025年01期" |
| Paper container | `#CataLogContent` | |
| Paper entries | `#CataLogContent dd.row` | |
| Paper title | `dd.row span.name a` | href to `kcms2/article/abstract` |
| Paper authors | `dd.row span.author` | semicolon-separated |
| Paper page range | `dd.row span.company` | class is "company" but holds page range |
| Paper ID | `dd.row b[name="encrypt"]` | id like "JSJX202512001" |
| 原版目录浏览 | `a.btn-preview:not(.btn-back)` | href to `bar.cnki.net/bar/download/order` |
| 返回 | `a.btn-preview.btn-back` | |

### Reader Page (kns.cnki.net/reader/report)

| Element | Pattern |
|---------|--------|
| Page title | `RootWebArea "期刊原版目录"` |
| Download button | `link` text "下载", URL to `bar.cnki.net/bar/download/order` |
| Current page | `textbox` value (page number) |
| Total pages | `StaticText` (e.g., "4") |
| Navigation | `generic` description "上一页" / "下一页" |

## Important Notes

- "原版目录浏览" only appears when a **specific issue** is selected (not for 网络首发 view).
- The reader page opens in a **new tab**.
- The download link in the reader requires login. If download fails, remind user to log in.
- The download URL is session-specific — do not cache or reuse.
