/**
 * @config
 * timeout: 30
 * blockImages: true
 * returnType: dom
 * keyword: Checking your browser|Just a moment|请稍候
 */

const baseUrl = 'https://momovod.app';
const headers = {
    'Referer': baseUrl,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

// 辅助函数：安全获取文本
function safeText(el) {
    if (!el) return '';
    return (el.textContent || el.innerText || '').replace(/\s+/g, ' ').trim();
}

// 辅助函数：补全 URL
function fixUrl(url, doc) {
    if (!url) return '';
    if (url.indexOf('http://') === 0 || url.indexOf('https://') === 0) return url;
    if (url.indexOf('//') === 0) return 'https:' + url;
    if (doc && typeof doc.fixUrl === 'function') return doc.fixUrl(url);
    return baseUrl.replace(/\/$/, '') + (url.charAt(0) === '/' ? url : '/' + url);
}

// 通用列表提取函数（首页、分类、搜索共用）
function extractList(doc, containerSelector) {
    var items = doc.querySelectorAll('.myui-vodlist__box');
    var list = [];
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        var thumb = el.querySelector('.myui-vodlist__thumb');
        var link = thumb && thumb.href ? thumb : el.querySelector('a');
        var img = thumb || el.querySelector('img');
        var titleEl = el.querySelector('.title');
        
        var vodId = link ? link.getAttribute('href') : '';
        var vodName = titleEl ? safeText(titleEl) : '';
        var vodPic = img ? (img.getAttribute('data-original') || img.src) : '';
        var vodRemarks = el.querySelector('.pic-text') ? safeText(el.querySelector('.pic-text')) : '';
        
        vodId = fixUrl(vodId, doc);
        vodPic = fixUrl(vodPic, doc);
        
        if (!vodId || !vodName) continue;
        list.push({
            vod_id: vodId,
            vod_name: vodName,
            vod_pic: vodPic,
            vod_remarks: vodRemarks
        });
    }
    return list;
}

// 分类和筛选（各分类独立硬编码）
async function homeContent(filter) {
    // 分类列表
    var classes = [
        { type_id: '1', type_name: '電影' },
        { type_id: '2', type_name: '劇集' },
        { type_id: '3', type_name: '綜藝' },
        { type_id: '4', type_name: '動漫' },
        { type_id: '27', type_name: '倫理片' }
    ];
    
    // 电影筛选
    var movieFilters = [
        { key: 'class', name: '類型', value: [
            { n: '全部', v: '' }, { n: '動作片', v: '6' }, { n: '喜劇片', v: '7' },
            { n: '愛情片', v: '8' }, { n: '科幻片', v: '9' }, { n: '恐怖片', v: '10' },
            { n: '劇情片', v: '11' }, { n: '戰爭片', v: '12' }, { n: '紀錄片', v: '20' },
            { n: '微電影', v: '21' }, { n: '動漫片', v: '22' }, { n: '倫理片', v: '27' }
        ]},
        { key: 'area', name: '地區', value: [
            { n: '全部', v: '' }, { n: '大陸', v: '大陸' }, { n: '香港', v: '香港' },
            { n: '臺灣', v: '臺灣' }, { n: '美國', v: '美國' }, { n: '法國', v: '法國' },
            { n: '英國', v: '英國' }, { n: '日本', v: '日本' }, { n: '韓國', v: '韓國' },
            { n: '德國', v: '德國' }, { n: '泰國', v: '泰國' }, { n: '印度', v: '印度' },
            { n: '意大利', v: '意大利' }, { n: '西班牙', v: '西班牙' }, { n: '加拿大', v: '加拿大' },
            { n: '其他', v: '其他' }
        ]},
        { key: 'year', name: '年份', value: [
            { n: '全部', v: '' }, { n: '2025', v: '2025' }, { n: '2024', v: '2024' },
            { n: '2023', v: '2023' }, { n: '2022', v: '2022' }, { n: '2021', v: '2021' },
            { n: '2020', v: '2020' }, { n: '2019', v: '2019' }, { n: '2018', v: '2018' },
            { n: '2017', v: '2017' }, { n: '2016', v: '2016' }, { n: '2015', v: '2015' },
            { n: '2014', v: '2014' }, { n: '2013', v: '2013' }, { n: '2012', v: '2012' },
            { n: '2011', v: '2011' }, { n: '2010', v: '2010' }
        ]},
        { key: 'by', name: '排序', value: [
            { n: '時間', v: 'time' }, { n: '人氣', v: 'hits' }, { n: '評分', v: 'score' }
        ]}
    ];
    
    // 剧集筛选（类型为剧集分类）
    var tvFilters = [
        { key: 'class', name: '類型', value: [
            { n: '全部', v: '' }, { n: '陸劇', v: '13' }, { n: '港劇', v: '14' },
            { n: '台劇', v: '15' }, { n: '日劇', v: '16' }, { n: '韓劇', v: '23' },
            { n: '美劇', v: '24' }, { n: '海外劇', v: '25' }
        ]},
        { key: 'area', name: '地區', value: [
            { n: '全部', v: '' }, { n: '大陸', v: '大陸' }, { n: '韓國', v: '韓國' },
            { n: '香港', v: '香港' }, { n: '臺灣', v: '臺灣' }, { n: '日本', v: '日本' },
            { n: '美國', v: '美國' }, { n: '泰國', v: '泰國' }, { n: '英國', v: '英國' },
            { n: '新加坡', v: '新加坡' }, { n: '其他', v: '其他' }
        ]},
        { key: 'year', name: '年份', value: movieFilters[2].value }, // 复用年份
        { key: 'by', name: '排序', value: movieFilters[3].value }  // 复用排序
    ];
    
    // 综艺筛选
    var varietyFilters = [
        { key: 'class', name: '類型', value: [
            { n: '全部', v: '' }, { n: '港台綜藝', v: '34' }, { n: '日韓綜藝', v: '35' },
            { n: '大陸綜藝', v: '36' }, { n: '歐美綜藝', v: '37' }
        ]},
        { key: 'year', name: '年份', value: movieFilters[2].value },
        { key: 'by', name: '排序', value: movieFilters[3].value }
    ];
    
    // 动漫筛选
    var animeFilters = [
        { key: 'class', name: '類型', value: [
            { n: '全部', v: '' }, { n: '港台動漫', v: '29' }, { n: '日韓動漫', v: '30' },
            { n: '大陸動漫', v: '31' }, { n: '歐美動漫', v: '32' }, { n: '海外動漫', v: '33' }
        ]},
        { key: 'year', name: '年份', value: movieFilters[2].value },
        { key: 'by', name: '排序', value: movieFilters[3].value }
    ];
    
    // 伦理片筛选（同电影）
    var ethicsFilters = movieFilters;
    
    var filters = {
        '1': movieFilters,   // 电影
        '2': tvFilters,      // 剧集
        '3': varietyFilters, // 综艺
        '4': animeFilters,   // 动漫
        '27': ethicsFilters  // 伦理片
    };
    
    return { class: classes, filters: filters };
}

// 首页推荐
async function homeVideoContent() {
    var res = await fetch(baseUrl + '/', { headers: headers });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    var list = extractList(res.doc);
    return { list: list };
}

// 分类列表（支持筛选和分页）
async function categoryContent(tid, pg, filter, extend) {
    var p = parseInt(pg) || 1;
    var ext = extend || {};
    
    // 构建 URL: /show/{tid}/{筛选参数}/page/{pg}.html
    // 或 /show/{tid}/page/{pg}.html（无筛选）
    // 或 /type/{tid}-{pg}.html（无筛选，简单列表）
    var url;
    var hasFilter = false;
    var parts = ['/show', tid];
    
    if (ext.class && ext.class !== '') {
        parts.push('class', ext.class);
        hasFilter = true;
    }
    if (ext.area && ext.area !== '') {
        parts.push('area', ext.area);
        hasFilter = true;
    }
    if (ext.year && ext.year !== '') {
        parts.push('year', ext.year);
        hasFilter = true;
    }
    if (ext.by && ext.by !== '' && ext.by !== 'time') {
        parts.push('by', ext.by);
        hasFilter = true;
    }
    
    if (hasFilter) {
        // 使用 show 页面：/show/1/class/6/area/大陸/year/2025/by/hits/page/1.html
        parts.push('page', p);
        url = baseUrl + parts.join('/') + '.html';
    } else {
        // 无筛选时使用 type 页面：/type/1-2.html
        url = baseUrl + '/type/' + tid + (p > 1 ? '-' + p : '') + '.html';
    }
    
    var res = await fetch(url, { headers: headers });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    
    var list = extractList(res.doc);
    
    // 提取分页信息
    var pageEl = res.doc.querySelector('.myui-page');
    var total = 1;
    var pagecount = p;
    
    if (pageEl) {
        var links = pageEl.querySelectorAll('a');
        var maxPage = 1;
        for (var i = 0; i < links.length; i++) {
            var href = links[i].getAttribute('href');
            if (href && href.indexOf('/type/') === 0) {
                var match = href.match(/\/type\/\d+-(\d+)\.html/);
                if (match && parseInt(match[1]) > maxPage) maxPage = parseInt(match[1]);
            }
            if (href && href.indexOf('/page/') !== -1) {
                var match2 = href.match(/\/page\/(\d+)\.html/);
                if (match2 && parseInt(match2[1]) > maxPage) maxPage = parseInt(match2[1]);
            }
        }
        // 检查是否有下一页按钮
        var nextBtn = pageEl.querySelector('a[href*="下一頁"]') || pageEl.querySelector('a[rel="next"]');
        if (nextBtn && nextBtn.getAttribute('href') && nextBtn.getAttribute('href').indexOf('.html') !== -1) {
            pagecount = p + 1;
        } else if (maxPage > p) {
            pagecount = maxPage;
        } else {
            pagecount = p;
        }
    }
    
    return { page: p, pagecount: pagecount, list: list, total: list.length };
}

// 详情页（路由模式 - 在 WebView 中执行，可提取多线路剧集）
async function detailContent(ids) {
    var id = Array.isArray(ids) ? ids[0] : ids;
    
    // 等待页面 DOM 完全加载
    await new Promise(function(resolve) { setTimeout(resolve, 1500); });
    
    // 提取基本信息
    var vodName = safeText(document.querySelector('h1, .myui-panel__head .title'));
    var vodPic = document.querySelector('.myui-vodlist__thumb img, .poster img');
    vodPic = vodPic ? fixUrl(vodPic.getAttribute('data-original') || vodPic.src, document) : '';
    
    var vodActor = '', vodDirector = '', vodYear = '', vodArea = '', vodType = '', vodContent = '';
    var detailItems = document.querySelectorAll('.myui-content__detail li, .info li');
    for (var i = 0; i < detailItems.length; i++) {
        var text = detailItems[i].innerText.trim();
        if (text.indexOf('主演') !== -1) vodActor = text.replace('主演：', '').replace('主演', '').trim();
        if (text.indexOf('導演') !== -1) vodDirector = text.replace('導演：', '').replace('導演', '').trim();
        if (text.indexOf('年份') !== -1) vodYear = text.replace('年份：', '').replace('年份', '').trim();
        if (text.indexOf('地區') !== -1) vodArea = text.replace('地區：', '').replace('地區', '').trim();
        if (text.indexOf('類型') !== -1) vodType = text.replace('類型：', '').replace('類型', '').trim();
    }
    vodContent = safeText(document.querySelector('.desc, .content-desc'));
    
    // 获取所有线路标签
    var tabs = document.querySelectorAll('.nav-tabs li a');
    if (tabs.length === 0) {
        tabs = document.querySelectorAll('[data-toggle="tab"]');
    }
    
    var allFrom = [];
    var allUrls = [];
    
    if (tabs.length > 0) {
        // 遍历每个线路标签
        for (var i = 0; i < tabs.length; i++) {
            var from = tabs[i].innerText.trim();
            if (!from) continue;
            
            // 点击标签切换线路
            tabs[i].click();
            await new Promise(function(resolve) { setTimeout(resolve, 800); });
            
            // 提取当前激活的剧集列表
            var eps = [];
            var activePane = document.querySelector('.tab-pane.active');
            if (!activePane) {
                activePane = document.querySelector('[class*="tab-pane"][style*="block"], .tab-pane:not(.fade)');
            }
            
            var episodeLinks = [];
            if (activePane) {
                episodeLinks = activePane.querySelectorAll('.myui-content__list a, .play-list a, [class*="playlist"] a');
            } else {
                episodeLinks = document.querySelectorAll('.myui-content__list a');
            }
            
            for (var j = 0; j < episodeLinks.length; j++) {
                var epName = episodeLinks[j].innerText.trim();
                var epUrl = episodeLinks[j].getAttribute('href');
                if (epUrl && epUrl.indexOf('/play/') !== -1) {
                    if (!epName || epName === '') {
                        epName = '第' + (j + 1) + '集';
                    }
                    eps.push(epName + '$' + fixUrl(epUrl, document));
                }
            }
            
            allFrom.push(from);
            allUrls.push(eps.join('#'));
        }
    } else {
        // 没有线路标签，直接提取当前页面的剧集
        allFrom.push('线路1');
        var eps = [];
        var links = document.querySelectorAll('.myui-content__list a');
        for (var i = 0; i < links.length; i++) {
            var epName = links[i].innerText.trim() || ('第' + (i + 1) + '集');
            var epUrl = links[i].getAttribute('href');
            if (epUrl && epUrl.indexOf('/play/') !== -1) {
                eps.push(epName + '$' + fixUrl(epUrl, document));
            }
        }
        allUrls.push(eps.join('#'));
    }
    
    return {
        list: [{
            vod_id: id,
            vod_name: vodName,
            vod_pic: vodPic,
            vod_actor: vodActor,
            vod_director: vodDirector,
            vod_year: vodYear,
            vod_area: vodArea,
            vod_type: vodType,
            vod_content: vodContent,
            vod_play_from: allFrom.join('$$$'),
            vod_play_url: allUrls.join('$$$')
        }]
    };
}

// 搜索
async function searchContent(key, quick, pg) {
    var p = parseInt(pg) || 1;
    var url = baseUrl + '/search.html?wd=' + encodeURIComponent(key) + '&page=' + p;
    var res = await fetch(url, { headers: headers });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    
    var list = extractList(res.doc);
    
    // 提取分页信息
    var pageEl = res.doc.querySelector('.myui-page');
    var pagecount = p;
    if (pageEl) {
        var nextBtn = pageEl.querySelector('a[href*="下一頁"]');
        if (nextBtn && nextBtn.getAttribute('href')) {
            pagecount = p + 1;
        }
    }
    
    return { page: p, pagecount: pagecount, list: list, total: list.length };
}

// 播放
async function playerContent(flag, id, vipFlags) {
    // id 是播放页 URL，如 /play/505786-5-1.html
    var playUrl = fixUrl(id);
    var res = await fetch(playUrl, { headers: headers });
    if (res.error || !res.doc) return { parse: 1, url: playUrl, header: headers };
    
    // 尝试从页面中提取 player_aaaa 变量的视频直链
    var html = res.body;
    var match = html.match(/url:\s*['"]([^'"]+\.m3u8[^'"]*)['"]/);
    if (match && match[1]) {
        // 找到直链，直接返回
        return { parse: 0, url: match[1], header: headers };
    }
    
    // 尝试从 iframe 中提取
    var iframe = res.doc.querySelector('.MacPlayer iframe');
    if (iframe && iframe.src && iframe.src.indexOf('vip.avdb.me') !== -1) {
        // 解析 iframe 中的视频地址
        return { parse: 1, url: iframe.src, header: headers };
    }
    
    // 默认嗅探
    return { parse: 1, url: playUrl, header: headers };
}

// 路由（detailContent 需要使用路由模式来获取多线路剧集）
var routes = {
    homeVideoContent: function () { return false; },
    categoryContent: function () { return false; },
    detailContent: function (ids) {
        // 返回详情页 URL，让 WebView 导航
        var id = Array.isArray(ids) ? ids[0] : ids;
        return fixUrl(id);
    },
    searchContent: function () { return false; }
};