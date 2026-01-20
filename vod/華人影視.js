/**
 * 華人影視（HRTV）
 * 修正內容：優化地區篩選 URL 構造，修復分頁與排序邏輯
 * 更新日期：2026年1月20日
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
                { n: "全部", v: "" },
                { n: "大陸", v: "大陸" },
                { n: "香港", v: "香港" },
                { n: "台灣", v: "台灣" },
                { n: "美國", v: "美國" },
                { n: "日本", v: "日本" },
                { n: "韓國", v: "韓國" }
            ]
        },
        {
            key: "year",
            name: "年份",
            value: [
                { n: "全部", v: "" },
                { n: "2026", v: "2026" },
                { n: "2025", v: "2025" },
                { n: "2024", v: "2024" },
                { n: "2023", v: "2023" },
                { n: "2022", v: "2022" }
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
        // 核心修正：嚴格依照蘋果 CMS 的偽靜態順
