/**
 * 紅果短劇爬蟲腳本
 * 版本：1.0
 * 最後更新：2026-01-23
 */

const baseUrl = 'https://www.gzmeigao.com';
const siteName = '紅果短劇';

// 常量定義
const CONSTANTS = {
    DEFAULT_LIMIT: 30,
    MAX_VIDEOS_PER_PAGE: 100,
    DEFAULT_YEAR: '2025',
    DEFAULT_AREA: '大陸',
    DEFAULT_LANG: '國語',
    DEFAULT_ACTOR: '內詳',
    DEFAULT_DIRECTOR: '內詳',
    DEFAULT_CONTENT: '紅果短劇',
    DEFAULT_PLAY_FROM: '紅果短劇'
};

// 分類映射
const CATEGORIES = [
    { type_id: "1", type_name: "重生" },
    { type_id: "2", type_name: "穿越" },
    { type_id: "3", type_name: "爽劇" },
    { type_id: "4", type_name: "言情" },
    { type_id: "5", type_name: "都市" },
    { type_id: "6", type_name: "古裝" },
    { type_id: "7", type_name: "懸疑" },
    { type_id: "8", type_name: "劇情" }
];

// 正則表達式預編譯
const REGEX = {
    VIDEO_ITEM: /<li class="col-md-5 col-sm-4 col-xs-3">([\s\S]*?)<\/li>/g,
    SEARCH_ITEM: /<li class="active[^"]*clearfix">([\s\S]*?)<\/li>/g,
    TITLE: /title="([^"]+)"/,
    HREF: /href="([^"]+)"/,
    IMAGE: /data-original="([^"]+)"/,
    REMARKS: /<span class="pic-text[^>]*>([^<]+)<\/span>/,
    ACTOR: /<p class="text[^>]*>([^<]+)<\/p>/,
    SEARCH_TITLE: /<h3 class="title"><a[^>]+href="([^"]+)"[^>]*>([^<]+)<\/a><\/h3>/,
    SEARCH_TYPE: /<span class="text-muted">類型：<\/span>([^<]+)/,
    SEARCH_AREA: /<span class="text-muted">地區：<\/span>([^<]+)/,
    SEARCH_YEAR: /<span class="text-muted">年份：<\/span>([^<]+)/,
    SEARCH_ACTOR: /<span class="text-muted">主演：<\/span>([\s\S]*?)<\/p>/,
    PAGINATION: /<li class="active visible-xs">\s*<span class="num">\d+\/(\d+)<\/span>\s*<\/li>/,
    DETAIL_TITLE: /<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)/,
    DETAIL_IMAGE: /data-original="([^"]+\.(jpg|png|jpeg))"/i,
    PLAY_LIST: /<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>([\s\S]*?)<\/ul>/,
    PLAY_LINK: /<a[^>]+href="([^"]+)"[^>]*>([^<]+)</g,
    M3U8_URL: /(https?:\/\/[^\s"']+\.m3u8[^\s"']*)/,
    VAR_NOW: /var\s+now\s*=\s*["']([^"']+)["']/
};

/**
 * 緩存管理
 */
const CacheManager = {
    cache: new Map(),
    ttl: 5 * 60 * 1000, // 5分鐘
    
    set(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    },
    
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() - item.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }
        
        return item.data;
    },
    
    clear() {
        this.cache.clear();
    }
};

/**
 * 請求管理器
 */
const RequestManager = {
    async fetch(url, options = {}) {
        const cacheKey = `req:${url}`;
        const cached = CacheManager.get(cacheKey);
        if (cached) {
            console.log(`[緩存] ${url}`);
            return cached;
        }
        
        console.log(`[請求] ${url}`);
        
        try {
            let html;
            if (typeof Java !== 'undefined' && Java.req) {
                // Java環境
                const result = Java.req(url);
                if (!result.body) {
                    throw new Error(result.error || '請求失敗');
                }
                html = result.body;
            } else if (typeof fetch !== 'undefined') {
                // 瀏覽器環境
                const response = await fetch(url, {
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': baseUrl,
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                html = await response.text();
            } else {
                throw new Error('不支持的環境');
            }
            
            CacheManager.set(cacheKey, html);
            return html;
            
        } catch (error) {
            console.error(`請求失敗 ${url}:`, error.message);
            throw error;
        }
    }
};

/**
 * URL工具
 */
const UrlUtils = {
    fixUrl(url) {
        if (!url) return '';
        if (url.startsWith('http')) return url;
        if (url.startsWith('//')) return 'https:' + url;
        if (url.startsWith('/')) return baseUrl + url;
        return baseUrl + '/' + url;
    },
    
    buildCategoryUrl(tid, page = 1) {
        if (page === 1) {
            return `${baseUrl}/hg/${tid}.html`;
        }
        return `${baseUrl}/hg/${tid}-${page}.html`;
    },
    
    buildSearchUrl(keyword, page = 1) {
        const encodedKey = encodeURIComponent(keyword.trim());
        return `${baseUrl}/search.php?searchtype=5&searchword=${encodedKey}&page=${page}`;
    }
};

/**
 * 文本工具
 */
const TextUtils = {
    clean(text) {
        if (!text) return '';
        return text
            .replace(/<[^>]+>/g, '')
            .replace(/&nbsp;/g, ' ')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&mdash;/g, '—')
            .replace(/\s+/g, ' ')
            .trim();
    },
    
    extractFullTitle(html, currentTitle) {
        if (!currentTitle.includes('..')) return currentTitle;
        
        const titleMatch = html.match(REGEX.TITLE);
        return titleMatch ? this.clean(titleMatch[1]) : currentTitle;
    }
};

/**
 * 解析器基類
 */
class BaseParser {
    constructor() {
        this.maxItems = CONSTANTS.MAX_VIDEOS_PER_PAGE;
    }
    
    parseVideoItem(html) {
        try {
            const titleMatch = html.match(REGEX.TITLE);
            const hrefMatch = html.match(REGEX.HREF);
            
            if (!titleMatch || !hrefMatch) return null;
            
            const vodName = TextUtils.extractFullTitle(html, TextUtils.clean(titleMatch[1]));
            let vodId = UrlUtils.fixUrl(hrefMatch[1]);
            
            const imgMatch = html.match(REGEX.IMAGE);
            const vodPic = imgMatch ? UrlUtils.fixUrl(imgMatch[1]) : '';
            
            const remarksMatch = html.match(REGEX.REMARKS);
            const vodRemarks = remarksMatch ? TextUtils.clean(remarksMatch[1]) : '全集';
            
            const actorMatch = html.match(REGEX.ACTOR);
            const vodActor = actorMatch ? TextUtils.clean(actorMatch[1]) : CONSTANTS.DEFAULT_ACTOR;
            
            return {
                vod_id: vodId,
                vod_name: vodName,
                vod_pic: vodPic,
                vod_remarks: vodRemarks,
                vod_actor: vodActor
            };
        } catch (error) {
            console.error('解析視頻項目錯誤:', error);
            return null;
        }
    }
}

/**
 * 分類頁面解析器
 */
class CategoryParser extends BaseParser {
    parse(html) {
        const videos = [];
        
        try {
            const videoListMatch = html.match(/<ul class="stui-vodlist clearfix">([\s\S]*?)<\/ul>/);
            if (!videoListMatch) return videos;
            
            const matches = videoListMatch[1].matchAll(REGEX.VIDEO_ITEM);
            
            for (const match of matches) {
                if (videos.length >= this.maxItems) break;
                
                const video = this.parseVideoItem(match[1]);
                if (video) videos.push(video);
            }
        } catch (error) {
            console.error('分類頁面解析錯誤:', error);
        }
        
        return videos;
    }
    
    getPageCount(html) {
        const pageMatch = html.match(REGEX.PAGINATION);
        if (pageMatch && pageMatch[1]) {
            return parseInt(pageMatch[1]);
        }
        
        const pageLinks = html.match(/<a href="\/hg\/\d+-\d+\.html">/g);
        return pageLinks ? pageLinks.length + 1 : 1;
    }
}

/**
 * 搜索頁面解析器
 */
class SearchParser extends BaseParser {
    parse(html) {
        const videos = [];
        
        try {
            const searchListMatch = html.match(/<ul class="stui-vodlist__media col-pd clearfix">([\s\S]*?)<\/ul>/);
            if (!searchListMatch) {
                // 回退到分類解析器
                const categoryParser = new CategoryParser();
                return categoryParser.parse(html);
            }
            
            const matches = searchListMatch[1].matchAll(REGEX.SEARCH_ITEM);
            
            for (const match of matches) {
                if (videos.length >= this.maxItems) break;
                
                const video = this.parseSearchItem(match[1]);
                if (video) videos.push(video);
            }
        } catch (error) {
            console.error('搜索頁面解析錯誤:', error);
        }
        
        return videos;
    }
    
    parseSearchItem(html) {
        try {
            const titleMatch = html.match(REGEX.SEARCH_TITLE);
            if (!titleMatch) return null;
            
            const vodId = UrlUtils.fixUrl(titleMatch[1]);
            const vodName = TextUtils.clean(titleMatch[2]);
            
            const imgMatch = html.match(REGEX.IMAGE);
            const vodPic = imgMatch ? UrlUtils.fixUrl(imgMatch[1]) : '';
            
            const remarksMatch = html.match(REGEX.REMARKS);
            const vodRemarks = remarksMatch ? TextUtils.clean(remarksMatch[1]) : '全集';
            
            const typeMatch = html.match(REGEX.SEARCH_TYPE);
            const vodType = typeMatch ? TextUtils.clean(typeMatch[1]) : '';
            
            const areaMatch = html.match(REGEX.SEARCH_AREA);
            const vodArea = areaMatch ? TextUtils.clean(areaMatch[1]) : CONSTANTS.DEFAULT_AREA;
            
            const yearMatch = html.match(REGEX.SEARCH_YEAR);
            const vodYear = yearMatch ? TextUtils.clean(yearMatch[1]) : CONSTANTS.DEFAULT_YEAR;
            
            let vodActor = CONSTANTS.DEFAULT_ACTOR;
            const actorMatch = html.match(REGEX.SEARCH_ACTOR);
            if (actorMatch) {
                const actorNameMatch = actorMatch[1].match(/<a[^>]*>([^<]+)<\/a>/);
                vodActor = actorNameMatch ? TextUtils.clean(actorNameMatch[1]) : TextUtils.clean(actorMatch[1].replace(/<[^>]+>/g, ''));
            }
            
            return {
                vod_id: vodId,
                vod_name: vodName,
                vod_pic: vodPic,
                vod_remarks: vodRemarks,
                vod_actor: vodActor,
                vod_type: vodType,
                vod_area: vodArea,
                vod_year: vodYear
            };
        } catch (error) {
            console.error('解析搜索項目錯誤:', error);
            return null;
        }
    }
    
    getPageCount(html) {
        const pageMatch = html.match(REGEX.PAGINATION);
        if (pageMatch && pageMatch[1]) {
            return parseInt(pageMatch[1]);
        }
        
        const totalMatch = html.match(/共有[^"]*"(\d+)"[^頁]*頁/);
        return totalMatch ? parseInt(totalMatch[1]) : 10;
    }
}

/**
 * 詳情頁面解析器
 */
class DetailParser {
    parse(html, url) {
        const video = {
            vod_id: url,
            vod_name: this.extractTitle(html, url),
            vod_pic: this.extractImage(html),
            vod_remarks: '',
            vod_year: CONSTANTS.DEFAULT_YEAR,
            vod_type: '',
            vod_actor: CONSTANTS.DEFAULT_ACTOR,
            vod_director: CONSTANTS.DEFAULT_DIRECTOR,
            vod_area: CONSTANTS.DEFAULT_AREA,
            vod_lang: CONSTANTS.DEFAULT_LANG,
            vod_content: CONSTANTS.DEFAULT_CONTENT,
            vod_play_from: CONSTANTS.DEFAULT_PLAY_FROM,
            vod_play_url: this.extractPlayUrl(html, url)
        };
        
        this.extractInfo(html, video);
        
        return video;
    }
    
    extractTitle(html, url) {
        const titleMatch = html.match(REGEX.DETAIL_TITLE);
        if (titleMatch) {
            return TextUtils.clean(titleMatch[1].replace(/-.*/, ''));
        }
        
        const urlMatch = url.match(/\/([^\/]+)\.html$/);
        return urlMatch ? decodeURIComponent(urlMatch[1].replace(/-/g, ' ')) : '未知劇集';
    }
    
    extractImage(html) {
        const imgMatch = html.match(REGEX.DETAIL_IMAGE);
        return imgMatch ? UrlUtils.fixUrl(imgMatch[1]) : '';
    }
    
    extractPlayUrl(html, url) {
        const playListMatch = html.match(REGEX.PLAY_LIST);
        if (!playListMatch) return `全集$${url}`;
        
        const episodes = [];
        const matches = playListMatch[1].matchAll(REGEX.PLAY_LINK);
        
        for (const match of matches) {
            const epUrl = UrlUtils.fixUrl(match[1]);
            const epTitle = TextUtils.clean(match[2]) || '第1集';
            episodes.push(`${epTitle}$${epUrl}`);
        }
        
        return episodes.length > 0 ? episodes.join('#') : `全集$${url}`;
    }
    
    extractInfo(html, video) {
        const infoPattern = /<p[^>]*>([^:]+):[^<]*<a[^>]*>([^<]+)<\/a>/g;
        let match;
        
        while ((match = infoPattern.exec(html)) !== null) {
            const key = TextUtils.clean(match[1]);
            const value = TextUtils.clean(match[2]);
            
            if (key.includes('類型') || key.includes('分类')) {
                video.vod_type = value;
            } else if (key.includes('地區') || key.includes('地区')) {
                video.vod_area = value;
            } else if (key.includes('年份')) {
                video.vod_year = value;
            } else if (key.includes('主演') || key.includes('演员')) {
                video.vod_actor = value;
            }
        }
    }
}

/**
 * 播放器解析器
 */
class PlayerParser {
    async parse(id) {
        if (!id) throw new Error('無效地址');
        
        // 直接m3u8地址
        if (id.includes('.m3u8')) {
            return this.createResponse(id);
        }
        
        // 播放頁面
        if (id.includes('/play/') || id.includes('/hongguo/')) {
            try {
                const html = await RequestManager.fetch(id);
                return this.extractFromHtml(html, id);
            } catch (error) {
                console.error('播放頁解析錯誤:', error);
            }
        }
        
        // 默認解析
        return this.createResponse(id, true);
    }
    
    extractFromHtml(html, referer) {
        // 從var now提取
        const nowMatch = html.match(REGEX.VAR_NOW);
        if (nowMatch && nowMatch[1]) {
            console.log('從var now找到地址:', nowMatch[1]);
            return this.createResponse(nowMatch[1], false, referer);
        }
        
        // 查找m3u8地址
        const m3u8Match = html.match(REGEX.M3U8_URL);
        if (m3u8Match) {
            console.log('找到m3u8地址:', m3u8Match[0]);
            return this.createResponse(m3u8Match[0], false, referer);
        }
        
        // 默認解析
        return this.createResponse(referer, true, referer);
    }
    
    createResponse(url, needParse = false, referer = baseUrl) {
        return {
            url: UrlUtils.fixUrl(url),
            parse: needParse ? 1 : 0,
            header: {
                'Referer': referer,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        };
    }
}

// 實例化解析器
const categoryParser = new CategoryParser();
const searchParser = new SearchParser();
const detailParser = new DetailParser();
const playerParser = new PlayerParser();

/**
 * 初始化
 */
async function init(cfg) {
    console.log(`[${siteName}] 爬蟲初始化`);
    return {
        sites: [{
            key: 'hongguo',
            name: siteName,
            type: 3,
            searchable: 1,
            changeable: 1,
            ext: '.html'
        }],
        player: {
            decode: 0,
            parse: 0,
            jx: 0
        }
    };
}

/**
 * 首頁分類配置
 */
async function homeContent(filter) {
    console.log('homeContent被調用');
    return { class: CATEGORIES };
}

/**
 * 首頁推薦視頻
 */
async function homeVideoContent() {
    try {
        console.log('獲取首頁推薦視頻...');
        const html = await RequestManager.fetch(baseUrl);
        const videos = categoryParser.parse(html).slice(0, 20);
        
        console.log('首頁推薦視頻數量:', videos.length);
        
        return Result.success(videos);
    } catch (error) {
        console.error('首頁推薦錯誤:', error);
        return Result.error(`首頁推薦錯誤: ${error.message}`);
    }
}

/**
 * 分類內容
 */
async function categoryContent(tid, pg, filter, extend) {
    console.log('分類請求:', { tid, pg });
    
    try {
        const page = pg || 1;
        const url = UrlUtils.buildCategoryUrl(tid, page);
        
        console.log('請求URL:', url);
        const html = await RequestManager.fetch(url);
        
        const videos = categoryParser.parse(html);
        const pagecount = categoryParser.getPageCount(html);
        
        console.log('提取到視頻數量:', videos.length, '總頁數:', pagecount);
        
        return {
            code: 1,
            msg: "數據列表",
            list: videos,
            page: page,
            pagecount: pagecount,
            limit: CONSTANTS.DEFAULT_LIMIT,
            total: videos.length > 0 ? videos.length * pagecount : 0
        };
    } catch (error) {
        console.error('分類頁錯誤:', error);
        return Result.error(`分類頁錯誤: ${error.message}`);
    }
}

/**
 * 詳情頁
 */
async function detailContent(ids) {
    if (!ids || !ids[0]) {
        return Result.error('無效ID');
    }
    
    const url = ids[0];
    console.log('詳情頁URL:', url);
    
    try {
        const html = await RequestManager.fetch(url);
        const video = detailParser.parse(html, url);
        
        return Result.success([video]);
    } catch (error) {
        console.error('詳情頁錯誤:', error);
        return Result.error(`詳情頁錯誤: ${error.message}`);
    }
}

/**
 * 搜索
 */
async function searchContent(key, quick, pg) {
    const keyword = key.trim();
    if (!keyword) return Result.error('搜索關鍵字為空');
    
    const page = pg || 1;
    const url = UrlUtils.buildSearchUrl(keyword, page);
    
    console.log('搜索URL:', url);
    
    try {
        const html = await RequestManager.fetch(url);
        
        const videos = searchParser.parse(html);
        const pagecount = searchParser.getPageCount(html);
        
        console.log('搜索結果數量:', videos.length, '總頁數:', pagecount);
        
        return {
            code: 1,
            msg: "搜索結果",
            list: videos,
            page: page,
            pagecount: pagecount,
            total: videos.length > 0 ? 1000 : 0
        };
    } catch (error) {
        console.error('搜索錯誤:', error);
        return Result.error(`搜索錯誤: ${error.message}`);
    }
}

/**
 * 播放器
 */
async function playerContent(flag, id, vipFlags) {
    console.log('播放器解析:', { flag, id });
    
    try {
        return await playerParser.parse(id);
    } catch (error) {
        console.error('播放器解析錯誤:', error);
        return playerParser.createResponse(id, true);
    }
}

/**
 * action
 */
async function action(actionStr) {
    console.log('action:', actionStr);
    return;
}

/**
 * 結果工具
 */
const Result = {
    success(list) {
        return {
            code: 1,
            msg: "成功",
            list: list,
            page: 1,
            pagecount: 1,
            total: list.length
        };
    },
    
    error(message) {
        return {
            code: 0,
            msg: message,
            list: [],
            page: 1,
            pagecount: 1,
            total: 0
        };
    }
};

/**
 * 測試函數
 */
async function testAll() {
    console.log('=== 紅果短劇爬蟲測試 ===');
    
    const results = {
        category: false,
        detail: false,
        search: false,
        home: false
    };
    
    try {
        // 測試分類
        console.log('\n1. 測試分類...');
        const categoryResult = await categoryContent('3', 1, {}, {});
        results.category = categoryResult.code === 1;
        console.log(`分類測試: ${results.category ? '成功' : '失敗'}, 找到視頻: ${categoryResult.list?.length || 0}`);
        
        // 測試詳情
        if (results.category && categoryResult.list?.length > 0) {
            console.log('\n2. 測試詳情...');
            const detailResult = await detailContent([categoryResult.list[0].vod_id]);
            results.detail = detailResult.code === 1;
            console.log(`詳情測試: ${results.detail ? '成功' : '失敗'}`);
        }
        
        // 測試搜索
        console.log('\n3. 測試搜索...');
        const searchResult = await searchContent('我', false, 1);
        results.search = searchResult.code === 1;
        console.log(`搜索測試: ${results.search ? '成功' : '失敗'}, 找到視頻: ${searchResult.list?.length || 0}`);
        
        // 測試首頁
        console.log('\n4. 測試首頁推薦...');
        const homeResult = await homeVideoContent();
        results.home = homeResult.code === 1;
        console.log(`首頁測試: ${results.home ? '成功' : '失敗'}`);
        
        console.log('\n=== 測試完成 ===');
        console.log('結果:', results);
        
    } catch (error) {
        console.error('測試錯誤:', error);
    }
    
    return results;
}

/**
 * 清除緩存
 */
function clearCache() {
    CacheManager.clear();
    console.log('緩存已清除');
}

/**
 * 性能監控
 */
const PerformanceMonitor = {
    timers: new Map(),
    
    start(label) {
        this.timers.set(label, performance.now());
    },
    
    end(label) {
        const start = this.timers.get(label);
        if (start) {
            const duration = performance.now() - start;
            console.log(`⏱️ ${label}: ${duration.toFixed(2)}ms`);
            this.timers.delete(label);
        }
    }
};

// 導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        init, 
        homeContent, 
        homeVideoContent, 
        categoryContent, 
        detailContent, 
        searchContent, 
        playerContent, 
        action,
        testAll,
        clearCache
    };
} else {
    Object.assign(window, { 
        init, 
        homeContent, 
        homeVideoContent, 
        categoryContent, 
        detailContent, 
        searchContent, 
        playerContent, 
        action,
        testAll,
        clearCache
    });
    console.log(`✅ ${siteName}爬蟲(優化版 v4.0)已加載`);
    console.log('可用命令: testAll(), clearCache()');
}