// 短剧one duanju.one 客户端单文件源
// 列表: /dramas  /dramas?filter=free|vip  /tag/{tag}  /dramas?q=xx
// 详情: /drama/{slug}   剧集: /drama/{slug}/ep/{N}   特辑: /drama/{slug}/special/sp-NNN
// 播放: 集页 <video src="mp4直链"> → parse:0
// 站点: Cloudflare 前置, 需带正常 UA/Referer

const HOST = 'https://duanju.one';
const UA = 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';

// 分类（站点为扁平标签体系，用大类占位 + 筛选）
const CLASSES = [
    { type_id: 'all', type_pid: '0', type_name: '全部' },
    { type_id: 'free', type_pid: '0', type_name: '免费' },
    { type_id: 'vip', type_pid: '0', type_name: 'VIP/积分' }
];

// 站点标签（来自首页 tag-strip）
const TAGS = [
    ['ntr', 'NTR'], ['Xianxia', '仙侠'], ['Historical', '古装'], ['Fantasy', '幻想'],
    ['dark-content', '暗黑'], ['school', '校园'], ['Workplace', '职场']
];

const TAG_FILTER = {
    key: 'tag',
    name: '标签',
    value: [{ n: '全部', v: '' }].concat(TAGS.map(function (t) { return { n: t[1], v: t[0] }; }))
};

const FILTERS = {
    'all': [TAG_FILTER],
    'free': [TAG_FILTER],
    'vip': [TAG_FILTER]
};

function full(u) {
    if (!u) return '';
    if (u.indexOf('http') === 0) return u;
    if (u.charAt(0) === '/') return HOST + u;
    return HOST + '/' + u;
}

function picUrl(u) {
    if (!u) return '';
    return u.indexOf('http') === 0 ? u : HOST + (u.charAt(0) === '/' ? u : '/' + u);
}

// HTML 实体解码
function decodeEnt(s) {
    if (!s) return '';
    return String(s)
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ');
}

async function get(url) {
    try {
        const resp = await req(url, {
            method: 'get',
            headers: {
                'User-Agent': UA,
                'Referer': HOST + '/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        });
        return (resp && typeof resp === 'object') ? (resp.content || '') : (resp || '');
    } catch (e) {
        console.log('[短剧one] get失败', url, e && e.message);
        return '';
    }
}

// 解析列表: 按 a class="drama-card" 切块
function parseList(html) {
    const list = [];
    if (!html) return list;
    const seen = {};
    const blocks = html.split('class="drama-card"');
    for (let i = 1; i < blocks.length; i++) {
        const b = blocks[i];
        const hrefM = b.match(/href=\\?["']([^"']*\/drama\/[^"']+)/);
        if (!hrefM) continue;
        const href = hrefM[1];
        if (seen[href]) continue;
        seen[href] = 1;
        const nameM = b.match(/<h2[^>]*>([\s\S]*?)<\/h2>/);
        const picM = b.match(/<img[^>]*src=\\?["']([^"']+)/);
        const epsM = b.match(/episode-count[^>]*>([^<]+)</);
        const remark = epsM ? epsM[1].trim() : '';
        list.push({
            vod_id: href,
            vod_name: nameM ? decodeEnt(nameM[1].replace(/<[^>]+>/g, '').trim()) : '',
            vod_pic: picM ? picUrl(picM[1]) : '',
            vod_remarks: remark
        });
    }
    return list;
}

async function init(cfg) {
    console.log('[短剧one] init');
}

async function home(filter) {
    return JSON.stringify({ class: CLASSES, filters: FILTERS });
}

async function homeContent(filter) {
    try {
        const html = await get(HOST + '/dramas');
        return JSON.stringify({ class: CLASSES, filters: FILTERS, list: parseList(html) });
    } catch (e) {
        console.log('[短剧one] homeContent err', e && e.message);
        return JSON.stringify({ class: CLASSES, filters: FILTERS, list: [] });
    }
}

async function homeVod() {
    try {
        const html = await get(HOST + '/dramas');
        return JSON.stringify({ list: parseList(html) });
    } catch (e) {
        console.log('[短剧one] homeVod err', e && e.message);
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    try {
        const tag = extend && extend.tag;
        let url;
        if (tag) {
            url = HOST + '/tag/' + tag;
        } else if (tid === 'free') {
            url = HOST + '/dramas?filter=free';
        } else if (tid === 'vip') {
            url = HOST + '/dramas?filter=vip';
        } else {
            url = HOST + '/dramas';
        }
        console.log('[短剧one] category', url);
        const html = await get(url);
        return JSON.stringify({ list: parseList(html), pagecount: 1, limit: 30, total: 9999 });
    } catch (e) {
        console.log('[短剧one] category err', e && e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

async function detail(ids) {
    try {
        const id = String(ids).split(',')[0];
        const url = full(id);
        console.log('[短剧one] detail', url);
        const html = await get(url);
        if (!html) return JSON.stringify({ list: [] });

        const nameM = html.match(/<meta property="og:title" content="([^"]*)"/) || html.match(/<title>([^<]*)<\/title>/);
        const picM = html.match(/<meta property="og:image" content="([^"]*)"/);
        const descM = html.match(/class="drama-description-content"[^>]*>([\s\S]*?)<\/div>/);

        let name = nameM ? decodeEnt(nameM[1]) : '';
        name = name.replace(/\s*第\s*\d+\s*集在线观看.*$/, '').replace(/\s*在线观看.*$/, '').replace(/\s*-\s*短剧one.*$/, '').trim();

        const eps = [];
        const re = /<a class="[^"]*episode-free[^"]*" href="([^"]*\/ep\/(\d+))"[^>]*><b>([^<]+)<\/b>/g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const label = decodeEnt((m[3] || m[2]).trim());
            eps.push(label + '$' + full(m[1]));
        }
        const spRe = /<a class="[^"]*episode-free[^"]*" href="([^"]*\/special\/[^"]+)"[^>]*><b>([^<]+)<\/b>/g;
        let sm;
        while ((sm = spRe.exec(html)) !== null) {
            eps.push('特辑-' + decodeEnt(sm[2].trim()) + '$' + full(sm[1]));
        }

        const vod = {
            vod_id: id,
            vod_name: name,
            vod_pic: picM ? picUrl(picM[1]) : '',
            vod_content: descM ? decodeEnt(descM[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()) : '',
            vod_play_from: '短剧one',
            vod_play_url: eps.join('#')
        };
        return JSON.stringify({ list: [vod] });
    } catch (e) {
        console.log('[短剧one] detail err', e && e.message);
        return JSON.stringify({ list: [] });
    }
}

async function search(wd, quick, pg) {
    try {
        const url = HOST + '/dramas?q=' + encodeURIComponent(wd);
        console.log('[短剧one] search', url);
        const html = await get(url);
        return JSON.stringify({ list: parseList(html), pagecount: 1 });
    } catch (e) {
        console.log('[短剧one] search err', e && e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

function isDirectVideoUrl(url) {
    return ['m3u', 'mp4'].some(function (x) { return (url + '').indexOf(x) >= 0; });
}

async function play(flag, id, flags) {
    const HEADER = { 'User-Agent': UA, 'Referer': HOST + '/' };
    try {
        let epUrl = id;
        if (epUrl.indexOf('http') !== 0) epUrl = full(epUrl);
        console.log('[短剧one] play', epUrl);

        if (isDirectVideoUrl(epUrl)) {
            return JSON.stringify({ parse: 0, url: epUrl, header: HEADER });
        }

        const html = await get(epUrl);
        if (html) {
            const m = html.match(/<video[^>]*src="([^"]+)"/);
            if (m && m[1]) {
                return JSON.stringify({ parse: 0, url: m[1], header: HEADER });
            }
            const m2 = html.match(/(https?:\/\/[^"']+\.mp4[^"']*)/);
            if (m2 && m2[1]) {
                return JSON.stringify({ parse: 0, url: m2[1], header: HEADER });
            }
        }
        return JSON.stringify({ parse: 1, url: epUrl, header: HEADER });
    } catch (e) {
        console.log('[短剧one] play err', e && e.message);
        return JSON.stringify({ parse: 1, url: full(id), header: HEADER });
    }
}

export default {
    init,
    home,
    homeVod,
    homeContent,
    category,
    detail,
    search,
    play
};