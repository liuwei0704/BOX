import cheerio from 'assets://js/lib/cheerio.min.js';

const HOST = 'https://xrpq.eu.cc';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

function mylog(...args) {
    console.log('[星空影院]', ...args);
}

function full(u) {
    if (!u) return '';
    u = u + '';
    if (u.indexOf('http') === 0) return u;
    if (u.indexOf('//') === 0) return 'https:' + u;
    return HOST + (u.indexOf('/') === 0 ? u : '/' + u);
}

async function get(url, options = {}) {
    try {
        const resp = await req(url, {
            method: (options.method || 'get').toUpperCase(),
            headers: Object.assign({
                'User-Agent': UA,
                'Referer': HOST + '/'
            }, options.headers || {})
        });
        return (resp && typeof resp === 'object') ? resp.content : resp;
    } catch (e) {
        mylog('get err', url, e.message);
        return '';
    }
}

function parseList($) {
    const list = [];
    $('div.myui-vodlist__box').each(function () {
        const box = $(this);
        const a = box.find('a.myui-vodlist__thumb').first();
        if (!a.length) return;
        let href = a.attr('href') || '';
        if (!href) return;
        let pic = '';
        // 优先 a 自身的 data-original（分类区 lazyload 写法）
        pic = a.attr('data-original') || a.attr('data-src') || '';
        // 其次 style 里的 background:url(...)（顶部轮播写法）
        if (!pic) {
            const style = a.attr('style') || '';
            const m = style.match(/url\(([^)]+)\)/);
            if (m) pic = m[1].replace(/['"]/g, '');
        }
        // 最后兜底 a 内的 img
        if (!pic) pic = a.find('img').attr('data-original') || a.find('img').attr('src') || '';
        const title = (a.attr('title') || box.find('h4.title a').attr('title') || box.find('h4.title a').text() || '').trim();
        const remarks = box.find('span.pic-text').first().text().trim();
        const score = box.find('span.pic-tag').first().text().trim();
        if (!title) return;
        list.push({
            vod_id: href,
            vod_name: title,
            vod_pic: pic,
            vod_remarks: remarks || score
        });
    });
    return list;
}

function parsePageCount($) {
    let pc = 1;
    const nums = [];
    $('.myui-page a, ul.myui-page li a').each(function () {
        const t = $(this).text().trim();
        const n = parseInt(t.replace(/[^0-9]/g, ''));
        if (!isNaN(n)) nums.push(n);
    });
    if (nums.length) pc = Math.max.apply(null, nums);
    return pc;
}

async function home(filter) {
    return JSON.stringify({
        class: [
            { type_id: '1', type_pid: '0', type_name: '电影' },
            { type_id: '2', type_pid: '0', type_name: '电视剧' },
            { type_id: '3', type_pid: '0', type_name: '综艺' },
            { type_id: '4', type_pid: '0', type_name: '动漫' },
            { type_id: '44', type_pid: '0', type_name: '电影解说' },
            { type_id: '45', type_pid: '0', type_name: '体育' },
            { type_id: '5', type_pid: '1', type_name: '动作片' },
            { type_id: '6', type_pid: '1', type_name: '爱情片' },
            { type_id: '7', type_pid: '1', type_name: '科幻片' },
            { type_id: '8', type_pid: '1', type_name: '恐怖片' },
            { type_id: '9', type_pid: '1', type_name: '战争片' },
            { type_id: '10', type_pid: '1', type_name: '喜剧片' },
            { type_id: '11', type_pid: '1', type_name: '纪录片' },
            { type_id: '12', type_pid: '1', type_name: '剧情片' },
            { type_id: '26', type_pid: '2', type_name: '国产剧' },
            { type_id: '27', type_pid: '2', type_name: '欧美剧' },
            { type_id: '28', type_pid: '2', type_name: '香港剧' },
            { type_id: '29', type_pid: '2', type_name: '韩国剧' },
            { type_id: '30', type_pid: '2', type_name: '台湾剧' },
            { type_id: '31', type_pid: '2', type_name: '日本剧' },
            { type_id: '32', type_pid: '2', type_name: '海外剧' },
            { type_id: '33', type_pid: '2', type_name: '泰国剧' },
            { type_id: '34', type_pid: '2', type_name: '短剧' },
            { type_id: '35', type_pid: '3', type_name: '大陆综艺' },
            { type_id: '36', type_pid: '3', type_name: '港台综艺' },
            { type_id: '37', type_pid: '3', type_name: '日韩综艺' },
            { type_id: '38', type_pid: '3', type_name: '欧美综艺' },
            { type_id: '39', type_pid: '4', type_name: '国产动漫' },
            { type_id: '40', type_pid: '4', type_name: '日韩动漫' },
            { type_id: '41', type_pid: '4', type_name: '欧美动漫' },
            { type_id: '42', type_pid: '4', type_name: '港台动漫' },
            { type_id: '43', type_pid: '4', type_name: '海外动漫' }
        ],
        filters: {}
    });
}

async function homeContent(filter) {
    const html = await get(HOST + '/');
    let clazz = [];
    try {
        clazz = JSON.parse(await home()).class || [];
    } catch (e) {}
    if (!html) return JSON.stringify({ class: clazz, filters: {}, list: [] });
    const $ = cheerio.load(html);
    return JSON.stringify({ class: clazz, filters: {}, list: parseList($) });
}

async function homeVod() {
    const html = await get(HOST + '/');
    if (!html) return JSON.stringify({ list: [] });
    const $ = cheerio.load(html);
    return JSON.stringify({ list: parseList($) });
}

async function category(tid, pg, filter, extend) {
    try {
        pg = parseInt(pg) || 1;
        const url = pg <= 1
            ? HOST + '/frim/index' + tid + '.html'
            : HOST + '/frim/index' + tid + '-' + pg + '.html';
        mylog('category url', url);
        const html = await get(url);
        if (!html) return JSON.stringify({ list: [], pagecount: 1 });
        const $ = cheerio.load(html);
        const list = parseList($);
        const pagecount = parsePageCount($);
        return JSON.stringify({ list: list, pagecount: pagecount || 9999 });
    } catch (e) {
        mylog('category err', e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

async function detail(id) {
    try {
        const url = full(id);
        mylog('detail url', url);
        const html = await get(url);
        if (!html) return JSON.stringify({ list: [] });
        const $ = cheerio.load(html);

        const vod = {};
        vod.vod_id = id;

        let name = $('.myui-content__detail h1.title').first().text().trim()
            || $('h1.title').first().text().trim()
            || ($('title').text() || '').replace(/^《|》.*$/g, '').trim();
        vod.vod_name = name;

        let pic = '';
        const picEl = $('.myui-content__thumb img').first();
        pic = picEl.attr('data-original') || picEl.attr('src') || '';
        if (!pic) {
            const style = $('.myui-content__thumb').attr('style') || '';
            const m = style.match(/url\(([^)]+)\)/);
            if (m) pic = m[1].replace(/['"]/g, '');
        }
        vod.vod_pic = pic;

        const txt = $('.myui-content__detail').text() || '';
        const grab = (label) => {
            const re = new RegExp(label + '[：:]\\s*([^\\s&\\n]+)');
            const mm = txt.match(re);
            return mm ? mm[1].trim() : '';
        };
        vod.type_name = grab('分类');
        vod.vod_year = grab('发行年份');
        vod.vod_area = grab('发行地区');
        vod.vod_lang = grab('语言');
        vod.vod_director = grab('导演');

        let actor = '';
        $('.myui-content__detail p').each(function () {
            const t = $(this).text();
            if (t.indexOf('演员') >= 0) {
                const names = [];
                $(this).find('a').each(function () {
                    const n = $(this).text().trim();
                    if (n) names.push(n);
                });
                actor = names.join(',');
            }
        });
        vod.vod_actor = actor;

        let content = '';
        $('.myui-panel').each(function () {
            const title = $(this).find('h3.title').text();
            if (title.indexOf('剧情') >= 0) {
                content = $(this).find('p, .col-pd').text().replace(/剧情介绍/g, '').trim();
            }
        });
        vod.vod_content = content;

        const playFrom = [];
        const playUrl = [];
        const paneIds = [];
        $('.nav-tabs li a').each(function () {
            const href = $(this).attr('href') || '';
            if (href.indexOf('#playlist') === 0) {
                paneIds.push(href.substring(1));
                playFrom.push($(this).text().trim() || '线路');
            }
        });
        if (!paneIds.length) paneIds.push('playlist1');

        paneIds.forEach(function (pid) {
            const eps = [];
            $('#' + pid + ' ul.myui-content__list li a').each(function () {
                const epName = ($(this).attr('title') || $(this).text() || '').trim();
                const epHref = $(this).attr('href') || '';
                if (epHref) eps.push(epName + '$' + full(epHref));
            });
            playUrl.push(eps.join('#'));
        });

        vod.vod_play_from = playFrom.join('$$$');
        vod.vod_play_url = playUrl.join('$$$');

        return JSON.stringify({ list: [vod] });
    } catch (e) {
        mylog('detail err', e.message);
        return JSON.stringify({ list: [] });
    }
}

async function search(wd, quick, pg) {
    try {
        pg = parseInt(pg) || 1;
        const url = HOST + '/search.php?searchword=' + encodeURIComponent(wd) + (pg > 1 ? '&page=' + pg : '');
        mylog('search url', url);
        const html = await get(url);
        if (!html) return JSON.stringify({ list: [], pagecount: 1 });
        const $ = cheerio.load(html);
        const list = parseList($);
        const pagecount = parsePageCount($);
        return JSON.stringify({ list: list, pagecount: pagecount || 1 });
    } catch (e) {
        mylog('search err', e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

async function play(flag, id, flags) {
    try {
        const playUrl = full(id);
        mylog('play url', playUrl);
        const html = await get(playUrl);
        if (!html) return JSON.stringify({ parse: 0, url: '' });
        let m = html.match(/var\s+now\s*=\s*["']([^"']+)["']/);
        if (m && m[1]) {
            mylog('play direct', m[1]);
            return JSON.stringify({ parse: 0, url: m[1] });
        }
        m = html.match(/\.src\s*=\s*["']([^"']+\.html)["']/);
        if (m && m[1]) {
            return JSON.stringify({ parse: 1, url: full(m[1]) });
        }
        return JSON.stringify({ parse: 1, url: playUrl });
    } catch (e) {
        mylog('play err', e.message);
        return JSON.stringify({ parse: 1, url: '' });
    }
}

export default {
    home,
    homeVod,
    homeContent,
    category,
    detail,
    search,
    play
};
