/**
 * 低端影视(ddys.run)爬虫
 * 作者：deepseek
 * 版本：1.1
 * 最后更新：2026-05-21
 * 发布页：https://www.ddys.diy/
 *
 * @config
 * debug: false
 * showWebView: false
 * percent: 80,60
 * returnType: dom
 * timeout: 30
 * keywords: 需要密码访问|系统安全验证|人机验证
 * blockImages: true
 * blockList: *.[ico|png|jpeg|jpg|gif|webp]*|*.css|*.js
 *
 */




const baseUrl = 'https://www.ddys.run';
const headers = { 'Referer': baseUrl };

/**
 * 初始化
 */
async function init(cfg) {
    // 检查是否有密码验证页面残留
    if (typeof document !== 'undefined' && document) {
        var passwordInput = document.querySelector('input[type="password"]');
        if (passwordInput) {
            console.log('检测到密码输入框，等待用户输入...');
        }
    }
    return;
}

/**
 * 首页分类（基于实际网站结构）
 */
async function homeContent(filter) {
    // 共同的筛选器（电影和剧集共用，动漫部分共用）
    var commonFilters = [
        { key: "class", name: "按剧情", value: [
            {n:"全部",v:""}, {n:"喜剧",v:"喜剧"}, {n:"爱情",v:"爱情"}, {n:"恐怖",v:"恐怖"},
            {n:"动作",v:"动作"}, {n:"科幻",v:"科幻"}, {n:"剧情",v:"剧情"}, {n:"战争",v:"战争"},
            {n:"警匪",v:"警匪"}, {n:"犯罪",v:"犯罪"}, {n:"动画",v:"动画"}, {n:"奇幻",v:"奇幻"},
            {n:"武侠",v:"武侠"}, {n:"冒险",v:"冒险"}, {n:"枪战",v:"枪战"}, {n:"悬疑",v:"悬疑"},
            {n:"惊悚",v:"惊悚"}, {n:"经典",v:"经典"}, {n:"青春",v:"青春"}, {n:"文艺",v:"文艺"},
            {n:"古装",v:"古装"}, {n:"历史",v:"历史"}, {n:"运动",v:"运动"}
        ] },
        { key: "area", name: "按地区", value: [
            {n:"全部",v:""}, {n:"大陆",v:"大陆"}, {n:"香港",v:"香港"}, {n:"台湾",v:"台湾"},
            {n:"美国",v:"美国"}, {n:"法国",v:"法国"}, {n:"英国",v:"英国"}, {n:"日本",v:"日本"},
            {n:"韩国",v:"韩国"}, {n:"德国",v:"德国"}, {n:"泰国",v:"泰国"}, {n:"印度",v:"印度"},
            {n:"意大利",v:"意大利"}, {n:"西班牙",v:"西班牙"}, {n:"加拿大",v:"加拿大"}, {n:"其他",v:"其他"}
        ] },
        { key: "year", name: "按年份", value: [
            {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"},
            {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"},
            {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"},
            {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"},
            {n:"2011",v:"2011"}, {n:"2010",v:"2010"}
        ] }
    ];

    // 动漫专用筛选（动漫没有剧情和地区筛选）
    var animeFilters = [
        { key: "year", name: "按年份", value: [
            {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"},
            {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"},
            {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"},
            {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"},
            {n:"2011",v:"2011"}, {n:"2010",v:"2010"}, {n:"2009",v:"2009"}, {n:"2008",v:"2008"},
            {n:"2007",v:"2007"}, {n:"2006",v:"2006"}, {n:"2005",v:"2005"}, {n:"2004",v:"2004"}
        ] }
    ];

    return {
        class: [
            { type_id: "dianying", type_name: "电影" },
            { type_id: "juji", type_name: "剧集" },
            { type_id: "dongman", type_name: "动漫" }
        ],
        filters: {
            "dianying": commonFilters,
            "juji": commonFilters,
            "dongman": animeFilters
        }
    };
}

/**
 * 首页推荐视频
 */
async function homeVideoContent() {
    const document = await Java.wvOpen(`${baseUrl}/`);  // 使用模板字符串
    const videos = parseVideoList(document);
    return { list: videos };
}

/**
 * 分类内容
 */
async function categoryContent(tid, pg, filter, extend) {
    var p = parseInt(pg) || 1;
    var area = extend.area || '';
    var year = extend.year || '';
    var cat = extend.class || '';
    
    var url = '';
    // 构建分类URL
    if (area && area !== '') {
        // 按地区筛选: /list/dianying-大陆----------.html
        url = `${baseUrl}/list/${tid}-${area}----------.html`;
    } else if (cat && cat !== '') {
        // 按剧情筛选: /list/dianying---喜剧--------.html
        url = `${baseUrl}/list/${tid}---${cat}--------.html`;
    } else if (year && year !== '') {
        // 按年份筛选: /list/dianying-----------2026.html
        url = `${baseUrl}/list/${tid}-----------${year}.html`;
    } else {
        // 无筛选，普通分页: /category/dianying-2.html
        url = `${baseUrl}/category/${tid}-${p}.html`;
    }
    
    console.log("categoryContent URL:", url);
    const document = await Java.wvOpen(url);
    const videos = parseVideoList(document);
    
    // 提取分页信息
    var page = p;
    var pagecount = p;
    var total = videos.length;
    try {
        // 修正选择器：匹配 li.active.num a
        var pageEl = document.querySelector("li.active.num a");
        if (pageEl) {
            var pageText = pageEl.textContent || pageEl.innerText;
            var parts = pageText.split('/');
            if (parts.length === 2) {
                page = parseInt(parts[0]);
                pagecount = parseInt(parts[1]);
                total = pagecount * 12;
            }
        }
    } catch(e) {
        console.log("parse page error:", e);
    }
    
    return { code: 1, msg: "数据列表", list: videos, page: page, pagecount: pagecount, limit: 12, total: total };
}

/**
 * 详情页
 */
async function detailContent(ids) {
	// Java.showWebView();
    const document = await Java.wvOpen(ids[0]);
    const list = parseDetailPage(document);
    return { code: 1, msg: "数据列表", page: 1, pagecount: 1, limit: 1, total: 1, list };
}

/**
 * 搜索
 */
async function searchContent(key, quick, pg) {
    var p = parseInt(pg) || 1;
    // 搜索URL格式: /search/关键词----------页码---.html
    var url = `${baseUrl}/search/${encodeURIComponent(key)}----------${p}---.html`;
    console.log("search URL:", url);
    
    var res = await Java.req(url);
    if (!res.doc) {
        return { code: 0, msg: "搜索失败", list: [], page: 1, pagecount: 1, limit: 12, total: 0 };
    }
    
    var videos = parseVideoList(res.doc);
    var page = p;
    var pagecount = p;
    var total = videos.length;
    
    try {
        var pageEl = res.doc.querySelector("li.active.num a");
        if (pageEl) {
            var pageText = pageEl.textContent || pageEl.innerText;
            var parts = pageText.split('/');
            if (parts.length === 2) {
                page = parseInt(parts[0]);
                pagecount = parseInt(parts[1]);
                total = pagecount * 12;
            }
        }
    } catch(e) {
        console.log("search parse page error:", e);
    }
    
    return { code: 1, msg: "数据列表", list: videos, page: page, pagecount: pagecount, limit: 12, total: total };
}

/**
 * 播放器
 */
async function playerContent(flag, id, vipFlags) {
    return { url: id, parse: 1 };
}

/**
 * action
 */
async function action(actionStr) {
    try {
        const params = JSON.parse(actionStr);
        console.log("action params:", params);
    } catch (e) {
        console.log("action is not JSON, treat as string");
    }
    return;
}


/* ---------------- 工具函数 ---------------- */

/**
 * 提取视频列表
 */
function parseVideoList(document) {
    var boxes = Array.from(document.querySelectorAll('.stui-vodlist__box'));
    var list = [];
    for (var i = 0; i < boxes.length; i++) {
        var box = boxes[i];
        var titleEl = box.querySelector('.title a');
        var thumbEl = box.querySelector('.stui-vodlist__thumb');
        var remarksEl = box.querySelector('.pic-text');
        
        // 处理 vod_id
        var vodId = titleEl ? titleEl.getAttribute('href') : '';
        if (vodId && !vodId.startsWith('http')) {
            vodId = baseUrl + (vodId.startsWith('/') ? '' : '/') + vodId;
        }
        
        // 提取角标（如 HD中字|国语、TC中字、更新至第09集、已完结等）
        var vod_remarks = remarksEl ? remarksEl.textContent.trim() : '';
        
        // 尝试从角标中提取年份（如包含年份数字）
        var vod_year = '';
        var yearMatch = vod_remarks.match(/(19|20)\d{2}/);
        if (yearMatch) {
            vod_year = yearMatch[0];
        }
        
        // 提取演员信息（从注释节点）
        var vod_actor = '';
        var textEl = box.querySelector('.text');
        if (textEl) {
            var comment = textEl.previousSibling;
            if (comment && comment.nodeType === 8) {
                vod_actor = comment.textContent.trim();
            }
        }
        
        list.push({
            vod_name: titleEl ? (titleEl.title || titleEl.textContent || '') : '',
            vod_pic: thumbEl ? (thumbEl.getAttribute('data-original') ||
                        (thumbEl.style.backgroundImage ? thumbEl.style.backgroundImage.match(/url\(["']?([^"')]+)["']?\)/)?.[1] : '') || '') : '',
            vod_remarks: vod_remarks,
            vod_year: vod_year,
            vod_id: vodId,
            vod_actor: vod_actor
        });
    }
    return list;
}

/**
 * 解析详情页
 */
function parseDetailPage(document) {
    const title = document.querySelector('.stui-content__detail .title')?.textContent.trim() || '';
    const vod_pic = document.querySelector('.stui-content__thumb img')?.src || '';
    const info = document.querySelectorAll('.stui-content__detail .data');

    const typeMatch = info[0]?.textContent.match(/类型：([^/]+)\s*\/\s*地区：([^/]+)\s*\/\s*年份：(\d+)/) || [];
    const type_name = typeMatch[1] || '', vod_area = typeMatch[2] || '', vod_year = typeMatch[3] || '';
    const vod_actor = info[1]?.textContent.replace('主演：', '').trim() || '';
    const vod_director = info[2]?.textContent.replace('导演：', '').trim() || '';
    const vod_remarks = info[3]?.textContent.replace('更新：', '').trim() || '';
    const vod_content = document.querySelector('.detail-content')?.textContent.trim() ||
                        document.querySelector('.detail-sketch')?.textContent.trim() || '';

    // 播放线路
    const head = document.querySelector('.stui-vodlist__head h3');
    const ul = document.querySelector('.stui-content__playlist');
    const episodes = ul ? Array.from(ul.querySelectorAll('a')).map(a =>
        `${a.textContent.trim()}$${baseUrl + a.getAttribute('href')}`) : [];
    const vod_play_from = head ? head.textContent.trim().replace('在线播放', '线路') : '';
    const vod_play_url = episodes.join('#');

    return [{
        vod_id: window.location.pathname.replace(/[^\w]/g, '_'),
        vod_name: title,
        vod_pic: vod_pic,
        vod_remarks: vod_remarks,
        vod_year: vod_year,
        vod_actor: vod_actor,
        vod_director: vod_director,
        vod_area: vod_area,
        vod_lang: vod_area.includes('大陆') ? '国语' : '其他',
        vod_content: vod_content,
        vod_play_from: vod_play_from,
        vod_play_url: vod_play_url
    }];
}
