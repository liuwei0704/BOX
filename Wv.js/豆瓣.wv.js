/**
 * 豆瓣站源脚本，包含移动端动态首页 UI 的完整演示。
 * 作者 @ccfork
 *
 * @config
 * timeout: 30
 * blockImages: true
 * returnType: dom
 * debug: false
 */

const baseUrl = 'https://movie.douban.com';
const apiUrl = 'https://m.douban.com/rexxar/api/v2';
const headers = {
    'Referer': baseUrl + '/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'
};
const imageHeader = '@Referer=' + encodeURIComponent(baseUrl + '/');
const pageSize = 20;
var homeListCache = null;

function values(items) {
    var out = [];
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        out.push({ n: item[0], v: item[1] });
    }
    return out;
}

function imageUrl(url) {
    if (!url) return '';
    return url + imageHeader;
}

function ratingText(item) {
    var value = item && item.rating ? Number(item.rating.value || 0) : 0;
    var episode = item && item.episodes_info ? item.episodes_info : '';
    if (episode && value) return episode + ' · ' + value + '分';
    if (episode) return episode;
    return value ? value + '分' : '暂无评分';
}

function subjectList(items) {
    var list = [];
    items = items || [];
    for (var i = 0; i < items.length; i++) {
        var item = items[i] || {};
        if (item.card && item.card !== 'subject') continue;
        if (item.layout && item.layout !== 'subject') continue;
        if (item.target) item = item.target;
        if (!item.id || !item.title) continue;
        var pic = item.pic ? (item.pic.large || item.pic.normal || '') : (item.cover_url || '');
        list.push({
            vod_id: String(item.id),
            vod_name: item.title,
            vod_pic: imageUrl(pic),
            vod_remarks: ratingText(item),
            vod_year: item.year || ''
        });
    }
    return list;
}

function copyObject(source) {
    var target = {};
    source = source || {};
    for (var key in source) if (Object.prototype.hasOwnProperty.call(source, key)) target[key] = source[key];
    return target;
}

function customBannerList(items) {
    var list = [];
    for (var i = 0; i < Math.min(items.length, 6); i++) {
        var item = items[i];
        list.push({
            vod_id: item.vod_id,
            vod_name: item.vod_name,
            vod_pic: item.vod_pic,
            vod_remarks: '自定义轮播 · ' + item.vod_remarks,
            vod_year: item.vod_year
        });
    }
    return list;
}

function selectedCategories(ext, tid) {
    var selected = {};
    if (ext.genre) selected['类型'] = ext.genre;
    if (ext.area) selected['地区'] = ext.area;
    if (tid === 'tv' && ext.platform) selected['平台'] = ext.platform;
    return JSON.stringify(selected);
}

function commonFilters(tid) {
    var movieGenres = ['全部','喜剧','爱情','动作','科幻','动画','悬疑','犯罪','惊悚','冒险','音乐','历史','奇幻','恐怖','战争','传记','歌舞','武侠','情色','灾难','西部','纪录片','短片'];
    var tvGenres = ['不限类型','全部剧集','全部综艺','喜剧','爱情','悬疑','动画','武侠','古装','家庭','犯罪','科幻','恐怖','历史','战争','动作','冒险','传记','剧情','奇幻','惊悚','灾难','歌舞','音乐','真人秀','脱口秀'];
    var movieAreas = ['全部','华语','欧美','韩国','日本','中国大陆','美国','中国香港','中国台湾','英国','法国','德国','意大利','西班牙','印度','泰国','俄罗斯','加拿大','澳大利亚','爱尔兰','瑞典','巴西','丹麦'];
    var tvAreas = ['全部','华语','欧美','国外','韩国','日本','中国大陆','中国香港','美国','英国','泰国','中国台湾','意大利','法国','德国','西班牙','俄罗斯','瑞典','巴西','丹麦','印度','加拿大','爱尔兰','澳大利亚'];
    var years = ['全部','2020年代','2026','2025','2024','2023','2022','2021','2020','2019','2010年代','2000年代','90年代','80年代','70年代','60年代','更早'];
    var genreValues = [];
    var areaValues = [];
    var yearValues = [];
    var genres = tid === 'tv' ? tvGenres : movieGenres;
    var areas = tid === 'tv' ? tvAreas : movieAreas;
    for (var i = 0; i < genres.length; i++) genreValues.push({ n: genres[i], v: i === 0 ? '' : genres[i] });
    for (var j = 0; j < areas.length; j++) areaValues.push({ n: areas[j], v: j === 0 ? '' : areas[j] });
    for (var k = 0; k < years.length; k++) yearValues.push({ n: years[k], v: k === 0 ? '' : years[k] });

    var modeValues = tid === 'movie' ? values([
        ['全部','all'], ['热门电影','hot'], ['最新电影','最新'], ['豆瓣高分','豆瓣高分'], ['冷门佳片','冷门佳片']
    ]) : values([
        ['全部','all'], ['热门剧集','tv'], ['国产剧','tv_domestic'], ['欧美剧','tv_american'], ['日剧','tv_japanese'], ['韩剧','tv_korean'], ['动画','tv_animation'], ['纪录片','tv_documentary'], ['热门综艺','show'], ['国内综艺','show_domestic'], ['国外综艺','show_foreign']
    ]);

    var filters = [
        { key: 'mode', name: '栏目', value: modeValues },
        { key: 'genre', name: '类型', value: genreValues },
        { key: 'area', name: '地区', value: areaValues },
        { key: 'year', name: '年代', value: yearValues },
        { key: 'sort', name: '排序', value: values([['综合排序','T'],['近期热度','U'],['首映时间','R'],['高分优先','S']]) },
        { key: 'score', name: '评分区间', value: values([['全部评分','0,10'],['9-10分','9,10'],['8-10分','8,10'],['7-10分','7,10'],['6-10分','6,10'],['0-6分','0,6']]) },
        { key: 'playable', name: '可播放', value: values([['不限',''],['可播放','true']]) }
    ];
    if (tid === 'tv') {
        filters.splice(4, 0, { key: 'platform', name: '平台', value: values([
            ['全部',''],['腾讯视频','腾讯视频'],['爱奇艺','爱奇艺'],['优酷','优酷'],['湖南卫视','湖南卫视'],
            ['Netflix','Netflix'],['HBO','HBO'],['BBC','BBC'],['NHK','NHK'],['CBS','CBS'],['NBC','NBC'],['tvN','tvN']
        ]) });
    }
    return filters;
}

async function getJson(url) {
    var res = await fetch(url, { headers: headers });
    if (res.error) throw new Error(res.error);
    if (typeof res.json === 'function') return await res.json();
    return JSON.parse(res.body || '{}');
}

async function getHomeList() {
    if (homeListCache !== null) return homeListCache;
    var data = await getJson(apiUrl + '/subject/recent_hot/movie?start=0&limit=' + pageSize);
    return homeListCache = subjectList(data.items);
}

async function homeContent(filter) {
    var bannerList = [];
    try {
        bannerList = customBannerList(await getHomeList());
    } catch (e) {
        homeListCache = null;
    }
    return {
        class: [
            { type_id: 'top200', type_name: 'TOP200' },
            { type_id: 'movie', type_name: '电影' },
            { type_id: 'tv', type_name: '剧集' },
            { type_id: 'movie_hot', type_name: '热门电影' },
            { type_id: 'tv_animation', type_name: '动画剧集' }
        ],
        filters: {
            top200: [],
            movie: commonFilters('movie'),
            tv: commonFilters('tv'),
            movie_hot: commonFilters('movie'),
            tv_animation: commonFilters('tv')
        },
        home_ui: {
            version: 1,
            mobile: {
                layout: 'sections',
                search: { enabled: true },
                blocks: [
                    // 独立 list 大轮播；实际站源可在 vod_pic 中提供专用横图。
                    {
                        type: 'banner',
                        title: '自定义大轮播',
                        enabled: true,
                        list: bannerList,
                        limit: 6,
                        autoplay_ms: 5000,
                        show_indicator: true,
                        show_title: true,
                        style: { type: 'rect', ratio: 1.78 }
                    },
                    // homeVideoContent 推荐数据，横向单行、屏内约两项。
                    {
                        type: 'recommend',
                        title: '热门推荐 · 横向大卡',
                        source: 'home',
                        enabled: true,
                        more: false,
                        offset: 0,
                        limit: 8,
                        layout: { direction: 'horizontal', span: 1, viewport_count: 2 },
                        style: { type: 'rect', ratio: 1.6 }
                    },
                    // 本地播放历史，纵向紧凑列表，“更多”复用历史页面。
                    {
                        type: 'history',
                        title: '播放历史 · 纵向列表',
                        enabled: true,
                        more: true,
                        limit: 3,
                        layout: { direction: 'vertical', span: 1 },
                        style: { type: 'list' }
                    },
                    // 本地收藏，横向圆形卡片，“更多”复用收藏页面。
                    {
                        type: 'favorite',
                        title: '我的收藏 · 横向圆卡',
                        enabled: true,
                        more: true,
                        limit: 6,
                        layout: { direction: 'horizontal', span: 1, viewport_count: 4 },
                        style: { type: 'oval', ratio: 1.0 }
                    },
                    // 单分类横向海报，点击“更多”进入独立分类页。
                    {
                        type: 'category',
                        id: 'top200',
                        title: 'TOP200 · 横向海报',
                        enabled: true,
                        more: true,
                        limit: 8,
                        layout: { direction: 'horizontal', span: 1, viewport_count: 3 },
                        style: { type: 'rect', ratio: 0.75 }
                    },
                    // 单分类纵向三列，演示分类筛选和首屏数据复用。
                    {
                        type: 'category',
                        id: 'movie',
                        title: '电影 · 纵向三列',
                        enabled: true,
                        more: true,
                        limit: 6,
                        layout: { direction: 'vertical', span: 3 },
                        style: { type: 'rect', ratio: 0.75 }
                    },
                    // 横向两行列表卡片。
                    {
                        type: 'category',
                        id: 'tv',
                        title: '剧集 · 横向双行列表',
                        enabled: true,
                        more: true,
                        limit: 8,
                        layout: { direction: 'horizontal', span: 2, viewport_count: 2 },
                        style: { type: 'list' }
                    },
                    // 展开未单独声明的分类，并演示 exclude 排除指定分类。
                    {
                        type: 'categories',
                        enabled: true,
                        more: true,
                        exclude: ['movie_hot'],
                        limit: 6,
                        layout: { direction: 'vertical', span: 2 },
                        style: { type: 'rect', ratio: 1.0 }
                    }
                ]
            }
        }
    };
}

async function homeVideoContent() {
    try {
        return { list: await getHomeList() };
    } catch (e) {
        return Result.error('豆瓣首页加载失败: ' + e.message);
    }
}

async function categoryContent(tid, pg, filter, extend) {
    var p = parseInt(pg) || 1;
    var start = (p - 1) * pageSize;
    var ext = copyObject(extend);
    // 演示分类仅是接口别名，继续复用原有电影、剧集 categoryContent。
    if (tid === 'movie_hot') {
        tid = 'movie';
        if (!ext.mode) ext.mode = 'hot';
    } else if (tid === 'tv_animation') {
        tid = 'tv';
        if (!ext.mode) ext.mode = 'tv_animation';
    }
    var mode = ext.mode || 'all';
    try {
        var data;
        if (tid === 'top200') {
            if (start >= 200) {
                return { page: p, pagecount: 10, limit: pageSize, total: 200, list: [] };
            }
            var topCount = Math.min(pageSize, 200 - start);
            data = await getJson(apiUrl + '/subject_collection/movie_top250/items?start=' + start + '&count=' + topCount);
            var topList = subjectList(data.subject_collection_items || data.items);
            return { page: p, pagecount: 10, limit: pageSize, total: 200, list: topList };
        }
        if (mode !== 'all') {
            var recentType = mode;
            var params = ['start=' + start, 'limit=' + pageSize];
            if (tid === 'movie') {
                if (mode !== 'hot') params.push('category=' + encodeURIComponent(mode));
                params.push('type=' + encodeURIComponent('全部'));
                recentType = 'movie';
            }
            data = await getJson(apiUrl + '/subject/recent_hot/' + encodeURIComponent(recentType) + '?' + params.join('&'));
        } else {
            var selected = selectedCategories(ext, tid);
            var query = [
                'refresh=0',
                'start=' + start,
                'count=' + pageSize,
                'selected_categories=' + encodeURIComponent(selected),
                'uncollect=false',
                'score_range=' + encodeURIComponent(ext.score || '0,10'),
                'tags=' + encodeURIComponent([ext.genre || '', ext.year || ''].filter(function (v) { return !!v; }).join(',')),
                'sort=' + encodeURIComponent(ext.sort || 'T')
            ];
            if (ext.playable) query.push('playable=true');
            data = await getJson(apiUrl + '/' + tid + '/recommend?' + query.join('&'));
        }
        var list = subjectList(data.items);
        var total = Number(data.total || 0);
        var pagecount = total ? Math.ceil(total / pageSize) : (list.length >= pageSize ? p + 1 : p);
        return { page: p, pagecount: pagecount, limit: pageSize, total: total || list.length, list: list };
    } catch (e) {
        return Result.error('豆瓣分类加载失败: ' + e.message);
    }
}

async function detailContent(ids) {
    var id = Array.isArray(ids) ? ids[0] : ids;
    id = String(id || '').match(/\d+/);
    id = id ? id[0] : '';
    if (!id) return Result.error('无效的豆瓣条目 ID');
    try {
        var item = await getJson(apiUrl + '/subject/' + id);
        var actors = [];
        var directors = [];
        var i;
        for (i = 0; i < (item.actors || []).length; i++) actors.push(item.actors[i].name);
        for (i = 0; i < (item.directors || []).length; i++) directors.push(item.directors[i].name);
        var play = [];
        for (i = 0; i < (item.trailers || []).length; i++) {
            var trailer = item.trailers[i];
            if (trailer.video_url) play.push((trailer.title || ('预告片' + (i + 1))) + '$' + trailer.video_url);
        }
        for (i = 0; i < (item.linewatches || []).length; i++) {
            var watch = item.linewatches[i];
            var watchUrl = watch.url || watch.uri || '';
            if (watchUrl.indexOf('http') === 0) play.push((watch.name || watch.title || '在线观看') + '$' + watchUrl);
        }
        if (!play.length) play.push('豆瓣详情$' + (item.url || (baseUrl + '/subject/' + id + '/')));
        return { list: [{
            vod_id: id,
            vod_name: item.title || id,
            vod_pic: imageUrl(item.cover_url || (item.pic && (item.pic.large || item.pic.normal)) || ''),
            vod_year: item.year || '',
            vod_area: (item.countries || []).join('/'),
            vod_actor: actors.join('/'),
            vod_director: directors.join('/'),
            vod_remarks: ratingText(item),
            vod_content: item.intro || '',
            vod_play_from: item.trailers && item.trailers.length ? '豆瓣预告' : '豆瓣详情',
            vod_play_url: play.join('#')
        }] };
    } catch (e) {
        return Result.error('豆瓣详情加载失败: ' + e.message);
    }
}

async function searchContent(key, quick, pg) {
    var p = parseInt(pg) || 1;
    var start = (p - 1) * pageSize;
    try {
        var url = apiUrl + '/search/subjects?q=' + encodeURIComponent(key) + '&type=movie&start=' + start + '&count=' + pageSize;
        var data = await getJson(url);
        var subjects = data.subjects || {};
        var list = subjectList(subjects.items);
        var total = Number(subjects.total || 0);
        return { page: p, pagecount: total ? Math.ceil(total / pageSize) : p, limit: pageSize, total: total, list: list };
    } catch (e) {
        return Result.error('豆瓣搜索失败: ' + e.message);
    }
}

async function playerContent(flag, id, vipFlags) {
    if (!id) return { parse: 0, url: '' };
    if (/\.(m3u8|mp4)(\?|$)/i.test(id) || id.indexOf('vt') === 0 || id.indexOf('https://vt') === 0) {
        return { parse: 0, url: id, header: headers };
    }
    return { parse: 1, url: id, header: headers };
}

var routes = {
    homeVideoContent: function () { return false; },
    categoryContent: function () { return false; },
    detailContent: function () { return false; },
    searchContent: function () { return false; }
};
