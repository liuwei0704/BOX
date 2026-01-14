/**
 * 在线之家 (zxzjys.com) 爬虫
 * 适配模板：低端影视.js
 * 版本：2.1
 * 最后更新：2026-01-14, 修复图片获取问题
 * 
 * @config
 * debug: true
 * showWebView: false
 * blockImages: true
 */

const baseUrl = 'https://www.zxzjys.com';

/**
 * 初始化配置
 */
async function init(cfg) {
    return {};
}

/**
 * 首页分类
 */
async function homeContent(filter) {
    const filterConfig = {
        class: [
            { type_id: "1", type_name: "电影" },
            { type_id: "2", type_name: "美剧" },
            { type_id: "3", type_name: "韩剧" },
            { type_id: "4", type_name: "日剧" },
            { type_id: "5", type_name: "泰剧" },
            { type_id: "6", type_name: "动漫" }
        ],
        filters: {
            "1": [ { key: "sort", name: "排序", value: [ {n:"按时间",v:"time"}, {n:"按人气",v:"hits"}, {n:"按评分",v:"score"} ] } ],
            "2": [ { key: "sort", name: "排序", value: [ {n:"按时间",v:"time"}, {n:"按人气",v:"hits"}, {n:"按评分",v:"score"} ] } ],
            "3": [ { key: "sort", name: "排序", value: [ {n:"按时间",v:"time"}, {n:"按人气",v:"hits"}, {n:"按评分",v:"score"} ] } ],
            "4": [ { key: "sort", name: "排序", value: [ {n:"按时间",v:"time"}, {n:"按人气",v:"hits"}, {n:"按评分",v:"score"} ] } ],
            "5": [ { key: "sort", name: "排序", value: [ {n:"按时间",v:"time"}, {n:"按人气",v:"hits"}, {n:"按评分",v:"score"} ] } ],
            "6": [ { key: "sort", name: "排序", value: [ {n:"按时间",v:"time"}, {n:"按人气",v:"hits"}, {n:"按评分",v:"score"} ] } ]
        }
    };
    return filterConfig;
}

/**
 * 首页推荐视频
 */
async function homeVideoContent() {
    const document = await Java.wvOpen(`${baseUrl}`);
    const videos = parseVideoList(document);
    return { list: videos };
}

/**
 * 分类内容
 */
async function categoryContent(tid, pg, filter, extend) {
    const type = extend.type || tid;
    // URL示例：https://www.zxzjys.com/list/1-2.html
    const document = await Java.wvOpen(`${baseUrl}/list/${type||tid}-${pg}.html`);
    const videos = parseVideoList(document);
    
    // 解析总页数
    let totalPages = pg;
    try {
        const pageLinks = document.querySelectorAll('.stui-page__item a');
        if (pageLinks.length > 0) {
            const lastHref = pageLinks[pageLinks.length - 1].getAttribute('href');
            const match = lastHref.match(/-(\d+)\.html/);
            if (match) totalPages = match[1];
        }
    } catch (e) {}

    return { 
        code: 1, 
        msg: "数据列表", 
        list: videos, 
        page: pg, 
        pagecount: totalPages, 
        limit: 20, 
        total: totalPages * 20 
    };
}

/**
 * 详情页
 */
async function detailContent(ids) {
    const document = await Java.wvOpen(ids[0]);
    const list = parseDetailPage(document);
    return { code: 1, msg: "数据列表", page: 1, pagecount: 1, limit: 1, total: 1, list };
}

/**
 * 搜索
 */
async function searchContent(key, quick, pg) {
    // 搜索URL：https://www.zxzjys.com/index.php/vod/search/page/1/wd/key.html
    const url = `${baseUrl}/index.php/vod/search/page/${pg}/wd/${encodeURIComponent(key)}.html`;
    let res = await Java.req(url);
    const videos = parseVideoList(res.doc);
    return { code: 1, msg: "数据列表", list: videos, page: pg, pagecount: pg, limit: 12, total: 100 };
}

/**
 * 播放器
 */
async function playerContent(flag, id, vipFlags) {
    // id 为具体播放页，由插件框架负责后续解析
    return { url: id, parse: 1, header: { 'Referer': baseUrl } };
}

/**
 * action
 */
async function action(actionStr) {
    return;
}


/* ---------------- 工具函数 ---------------- */

/**
 * 提取视频列表 (修复图片获取逻辑)
 */
function parseVideoList(document) {
    const boxes = Array.from(document.querySelectorAll('.stui-vodlist__item, .stui-vodlist li, ul.stui-vodlist__media li'));
    const list = boxes.map(box => {
        const thumbEl = box.querySelector('.stui-vodlist__thumb, .pic, a.stui-vodlist__thumb');
        const titleEl = box.querySelector('.title a') || box.querySelector('a.title') || thumbEl;
        const remarksEl = box.querySelector('.pic-text, .stui-vodlist__pic-text');

        // ID 提取与补全
        let vodId = thumbEl?.getAttribute('href') || '';
        if (!vodId && titleEl) vodId = titleEl.getAttribute('href') || '';
        if (vodId && !vodId.startsWith('http')) {
            vodId = baseUrl + (vodId.startsWith('/') ? '' : '/') + vodId;
        }

        // 图片提取 - 多种尝试方案
        let vodPic = '';
        
        // 方案1: 直接获取img标签的src或data-original
        const imgEl = box.querySelector('img');
        if (imgEl) {
            vodPic = imgEl.getAttribute('data-original') || 
                     imgEl.getAttribute('data-src') || 
                     imgEl.getAttribute('src') || 
                     imgEl.getAttribute('_src') || '';
        }
        
        // 方案2: 从背景图片中提取
        if (!vodPic && thumbEl) {
            const style = thumbEl.getAttribute('style') || thumbEl.style.backgroundImage;
            if (style) {
                const match = style.match(/url\(["']?([^"')]+)["']?\)/);
                if (match) vodPic = match[1];
            }
        }
        
        // 方案3: 从data-original属性获取
        if (!vodPic) {
            vodPic = thumbEl?.getAttribute('data-original') || 
                     thumbEl?.getAttribute('data-src') || '';
        }

        // 图片URL处理
        if (vodPic) {
            if (vodPic.startsWith('//')) {
                vodPic = 'https:' + vodPic;
            } else if (vodPic.startsWith('/')) {
                vodPic = baseUrl + vodPic;
            } else if (!vodPic.startsWith('http')) {
                vodPic = baseUrl + '/' + vodPic;
            }
            
            // 移除可能的URL参数中的尺寸限制
            vodPic = vodPic.replace(/_\d+x\d+\./g, '.');
        }

        // 标题提取
        let vodName = '';
        if (titleEl) {
            vodName = titleEl.getAttribute('title') || titleEl.textContent?.trim() || '';
        }
        if (!vodName && imgEl) {
            vodName = imgEl.getAttribute('alt') || imgEl.getAttribute('title') || '';
        }

        return {
            vod_name: vodName || '',
            vod_pic: vodPic,
            vod_remarks: remarksEl?.textContent?.trim() || '',
            vod_id: vodId,
            vod_actor: box.querySelector('.text, .stui-vodlist__detail p')?.textContent?.trim() || ''
        };
    }).filter(it => it.vod_id);

    return list;
}

/**
 * 解析详情页 (实现播放线路合并与数据清洗)
 */
function parseDetailPage(document) {
    const title = document.querySelector('.stui-content__detail .title')?.textContent.trim() || '';
    const vod_pic = document.querySelector('.stui-content__thumb img')?.getAttribute('data-original') || 
                    document.querySelector('.stui-content__thumb img')?.getAttribute('src') || '';
    
    // 提取并清洗详情数据 (去除前缀标签)
    const infoElements = Array.from(document.querySelectorAll('.stui-content__detail .data, .stui-content__detail p'));
    const findInfo = (tag) => {
        const el = infoElements.find(el => el.textContent.includes(tag));
        if (!el) return '';
        return el.textContent.replace(tag, '').replace(/[:：]/g, '').trim();
    };

    const vod_year = findInfo('年份');
    const vod_area = findInfo('地区');
    const vod_actor = findInfo('主演');
    const vod_director = findInfo('导演');
    const vod_remarks = findInfo('更新') || findInfo('状态');
    const vod_content = document.querySelector('.detail-content')?.textContent.trim() || 
                        document.querySelector('.detail-sketch')?.textContent.trim() || 
                        document.querySelector('.stui-content__desc')?.textContent.trim() || '';

    // 播放线路合并逻辑
    const tabEls = Array.from(document.querySelectorAll('.nav-tabs li a'));
    const playlistEls = Array.from(document.querySelectorAll('.stui-content__playlist'));
    
    let playFroms = [];
    let playUrls = [];

    playlistEls.forEach((ul, index) => {
        const fromName = tabEls[index]?.textContent.trim() || `线路${index + 1}`;
        const links = Array.from(ul.querySelectorAll('li a')).map(a => {
            let href = a.getAttribute('href');
            if (href && !href.startsWith('http')) href = baseUrl + (href.startsWith('/') ? '' : '/') + href;
            const episodeName = a.textContent.trim();
            return `${episodeName}$${href}`;
        });

        if (links.length > 0) {
            playFroms.push(fromName);
            playUrls.push(links.join('#'));
        }
    });

    return [{
        vod_id: window.location.pathname,
        vod_name: title,
        vod_pic: vod_pic,
        vod_remarks: vod_remarks,
        vod_year: vod_year,
        vod_actor: vod_actor,
        vod_director: vod_director,
        vod_area: vod_area,
        vod_lang: '中文字幕',
        vod_content: vod_content,
        vod_play_from: playFroms.join('$$$'),
        vod_play_url: playUrls.join('$$$')
    }];
}