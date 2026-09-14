/**
 * @config
 * timeout: 30
 * blockImages: true
 * returnType: dom
 * keyword: Checking your browser|Just a moment|请稍候
 */

const baseUrl = 'https://game.fanjugou12.top';
const apiUrl = 'https://macapi2.com';
const fallbackApiUrl = 'https://macapi1.com';

const headers = {
    'Referer': baseUrl,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
};

// 影视数据库分类映射
const DB_CONFIG = [
    { dbname: '155', name: '福利姬', type: 'av', icon: '🎬' },
    { dbname: '91md', name: '91麻豆', type: 'av', icon: '🎬' },
    { dbname: 'aosika', name: '奥斯卡', type: 'av', icon: '🎬' },
    { dbname: 'baipiao', name: '白嫖', type: 'av', icon: '🎬' },
    { dbname: 'baidu', name: '百度', type: 'movies', icon: '🎬' },
    { dbname: 'baofeng', name: '暴风资源', type: 'movies', icon: '🎬' },
    { dbname: 'dadi', name: '大地', type: 'av', icon: '🎬' },
    { dbname: 'danai', name: '大奶', type: 'av', icon: '🎬' },
    { dbname: 'didi', name: '滴滴', type: 'av', icon: '🎬' },
    { dbname: 'doudou', name: '豆豆', type: 'av', icon: '🎬' },
    { dbname: 'dyttzy', name: '电影天堂', type: 'movies', icon: '🎬' },
    { dbname: 'fanhao', name: '番號', type: 'av', icon: '🎬' },
    { dbname: 'fanqie', name: '番茄', type: 'av', icon: '🎬' },
    { dbname: 'feifan', name: '非凡', type: 'movies', icon: '🎬' },
    { dbname: 'guagnsu', name: '光速', type: 'movies', icon: '🎬' },
    { dbname: 'haohua', name: '豪华', type: 'movies', icon: '🎬' },
    { dbname: 'heiliaozyapi', name: '黑料', type: 'av', icon: '🎬' },
    { dbname: 'hlzy', name: '红楼', type: 'av', icon: '🎬' },
    { dbname: 'hongniu', name: '红牛', type: 'movies', icon: '🎬' },
    { dbname: 'huya', name: '虎牙', type: 'movies', icon: '🎬' },
    { dbname: 'jiangsu', name: '江苏', type: 'movies', icon: '🎬' },
    { dbname: 'jiujiuyy', name: '久久', type: 'movies', icon: '🎬' },
    { dbname: 'kuaibo', name: '快播', type: 'av', icon: '🎬' },
    { dbname: 'kuaikan', name: '快看', type: 'movies', icon: '🎬' },
    { dbname: 'kuaishou', name: '快手', type: 'movies', icon: '🎬' },
    { dbname: 'laosiji', name: '老司机', type: 'av', icon: '🎬' },
    { dbname: 'lspzy', name: '老色批', type: 'av', icon: '🎬' },
    { dbname: 'maizi', name: '麦子', type: 'movies', icon: '🎬' },
    { dbname: 'mgtv', name: '芒果TV', type: 'movies', icon: '🎬' },
    { dbname: 'mzzy', name: '麻子', type: 'av', icon: '🎬' },
    { dbname: 'niuniu', name: '妞妞', type: 'av', icon: '🎬' },
    { dbname: 'pianku', name: '片库', type: 'movies', icon: '🎬' },
    { dbname: 'qianxun', name: '千寻', type: 'movies', icon: '🎬' },
    { dbname: 'qiyi', name: '奇艺', type: 'movies', icon: '🎬' },
    { dbname: 'qqzy', name: 'QQ资源', type: 'movies', icon: '🎬' },
    { dbname: 'shenma', name: '神马', type: 'movies', icon: '🎬' },
    { dbname: 'shihua', name: '湿滑', type: 'av', icon: '🎬' },
    { dbname: 'sihu', name: '私护', type: 'av', icon: '🎬' },
    { dbname: 'sugar', name: '糖果', type: 'movies', icon: '🎬' },
    { dbname: 'taotao', name: '淘淘', type: 'av', icon: '🎬' },
    { dbname: 'tianya', name: '天涯', type: 'movies', icon: '🎬' },
    { dbname: 'tudou', name: '土豆', type: 'movies', icon: '🎬' },
    { dbname: 'tuzi', name: '兔子', type: 'av', icon: '🎬' },
    { dbname: 'vipzy', name: 'VIP资源', type: 'movies', icon: '🎬' },
    { dbname: 'wanmei', name: '完美', type: 'movies', icon: '🎬' },
    { dbname: 'woyao', name: '我要', type: 'av', icon: '🎬' },
    { dbname: 'xigua', name: '西瓜', type: 'movies', icon: '🎬' },
    { dbname: 'xiaomi', name: '小米', type: 'movies', icon: '🎬' },
    { dbname: 'yiku', name: '一库', type: 'av', icon: '🎬' },
    { dbname: 'youku', name: '优酷', type: 'movies', icon: '🎬' },
    { dbname: 'yueguang', name: '月光', type: 'av', icon: '🎬' },
    { dbname: 'yunpan', name: '云盘', type: 'movies', icon: '🎬' },
    { dbname: 'zhongzi', name: '种子', type: 'av', icon: '🎬' },
    { dbname: 'zuiyou', name: '最右', type: 'movies', icon: '🎬' }
];

// 小说数据源配置
const NOVEL_CONFIG = [
    { dname: 'sis', name: '综合小说', icon: '📚' },
    { dname: 'pixiv', name: 'Pixiv小说', icon: '📚' }
];

function safeText(obj) {
    if (!obj) return '';
    if (typeof obj === 'string') return obj.trim();
    if (typeof obj === 'number') return String(obj);
    return '';
}

function fixUrl(url) {
    if (!url) return '';
    if (url.indexOf('http://') === 0 || url.indexOf('https://') === 0) return url;
    if (url.indexOf('//') === 0) return 'https:' + url;
    return url;
}

function extractList(data, dbname) {
    if (!data || !data.list || !Array.isArray(data.list)) return [];
    var list = [];
    for (var i = 0; i < data.list.length; i++) {
        var item = data.list[i];
        var vodId = safeText(item.vod_id);
        var vodName = safeText(item.vod_name);
        if (!vodId || !vodName) continue;
        // 编码 vod_id: dbname@@vod_id
        var encodedId = dbname + '@@' + vodId;
        list.push({
            vod_id: encodedId,
            vod_name: vodName,
            vod_pic: fixUrl(item.vod_pic || ''),
            vod_remarks: safeText(item.vod_remarks) || safeText(item.type_name) || '',
            vod_year: safeText(item.vod_year)
        });
    }
    return list;
}

function extractNovelList(data, dname) {
    if (!data || !data.data || !Array.isArray(data.data)) return [];
    var list = [];
    for (var i = 0; i < data.data.length; i++) {
        var item = data.data[i];
        var novelId = safeText(item.novel_id);
        var novelName = safeText(item.title);
        if (!novelId || !novelName) continue;
        
        var encodedId = dname + '_' + novelId;
        
        var remarks = safeText(item.author) || '';
        if (item.total_chapters) {
            remarks = remarks + (remarks ? ' | ' : '') + safeText(item.total_chapters) + '章';
        }
        if (item.category) {
            remarks = remarks + (remarks ? ' | ' : '') + safeText(item.category);
        }
        
        list.push({
            vod_id: encodedId,
            vod_name: novelName,
            vod_pic: fixUrl(item.cover_url || ''),
            vod_remarks: remarks || '小说',
            vod_year: ''
        });
    }
    return list;
}

async function apiRequest(url) {
    var res = await fetch(url, { headers: headers });
    if (res.error) return null;
    try {
        return JSON.parse(res.body);
    } catch(e) {
        return null;
    }
}

function isNovelSource(tid) {
    if (!tid) return false;
    for (var i = 0; i < NOVEL_CONFIG.length; i++) {
        if (NOVEL_CONFIG[i].dname === tid) return true;
    }
    return false;
}

function parseNovelId(encodedId) {
    if (!encodedId) return null;
    var parts = encodedId.split('_');
    if (parts.length === 2) {
        var dname = parts[0];
        var novelId = parts[1];
        for (var i = 0; i < NOVEL_CONFIG.length; i++) {
            if (NOVEL_CONFIG[i].dname === dname) {
                return { dname: dname, novelId: novelId };
            }
        }
    }
    return null;
}

function isNovelUrl(url) {
    if (!url) return false;
    return url.indexOf('/novel/') !== -1 || url.indexOf('novel://') !== -1;
}

function extractNovelInfoFromUrl(url) {
    var match = url.match(/\/novel\/([^\/]+)\/([^\/]+)\/read\/(\d+)/);
    if (match) {
        return { dname: match[1], novelId: match[2], chapterIdx: match[3] };
    }
    return null;
}

// 从编码的vod_id中提取dbname和真实vod_id
function parseVodId(encodedId) {
    if (!encodedId) return null;
    // 格式: dbname@@vod_id
    var parts = encodedId.split('@@');
    if (parts.length === 2) {
        return { dbname: parts[0], vodId: parts[1] };
    }
    // 如果是纯数字，可能是旧格式，需要额外处理
    if (/^\d+$/.test(encodedId)) {
        return { dbname: null, vodId: encodedId };
    }
    return null;
}

async function homeContent(filter) {
    var classList = [];
    var filters = {};
    
    for (var k = 0; k < NOVEL_CONFIG.length; k++) {
        var novel = NOVEL_CONFIG[k];
        classList.push({ type_id: novel.dname, type_name: novel.icon + ' ' + novel.name });
        filters[novel.dname] = [];
    }
    
    var homeDbnames = ['155', 'baidu', 'dadi', 'guagnsu'];
    for (var i = 0; i < homeDbnames.length; i++) {
        var db = DB_CONFIG.find(function(d) { return d.dbname === homeDbnames[i]; });
        if (db) {
            classList.push({ type_id: db.dbname, type_name: db.icon + ' ' + db.name });
            filters[db.dbname] = [];
        }
    }
    
    for (var j = 0; j < DB_CONFIG.length; j++) {
        var d = DB_CONFIG[j];
        if (homeDbnames.indexOf(d.dbname) === -1) {
            classList.push({ type_id: d.dbname, type_name: d.icon + ' ' + d.name });
            filters[d.dbname] = [];
        }
    }
    
    return {
        class: classList,
        filters: filters
    };
}

async function homeVideoContent() {
    var dbname = '155';
    var url = apiUrl + '/maccms/json/' + dbname + '/?page=1&limit=20';
    var data = await apiRequest(url);
    if (!data || data.code !== 1) return Result.error('获取首页数据失败');
    return { list: extractList(data, dbname) };
}

async function categoryContent(tid, pg, filter, extend) {
    var p = parseInt(pg) || 1;
    var limit = 20;
    
    if (isNovelSource(tid)) {
        var novelUrl = apiUrl + '/book/' + tid + '/novels?page=' + p + '&limit=' + limit;
        var novelData = await apiRequest(novelUrl);
        if (!novelData || !novelData.data) {
            return { page: p, pagecount: 1, list: [], total: 0 };
        }
        var list = extractNovelList(novelData, tid);
        var pagecount = novelData.pagecount || Math.ceil((novelData.total || list.length) / limit);
        if (pagecount < p) pagecount = p;
        return {
            page: p,
            pagecount: pagecount,
            list: list,
            total: novelData.total || list.length
        };
    }
    
    var dbname = tid || '155';
    var url = apiUrl + '/maccms/json/' + dbname + '/?page=' + p + '&limit=' + limit;
    var data = await apiRequest(url);
    if (!data || data.code !== 1) return Result.error('获取分类数据失败');
    
    var list = extractList(data, dbname);
    var pagecount = data.pagecount || Math.ceil((data.total || list.length) / limit);
    if (pagecount < p) pagecount = p;
    var total = data.total || list.length;
    
    return {
        page: p,
        pagecount: pagecount,
        list: list,
        total: total
    };
}

async function novelDetailContent(encodedId) {
    var parsed = parseNovelId(encodedId);
    if (!parsed) return Result.error('无效的小说ID');
    
    var dname = parsed.dname;
    var novelId = parsed.novelId;
    
    var url = apiUrl + '/book/' + dname + '/novels/' + novelId;
    var data = await apiRequest(url);
    if (!data || !data.data) return Result.error('获取小说详情失败');
    
    var item = data.data;
    var chapterUrl = apiUrl + '/book/' + dname + '/novels/' + novelId + '/chapters?page=1&limit=100';
    var chapterData = await apiRequest(chapterUrl);
    var chapters = [];
    
    if (chapterData && chapterData.data && Array.isArray(chapterData.data)) {
        for (var i = 0; i < chapterData.data.length; i++) {
            var ch = chapterData.data[i];
            var chTitle = safeText(ch.title || ch.name || ('第' + (i + 1) + '章'));
            var readUrl = 'novel://' + dname + '/' + novelId + '/' + i;
            chapters.push(chTitle + '$' + readUrl);
        }
    }
    
    if (chapters.length === 0) {
        chapters.push('第1章$novel://' + dname + '/' + novelId + '/0');
    }
    
    var playUrl = chapters.join('#');
    var playFrom = '小说阅读';
    
    return {
        list: [{
            vod_id: encodedId,
            vod_name: safeText(item.title || item.name),
            vod_pic: fixUrl(item.cover_url || item.cover || item.pic || ''),
            vod_content: safeText(item.description || item.content || item.summary || ''),
            vod_year: '',
            vod_actor: safeText(item.author || ''),
            vod_play_from: playFrom,
            vod_play_url: playUrl
        }]
    };
}

async function detailContent(ids) {
    var id = Array.isArray(ids) ? ids[0] : ids;
    
    // 检查是否为小说
    var novelParsed = parseNovelId(id);
    if (novelParsed) {
        return await novelDetailContent(id);
    }
    
    // 解析影视ID: 格式 dbname@@vod_id
    var parsed = parseVodId(id);
    var dbname = parsed ? parsed.dbname : '155';
    var vodId = parsed ? parsed.vodId : id;
    
    // 如果 dbname 为空，尝试从 DB_CONFIG 中查找
    if (!dbname) {
        // 尝试从列表中匹配
        for (var i = 0; i < DB_CONFIG.length; i++) {
            if (DB_CONFIG[i].dbname === id.substring(0, 3)) {
                dbname = DB_CONFIG[i].dbname;
                break;
            }
        }
        if (!dbname) dbname = '155';
    }
    
    var listUrl = apiUrl + '/maccms/json/' + dbname + '/?ids=' + vodId;
    var listData = await apiRequest(listUrl);
    
    if (!listData || listData.code !== 1 || !listData.list || listData.list.length === 0) {
        return Result.error('获取详情失败');
    }
    
    var item = listData.list[0];
    var playUrl = '';
    var playFrom = item.vod_play_from || '线路1';
    var playUrlData = '';
    
    // 尝试获取播放地址
    var playDetailUrl = apiUrl + '/maccms/json/' + dbname + '/?ids=' + vodId + '&play=1';
    var playData = await apiRequest(playDetailUrl);
    if (playData && playData.code === 1 && playData.list && playData.list.length > 0) {
        var playItem = playData.list[0];
        if (playItem.vod_play_url) {
            playUrlData = playItem.vod_play_url;
        }
    }
    
    if (playUrlData) {
        playUrl = playUrlData;
    } else {
        var detailPageUrl = baseUrl + '/db/' + dbname + '/detail/' + vodId;
        playUrl = '第1集$' + detailPageUrl;
    }
    
    return {
        list: [{
            vod_id: id,
            vod_name: safeText(item.vod_name),
            vod_pic: fixUrl(item.vod_pic || ''),
            vod_content: safeText(item.vod_blurb || item.vod_content || ''),
            vod_year: safeText(item.vod_year),
            vod_actor: safeText(item.vod_actor),
            vod_play_from: playFrom,
            vod_play_url: playUrl
        }]
    };
}

async function searchContent(key, quick, pg) {
    var p = parseInt(pg) || 1;
    if (!key || key.trim() === '') return { page: 1, pagecount: 1, list: [], total: 0 };
    
    var limit = 20;
    var dbname = '155';
    var url = apiUrl + '/maccms/json/' + dbname + '/?wd=' + encodeURIComponent(key) + '&page=' + p + '&limit=' + limit;
    var data = await apiRequest(url);
    if (!data || data.code !== 1) {
        var novelSearchUrl = apiUrl + '/book/sis/novels/search?q=' + encodeURIComponent(key) + '&page=' + p + '&limit=' + limit;
        var novelData = await apiRequest(novelSearchUrl);
        if (novelData && novelData.data) {
            var list = extractNovelList(novelData, 'sis');
            var pagecount = novelData.pagecount || Math.ceil((novelData.total || list.length) / limit);
            if (pagecount < p) pagecount = p;
            return {
                page: p,
                pagecount: pagecount,
                list: list,
                total: novelData.total || list.length
            };
        }
        return { page: 1, pagecount: 1, list: [], total: 0 };
    }
    
    var list = extractList(data, dbname);
    var pagecount = data.pagecount || Math.ceil((data.total || list.length) / limit);
    if (pagecount < p) pagecount = p;
    var total = data.total || list.length;
    
    return {
        page: p,
        pagecount: pagecount,
        list: list,
        total: total
    };
}

async function playerContent(flag, id, vipFlags) {
    var playUrl = id;
    
    // ========== 小说处理 ==========
    if (id && typeof id === 'string' && id.indexOf('novel://') === 0) {
        var parts = id.replace('novel://', '').split('/');
        if (parts.length >= 3) {
            var source = parts[0];
            var novelId = parts[1];
            var chapterIdx = parts[2];
            var url = apiUrl + '/book/' + source + '/novels/' + novelId + '/chapters/' + chapterIdx;
            var data = await apiRequest(url);
            if (data && data.code === 0) {
                var content = data.data.content || '';
                var jsonData = {
                    title: '第' + (parseInt(chapterIdx) + 1) + '章',
                    content: content
                };
                var encoded = JSON.stringify(jsonData);
                return {
                    parse: 0,
                    url: 'novel://' + encoded,
                    header: headers
                };
            }
        }
        return {
            parse: 1,
            url: id,
            header: headers
        };
    }
    
    if (isNovelUrl(id)) {
        var info = extractNovelInfoFromUrl(id);
        if (info) {
            playUrl = 'novel://' + info.dname + '/' + info.novelId + '/' + info.chapterIdx;
            return {
                parse: 0,
                url: playUrl,
                header: headers
            };
        }
        return {
            parse: 0,
            url: id,
            header: headers
        };
    }
    
    var novelParsed = parseNovelId(id);
    if (novelParsed) {
        playUrl = 'novel://' + novelParsed.dname + '/' + novelParsed.novelId + '/0';
        return {
            parse: 0,
            url: playUrl,
            header: headers
        };
    }
    
    // ========== 影视播放 ==========
    // 解析 vod_id 获取 dbname 和真实 vodId
    var parsed = parseVodId(id);
    var dbname = parsed ? parsed.dbname : '155';
    var vodId = parsed ? parsed.vodId : id;
    
    // 如果 id 已经是完整URL
    if (id.indexOf('http://') === 0 || id.indexOf('https://') === 0) {
        if (id.indexOf('.m3u8') !== -1 || id.indexOf('.mp4') !== -1 || id.indexOf('index.m3u8') !== -1) {
            return {
                parse: 0,
                url: id,
                header: headers
            };
        }
        return {
            parse: 1,
            url: id,
            header: headers
        };
    }
    
    // 构造详情页URL
    var detailUrl = baseUrl + '/db/' + dbname + '/detail/' + vodId;
    return {
        parse: 1,
        url: detailUrl,
        header: headers
    };
}

var routes = {
    homeContent: function () { return false; },
    homeVideoContent: function () { return false; },
    categoryContent: function () { return false; },
    detailContent: function () { return false; },
    searchContent: function () { return false; },
    playerContent: function () { return false; }
};