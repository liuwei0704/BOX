/**
 * 華人影視（HRTV）- 篩選功能修復版
 * 修正：URL 構造邏輯與正則提取規則
 */

const baseUrl = 'https://www.men.cc';
const siteName = 'HRTV';

async function init(cfg) {
    return {
        sites: [{
            key: 'hrtv',
            name: siteName,
            type: 3,
            searchable: 1,
            changeable: 1,
            ext: '.html'
        }]
    };
}

async function homeContent(filter) {
    const commonFilters = [
        {
            key: "sort",
            name: "排序",
            value: [
                { n: "最新", v: "time" },
                { n: "熱度", v: "hits" },
                { n: "評分", v: "score" }
            ]
        },
        {
            key: "area",
            name: "地區",
            value: [
                { n: "全部", v: "" }, { n: "大陸", v: "大陸" }, { n: "香港", v: "香港" }, 
                { n: "台灣", v: "台灣" }, { n: "美國", v: "美國" }, { n: "日本", v: "日本" }, 
                { n: "韓國", v: "韓國" }, { n: "泰國", v: "泰國" }
            ]
        },
        {
            key: "year",
            name: "年份",
            value: [
                { n: "全部", v: "" }, { n: "2026", v: "2026" }, { n: "2025", v: "2025" }, 
                { n: "2024", v: "2024" }, { n: "2023", v: "2023" }, { n: "2022", v: "2022" },
                { n: "2021", v: "2021" }, { n: "2020", v: "2020" }
            ]
        }
    ];

    const classes = [
        { type_id: "1", type_name: "電影" },
        { type_id: "2", type_name: "連續劇" },
        { type_id: "4", type_name: "動漫" },
        { type_id: "31", type_name: "紀錄片" }
    ];

    const filters = {};
    classes.forEach(c => { filters[c.type_id] = commonFilters; });

    return { class: classes, filters: filters };
}

async function categoryContent(tid, pg, filter, extend) {
    try {
        const page = pg || 1;
        // 核心修正：構造符合該站點偽靜態規則的 URL
        let url = `${baseUrl}/index.php/vod/show/id/${tid}`;
        
        if (extend.area) url += `/area/${encodeURIComponent(extend.area)}`;
        if (extend.sort) url += `/by/${extend.sort}`;
        if (extend.year) url += `/year/${extend.year}`;
        if (page > 1) url += `/page/${page}`;
        url += '.html';

        console.log(`[HRTV] 分類地址: ${url}`);

        const res = await req(url);
        if (res.error || !res.body) return Result.error("請求網頁失敗");

        const html = res.body;
        const videos = extractVideos(html);
        
        return {
            code: 1,
            msg: "成功",
            list: videos,
            page: page,
            pagecount: 999, // 簡化處理分頁
            limit: 20,
            total: 999
        };
    } catch (e) {
        return Result.error(e.message);
    }
}

async function detailContent(ids) {
    try {
        const vodId = ids[0];
        const url = `${baseUrl}/index.php/vod/detail/id/${vodId}.html`;
        const res = await req(url);
        const html = res.body;

        const name = (html.match(/<h2 class="hl-dc-title[^>]*>([^<]+)<\/h2>/) || [])[1];
        const pic = (html.match(/data-original="([^"]+)"/) || [])[1];
        
        const episodes = [];
        const playListMatch = html.match(/<ul class="hl-plays-list[^>]*>([\s\S]*?)<\/ul>/);
        if (playListMatch) {
            const epPattern = /href="\/index\.php\/vod\/play\/id\/\d+\/sid\/(\d+)\/nid\/(\d+)\.html"[^>]*>([^<]+)<\/a
