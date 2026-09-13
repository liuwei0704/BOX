// 八影短劇網 8movie.com 客户端单文件源
// 分类: /movies/{tid}/  /movies/{tid}/{pg}.html
// 标签筛选: /movies/tags/{tag}/  /movies/tags/{tag}/{pg}.html
// 搜索: /search/?key=xx&page=N
// 详情: /movies/{id}   剧集: /play/{id}/{ep}
// 播放: parse:1 交 App 嗅探器（m3u8 需 Referer）
// 图片: 附加 @User-Agent=...@Referer=... 绕过 Cloudflare

const HOST = 'https://8movie.com';
const IMG_HOST = 'https://www.8movie.com';
const UA = 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';

const CLASSES = [
    { type_id: '1', type_pid: '0', type_name: '穿越古代' },
    { type_id: '4', type_pid: '0', type_name: '都市情爱' },
    { type_id: '5', type_pid: '0', type_name: '复仇爽剧' },
    { type_id: '2', type_pid: '0', type_name: '玄幻武侠' },
    { type_id: '3', type_pid: '0', type_name: '奇幻悬疑' },
    { type_id: '6', type_pid: '0', type_name: '其他短剧' }
];

// 站点标签（代码 -> 中文名）
const TAGS = [
    ['NiXi', '逆袭'], ['Chou', '复仇'], ['QiHuan', '奇幻'], ['NueLian', '虐恋'],
    ['ShuangJu', '爽剧'], ['ZhongSheng', '重生'], ['XuanHuan', '玄幻'], ['AiQing', '爱情'],
    ['JiaTing', '家庭'], ['ChuanYue', '穿越'], ['XianHunHouAi', '先婚后爱'], ['BaZong', '霸总'],
    ['DuShi', '都市'], ['DaNvZhu', '大女主'], ['TianChong', '甜宠'], ['NvQiang', '女强'],
    ['XuanYi', '悬疑'], ['GongZz', '宫斗'], ['ZhiChang', '职场'], ['XiuZhen', '修真'],
    ['QiYueHunYin', '契约婚姻'], ['QuanMou', '权谋'], ['HaoMen', '豪门'], ['NueZha', '虐渣'],
    ['LangMan', '浪漫'], ['TiJia', '替嫁'], ['PoJingZhongYuan', '破镜重圆'], ['JiuShu', '救赎'],
    ['ZhenJiaQianJin', '真假千金'], ['FanZhuan', '反转'], ['ReXue', '热血'], ['DaLian', '打脸'],
    ['QingMeiZhuMa', '青梅竹马'], ['AnLian', '暗恋'], ['ZhaiZz', '宅斗'], ['GaoXiao', '搞笑'],
    ['MengBao', '萌宝'], ['DaiQiuPao', '带球跑'], ['GuZhuang', '古装'], ['ZhuiQi', '追妻'],
    ['XianXia', '仙侠'], ['HunLian', '婚恋'], ['Zhi', '治愈'], ['ShanHun', '闪婚'],
    ['ZhanShen', '战神'], ['MaJia', '马甲'], ['TanAn', '探案'], ['ShenHao', '神豪'],
    ['LongWang', '龙王'], ['NanPin', '男频']
];

// 标签筛选器（影视+/TVBox 格式：filters[tid] = [ {key,name,value} ]）
const TAG_FILTER = {
    key: 'tag',
    name: '标签',
    value: [{ n: '全部', v: '' }].concat(TAGS.map(function (t) { return { n: t[1], v: t[0] }; }))
};

const FILTERS = {
    '1': [TAG_FILTER],
    '4': [TAG_FILTER],
    '5': [TAG_FILTER],
    '2': [TAG_FILTER],
    '3': [TAG_FILTER],
    '6': [TAG_FILTER]
};

function full(u) {
    if (!u) return '';
    if (u.indexOf('http') === 0) return u;
    if (u.charAt(0) === '/') return HOST + u;
    return HOST + '/' + u;
}

function picUrl(u) {
    if (!u) return '';
    let p = u;
    if (p.indexOf('http') !== 0) p = (p.charAt(0) === '/' ? IMG_HOST + p : IMG_HOST + '/' + p);
    return p + '@User-Agent=' + UA + '@Referer=' + HOST + '/';
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
        console.log('[八影] get失败', url, e && e.message);
        return '';
    }
}

function parseList(html) {
    const list = [];
    if (!html) return list;
    const seen = {};
    const blocks = html.split('col-4 col-sm-4 col-md-4 col-lg-2 p-2');
    for (let i = 1; i < blocks.length; i++) {
        const b = blocks[i];
        const mid = b.match(/href=\\?['"]\/movies\/(\d+)/);
        if (!mid) continue;
        const vid = mid[1];
        if (seen[vid]) continue;
        seen[vid] = 1;
        const name = b.match(/title=\\?['"]([^'"]+)/);
        const pic = b.match(/<img[^>]*src=\\?["]([^"\\]+)/);
        const eps = b.match(/<eps>(\d+)/);
        list.push({
            vod_id: vid,
            vod_name: name ? name[1] : '',
            vod_pic: pic ? picUrl(pic[1]) : '',
            vod_remarks: eps ? (eps[1] + '集') : ''
        });
    }
    return list;
}

function parseCatSwipe(html, tid) {
    const m = html.match(/id="catSwipeData"[^>]*>([\s\S]*?)<\/script>/);
    if (!m) return null;
    let data;
    try { data = JSON.parse(m[1]); } catch (e) { return null; }
    if (!data || !data.cats) return null;
    for (let i = 0; i < data.cats.length; i++) {
        if (String(data.cats[i].id) === String(tid)) return data.cats[i].html || '';
    }
    return null;
}

async function init(cfg) {
    console.log('[八影] init');
}

async function home(filter) {
    return JSON.stringify({ class: CLASSES, filters: FILTERS });
}

async function homeContent(filter) {
    return JSON.stringify({ class: CLASSES, filters: FILTERS, list: [] });
}

async function homeVod() {
    try {
        const html = await get(HOST + '/movies/1/');
        const seg = parseCatSwipe(html, '1');
        return JSON.stringify({ list: parseList(seg !== null ? seg : html) });
    } catch (e) {
        console.log('[八影] homeVod err', e && e.message);
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    try {
        const page = parseInt(pg) || 1;
        const tag = extend && (extend.tag || extend['tag']);
        let list = [];

        if (tag) {
            const url = page <= 1
                ? HOST + '/movies/tags/' + tag + '/'
                : HOST + '/movies/tags/' + tag + '/' + page + '.html';
            console.log('[八影] tag', url);
            const html = await get(url);
            list = parseList(html);
        } else if (page <= 1) {
            const url = HOST + '/movies/' + tid + '/';
            console.log('[八影] category p1', url);
            const html = await get(url);
            const seg = parseCatSwipe(html, tid);
            list = parseList(seg !== null ? seg : html);
        } else {
            const url = HOST + '/movies/' + tid + '/' + page + '.html';
            console.log('[八影] category', url);
            const html = await get(url);
            list = parseList(html);
        }

        return JSON.stringify({ list: list, pagecount: 9999, limit: 30, total: 9999 });
    } catch (e) {
        console.log('[八影] category err', e && e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

async function detail(ids) {
    try {
        const id = String(ids).split(',')[0].replace(/\D/g, '');
        const url = HOST + '/movies/' + id;
        console.log('[八影] detail', url);
        const html = await get(url);
        if (!html) return JSON.stringify({ list: [] });

        const nameM = html.match(/<meta property="og:title" content="([^"]*)"/) || html.match(/<title>([^<]*)<\/title>/);
        const picM = html.match(/<meta property="og:image" content="([^"]*)"/) || html.match(/<meta name="pic" content="([^"]*)"/);
        const descM = html.match(/class="full_text[^"]*"[^>]*>([\s\S]*?)<\/h6>/);

        const eps = [];
        const re = /href='\/play\/(\d+)\/(\d+)'[^>]*>([^<]+)<\/a>/g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const label = (m[3] || ('第' + m[2] + '集')).trim();
            eps.push(label + '$' + HOST + '/play/' + m[1] + '/' + m[2]);
        }

        const vod = {
            vod_id: id,
            vod_name: nameM ? nameM[1].replace(/\s*-\s*8movie.*$/, '').replace(/\s*-\s*八影.*$/, '').trim() : '',
            vod_pic: picM ? picUrl(picM[1]) : '',
            vod_content: descM ? descM[1].replace(/<[^>]+>/g, '').trim() : '',
            vod_play_from: '八影短剧',
            vod_play_url: eps.join('#')
        };
        return JSON.stringify({ list: [vod] });
    } catch (e) {
        console.log('[八影] detail err', e && e.message);
        return JSON.stringify({ list: [] });
    }
}

async function search(wd, quick, pg) {
    try {
        const page = parseInt(pg) || 1;
        let url = HOST + '/search/?key=' + encodeURIComponent(wd);
        if (page > 1) url += '&page=' + page;
        console.log('[八影] search', url);
        const html = await get(url);
        return JSON.stringify({ list: parseList(html), pagecount: 9999 });
    } catch (e) {
        console.log('[八影] search err', e && e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

async function play(flag, id, flags) {
    try {
        let epUrl = id;
        if (epUrl.indexOf('http') !== 0) epUrl = full(epUrl);
        if (!/\/play\//.test(epUrl)) epUrl = full('/play/' + epUrl);
        console.log('[八影] play', epUrl);
        return JSON.stringify({ parse: 1, url: epUrl, header: { 'User-Agent': UA, 'Referer': HOST + '/' } });
    } catch (e) {
        console.log('[八影] play err', e && e.message);
        return JSON.stringify({ parse: 0, url: '' });
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