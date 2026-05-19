/**
 * 新韩剧网(hanju7.com)爬虫
 * 作者：deepseek
 * 版本：2.0
 * 最后更新：2026-05-20
 * 
 * @config
 * debug: true
 * returnType: dom
 * timeout: 30
 * blockImages: true
 * blockList: *.[ico|png|jpeg|jpg|gif|webp]*,.css
 */

const baseUrl = 'https://www.hanju7.com';
const headers = {
    'Referer': baseUrl,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
};

// 辅助函数
function safeText(el) {
    if (!el) return '';
    return (el.textContent || el.innerText || '').replace(/\s+/g, ' ').trim();
}

function fixUrl(url, doc) {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    if (url.startsWith('//')) return 'https:' + url;
    if (doc && typeof doc.fixUrl === 'function') return doc.fixUrl(url);
    return baseUrl.replace(/\/$/, '') + (url.startsWith('/') ? url : '/' + url);
}

// 通用列表提取
function extractList(doc, isSearch) {
    var items = doc.querySelectorAll('.list ul li, .txt ul li');
    var list = [];
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        // 跳过表头行
        if (el.id === 't') continue;
        
        var link = el.querySelector('a[href^="/detail/"]');
        var img = el.querySelector('.tu');
        var vodId = link ? fixUrl(link.getAttribute('href'), doc) : '';
        var vodName = '';
        if (isSearch) {
            var nameEl = el.querySelector('#name a');
            vodName = nameEl ? safeText(nameEl) : '';
        } else {
            vodName = link ? link.getAttribute('title') || safeText(link) : '';
        }
        var vodPic = img ? fixUrl(img.getAttribute('data-original') || img.getAttribute('src'), doc) : '';
        var vodRemarks = '';
        var tipEl = el.querySelector('.tip');
        if (tipEl) {
            vodRemarks = safeText(tipEl);
        } else if (isSearch) {
            var actorEl = el.querySelector('#actor');
            vodRemarks = actorEl ? safeText(actorEl) : '';
        }
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

// 提取剧集列表
function extractPlayList(doc) {
    var items = doc.querySelectorAll('.play ul li a');
    var eps = [];
    for (var i = 0; i < items.length; i++) {
        var a = items[i];
        var title = safeText(a);
        var onclick = a.getAttribute('onclick');
        var match = onclick ? onclick.match(/bb_a\('([^']+)'/) : null;
        var playId = match ? match[1] : '';
        if (playId) {
            eps.push(title + '$' + playId);
        }
    }
    return eps.join('#');
}

// 初始化
async function init(cfg) {
    return;
}

// 首页分类和筛选
async function homeContent(filter) {
    var filterConfig = {
        class: [
            { type_id: "1", type_name: "韩剧" },
            { type_id: "3", type_name: "韩国电影" },
            { type_id: "4", type_name: "韩国综艺" },
            { type_id: "hot", type_name: "排行榜" },
            { type_id: "new", type_name: "最新更新" }
        ],
        filters: {
            "1": [
                { key: "year", name: "年份", value: [{n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"10后",v:"2010__2019"}, {n:"00后",v:"2000__2009"}, {n:"90后",v:"1990__1999"}, {n:"80后",v:"1980__1989"}, {n:"更早",v:"1900__1980"}] },
                { key: "sort", name: "排序", value: [{n:"最新",v:"newstime"}, {n:"热门",v:"onclick"}] }
            ],
            "3": [
                { key: "year", name: "年份", value: [{n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"10后",v:"2010__2019"}, {n:"00后",v:"2000__2009"}, {n:"90后",v:"1990__1999"}, {n:"80后",v:"1980__1989"}, {n:"更早",v:"1900__1980"}] },
                { key: "sort", name: "排序", value: [{n:"最新",v:"newstime"}, {n:"热门",v:"onclick"}] }
            ],
            "4": [
                { key: "year", name: "年份", value: [{n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"10后",v:"2010__2019"}, {n:"00后",v:"2000__2009"}, {n:"90后",v:"1990__1999"}, {n:"80后",v:"1980__1989"}, {n:"更早",v:"1900__1980"}] },
                { key: "sort", name: "排序", value: [{n:"最新",v:"newstime"}, {n:"热门",v:"onclick"}] }
            ]
        }
    };
    return filterConfig;
}

// 首页推荐
async function homeVideoContent() {
    var res = await fetch(baseUrl + '/', { headers: headers });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    var list = extractList(res.doc, false);
    return { list: list };
}

// 分类内容
async function categoryContent(tid, pg, filter, extend) {
    pg = parseInt(pg) || 1;
    // pg 从 1 开始，但网站从 0 开始（0=第1页）
    var realPg = pg - 1;
    var ext = extend || {};
    var year = ext.year || '';
    var sort = ext.sort || '';
    
    if (tid === 'hot') {
        var res = await fetch(baseUrl + '/hot.html', { headers: headers });
        if (res.error || !res.doc) return Result.error(res.error || '请求失败');
        var list = extractHotList(res.doc);
        var pagecount = 1;
        return { page: pg, pagecount: pagecount, list: list, total: list.length };
    }
    if (tid === 'new') {
        var res = await fetch(baseUrl + '/new.html', { headers: headers });
        if (res.error || !res.doc) return Result.error(res.error || '请求失败');
        var list = extractNewList(res.doc);
        var pagecount = 1;
        return { page: pg, pagecount: pagecount, list: list, total: list.length };
    }
    
    var url = baseUrl + '/list/' + tid + '-' + year + '-' + sort + '-' + realPg + '.html';
    var res = await fetch(url, { headers: headers });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    var list = extractList(res.doc, false);
    
    // 获取总页数
    var pageLinks = res.doc.querySelectorAll('.page a');
    var maxPage = pg;
    for (var i = 0; i < pageLinks.length; i++) {
        var linkText = pageLinks[i].textContent;
        var pageNum = parseInt(linkText);
        if (!isNaN(pageNum) && pageNum > maxPage) {
            maxPage = pageNum;
        }
    }
    var pagecount = maxPage > pg ? maxPage : pg;
    
    return { page: pg, pagecount: pagecount, list: list, total: list.length };
}

// 提取排行榜列表
function extractHotList(doc) {
    var items = doc.querySelectorAll('.list_txt ul li');
    var list = [];
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        var link = el.querySelector('a');
        var vodId = link ? fixUrl(link.getAttribute('href'), doc) : '';
        var vodName = link ? safeText(link) : '';
        var vodRemarks = el.querySelector('span') ? safeText(el.querySelector('span')) : '';
        if (!vodId || !vodName) continue;
        list.push({
            vod_id: vodId,
            vod_name: vodName,
            vod_pic: '',
            vod_remarks: vodRemarks
        });
    }
    return list;
}

// 提取最新更新列表
function extractNewList(doc) {
    return extractHotList(doc);
}

// 详情内容
async function detailContent(ids) {
    var id = Array.isArray(ids) ? ids[0] : ids;
    var res = await fetch(fixUrl(id), { headers: headers });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    var doc = res.doc;
    
    // 提取基本信息
    var name = '';
    var pic = '';
    var remarks = '';
    var year = '';
    var actor = '';
    var content = '';
    
    // 标题
    var titleEl = doc.querySelector('.name dd');
    if (titleEl) name = safeText(titleEl);
    
    // 封面
    var picEl = doc.querySelector('.pic img');
    if (picEl) pic = fixUrl(picEl.getAttribute('src') || picEl.getAttribute('data-original'), doc);
    
    // 详情字段
    var infoItems = doc.querySelectorAll('.info dl');
    for (var i = 0; i < infoItems.length; i++) {
        var dt = infoItems[i].querySelector('dt');
        var dd = infoItems[i].querySelector('dd');
        if (!dt || !dd) continue;
        var label = safeText(dt);
        var value = safeText(dd);
        if (label === '状态：') {
            remarks = value;
        } else if (label === '主演：') {
            actor = value;
        } else if (label === '上映：') {
            year = value.split('-')[0];
        }
    }
    
    // 剧情
    var contentEl = doc.querySelector('.juqing');
    if (contentEl) content = safeText(contentEl);
    
    // 剧集列表
    var playUrl = extractPlayList(doc);
    if (!playUrl && id) {
        playUrl = '第1集$' + id;
    }
    
    var list = [{
        vod_id: id,
        vod_name: name,
        vod_pic: pic,
        vod_remarks: remarks,
        vod_year: year,
        vod_actor: actor,
        vod_content: content,
        vod_play_from: '新韩剧网',
        vod_play_url: playUrl
    }];
    
    return { code: 1, msg: "数据列表", page: 1, pagecount: 1, limit: 1, total: 1, list: list };
}

// 搜索内容
async function searchContent(key, quick, pg) {
    pg = parseInt(pg) || 1;
    var res = await fetch(baseUrl + '/search/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'show=searchkey&keyboard=' + encodeURIComponent(key)
    });
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    var doc = res.doc;
    var items = doc.querySelectorAll('.txt ul li');
    var list = [];
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        if (el.id === 't') continue;
        var link = el.querySelector('#name a');
        var vodId = link ? fixUrl(link.getAttribute('href'), doc) : '';
        var vodName = link ? safeText(link) : '';
        var vodRemarks = '';
        var actorEl = el.querySelector('#actor');
        if (actorEl) vodRemarks = safeText(actorEl);
        if (!vodId || !vodName) continue;
        list.push({
            vod_id: vodId,
            vod_name: vodName,
            vod_pic: '',
            vod_remarks: vodRemarks
        });
    }
    var pagecount = list.length > 0 ? 1 : 1;
    return { code: 1, msg: "数据列表", list: list, page: pg, pagecount: pagecount, limit: list.length, total: list.length };
}

// 播放器
async function playerContent(flag, id, vipFlags) {
    // id 格式如 "3669_1_1"
    // 调用解密接口获取真实播放地址
    var res = await fetch(baseUrl + '/u/u1.php?ud=' + id, { headers: headers });
    if (res.error) {
        return { parse: 1, url: baseUrl + '/detail/' + id.split('_')[0] + '.html', header: headers };
    }
    // 返回嗅探模式，让宿主处理
    return {
        type: 'sniff',
        url: baseUrl + '/detail/' + id.split('_')[0] + '.html',
        keyword: '.m3u8|.mp4',
        script: 'var a=document.querySelector(\'a[onclick*="' + id + '"]\');if(a)a.click();',
        headers: headers,
        timeout: 15
    };
}

// action
async function action(actionStr) {
    try {
        var params = JSON.parse(actionStr);
        console.log("action params:", params);
    } catch (e) {
        console.log("action is not JSON, treat as string");
    }
    return;
}

// 路由配置
var routes = {
    homeVideoContent: function() { return false; },
    categoryContent: function() { return false; },
    detailContent: function() { return false; },
    searchContent: function() { return false; }
};

var spider = { init, homeContent, homeVideoContent, categoryContent, detailContent, searchContent, playerContent, action };
spider;