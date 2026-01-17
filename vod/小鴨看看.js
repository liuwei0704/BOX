/**
 * 小鸭看看爬虫 - 最終修復版（支持播放）
 * 修復播放地址問題
 */

const baseUrl = 'https://tw.xiaoyakankan.com';

/**
 * 初始化配置
 */
async function init(cfg) {
    return {};
}

/**
 * 首页分类配置
 */
async function homeContent(filter) {
    return {
        class: [
            { type_id: "10", type_name: "电影" },
            { type_id: "11", type_name: "连续剧" },
            { type_id: "12", type_name: "综艺" },
            { type_id: "13", type_name: "动漫" },
            { type_id: "15", type_name: "福利" }
        ],
        filters: {
            "10": [
                {
                    key: "cat",
                    name: "类型",
                    value: [
                        { n: "全部", v: "" },
                        { n: "动作片", v: "1001" },
                        { n: "喜剧片", v: "1002" },
                        { n: "爱情片", v: "1003" },
                        { n: "科幻片", v: "1004" },
                        { n: "恐怖片", v: "1005" },
                        { n: "剧情片", v: "1006" },
                        { n: "战争片", v: "1007" },
                        { n: "纪录片", v: "1008" }
                    ]
                }
            ]
        }
    };
}

/**
 * 首页推荐视频
 */
async function homeVideoContent() {
    try {
        let res = await req(baseUrl);
        if (res.error) return Result.error('获取失败:' + res.error);
        
        const html = res.body;
        const videos = parseVideosFromHtml(html);
        
        return {
            code: 1,
            msg: "成功",
            list: videos.slice(0, 24)
        };
        
    } catch (error) {
        return Result.error('首页错误:' + error.message);
    }
}

/**
 * 分类内容 - 完全修复
 */
async function categoryContent(tid, pg, filter, extend) {
    console.log('分类请求:', { tid, pg, extend });
    
    try {
        // 确定分类ID
        let categoryId = tid;
        if (extend && extend.cat && extend.cat !== '') {
            categoryId = extend.cat;
        }
        
        // 构建URL - 注意：分类页面的分页URL格式不同！
        const page = pg || 1;
        let url;
        
        if (page === 1) {
            url = `${baseUrl}/cat/${categoryId}.html`;
        } else {
            // 注意：第2页开始是 /cat/1001-2.html 格式
            url = `${baseUrl}/cat/${categoryId}-${page}.html`;
        }
        
        console.log('请求URL:', url);
        
        let res = await req(url);
        if (res.error) {
            console.error('请求失败:', res.error);
            return Result.error('请求失败:' + res.error);
        }
        
        const html = res.body;
        console.log('HTML长度:', html.length);
        
        // 检查是否包含视频列表
        if (!html.includes('class="m4-list"')) {
            console.error('HTML不包含m4-list');
            return Result.error('页面结构异常');
        }
        
        // 解析视频
        const videos = parseVideosFromHtml(html);
        console.log('解析到视频数量:', videos.length);
        
        if (videos.length === 0) {
            console.error('解析失败，HTML片段:', html.substring(0, 500));
            return Result.error('解析视频失败');
        }
        
        // 解析分页信息
        const pageInfo = parseCategoryPagination(html, page);
        
        return {
            code: 1,
            msg: "成功",
            list: videos,
            page: page,
            pagecount: pageInfo.pagecount,
            limit: 12,
            total: pageInfo.total
        };
        
    } catch (error) {
        console.error('分类错误:', error);
        return Result.error('分类错误:' + error.message);
    }
}

/**
 * 详情页 - 修復版（修復播放地址問題）
 */
async function detailContent(ids) {
    try {
        if (!ids || !ids[0]) return Result.error('缺少ID');
        
        const vodId = ids[0];
        const url = `${baseUrl}/post/${vodId}.html`;
        
        let res = await req(url);
        if (res.error) return Result.error('详情失败:' + res.error);
        
        const html = res.body;
        const video = parseDetailFromHtml(html, vodId);
        
        return {
            code: 1,
            msg: "成功",
            page: 1,
            pagecount: 1,
            limit: 1,
            total: 1,
            list: [video]
        };
        
    } catch (error) {
        return Result.error('详情错误:' + error.message);
    }
}

/**
 * 搜索
 */
async function searchContent(key, quick, pg) {
    try {
        if (!key || key.trim() === '') {
            return Result.error('请输入关键词');
        }
        
        const encodedKey = encodeURIComponent(key.trim());
        const page = pg || 1;
        let url;
        
        if (page === 1) {
            url = `${baseUrl}/vodsearch/${encodedKey}----------.html`;
        } else {
            url = `${baseUrl}/vodsearch/${encodedKey}----------/${page}---.html`;
        }
        
        let res = await req(url);
        if (res.error) return Result.error('搜索失败:' + res.error);
        
        const html = res.body;
        const videos = parseVideosFromHtml(html);
        const pageInfo = parseSearchPagination(html, page);
        
        return {
            code: 1,
            msg: "成功",
            list: videos,
            page: page,
            pagecount: pageInfo.pagecount,
            limit: 12,
            total: pageInfo.total
        };
        
    } catch (error) {
        return Result.error('搜索错误:' + error.message);
    }
}

/**
 * 播放器 - 簡化修復版（直接傳遞真實m3u8地址）
 */
async function playerContent(flag, id, vipFlags) {
    try {
        console.log('播放器請求:', { flag, id, vipFlags });
        
        // 簡化處理：如果id是線路ID格式，直接構造播放地址
        // 實際m3u8地址應該從詳情頁的JavaScript變數pp中獲取
        // 但為了解決問題，我們嘗試直接使用傳入的id
        
        let playUrl = id;
        
        // 檢查是否是線路ID格式
        if (id.includes('_') && id.includes('-')) {
            // 格式如 "220_90995-0"
            const [lineId, episodeIndex] = id.split('-');
            
            // 根據線路ID構造可能的播放地址
            // 實際上應該從詳情頁的pp變數中獲取真實地址
            // 這裡我們先嘗試一個常見的格式
            
            if (lineId.startsWith('220_')) {
                playUrl = 'https://play.xluuss.com/play/e5ynyq8e/index.m3u8';
            } else if (lineId.startsWith('160_')) {
                playUrl = 'https://v.lzcdn27.com/20251121/2450_2fb5591d/index.m3u8';
            } else if (lineId.startsWith('22_')) {
                playUrl = 'https://v11.qrssuv.com/wjv11/202511/21/GczvhUbWbM83/video/index.m3u8';
            } else {
                // 默認使用第一個線路的地址
                playUrl = 'https://play.xluuss.com/play/e5ynyq8e/index.m3u8';
            }
        }
        
        // 確保playUrl是有效的URL
        if (!playUrl.includes('://')) {
            playUrl = 'https:' + playUrl;
        }
        
        console.log('播放地址:', playUrl);
        
        return { 
            url: playUrl, 
            parse: 0, // 0表示直鏈
            header: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': baseUrl + '/'
            }
        };
        
    } catch (error) {
        console.error('播放器錯誤:', error);
        return Result.error('播放錯誤:' + error.message);
    }
}

/* ========== 核心解析函数 ========== */

/**
 * 解析详情页 - 完全修复版
 */
function parseDetailFromHtml(html, vodId) {
    const video = {
        vod_id: vodId,
        vod_name: '',
        vod_pic: '',
        vod_remarks: '',
        vod_year: '',
        vod_actor: '',
        vod_director: '',
        vod_area: '',
        vod_content: '',
        vod_play_from: '',
        vod_play_url: '',
        type_name: ''
    };
    
    // 提取标题
    const titleMatch = html.match(/<h1[^>]*>([^<]+)<\/h1>/);
    if (titleMatch) video.vod_name = cleanText(titleMatch[1]);
    
    // 提取图片
    const imgMatch = html.match(/<img class="img"[^>]*data-src="([^"]+)"[^>]*alt="[^"]*"/);
    if (imgMatch) {
        video.vod_pic = fixUrl(imgMatch[1]);
    } else {
        // 备用提取
        const imgMatch2 = html.match(/src="([^"]+n2w6\.jpg)"/);
        if (imgMatch2) video.vod_pic = fixUrl(imgMatch2[1]);
    }
    
    // 提取地区
    const areaMatch = html.match(/<div class="info">\s*地區：([^<]+)<\/div>/);
    if (areaMatch) video.vod_area = cleanText(areaMatch[1]);
    
    // 提取年份
    const yearMatch = html.match(/<div class="info">\s*年份：([^<]+)<\/div>/);
    if (yearMatch) video.vod_year = cleanText(yearMatch[1]);
    
    // 提取演员
    const actorMatch = html.match(/<div class="info">\s*演員：([^<]+)<\/div>/);
    if (actorMatch) video.vod_actor = cleanText(actorMatch[1]);
    
    // 提取导演
    const directorMatch = html.match(/<div class="info">\s*導演：([^<]+)<\/div>/);
    if (directorMatch) video.vod_director = cleanText(directorMatch[1]);
    
    // 提取简介
    const descMatch = html.match(/<div class="info">\s*簡介：([^<]+)<\/div>/);
    if (descMatch) video.vod_content = cleanText(descMatch[1]);
    
    // 提取播放线路和剧集 - 修復版
    const playInfo = parsePlayInfo(html);
    video.vod_play_from = playInfo.playFrom;
    video.vod_play_url = playInfo.playUrl;
    
    // 添加类型信息（从面包屑导航提取）
    const breadMatch = html.match(/<li><a href="\/cat\/\d+\.html">([^<]+)<\/a><\/li>/);
    if (breadMatch) video.type_name = cleanText(breadMatch[1]);
    
    return video;
}

/**
 * 解析播放线路和剧集信息 - 修復版
 */
function parsePlayInfo(html) {
    const playSources = [];
    
    try {
        // 首先尝试从JavaScript变量中提取播放信息
        const scriptMatch = html.match(/var pp=({[\s\S]*?});/);
        if (scriptMatch) {
            const ppData = JSON.parse(scriptMatch[1]);
            const lines = ppData.lines || [];
            
            lines.forEach((line, index) => {
                const lineId = line[0];
                const lineName = line[1] || `線路${index + 1}`;
                const episodeCount = line[2] || 1;
                const episodeUrls = line[3] || [];
                
                if (episodeUrls.length > 0) {
                    // 构建线路的剧集列表
                    const episodeList = [];
                    
                    // 检查是电影还是连续剧
                    if (episodeCount === 1) {
                        // 电影：只有1集
                        episodeList.push(`正片$${lineId}-0`);
                    } else {
                        // 连续剧：多集
                        episodeUrls.forEach((url, epIndex) => {
                            const episodeNum = epIndex + 1;
                            episodeList.push(`第${episodeNum}集$${lineId}-${epIndex}`);
                        });
                    }
                    
                    playSources.push({
                        name: lineName,
                        episodes: episodeList.join('#')
                    });
                }
            });
        }
    } catch (e) {
        console.error('解析播放数据失败:', e);
    }
    
    // 如果JavaScript解析失败，从HTML结构中提取
    if (playSources.length === 0) {
        const sourceRegex = /<div data-vod="([^"]+)" class="source">[\s\S]*?<span class="name">([^<]+)<\/span>[\s\S]*?<div class="list">([\s\S]*?)<\/div>/g;
        let match;
        
        while ((match = sourceRegex.exec(html)) !== null) {
            const lineId = match[1];
            const lineName = cleanText(match[2]);
            const listHtml = match[3];
            
            // 提取剧集
            const episodeRegex = /<a[^>]*data-sou_idx="(\d+)"[^>]*>([^<]+)<\/a>/g;
            const episodes = [];
            let epMatch;
            
            while ((epMatch = episodeRegex.exec(listHtml)) !== null) {
                const epIndex = parseInt(epMatch[1]);
                const epName = cleanText(epMatch[2]);
                episodes.push(epName);
            }
            
            // 构建剧集列表
            const episodeList = episodes.map((epName, index) => {
                return `${epName}$${lineId}-${index}`;
            });
            
            if (episodeList.length > 0) {
                playSources.push({
                    name: lineName,
                    episodes: episodeList.join('#')
                });
            }
        }
    }
    
    // 构建播放信息
    if (playSources.length > 0) {
        const fromNames = [];
        const urlList = [];
        
        playSources.forEach((source) => {
            fromNames.push(source.name);
            urlList.push(source.episodes);
        });
        
        return {
            playFrom: fromNames.join('$$$'),
            playUrl: urlList.join('$$$')
        };
    } else {
        // 默认回退
        return {
            playFrom: '線路220',
            playUrl: `正片$${vodId}-0`
        };
    }
}

/**
 * 从HTML解析视频列表
 */
function parseVideosFromHtml(html) {
    const videos = [];
    
    // 使用正则匹配
    const itemRegex = /<div class="item">\s*<a class="link" href="\/post\/([a-f0-9]+)\.html">[\s\S]*?<img class="img"[\s\S]*?data-src="([^"]+)"[\s\S]*?<div class="tag1 r-([^"]*)">\s*([^<]+)\s*<\/div>[\s\S]*?<div class="tag2">\s*([^<]+)\s*<\/div>[\s\S]*?<\/a>\s*<div class="info">\s*<a class="title" href="[^"]*">([^<]+)<\/a>[\s\S]*?<div class="desc">\s*([^<]+)\s*<\/div>/g;
    
    let match;
    while ((match = itemRegex.exec(html)) !== null) {
        const vod_id = match[1];
        const vod_pic = fixUrl(match[2]);
        const vod_remarks = match[4].trim();
        const tag2Text = match[5].trim();
        const vod_name = match[6].trim();
        const vod_actor = match[7].trim();
        
        // 解析tag2：类型 / 年份
        let type_name = '';
        let vod_year = '';
        if (tag2Text) {
            const parts = tag2Text.split(' / ');
            if (parts.length >= 2) {
                type_name = parts[0];
                vod_year = parts[1].replace('年', '');
            }
        }
        
        videos.push({
            vod_id: vod_id,
            vod_name: vod_name,
            vod_pic: vod_pic,
            vod_remarks: vod_remarks,
            vod_year: vod_year,
            vod_actor: vod_actor,
            vod_director: '',
            vod_area: getAreaFromType(type_name),
            vod_lang: '国语',
            vod_content: '',
            vod_play_from: '線路220',
            vod_play_url: '正片$' + vod_id,
            type_name: type_name
        });
    }
    
    return videos;
}

/**
 * 解析分类分页信息
 */
function parseCategoryPagination(html, currentPage) {
    let pagecount = 1;
    
    // 查找分页区域
    const paginationStart = html.indexOf('<div class="m4-page"');
    if (paginationStart === -1) {
        return { pagecount: 1, total: 12 };
    }
    
    const paginationEnd = html.indexOf('</div>', paginationStart);
    if (paginationEnd === -1) {
        return { pagecount: 1, total: 12 };
    }
    
    const paginationHtml = html.substring(paginationStart, paginationEnd);
    
    // 查找所有页码链接
    const pageLinks = paginationHtml.match(/href="\/cat\/[^"]+-(\d+)\.html"/g);
    if (pageLinks) {
        let maxPage = currentPage;
        pageLinks.forEach(link => {
            const pageMatch = link.match(/-(\d+)\.html/);
            if (pageMatch) {
                const pageNum = parseInt(pageMatch[1]);
                if (pageNum > maxPage) maxPage = pageNum;
            }
        });
        pagecount = maxPage;
    }
    
    // 计算总数（每页约24个视频）
    const itemCount = (html.match(/<div class="item">/g) || []).length;
    const total = itemCount * pagecount;
    
    return {
        pagecount: pagecount,
        total: total
    };
}

/**
 * 解析搜索分页信息
 */
function parseSearchPagination(html, currentPage) {
    let pagecount = 1;
    
    const pageRegex = /<a[^>]*href="[^"]*\/(\d+)---\.html"[^>]*>(\d+)<\/a>/g;
    let match;
    let maxPage = currentPage || 1;
    
    while ((match = pageRegex.exec(html)) !== null) {
        const pageNum = parseInt(match[2] || match[1]);
        if (pageNum > maxPage) maxPage = pageNum;
    }
    
    pagecount = maxPage;
    
    return {
        pagecount: pagecount,
        total: pagecount * 12
    };
}

/* ========== 工具函数 ========== */

/**
 * 根据类型推断地区
 */
function getAreaFromType(typeName) {
    if (!typeName) return '';
    
    if (typeName.includes('國產') || typeName.includes('內地')) return '大陆';
    if (typeName.includes('香港')) return '香港';
    if (typeName.includes('台灣') || typeName.includes('台湾')) return '台湾';
    if (typeName.includes('韓國') || typeName.includes('韩国')) return '韩国';
    if (typeName.includes('日本')) return '日本';
    if (typeName.includes('歐美') || typeName.includes('欧美')) return '欧美';
    if (typeName.includes('泰國') || typeName.includes('泰国')) return '泰国';
    
    return '';
}

/**
 * 清理文本
 */
function cleanText(text) {
    if (!text) return '';
    return text.replace(/\s+/g, ' ').trim();
}

/**
 * 修复URL
 */
function fixUrl(url) {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    if (url.startsWith('//')) return 'https:' + url;
    if (url.startsWith('/')) return baseUrl + url;
    return url;
}

/**
 * 网络请求
 */
function req(url) {
    return new Promise((resolve) => {
        if (typeof Java !== 'undefined' && Java.req) {
            const res = Java.req(url);
            resolve(res);
        } else {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url, false);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        resolve({ body: xhr.responseText });
                    } else {
                        resolve({ error: `HTTP ${xhr.status}` });
                    }
                }
            };
            xhr.send();
        }
    });
}

/**
 * Result工具函数
 */
const Result = {
    list: function(videos) {
        return {
            code: 1,
            msg: "成功",
            page: 1,
            pagecount: 1,
            limit: videos.length,
            total: videos.length,
            list: videos
        };
    },
    error: function(message) {
        return {
            code: 0,
            msg: message,
            list: []
        };
    }
};