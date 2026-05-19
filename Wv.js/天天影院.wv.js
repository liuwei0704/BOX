/**
 * 天天影院爬虫 - 最新规范版
 * @config
 * timeout: 30
 * blockImages: true
 * returnType: dom
 * keyword: Checking your browser|Just a moment|请稍候
 */

const baseUrl = 'https://www.baixiaotangtop.com';

const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': baseUrl
};

function fixUrl(url) {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    if (url.startsWith('//')) return 'https:' + url;
    return baseUrl.replace(/\/$/, '') + (url.startsWith('/') ? url : '/' + url);
}

function homeContent() {
    return {
        class: [
            { type_id: "1", type_name: "电影" },
            { type_id: "2", type_name: "电视剧" },
            { type_id: "3", type_name: "综艺" },
            { type_id: "4", type_name: "动漫" },
            { type_id: "36", type_name: "短剧" }
        ],
        filters: {}
    };
}

async function homeVideoContent() {
    let resp = await Java.req(baseUrl, { headers: headers });
    let list = parseHtmlForList(resp.body);
    return { list: list };
}

async function categoryContent(tid, pg, filter, extend) {
    let url = baseUrl + '/vodshow/' + tid + '--------' + (pg || 1) + '---.html';
    let resp = await Java.req(url, { headers: headers });
    let list = parseHtmlForList(resp.body);
    let total = parseHtmlForTotalPages(resp.body);
    let currentPage = parseInt(pg) || 1;
    return {
        list: list,
        page: currentPage,
        pagecount: total || currentPage,
        total: (total || currentPage) * 20
    };
}

async function detailContent(ids) {
    let id = Array.isArray(ids) ? ids[0] : ids;
    let resp = await Java.req(id, { headers: headers });
    let detail = parseHtmlForDetail(resp.body, id);
    return { list: [detail] };
}

async function searchContent(key, quick, pg) {
    let currentPage = parseInt(pg) || 1;
    let url = baseUrl + '/vodsearch/' + encodeURIComponent(key) + '----------' + currentPage + '---.html';
    let resp = await Java.req(url, { headers: headers });
    let list = parseHtmlForList(resp.body);
    let total = parseHtmlForTotalPages(resp.body);
    return {
        list: list,
        page: currentPage,
        pagecount: total || currentPage,
        total: (total || currentPage) * 20
    };
}

async function playerContent(flag, id, vipFlags) {
    let resp = await Java.req(id, { headers: headers });
    let html = resp.body;
    let m3u8 = '';
    
    // 匹配播放地址（支持多种格式）
    let patterns = [
        /"url":"([^"]+\.m3u8[^"]*)"/i,
        /"url":"([^"]+\.mp4[^"]*)"/i,
        /video[^>]+src=["']([^"']+\.m3u8[^"']*)["']/i,
        /source[^>]+src=["']([^"']+\.m3u8[^"']*)["']/i
    ];
    
    for (var i = 0; i < patterns.length; i++) {
        let match = html.match(patterns[i]);
        if (match && match[1]) {
            m3u8 = match[1].replace(/\\/g, '');
            break;
        }
    }
    
    // 处理转义字符
    if (m3u8) {
        m3u8 = m3u8.replace(/\\\//g, '/');
    }
    
    if (m3u8 && (m3u8.indexOf('.m3u8') > -1 || m3u8.indexOf('.mp4') > -1)) {
        return { parse: 0, url: m3u8 };
    }
    
    // 嗅探模式
    return { parse: 1, url: id, header: headers };
}

function parseHtmlForList(html) {
    var vods = [];
    // 匹配每个视频项（兼容多种 class）
    var itemRegex = /<li[^>]*class="[^"]*(?:col-md-6|module-item)[^"]*"[^>]*>([\s\S]*?)<\/li>/gi;
    var match;
    while ((match = itemRegex.exec(html)) !== null) {
        var itemHtml = match[1];
        
        // 提取详情页链接
        var linkMatch = itemHtml.match(/href="([^"]*\/voddetail\/[^"]*)"/);
        if (!linkMatch) continue;
        var href = linkMatch[1];
        
        // 提取标题
        var titleMatch = itemHtml.match(/title="([^"]*)"/);
        var title = titleMatch ? titleMatch[1] : '';
        if (!title) {
            var altMatch = itemHtml.match(/alt="([^"]*)"/);
            title = altMatch ? altMatch[1] : '';
        }
        if (!title) {
            var textMatch = itemHtml.match(/<a[^>]*>([^<]+)<\/a>/);
            title = textMatch ? textMatch[1].trim() : '';
        }
        
        // 提取图片
        var imgMatch = itemHtml.match(/data-original="([^"]*)"/);
        var pic = imgMatch ? imgMatch[1] : '';
        if (!pic) {
            var srcMatch = itemHtml.match(/src="([^"]*)"/);
            pic = srcMatch ? srcMatch[1] : '';
        }
        
        // 提取备注（集数/清晰度）
        var remarkMatch = itemHtml.match(/pic-text[^>]*>([^<]*)</);
        var remark = remarkMatch ? remarkMatch[1].trim() : '';
        if (!remark) {
            var tagMatch = itemHtml.match(/<span[^>]*class="[^"]*tag[^"]*"[^>]*>([^<]*)<\/span>/);
            remark = tagMatch ? tagMatch[1].trim() : '';
        }
        
        if (href && title) {
            vods.push({
                vod_id: fixUrl(href),
                vod_name: title.trim(),
                vod_pic: fixUrl(pic),
                vod_remarks: remark
            });
        }
    }
    return vods;
}

function parseHtmlForDetail(html, vodId) {
    // 标题
    var titleMatch = html.match(/<h1[^>]*class="[^"]*title[^"]*"[^>]*>[\s\S]*?<span[^>]*>([^<]*)<\/span>/);
    var title = titleMatch ? titleMatch[1] : '';
    if (!title) {
        var h1Match = html.match(/<h1[^>]*>([^<]+)<\/h1>/);
        title = h1Match ? h1Match[1].trim() : '';
    }
    
    // 图片
    var imgMatch = html.match(/<img[^>]*class="[^"]*lazyload[^"]*"[^>]*data-original="([^"]*)"/);
    var pic = imgMatch ? imgMatch[1] : '';
    if (!pic) {
        var posterMatch = html.match(/<img[^>]*class="[^"]*poster[^"]*"[^>]*src="([^"]*)"/);
        pic = posterMatch ? posterMatch[1] : '';
    }
    
    // 简介
    var descMatch = html.match(/<div[^>]*id="desc"[^>]*>[\s\S]*?<div[^>]*class="[^"]*col-pd[^"]*"[^>]*>([\s\S]*?)<\/div>/);
    var desc = descMatch ? descMatch[1].replace(/<[^>]*>/g, '').trim() : '';
    if (!desc) {
        var contentMatch = html.match(/<div[^>]*class="[^"]*vod_content[^"]*"[^>]*>([\s\S]*?)<\/div>/);
        desc = contentMatch ? contentMatch[1].replace(/<[^>]*>/g, '').trim() : '';
    }
    
    // 导演
    var director = '';
    var directorMatch = html.match(/导演[：:][\s\S]*?<a[^>]*>([^<]*)<\/a>/);
    if (directorMatch) director = directorMatch[1];
    
    // 主演
    var actor = '';
    var actorMatch = html.match(/主演[：:][\s\S]*?<a[^>]*>([^<]*)<\/a>/);
    if (actorMatch) actor = actorMatch[1];
    
    // 播放列表
    var playUrl = '';
    var playFrom = '';
    var playRegex = /<li[^>]*><a[^>]*href="([^"]*\/vodplay\/[^"]*)"[^>]*>([^<]*)<\/a><\/li>/gi;
    var playMatch;
    var urls = [];
    while ((playMatch = playRegex.exec(html)) !== null && urls.length < 200) {
        urls.push(playMatch[2] + '$' + fixUrl(playMatch[1]));
    }
    if (urls.length) {
        playUrl = urls.join('#');
        playFrom = '云播资源';
    }
    
    return {
        vod_id: vodId,
        vod_name: title,
        vod_pic: fixUrl(pic),
        vod_content: desc,
        vod_director: director,
        vod_actor: actor,
        vod_play_from: playFrom,
        vod_play_url: playUrl
    };
}

function parseHtmlForTotalPages(html) {
    // 匹配尾页页码
    var lastMatch = html.match(/href="[^"]*--------(\d+)---\.html"[^>]*>尾页</);
    if (lastMatch && lastMatch[1]) {
        return parseInt(lastMatch[1]);
    }
    // 备选：匹配页码选项中的最大值
    var pageMatch = html.match(/<option[^>]*value="(\d+)"[^>]*>第\d+页<\/option>/g);
    if (pageMatch && pageMatch.length) {
        var maxPage = 1;
        for (var i = 0; i < pageMatch.length; i++) {
            var valMatch = pageMatch[i].match(/value="(\d+)"/);
            if (valMatch && parseInt(valMatch[1]) > maxPage) {
                maxPage = parseInt(valMatch[1]);
            }
        }
        return maxPage;
    }
    return 1;
}

// fetch API 模式：routes 全部返回 false
var routes = {
    homeVideoContent: function() { return false; },
    categoryContent: function() { return false; },
    detailContent: function() { return false; },
    searchContent: function() { return false; }
};