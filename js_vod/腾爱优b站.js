// 腾爱优聚合 - TVBox/VOD 源插件

import cheerio from 'assets://js/lib/cheerio.min.js';

// ========== 配置 ==========
const sites = [
    'http://cj.tianwe.cn',
    'https://tianwei.qzz.io',
    'https://cj.10010888.xyz'
];
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36';
const parseApiList = ['https://jx.kptv.us/?url='];
let baseUrl = sites[0];

// ========== 工具函数 ==========

function safeJsonParse(str) {
    try {
        return typeof str === 'string' ? JSON.parse(str) : str;
    } catch (e) {
        return str;
    }
}

async function myFetch(url, options = {}) {
    let resp = null;
    try {
        resp = await req(url, {
            method: options.method || 'get',
            headers: { 'user-agent': UA },
            ...options
        });
        return safeJsonParse(resp?.content);
    } catch (err) {
        mylog('myfetch err ', err);
        return resp?.content;
    }
}

function backErr(err, prefix = '') {
    mylog(prefix ? prefix + ' err:' : '', err);
    return JSON.stringify({
        msg: err.message || String(err)
    });
}

function mylog() {
    console.log('腾爱优聚合', ...arguments);
}

// ========== 核心接口 ==========

async function init(ext) {
    // 初始化（空实现）
}

async function homeVod() {
    return JSON.stringify({ list: [] });
}

async function home(filter) {
    try {
        const classList = [
            { type_id: 'qq', type_pid: 0, type_name: '腾讯视频' },
            { type_id: 'qiyi', type_pid: 0, type_name: '爱奇艺' },
            { type_id: 'youku', type_pid: 0, type_name: '优酷视频' },
            { type_id: 'mgtv', type_pid: 0, type_name: '芒果TV' },
            { type_id: 'bilibili', type_pid: 0, type_name: 'B站' }
        ];

        const typeFilter = {
            key: 'class',
            name: '类型',
            value: [
                { n: '全部', v: '' },
                { n: '连续剧', v: '2' },
                { n: '电影', v: '1' },
                { n: '动漫', v: '4' },
                { n: '综艺', v: '3' },
                { n: '少儿', v: '5' },
                { n: '纪录片', v: '6' },
                { n: '短剧', v: '7' }
            ]
        };

        const yearFilter = {
            key: 'year',
            name: '年份',
            value: [
                { n: '全部', v: '' },
                { n: '2026', v: '2026' },
                { n: '2025', v: '2025' },
                { n: '2024', v: '2024' },
                { n: '2023', v: '2023' },
                { n: '2022', v: '2022' }
            ]
        };

        let filters = {};
        classList.forEach(item => {
            filters[item.type_id] = [typeFilter, yearFilter];
        });

        return JSON.stringify({ class: classList, filters });
    } catch (err) {
        return backErr(err);
    }
}

async function detail(ids) {
    try {
        let url = baseUrl + '/api.php/provide/vod/?' + ['ac=detail', 'ids=' + ids].join('&');
        mylog('detailurl', url);

        let data = await myFetch(url);
        let list = [];

        if (Array.isArray(data?.list)) {
            list = data.list
                .map(item => ({
                    vod_id: item.vod_id,
                    vod_name: item.vod_name,
                    vod_pic: item.vod_pic,
                    vod_remarks: item.vod_remarks,
                    vod_year: item.vod_year,
                    type_name: item.type_name,
                    vod_area: item.vod_area,
                    vod_lang: item.vod_lang,
                    vod_content: item.vod_content,
                    vod_play_from: item.vod_play_from,
                    vod_play_url: item.vod_play_url
                }))
                .filter(item => item.vod_id);
        }

        return JSON.stringify({ list });
    } catch (err) {
        return backErr(err);
    }
}

async function category(tid, pg, ext, filters) {
    pg = pg || 1;
    filters = filters || {};
    try {
        let params = [
            'from=' + (tid || 'qq'),
            'ac=detail',
            'limit=24',
            'pg=' + (parseInt(pg) || 1)
        ];

        let typeClass = filters && filters.class ? filters.class : '2';
        params.push('t=' + typeClass);

        if (filters && filters.year) {
            params.push('year=' + encodeURIComponent(filters.year));
        }

        let url = baseUrl + '/api.php/provide/vod/?' + params.join('&');
        mylog('api category url ->', url);

        let data = await myFetch(url);
        if (!data) throw new Error('API 请求无响应');

        let list = [];
        if (Array.isArray(data?.list)) {
            list = data.list.map(item => {
                return {
                    vod_id: item.vod_id,
                    vod_name: item.vod_name,
                    vod_pic: item.vod_pic,
                    vod_remarks: item.vod_remarks,
                    vod_year: item.vod_year
                };
            });
        }

        let pagecount = parseInt(data?.pagecount) || 1;
        return JSON.stringify({ list, pagecount });
    } catch (err) {
        return backErr(err, 'category');
    }
}

async function search(wd, quick, pg) {
    let page = pg ? parseInt(pg) : 1;
    try {
        let url = baseUrl + '/api.php/provide/vod/?ac=detail&wd=' + encodeURIComponent(wd) + '&pg=' + page;
        mylog('api searchUrl:', url);

        let data = await myFetch(url);
        if (!data) throw new Error('搜索请求未返回数据');

        let list = [];
        if (Array.isArray(data?.list)) {
            list = data.list
                .map(item => ({
                    vod_id: item.vod_id,
                    vod_name: item.vod_name || item.name,
                    vod_pic: item.vod_pic || item.pic,
                    vod_remarks: item.vod_remarks || ''
                }))
                .filter(item => item.vod_id);
        }

        let pagecount = parseInt(data?.pagecount) || 1;
        return JSON.stringify({ list, pagecount });
    } catch (err) {
        return backErr(err);
    }
}

// ========== 播放相关 ==========

function isDirectVideoUrl(url) {
    return ['m3u', 'mp4'].some(ext => (url + '').includes(ext));
}

function extractConfig(html) {
    let match = html.match(/apiToken\s*:\s*["']([^"']+)["']/);
    return { apiToken: match ? match[1] : null };
}

function formatUrl(url) {
    if (!url) return '';
    return url
        .replace(/\\/g, '')
        .replace(/^(https?:\/)(?!\/)/i, '$1/');
}

async function parseVideoUrl(videoUrl) {
    if (isDirectVideoUrl(videoUrl)) {
        mylog('直链无需解析，直接返回');
        return videoUrl;
    }

    const parseApi = parseApiList[0];
    const fullUrl = parseApi + videoUrl;
    mylog('正在请求解析地址:', fullUrl);

    try {
        let resp = await req(fullUrl, { headers: { 'user-agent': UA } });
        let html = resp?.content || '';
        let { apiToken } = extractConfig(html);

        if (!apiToken) throw new Error('解析源无 token');

        let domain = parseApi.split('//')[1].split('/')[0];
        let tokenUrl = 'https://' + domain + '/api/resolve.php?token=' + encodeURIComponent(apiToken);
        let tokenResp = await req(tokenUrl, { headers: { 'user-agent': UA } });
        let realUrl = formatUrl(JSON.parse(tokenResp.content).url);

        if (!realUrl) throw new Error('解析源链接为空');

        mylog('解析成功并返回 ->', realUrl);
        return realUrl;
    } catch (err) {
        mylog('解析失败: ', err.message);
        return '';
    }
}

async function play(flag, id, flags) {
    mylog('开始获取播放地址: ' + id);
    const realUrl = await parseVideoUrl(id);

    try {
        return JSON.stringify({ parse: 0, url: realUrl });
    } catch (err) {
        mylog('play失败: ' + err.message);
        return JSON.stringify({ msg: err.message });
    }
}

// ========== 导出 ==========
export default {
    init,
    home,
    homeVod,
    category,
    detail,
    play,
    search
};
