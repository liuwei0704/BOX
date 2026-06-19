/**
 * 红果短剧爬虫 - 基础版（搜索返回空）
 */

const baseUrl = 'https://www.hongguoapp.cn';

function safeText(el) {
    if (!el) return '';
    return (el.textContent || el.innerText || '').replace(/\s+/g, ' ').trim();
}

function homeContent() {
    return {
        class: [
            { type_id: '51', type_name: '短剧' }
        ],
        filters: {}
    };
}

async function homeVideoContent() {
    var resp = await Java.req(baseUrl + '/vodshow/51-----------.html');
    var list = parseList(resp.body);
    return { list: list };
}

async function categoryContent(tid, pg) {
    var p = parseInt(pg) || 1;
    var url;
    if (p <= 1) {
        url = baseUrl + '/vodshow/51-----------.html';
    } else {
        url = baseUrl + '/vodshow/51--------' + p + '---.html';
    }
    var resp = await Java.req(url);
    var list = parseList(resp.body);
    var total = 492;
    return {
        list: list,
        page: p,
        pagecount: total,
        total: total
    };
}

async function detailContent(ids) {
    var id = Array.isArray(ids) ? ids[0] : ids;
    var res = await fetch(baseUrl + id);
    if (res.error || !res.doc) return Result.error(res.error || '请求失败');
    var doc = res.doc;
    var title = safeText(doc.querySelector('h2.hl-dc-title'));
    var pic = doc.querySelector('.hl-dc-pic .hl-item-thumb')?.getAttribute('data-original') || '';
    var content = safeText(doc.querySelector('.hl-content-text em'));
    var eps = [];
    doc.querySelectorAll('.hl-plays-list li a').forEach(function(el) {
        var epName = safeText(el) || '第1集';
        var epUrl = el.getAttribute('href');
        if (epUrl) eps.push(epName + '$' + epUrl);
    });
    var playUrl = eps.length ? eps.join('#') : '';
    return {
        list: [{
            vod_id: id,
            vod_name: title,
            vod_pic: pic,
            vod_content: content,
            vod_play_from: '正片合辑',
            vod_play_url: playUrl
        }]
    };
}

// 搜索需要认证，直接返回空列表
async function searchContent(key, quick, pg) {
    return { list: [] };
}

async function playerContent(flag, id, vipFlags) {
    var resp = await Java.req(baseUrl + id);
    var html = resp.body;
    var match = html.match(/["']url["']\s*:\s*["'](https?:\\\/\\\/[^"']+\.m3u8)["']/);
    if (match) {
        var videoUrl = match[1].replace(/\\\//g, '/');
        if (videoUrl && videoUrl.indexOf('.m3u8') > 0) {
            return { parse: 0, url: videoUrl, header: { 'Referer': baseUrl } };
        }
    }
    var match2 = html.match(/["']url["']\s*:\s*["']([^"']+)["']/);
    if (match2) {
        var videoUrl2 = match2[1].replace(/\\\//g, '/');
        if (videoUrl2 && videoUrl2.indexOf('.m3u8') > 0) {
            return { parse: 0, url: videoUrl2, header: { 'Referer': baseUrl } };
        }
    }
    var match3 = html.match(/var\s+player_aaaa\s*=\s*\{([^}]*)\}/);
    if (match3) {
        var objStr = match3[1];
        var urlMatch = objStr.match(/["']url["']\s*:\s*["']([^"']+)["']/);
        if (urlMatch) {
            var videoUrl3 = urlMatch[1].replace(/\\\//g, '/');
            if (videoUrl3 && videoUrl3.indexOf('.m3u8') > 0) {
                return { parse: 0, url: videoUrl3, header: { 'Referer': baseUrl } };
            }
        }
    }
    return { parse: 1, url: id, header: { 'Referer': baseUrl } };
}

function parseList(html) {
    var vods = [];
    var itemRegex = /<li[^>]*class="[^"]*hl-list-item[^"]*"[^>]*>([\s\S]*?)<\/li>/gi;
    var match;
    while ((match = itemRegex.exec(html)) !== null) {
        var innerHtml = match[1];
        var linkMatch = innerHtml.match(/href="([^"]*\/voddetail\/[^"]*)"/);
        if (!linkMatch) continue;
        var href = linkMatch[1];
        var titleMatch = innerHtml.match(/title="([^"]*)"/);
        var title = titleMatch ? titleMatch[1] : '';
        if (!title) {
            var titleTag = innerHtml.match(/<a[^>]*class="[^"]*hl-item-title[^"]*"[^>]*>([^<]*)<\/a>/);
            title = titleTag ? titleTag[1].trim() : '';
        }
        var imgMatch = innerHtml.match(/data-original="([^"]*)"/);
        var pic = imgMatch ? imgMatch[1] : '';
        var remarkMatch = innerHtml.match(/<span[^>]*class="[^"]*remarks[^"]*"[^>]*>([^<]*)<\/span>/);
        var remark = remarkMatch ? remarkMatch[1].trim() : '';
        if (href && title) {
            vods.push({
                vod_id: href,
                vod_name: title,
                vod_pic: pic,
                vod_remarks: remark
            });
        }
    }
    return vods;
}

var routes = {
    homeVideoContent: function () { return false; },
    categoryContent: function () { return false; },
    detailContent: function () { return false; },
    searchContent: function () { return false; },
    playerContent: function (flag, id, vipFlags) { return false; }
};