// 拾光影视 - 基于麒麟采集API
const API = "https://cj.rycjapi.com/api.php/provide/vod/";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const parseAPiUrl = "https://svip.qlplayer.cyou/?url=";

function mylog(...args) {
    console.log(`[拾光影视]`, ...args);
}

function safeJsonParse(json) {
    try {
        return typeof json === "string" ? JSON.parse(json) : json;
    } catch (e) {
        return null;
    }
}

async function myFetch(url, options = {}, needJsonParse = true) {
    try {
        let res = await req(url, {
            method: options?.method || "get",
            headers: { "User-Agent": UA },
            ...options
        });
        return needJsonParse ? safeJsonParse(res?.content) : res?.content;
    } catch (err) {
        mylog("myfetch err ", err);
        return null;
    }
}

async function init(cfg) {
    mylog("Spider Init Done");
}

// 分类（取一级 + 二级，方便分栏）
async function home(filter) {
    try {
        const data = await myFetch(API + "?ac=list");
        if (!data || !data.class) {
            return JSON.stringify({ class: [], filters: {} });
        }
        const classList = data.class.map(function (c) {
            return { type_id: String(c.type_id), type_pid: c.type_pid || 0, type_name: c.type_name };
        });
        return JSON.stringify({ class: classList, filters: {} });
    } catch (e) {
        mylog("home err", e.message);
        return JSON.stringify({ class: [], filters: {} });
    }
}

async function homeVod() {
    try {
        const data = await myFetch(API + "?ac=videolist&pg=1");
        if (!data || !data.list) return JSON.stringify({ list: [] });
        const list = data.list.map(function (it) {
            return {
                vod_id: String(it.vod_id),
                vod_name: it.vod_name || '',
                vod_pic: it.vod_pic || '',
                vod_remarks: it.vod_remarks || ''
            };
        });
        return JSON.stringify({ list: list });
    } catch (e) {
        mylog("homeVod err", e.message);
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    try {
        pg = pg || 1;
        const url = API + "?ac=videolist&t=" + encodeURIComponent(tid) + "&pg=" + pg;
        mylog("category url", url);
        const data = await myFetch(url);
        if (!data || !data.list) {
            return JSON.stringify({ list: [], pagecount: 1 });
        }
        const list = data.list.map(function (it) {
            return {
                vod_id: String(it.vod_id),
                vod_name: it.vod_name || '',
                vod_pic: it.vod_pic || '',
                vod_remarks: it.vod_remarks || ''
            };
        });
        return JSON.stringify({ list: list, pagecount: data.pagecount || 1 });
    } catch (e) {
        mylog("category err", e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

async function detail(id) {
    try {
        const url = API + "?ac=detail&ids=" + id;
        mylog("detail url", url);
        const data = await myFetch(url);
        if (!data || !data.list || !data.list[0]) {
            return JSON.stringify({ list: [] });
        }
        const it = data.list[0];
        const vod = {
            vod_id: String(it.vod_id),
            vod_name: it.vod_name || '',
            vod_pic: it.vod_pic || '',
            type_name: it.vod_class || '',
            vod_year: it.vod_year || '',
            vod_area: it.vod_area || '',
            vod_lang: it.vod_lang || '',
            vod_director: it.vod_director || '',
            vod_actor: it.vod_actor || '',
            vod_content: it.vod_content || '',
            vod_remarks: it.vod_remarks || '',
            vod_play_from: it.vod_play_from || '',
            vod_play_url: it.vod_play_url || ''
        };
        return JSON.stringify({ list: [vod] });
    } catch (e) {
        mylog("detail err", e.message);
        return JSON.stringify({ list: [] });
    }
}

async function search(kw, quick, pg) {
    try {
        const page = pg ? parseInt(pg) : 1;
        const url = API + "?ac=videolist&wd=" + encodeURIComponent(kw) + "&pg=" + page;
        mylog("search url", url);
        const data = await myFetch(url);
        if (!data || !data.list) {
            return JSON.stringify({ list: [], pagecount: 1 });
        }
        const list = data.list.map(function (it) {
            return {
                vod_id: String(it.vod_id),
                vod_name: it.vod_name || '',
                vod_pic: it.vod_pic || '',
                vod_remarks: it.vod_remarks || ''
            };
        });
        return JSON.stringify({ list: list, pagecount: data.pagecount || 1 });
    } catch (e) {
        mylog("search err", e.message);
        return JSON.stringify({ list: [], pagecount: 1 });
    }
}

// ==== 播放解析（保留原逻辑）====
function formatUrl(url) {
    if (!url) return "";
    return url.replace(/\\/g, "").replace(/^(https?:\/)((?!\/))/i, "$1/");
}

function extractConfig(html) {
    const apiTokenMatch = html.match(/apiToken\s*:\s*["']([^"']+)["']/);
    return { apiToken: apiTokenMatch ? apiTokenMatch[1] : null };
}

function isDirectVideoUrl(url) {
    return ['m3u', "mp4"].some(item => (url + "").includes(item));
}

async function parseVideoUrl(videoUrl) {
    try {
        if (isDirectVideoUrl(videoUrl)) {
            mylog('直链无需解析，直接返回');
            return videoUrl;
        }
        const resoleUrl = parseAPiUrl + videoUrl;
        mylog("解析地址", resoleUrl);
        const html1 = (await req(resoleUrl)).content || "";
        const { apiToken } = extractConfig(html1);
        if (!apiToken) return "";
        const parseTokenUrl = `https://svip.qlplayer.cyou/api/resolve.php?token=${encodeURIComponent(apiToken)}`;
        mylog("parseTokenUrl", parseTokenUrl);
        const res = await req(parseTokenUrl);
        const data = JSON.parse(res.content);
        const finalUrl = formatUrl(data.url);
        mylog("finalUrl", finalUrl);
        return finalUrl;
    } catch (e) {
        mylog("视频解析失败:", e.message);
        return "";
    }
}

async function play(flag, id, flags) {
    mylog(`开始获取播放地址: ${id}`);
    // 直链直接返回
    if (isDirectVideoUrl(id)) {
        return JSON.stringify({ parse: 0, url: id });
    }
    const finalUrl = await parseVideoUrl(id);
    try {
        return JSON.stringify({ parse: 0, url: finalUrl });
    } catch (e) {
        mylog(`play失败: ${e.message}`);
        return JSON.stringify({ msg: e.message });
    }
}

export default {
    init,
    home,
    homeVod,
    category,
    detail,
    search,
    play
};