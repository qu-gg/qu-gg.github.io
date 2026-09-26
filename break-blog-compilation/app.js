const SOURCE_POST_BASE = "source-posts/";
const PAGE_WIDTH_INCHES = 8.5;
const ZOOM_MIN = 60;
const ZOOM_MAX = 140;
const ZOOM_STEP = 10;
const TOC_ITEMS_PER_PAGE = 80;
const PAPER_BACKGROUND = [250, 246, 237];
const FALLBACK_SOURCE_COLOR = "rgb(32, 37, 58)";

const state = {
    manifest: null,
    entries: [],
    pageRecords: [],
    entryRecords: new Map(),
    frontMatterRecords: new Map(),
    tocPages: [],
    zoom: 100,
};

const elements = {
    bookContainer: document.getElementById("book-container"),
    bookPages: document.getElementById("book-pages"),
    loadingStatus: document.getElementById("loading-status"),
    sidebar: document.getElementById("toc-sidebar"),
    sidebarContent: document.getElementById("toc-sidebar-content"),
    menuToggle: document.getElementById("menu-toggle"),
    mobileScrim: document.getElementById("mobile-scrim"),
    printButton: document.getElementById("print-button"),
    zoomOut: document.getElementById("zoom-out"),
    zoomLevel: document.getElementById("zoom-level"),
    zoomIn: document.getElementById("zoom-in"),
};

function createElement(tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
}

function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return value || "Unknown date";
    return new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        timeZone: "UTC",
    }).format(date);
}

function formatMonthYear(value) {
    const date = new Date(`${value}T00:00:00Z`);
    if (Number.isNaN(date.valueOf())) return value || "Unknown date";
    return new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "long",
        timeZone: "UTC",
    }).format(date);
}

const TOC_SMALL_WORDS = new Set(["a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to"]);

function toTocTitle(title) {
    const loweredTitle = title.toLocaleLowerCase();
    let wordNumber = 0;
    const standardizedTitle = loweredTitle.replace(/[A-Za-z0-9][A-Za-z0-9'’!?]*/g, (word, offset) => {
        const previousText = loweredTitle.slice(0, offset).trimEnd();
        const followsColon = previousText.endsWith(":");
        const isFirstWord = wordNumber === 0;
        wordNumber += 1;

        if (word === "break!!") return "BREAK!!";
        if (word === "break??") return "BREAK??";
        if (word === "click!") return "CLICK!";
        if (!isFirstWord && !followsColon && TOC_SMALL_WORDS.has(word)) return word;
        return word.charAt(0).toLocaleUpperCase() + word.slice(1);
    });
    return standardizedTitle.replace(/BREAK!!-Ing/g, "BREAK!!-ing");
}

function cleanPostTitle(title) {
    return title
        .replace(/^Option Menu:\s*/i, "")
        .replace(/^Setting\/Freebie:\s*/i, "")
        .replace(/^Setting:\s*/i, "")
        .replace(/^Freebie Mini-Entry:\s*/i, "")
        .replace(/^Freebie:\s*/i, "")
        .replace(/^Ennies Update and Freebie:\s*/i, "")
        .trim();
}

function flattenEntries(manifest) {
    const entries = [];
    for (const category of manifest.categories) {
        const sections = category.sections || [{
            title: category.section,
            entries: category.entries,
        }];
        for (const section of sections) {
            for (const entry of section.entries) {
                entries.push({
                    ...entry,
                    categoryId: category.id,
                    categoryTitle: category.title,
                    sectionTitle: section.title,
                });
            }
        }
    }
    return entries;
}

async function fetchJSON(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`Could not load ${url} (${response.status})`);
    }
    return response.json();
}

async function fetchPost(postId) {
    return fetchJSON(`${SOURCE_POST_BASE}${postId}.json`);
}

function setLoadingStatus(text) {
    if (elements.loadingStatus) elements.loadingStatus.textContent = text;
}

function createPageShell(page, options = {}) {
    const shell = createElement("section", "page-shell");
    if (options.className) shell.classList.add(options.className);
    if (options.id) shell.id = options.id;
    if (options.entryId) shell.dataset.entryId = options.entryId;
    shell.appendChild(page);
    elements.bookPages.appendChild(shell);
    const record = {
        shell,
        page,
        showNumber: options.showNumber !== false,
        kind: options.kind || "front-matter",
        entryId: options.entryId || null,
    };
    state.pageRecords.push(record);
    return record;
}

function createPage(className) {
    return createElement("article", `page ${className}`);
}

function createCoverPage() {
    const page = createPage("cover-page");
    const title = createElement("h1");
    title.appendChild(createElement("span", null, "BREAK!!"));
    title.appendChild(createElement("span", null, "Blog Compendium"));
    page.appendChild(title);
    page.appendChild(createElement("div", "cover-rule"));
    page.appendChild(createElement("p", "cover-credit cover-credit-label", "Original Blog Content by:"));
    page.appendChild(createElement("p", "cover-credit cover-credit-names", "Reynaldo Madriñan and Carlo Tartaglia"));
    page.appendChild(createElement("p", "cover-credit cover-credit-label cover-credit-compilation-label", "Compilation by:"));
    page.appendChild(createElement("p", "cover-credit cover-credit-names cover-credit-compilation-name", "Quagg"));
    page.appendChild(createElement("p", "cover-credit cover-credit-label cover-credit-coverage-label", "COVERS THE BREAK!! BLOG FROM:"));
    page.appendChild(createElement("p", "cover-credit cover-credit-coverage-dates", `${formatMonthYear(state.manifest.coverage.start)} - ${formatMonthYear(state.manifest.coverage.end)}`));
    return page;
}

function createBlankPage() {
    const page = createPage("blank-page");
    page.appendChild(createElement("div", "blank-mark"));
    return page;
}

function createTocPage(index) {
    const page = createPage("toc-page");
    const header = createElement("header", "toc-header");
    header.appendChild(createElement("h1", null, index === 0 ? "Contents" : "Contents continued"));
    header.appendChild(createElement("div", "header-divider"));
    page.appendChild(header);
    page.appendChild(createElement("div", "toc-list"));
    return page;
}

function createBackCoverPage() {
    const page = createPage("back-page");
    page.appendChild(createElement("div", "back-mark"));
    page.appendChild(createElement("div", "disclaimer", "BREAK!! Blog Compendium is an independent product published under BREAK!! RPG's Non-Commercial License and is not affiliated with BREAK!!'s creators or publishers."));
    return page;
}

function buildFrontMatter() {
    createPageShell(createCoverPage(), { kind: "cover", showNumber: false, id: "cover-page" });
    createPageShell(createBlankPage(), { kind: "blank", showNumber: false, id: "blank-page" });

    const tocCount = Math.ceil(buildTocItems().length / TOC_ITEMS_PER_PAGE);
    for (let index = 0; index < tocCount; index += 1) {
        const record = createPageShell(createTocPage(index), {
            kind: "toc",
            id: `toc-page-${index + 1}`,
        });
        state.tocPages.push(record);
    }

}

function buildTocItems() {
    const items = [];
    for (const category of state.manifest.categories) {
        items.push({ type: "category", title: category.title });
        const sections = category.sections || [{ title: category.section, entries: category.entries }];
        for (const section of sections) {
            items.push({ type: "section", title: section.title });
            for (const entry of section.entries) {
                items.push({
                    type: "article",
                    title: entry.tocTitle,
                    target: entry.id,
                });
            }
        }
    }
    return items;
}

function renderToc() {
    const items = buildTocItems();
    const chunks = [];
    for (let index = 0; index < items.length; index += TOC_ITEMS_PER_PAGE) {
        chunks.push(items.slice(index, index + TOC_ITEMS_PER_PAGE));
    }

    chunks.forEach((chunk, pageIndex) => {
        const list = state.tocPages[pageIndex].page.querySelector(".toc-list");
        list.replaceChildren();
        for (const item of chunk) {
            if (item.type === "category") {
                list.appendChild(createElement("div", "toc-entry category-entry", item.title));
                continue;
            }
            if (item.type === "section") {
                list.appendChild(createElement("div", "toc-entry section-entry", item.title));
                continue;
            }
            const row = createElement("div", "toc-entry");
            row.dataset.tocTarget = item.target;
            row.appendChild(createElement("span", "toc-title", toTocTitle(item.title)));
            list.appendChild(row);
        }
    });
}

function parseRGBColor(color) {
    const match = color.match(/^rgba?\(([^)]+)\)$/i);
    if (!match) return null;

    const channels = match[1].split(/[\s,\/]+/).filter(Boolean);
    if (channels.length < 3) return null;

    const rgb = channels.slice(0, 3).map((channel) => {
        const value = Number.parseFloat(channel);
        return channel.endsWith("%") ? value * 2.55 : value;
    });
    if (rgb.some((channel) => Number.isNaN(channel))) return null;

    const alphaValue = channels[3] || "1";
    const alpha = alphaValue.endsWith("%")
        ? Number.parseFloat(alphaValue) / 100
        : Number.parseFloat(alphaValue);
    if (Number.isNaN(alpha)) return null;

    return rgb.map((channel, index) => (
        channel * alpha + PAPER_BACKGROUND[index] * (1 - alpha)
    ));
}

function relativeLuminance(channel) {
    const normalized = channel / 255;
    return normalized <= 0.03928
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
}

function contrastRatio(firstColor, secondColor) {
    const firstLuminance = 0.2126 * relativeLuminance(firstColor[0])
        + 0.7152 * relativeLuminance(firstColor[1])
        + 0.0722 * relativeLuminance(firstColor[2]);
    const secondLuminance = 0.2126 * relativeLuminance(secondColor[0])
        + 0.7152 * relativeLuminance(secondColor[1])
        + 0.0722 * relativeLuminance(secondColor[2]);
    const lighter = Math.max(firstLuminance, secondLuminance);
    const darker = Math.min(firstLuminance, secondLuminance);
    return (lighter + 0.05) / (darker + 0.05);
}

function getReadableSourceColor(styleText) {
    const match = styleText.match(/(?:^|;)\s*color\s*:\s*([^;]+)/i);
    if (!match) return null;

    const candidate = match[1].replace(/\s*!important\s*$/i, "").trim();
    const probe = document.createElement("span");
    probe.style.color = candidate;
    if (!probe.style.color) return null;
    document.body.appendChild(probe);
    const computedColor = getComputedStyle(probe).color;
    probe.remove();

    const rgbColor = parseRGBColor(computedColor);
    if (!rgbColor) return null;
    return contrastRatio(rgbColor, PAPER_BACKGROUND) >= 4.5
        ? computedColor
        : FALLBACK_SOURCE_COLOR;
}

function getSourceFormatting(styleText) {
    const probe = document.createElement("span");
    probe.style.cssText = styleText;
    const formatting = {};
    const properties = [
        ["fontWeight", /^(normal|bold|bolder|lighter|[1-9]00)$/i],
        ["fontStyle", /^(normal|italic|oblique(?:\s+-?[0-9.]+deg)?)$/i],
        ["textDecoration", /^(none|underline|overline|line-through)(?:\s+(?:solid|double|dotted|dashed|wavy))?(?:\s+[^\s]+)?$/i],
        ["textAlign", /^(left|right|center|justify|start|end)$/i],
        ["verticalAlign", /^(baseline|sub|super|top|text-top|middle|bottom|text-bottom)$/i],
        ["backgroundColor", /^(?!transparent$)(?:[a-z]+|#[0-9a-f]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\))$/i],
    ];

    for (const [property, pattern] of properties) {
        const value = probe.style[property];
        if (value && pattern.test(value)) formatting[property] = value;
    }
    return formatting;
}

function sanitizeSourceHTML(html) {
    const template = document.createElement("template");
    template.innerHTML = html || "";
    const forbidden = "script, style, iframe, object, embed, form, input, button, textarea, select";
    template.content.querySelectorAll(forbidden).forEach((element) => element.remove());

    template.content.querySelectorAll("*").forEach((element) => {
        const sourceColor = getReadableSourceColor(element.getAttribute("style") || "");
        const sourceFormatting = getSourceFormatting(element.getAttribute("style") || "");
        [...element.attributes].forEach((attribute) => {
            const name = attribute.name.toLowerCase();
            if (name === "style" || name === "class" || name === "id" || name.startsWith("on")) {
                element.removeAttribute(attribute.name);
            }
        });

        if (sourceColor) element.style.color = sourceColor;
        for (const [property, value] of Object.entries(sourceFormatting)) {
            element.style[property] = value;
        }

        if (element.matches("a")) {
            const href = element.getAttribute("href") || "";
            if (!/^(https?:|mailto:|#|\/)/i.test(href)) element.removeAttribute("href");
            if (element.hasAttribute("href")) {
                element.target = "_blank";
                element.rel = "noopener noreferrer";
            }
        }

        if (element.matches("img")) {
            const src = element.getAttribute("src") || element.getAttribute("data-src") || "";
            if (src.startsWith("//")) element.src = `https:${src}`;
            if (src && !/^(https?:|data:|\/)/i.test(src)) element.removeAttribute("src");
            element.loading = "lazy";
            element.addEventListener("error", () => {
                element.classList.add("media-missing");
                element.alt = element.alt || "Image unavailable at source URL";
            });
        }
    });
    return template.content;
}

const SOURCE_BLOCK_TAGS = new Set([
    "ADDRESS", "ARTICLE", "ASIDE", "BLOCKQUOTE", "DD", "DL", "DT", "FIGCAPTION",
    "FIGURE", "FOOTER", "FORM", "H1", "H2", "H3", "H4", "H5", "H6", "HR",
    "LI", "MAIN", "NAV", "OL", "P", "PRE", "SECTION", "TABLE", "UL",
]);

function hasSourceBlockDescendant(node) {
    return [...node.children].some((child) => (
        SOURCE_BLOCK_TAGS.has(child.tagName)
            || child.tagName === "DIV"
            || hasSourceBlockDescendant(child)
    ));
}

function hasInlineContent(nodes) {
    return nodes.some((node) => (
        node.nodeType === Node.TEXT_NODE
            ? node.textContent.trim()
            : node.nodeType === Node.ELEMENT_NODE
                && (node.tagName === "BR" || node.textContent.trim())
    ));
}

function isEmptySourceSpacer(node) {
    if (node.nodeType !== Node.ELEMENT_NODE || node.textContent.trim()) return false;
    if (["IMG", "TABLE", "HR", "VIDEO", "AUDIO", "CANVAS"].some((tag) => node.querySelector(tag))) {
        return false;
    }
    return true;
}

function cloneContainerFragment(container, children) {
    const fragment = container.cloneNode(false);
    children.forEach((child) => fragment.appendChild(child.cloneNode(true)));
    return fragment;
}

function prependSourceSeparator(node) {
    const clone = node.cloneNode(false);
    clone.appendChild(document.createTextNode(" "));
    [...node.childNodes].forEach((child) => clone.appendChild(child.cloneNode(true)));
    return clone;
}

function appendSourceSeparator(node) {
    const clone = node.cloneNode(true);
    clone.appendChild(document.createTextNode(" "));
    return clone;
}

function flattenSourceNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
        if (!node.textContent.trim()) return [];
        const paragraph = createElement("p");
        paragraph.textContent = node.textContent;
        return [paragraph];
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return [];
    if (isEmptySourceSpacer(node)) {
        if (/\s/.test(node.textContent)) {
            const separator = createElement("span", "source-separator");
            separator.textContent = " ";
            return [separator];
        }
        return [];
    }
    if (SOURCE_BLOCK_TAGS.has(node.tagName) || !hasSourceBlockDescendant(node)) return [node];

    const output = [];
    let inlineChildren = [];
    let pendingSeparator = false;
    const flushInline = () => {
        if (hasInlineContent(inlineChildren)) {
            output.push(cloneContainerFragment(node, inlineChildren));
        } else if (inlineChildren.some((child) => /\s/.test(child.textContent || ""))) {
            pendingSeparator = true;
        }
        inlineChildren = [];
    };

    for (const child of [...node.childNodes]) {
        if (child.nodeType === Node.ELEMENT_NODE
            && (SOURCE_BLOCK_TAGS.has(child.tagName)
                || child.tagName === "DIV"
                || hasSourceBlockDescendant(child))) {
            flushInline();
            const childUnits = flattenSourceNode(child);
            if (pendingSeparator && childUnits.length) {
                childUnits[0] = prependSourceSeparator(childUnits[0]);
                pendingSeparator = false;
            }
            output.push(...childUnits);
        } else {
            inlineChildren.push(child);
        }
    }
    flushInline();
    if (pendingSeparator && output.length) {
        output[output.length - 1] = appendSourceSeparator(output[output.length - 1]);
    }
    return output;
}

function sourceNodes(fragment) {
    const nodes = [];
    for (const node of [...fragment.childNodes]) {
        nodes.push(...flattenSourceNode(node));
    }
    return nodes;
}

function nodeTextLength(node) {
    return (node.textContent || "").length;
}

function cloneTextRange(node, start, end, state = { offset: 0 }) {
    if (node.nodeType === Node.TEXT_NODE) {
        const nodeStart = state.offset;
        const nodeEnd = nodeStart + node.data.length;
        state.offset = nodeEnd;
        const from = Math.max(0, start - nodeStart);
        const to = Math.min(node.data.length, end - nodeStart);
        return to > from ? document.createTextNode(node.data.slice(from, to)) : null;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return null;
    const clone = node.cloneNode(false);
    for (const child of [...node.childNodes]) {
        const childLength = nodeTextLength(child);
        if (childLength === 0) {
            if (state.offset >= start && state.offset <= end) clone.appendChild(child.cloneNode(true));
            continue;
        }
        const childClone = cloneTextRange(child, start, end, state);
        if (childClone) clone.appendChild(childClone);
    }
    return clone.childNodes.length ? clone : null;
}

function lastWordBoundary(text, limit) {
    const slice = text.slice(0, limit);
    const boundary = Math.max(slice.lastIndexOf(" "), slice.lastIndexOf("\n"), slice.lastIndexOf("\t"));
    return boundary > 24 ? boundary : limit;
}

function splitNode(node, body) {
    const total = nodeTextLength(node);
    if (total < 40) return null;

    let low = 1;
    let high = total;
    let best = 0;
    while (low <= high) {
        const middle = Math.floor((low + high) / 2);
        const candidate = cloneTextRange(node, 0, middle);
        if (!candidate) {
            high = middle - 1;
            continue;
        }
        body.appendChild(candidate);
        const fits = body.scrollHeight <= body.clientHeight + 1;
        body.removeChild(candidate);
        if (fits) {
            best = middle;
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }
    if (!best || best >= total) return null;

    const boundary = lastWordBoundary(node.textContent, best);
    const prefix = cloneTextRange(node, 0, boundary);
    const remainder = cloneTextRange(node, boundary, total);
    if (!prefix || !remainder || !prefix.textContent.trim() || !remainder.textContent.trim()) return null;
    return { prefix, remainder };
}

function bodyHasContent(body) {
    return [...body.childNodes].some((node) => node.nodeType === Node.ELEMENT_NODE || node.textContent.trim());
}

function pageFits(body) {
    return body.scrollHeight <= body.clientHeight + 1;
}

function bodyContentExtent(body) {
    const lastChild = body.lastElementChild;
    if (!lastChild) return 0;
    const bodyRect = body.getBoundingClientRect();
    return lastChild.getBoundingClientRect().bottom - bodyRect.top;
}

const BLOCK_BOUNDARY_TAGS = new Set([
    "ADDRESS", "ARTICLE", "ASIDE", "BLOCKQUOTE", "DD", "DIV", "DL", "DT",
    "FIGCAPTION", "FIGURE", "FOOTER", "FORM", "H1", "H2", "H3", "H4", "H5",
    "H6", "HEADER", "HR", "LI", "MAIN", "NAV", "OL", "P", "PRE", "SECTION",
    "TABLE", "UL",
]);

function isBlockBoundary(node) {
    return node.nodeType === Node.ELEMENT_NODE
        && (BLOCK_BOUNDARY_TAGS.has(node.tagName) || node.tagName === "BR");
}

function cloneWithChildren(node, children) {
    const clone = node.cloneNode(false);
    children.forEach((child) => clone.appendChild(child.cloneNode(true)));
    return clone;
}

function findListPaths(node, path = [], paths = []) {
    if (node.nodeType !== Node.ELEMENT_NODE) return paths;
    if ((node.tagName === "UL" || node.tagName === "OL")
        && [...node.children].some((child) => child.tagName === "LI")) {
        paths.push(path);
    }

    for (const [index, child] of [...node.childNodes].entries()) {
        findListPaths(child, [...path, index], paths);
    }
    return paths;
}

function nodeAtPath(node, path) {
    return path.reduce((current, index) => current?.childNodes[index], node);
}

function cloneListPortion(node, path, boundary, prefix) {
    function cloneAt(current, depth) {
        if (depth === path.length) {
            const children = [...current.childNodes];
            const selected = prefix ? children.slice(0, boundary) : children.slice(boundary);
            return cloneWithChildren(current, selected);
        }

        const targetIndex = path[depth];
        const clone = current.cloneNode(false);
        [...current.childNodes].forEach((child, index) => {
            if (prefix) {
                if (index < targetIndex) clone.appendChild(child.cloneNode(true));
                if (index === targetIndex) clone.appendChild(cloneAt(child, depth + 1));
            } else {
                if (index === targetIndex) clone.appendChild(cloneAt(child, depth + 1));
                if (index > targetIndex) clone.appendChild(child.cloneNode(true));
            }
        });
        return clone;
    }

    return cloneAt(node, 0);
}

function splitNodeAtListBoundary(node, body) {
    let bestSplit = null;
    let bestLength = 0;
    for (const path of findListPaths(node)) {
        const list = nodeAtPath(node, path);
        const children = [...list.childNodes];
        let bestBoundary = 0;
        for (let index = 1; index < children.length; index += 1) {
            if (children[index - 1].nodeType !== Node.ELEMENT_NODE
                || children[index - 1].tagName !== "LI") continue;
            const candidate = cloneListPortion(node, path, index, true);
            if (!candidate.textContent.trim()) continue;
            body.appendChild(candidate);
            const fits = pageFits(body);
            body.removeChild(candidate);
            if (!fits) break;
            bestBoundary = index;
        }

        if (!bestBoundary || bestBoundary >= children.length) continue;
        const prefix = cloneListPortion(node, path, bestBoundary, true);
        const remainder = cloneListPortion(node, path, bestBoundary, false);
        if (prefix.textContent.trim() && remainder.textContent.trim()
            && prefix.textContent.length > bestLength) {
            bestSplit = { prefix, remainder };
            bestLength = prefix.textContent.length;
        }
    }
    return bestSplit;
}

function chooseSemanticSplit(first, second) {
    if (!first) return second;
    if (!second) return first;
    return first.prefix.textContent.length >= second.prefix.textContent.length ? first : second;
}

function chooseBalancedSemanticSplit(node, currentBody, freshBody) {
    let best = null;
    let bestScore = -Infinity;
    for (const candidate of semanticSplitCandidates(node)) {
        currentBody.appendChild(candidate.prefix);
        freshBody.appendChild(candidate.remainder);

        if (pageFits(currentBody) && pageFits(freshBody)) {
            const currentRatio = bodyContentExtent(currentBody) / currentBody.clientHeight;
            const freshRatio = bodyContentExtent(freshBody) / freshBody.clientHeight;
            const score = Math.min(currentRatio, freshRatio)
                - Math.abs(currentRatio - freshRatio) * 0.1;
            if (score > bestScore) {
                bestScore = score;
                best = candidate;
            }
        }

        currentBody.removeChild(candidate.prefix);
        freshBody.removeChild(candidate.remainder);
    }
    return best;
}

function isBoldElement(node) {
    if (node.nodeType !== Node.ELEMENT_NODE) return false;
    if (node.tagName === "B" || node.tagName === "STRONG") return true;
    return /(?:^|;)\s*font-weight\s*:\s*(?:bold|[6-9]00)\b/i.test(node.getAttribute("style") || "");
}

function allTextIsBold(node) {
    let hasText = false;
    let bold = true;
    function visit(current, inheritedBold = false) {
        if (current.nodeType === Node.TEXT_NODE) {
            if (current.textContent.trim()) {
                hasText = true;
                if (!inheritedBold) bold = false;
            }
            return;
        }
        if (current.nodeType !== Node.ELEMENT_NODE) return;
        const currentBold = inheritedBold || isBoldElement(current);
        [...current.childNodes].forEach((child) => visit(child, currentBold));
    }
    visit(node);
    return hasText && bold;
}

function isLeadBlock(node) {
    if (node.nodeType !== Node.ELEMENT_NODE) return false;
    if (/^H[1-6]$/.test(node.tagName)) return true;
    if (!["P", "DIV", "B", "STRONG"].includes(node.tagName)) return false;
    const text = node.textContent.trim();
    return text.length <= 180 && allTextIsBold(node);
}

function isListLeadNode(node) {
    if (node.nodeType !== Node.ELEMENT_NODE || findListPaths(node).length) return false;
    const text = node.textContent.trim().replace(/\s+/g, " ");
    return text.length > 0
        && text.length <= 220
        && /(?:following|below|these|options|abilities|traits|quirks)\s*:\s*$/i.test(text);
}

function nextMeaningfulNode(nodes) {
    return nodes.find((node) => node.textContent.trim());
}

function nextMeaningfulNodeIndex(nodes) {
    return nodes.findIndex((node) => node.textContent.trim());
}

function boundaryLeavesLeadAlone(children, boundary) {
    let previous = boundary - 1;
    while (previous >= 0 && !children[previous].textContent.trim()) previous -= 1;
    let next = boundary;
    while (next < children.length && !children[next].textContent.trim()) next += 1;
    return previous >= 0 && next < children.length && isLeadBlock(children[previous]);
}

function splitNodeAtBoundary(node, body) {
    if (node.nodeType !== Node.ELEMENT_NODE) return null;

    const children = [...node.childNodes];
    if (children.length < 2 || !children.some(isBlockBoundary)) return null;

    let bestBoundary = 0;
    for (let index = 1; index < children.length; index += 1) {
        if (!isBlockBoundary(children[index - 1])) continue;
        if (boundaryLeavesLeadAlone(children, index)) continue;
        const candidate = cloneWithChildren(node, children.slice(0, index));
        if (!candidate.textContent.trim()) continue;
        body.appendChild(candidate);
        const fits = pageFits(body);
        body.removeChild(candidate);
        if (!fits) break;
        bestBoundary = index;
    }

    if (!bestBoundary || bestBoundary >= children.length) return null;
    const prefix = cloneWithChildren(node, children.slice(0, bestBoundary));
    const remainder = cloneWithChildren(node, children.slice(bestBoundary));
    if (!prefix.textContent.trim() || !remainder.textContent.trim()) return null;
    return { prefix, remainder };
}

function semanticSplitCandidates(node) {
    if (node.nodeType !== Node.ELEMENT_NODE) return [];
    const candidates = [];
    const children = [...node.childNodes];

    for (let index = 1; index < children.length; index += 1) {
        if (!isBlockBoundary(children[index - 1])) continue;
        const prefix = cloneWithChildren(node, children.slice(0, index));
        const remainder = cloneWithChildren(node, children.slice(index));
        if (prefix.textContent.trim() && remainder.textContent.trim()) {
            candidates.push({ prefix, remainder });
        }
    }

    for (const path of findListPaths(node)) {
        const list = nodeAtPath(node, path);
        const listChildren = [...list.childNodes];
        for (let index = 1; index < listChildren.length; index += 1) {
            if (listChildren[index - 1].nodeType !== Node.ELEMENT_NODE
                || listChildren[index - 1].tagName !== "LI") continue;
            const prefix = cloneListPortion(node, path, index, true);
            const remainder = cloneListPortion(node, path, index, false);
            if (prefix.textContent.trim() && remainder.textContent.trim()) {
                candidates.push({ prefix, remainder });
            }
        }
    }

    const seenLengths = new Set();
    return candidates.filter((candidate) => {
        const length = candidate.prefix.textContent.length;
        if (seenLengths.has(length)) return false;
        seenLengths.add(length);
        return true;
    });
}

function rebalanceFinalArticlePage(articleRecords) {
    if (articleRecords.length < 2) return;

    const previousBody = articleRecords.at(-2).page.querySelector(".article-body");
    const finalBody = articleRecords.at(-1).page.querySelector(".article-body");
    if (!previousBody || !finalBody || bodyContentExtent(finalBody) > finalBody.clientHeight * 0.58) return;

    const originalPreviousChildren = [...previousBody.childNodes];
    const originalFinalChildren = [...finalBody.childNodes];
    const originalText = previousBody.textContent + finalBody.textContent;

    const previousNodes = [...previousBody.children];
    const candidateNode = [...previousNodes]
        .reverse()
        .find((node) => node.textContent.trim());
    if (!candidateNode) return;

    const candidates = semanticSplitCandidates(candidateNode);
    const originalNext = candidateNode.nextSibling;
    let best = null;
    let bestScore = -Infinity;

    const scoreCurrentLayout = () => {
        if (!pageFits(previousBody) || !pageFits(finalBody)) return null;
        const previousRatio = bodyContentExtent(previousBody) / previousBody.clientHeight;
        const finalRatio = bodyContentExtent(finalBody) / finalBody.clientHeight;
        return Math.min(previousRatio, finalRatio)
            - Math.abs(previousRatio - finalRatio) * 0.1;
    };

    const pageChildren = [...previousBody.children];
    const groupLimit = Math.min(16, pageChildren.length);
    for (let start = pageChildren.length - 1; start >= pageChildren.length - groupLimit; start -= 1) {
        if (start > 0 && (isLeadBlock(pageChildren[start - 1]) || isListLeadNode(pageChildren[start - 1]))) {
            continue;
        }
        const moving = pageChildren.slice(start);
        if (!moving.some((node) => node.textContent.trim())) continue;

        moving.forEach((node) => previousBody.removeChild(node));
        const clones = moving.map((node) => node.cloneNode(true));
        const finalAnchor = finalBody.firstChild;
        clones.forEach((clone) => finalBody.insertBefore(clone, finalAnchor));
        const score = scoreCurrentLayout();
        if (score !== null && score > bestScore) {
            bestScore = score;
            best = { group: moving };
        }
        clones.forEach((clone) => finalBody.removeChild(clone));
        moving.forEach((node) => previousBody.appendChild(node));
    }

    previousBody.removeChild(candidateNode);
    const wholeRemainder = candidateNode.cloneNode(true);
    finalBody.insertBefore(wholeRemainder, finalBody.firstChild);
    const wholeScore = scoreCurrentLayout();
    if (wholeScore !== null && wholeScore > bestScore) {
        bestScore = wholeScore;
        best = { whole: true };
    }
    finalBody.removeChild(wholeRemainder);
    previousBody.insertBefore(candidateNode, originalNext);

    for (const candidate of candidates) {
        previousBody.removeChild(candidateNode);
        previousBody.insertBefore(candidate.prefix, originalNext);
        finalBody.insertBefore(candidate.remainder, finalBody.firstChild);

        const score = scoreCurrentLayout();
        if (score !== null && score > bestScore) {
            bestScore = score;
            best = { candidate };
        }

        finalBody.removeChild(candidate.remainder);
        previousBody.removeChild(candidate.prefix);
        previousBody.insertBefore(candidateNode, originalNext);
    }

    if (!best) return;
    if (best.group) {
        best.group.forEach((node) => previousBody.removeChild(node));
        const finalAnchor = finalBody.firstChild;
        best.group.forEach((node) => finalBody.insertBefore(node, finalAnchor));
    } else {
        previousBody.removeChild(candidateNode);
    }
    if (best.whole) {
        finalBody.insertBefore(candidateNode, finalBody.firstChild);
    } else if (!best.group) {
        previousBody.insertBefore(best.candidate.prefix, originalNext);
        finalBody.insertBefore(best.candidate.remainder, finalBody.firstChild);
    }

    if (previousBody.textContent + finalBody.textContent !== originalText) {
        previousBody.replaceChildren(...originalPreviousChildren);
        finalBody.replaceChildren(...originalFinalChildren);
    }
}

function rebalanceArticlePagePairs(articleRecords) {
    if (articleRecords.length < 2) return;

    for (let pass = 0; pass < 8; pass += 1) {
        let changed = false;
        for (let index = 0; index < articleRecords.length - 1; index += 1) {
            const currentBody = articleRecords[index].page.querySelector(".article-body");
            const nextBody = articleRecords[index + 1].page.querySelector(".article-body");
            if (!currentBody || !nextBody) continue;

            const currentRatio = bodyContentExtent(currentBody) / currentBody.clientHeight;
            const nextRatio = bodyContentExtent(nextBody) / nextBody.clientHeight;
            if (currentRatio >= 0.9 || nextRatio <= currentRatio + 0.04) continue;

            const firstNode = nextBody.firstElementChild;
            if (!firstNode || !firstNode.textContent.trim() || isLeadBlock(firstNode) || isListLeadNode(firstNode)) {
                continue;
            }

            const originalCurrentChildren = [...currentBody.childNodes];
            const originalNextChildren = [...nextBody.childNodes];
            const originalText = currentBody.textContent + nextBody.textContent;
            const originalNext = firstNode.nextSibling;
            const baseline = Math.min(currentRatio, nextRatio)
                - Math.abs(currentRatio - nextRatio) * 0.1;
            const candidates = [{ whole: true }, ...semanticSplitCandidates(firstNode).map((candidate) => ({ candidate }))];
            let best = null;
            let bestScore = baseline;

            for (const option of candidates) {
                nextBody.removeChild(firstNode);
                if (option.whole) {
                    currentBody.appendChild(firstNode.cloneNode(true));
                } else {
                    nextBody.insertBefore(option.candidate.remainder, originalNext);
                    currentBody.appendChild(option.candidate.prefix);
                }

                if (pageFits(currentBody) && pageFits(nextBody)) {
                    const currentCandidateRatio = bodyContentExtent(currentBody) / currentBody.clientHeight;
                    const nextCandidateRatio = bodyContentExtent(nextBody) / nextBody.clientHeight;
                    const score = Math.min(currentCandidateRatio, nextCandidateRatio)
                        - Math.abs(currentCandidateRatio - nextCandidateRatio) * 0.1;
                    if (score > bestScore) {
                        bestScore = score;
                        best = option;
                    }
                }

                currentBody.replaceChildren(...originalCurrentChildren);
                nextBody.replaceChildren(...originalNextChildren);
            }

            if (!best) continue;
            nextBody.removeChild(firstNode);
            if (best.whole) {
                currentBody.appendChild(firstNode);
            } else {
                nextBody.insertBefore(best.candidate.remainder, originalNext);
                currentBody.appendChild(best.candidate.prefix);
            }

            if (currentBody.textContent + nextBody.textContent !== originalText) {
                currentBody.replaceChildren(...originalCurrentChildren);
                nextBody.replaceChildren(...originalNextChildren);
                continue;
            }
            changed = true;
        }
        if (!changed) break;
    }
}

function createArticlePage(post, entry) {
    const page = createPage("article-page");
    const header = createElement("header", "article-header");
    header.appendChild(createElement("div", "article-kicker", `${entry.categoryTitle} · ${entry.sectionTitle}`));
    header.appendChild(createElement("h1", null, cleanPostTitle(post.title)));
    const meta = createElement("div", "article-meta");
    const primaryMeta = createElement("div", "article-meta-primary");
    primaryMeta.appendChild(createElement("time", null, formatDate(post.published)));
    const source = createElement("a", null, "Original post");
    source.href = post.url;
    source.target = "_blank";
    source.rel = "noopener noreferrer";
    primaryMeta.appendChild(source);
    meta.appendChild(primaryMeta);
    if (post.labels?.length) {
        const labels = createElement("div", "article-labels");
        labels.appendChild(createElement("span", "article-labels-heading", "Labels:"));
        labels.appendChild(createElement("span", null, post.labels.map(toTocTitle).join(" · ")));
        meta.appendChild(labels);
    }
    header.appendChild(meta);
    page.appendChild(header);
    const body = createElement("div", "article-body");
    page.appendChild(body);
    return { page, body };
}

async function renderArticle(entry) {
    const post = await fetchPost(entry.id);
    const nodes = sourceNodes(sanitizeSourceHTML(post.content_html));
    const article = createArticlePage(post, entry);
    const firstRecord = createPageShell(article.page, {
        kind: "article",
        className: "article-shell",
        entryId: entry.id,
        id: `article-${entry.id}`,
        showNumber: false,
    });
    state.entryRecords.set(entry.id, { entry, post, firstRecord });
    nodes.forEach((node) => article.body.appendChild(node));
    article.page.classList.add("article-start", "article-end");
}

function buildSidebar() {
    elements.sidebarContent.replaceChildren();
    const addItem = (label, target, className = "toc-item") => {
        const item = createElement("button", className, label);
        item.type = "button";
        item.dataset.target = target;
        item.addEventListener("click", () => jumpToTarget(target));
        elements.sidebarContent.appendChild(item);
    };

    addItem("Cover", "cover-page", "toc-item front-matter");
    addItem("Contents", "toc-page-1", "toc-item front-matter");

    for (const category of state.manifest.categories) {
        elements.sidebarContent.appendChild(createElement("div", "toc-category", category.title));
        const sections = category.sections || [{ title: category.section, entries: category.entries }];
        for (const section of sections) {
            elements.sidebarContent.appendChild(createElement("div", "toc-section", section.title));
            for (const entry of section.entries) {
                addItem(toTocTitle(entry.tocTitle), entry.id);
            }
        }
    }
    addItem("Back Cover", "back-cover-page", "toc-item front-matter");
}

function jumpToTarget(target) {
    const record = state.frontMatterRecords.get(target) || state.entryRecords.get(target)?.firstRecord;
    const direct = document.getElementById(target);
    const shell = record?.shell || direct;
    if (!shell) return;
    const previousScrollBehavior = elements.bookContainer.style.scrollBehavior;
    elements.bookContainer.style.scrollBehavior = "auto";
    shell.scrollIntoView({ behavior: "auto", block: "start", inline: "nearest" });
    elements.bookContainer.style.scrollBehavior = previousScrollBehavior;
    setActiveSidebarTarget(target);
    closeMobileMenu();
}

function setActiveSidebarTarget(target) {
    document.querySelectorAll(".toc-item.active").forEach((item) => item.classList.remove("active"));
    const active = elements.sidebarContent.querySelector(`[data-target="${CSS.escape(target)}"]`);
    if (active) active.classList.add("active");
}

function observePages() {
    const observer = new IntersectionObserver((entries) => {
        const visible = entries
            .filter((entry) => entry.isIntersecting)
            .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (!visible.length) return;
        const target = visible[0].target.dataset.entryId || visible[0].target.id;
        setActiveSidebarTarget(target);
    }, {
        root: elements.bookContainer,
        threshold: 0.45,
    });
    state.pageRecords.forEach((record) => observer.observe(record.shell));
}

function applyZoom(value) {
    state.zoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, value));
    elements.bookPages.style.zoom = `${state.zoom / 100}`;
    elements.zoomLevel.textContent = `${state.zoom}%`;
    sessionStorage.setItem("breakBlogCompendiumZoom", String(state.zoom));
}

function toggleMobileMenu() {
    const open = elements.sidebar.classList.toggle("open");
    elements.mobileScrim.classList.toggle("visible", open);
    elements.menuToggle.setAttribute("aria-expanded", String(open));
}

function closeMobileMenu() {
    elements.sidebar.classList.remove("open");
    elements.mobileScrim.classList.remove("visible");
    elements.menuToggle.setAttribute("aria-expanded", "false");
}

function bindControls() {
    elements.printButton.addEventListener("click", () => window.print());
    elements.zoomOut.addEventListener("click", () => applyZoom(state.zoom - ZOOM_STEP));
    elements.zoomIn.addEventListener("click", () => applyZoom(state.zoom + ZOOM_STEP));
    elements.zoomLevel.addEventListener("click", () => applyZoom(100));
    elements.menuToggle.addEventListener("click", toggleMobileMenu);
    elements.mobileScrim.addEventListener("click", closeMobileMenu);
}

async function init() {
    bindControls();
    const savedZoom = Number(sessionStorage.getItem("breakBlogCompendiumZoom"));
    if (savedZoom) applyZoom(savedZoom);

    try {
        state.manifest = await fetchJSON("compendium-data.json");
        state.entries = flattenEntries(state.manifest);
        elements.bookPages.replaceChildren();
        buildFrontMatter();
        renderToc();

        for (let index = 0; index < state.entries.length; index += 1) {
            const entry = state.entries[index];
            setLoadingStatus(`Loading ${index + 1} of ${state.entries.length}`);
            await renderArticle(entry);
        }

        const backCover = createPageShell(createBackCoverPage(), {
            kind: "back-cover",
            showNumber: false,
            id: "back-cover-page",
        });
        state.frontMatterRecords.set("back-cover", backCover);

        if (document.fonts?.ready) await document.fonts.ready;
        buildSidebar();
        observePages();
        setLoadingStatus(`${state.entries.length} articles ready`);
    } catch (error) {
        console.error(error);
        elements.bookPages.replaceChildren();
        const errorPage = createElement("section", "error-page");
        errorPage.appendChild(createElement("h1", null, "The compendium could not load"));
        errorPage.appendChild(createElement("p", null, "Run this folder through a local web server so the archive JSON files can be fetched."));
        elements.bookPages.appendChild(errorPage);
        setLoadingStatus("Load failed");
    }
}

init();