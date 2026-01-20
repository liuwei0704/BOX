/**
 * 短剧网爬虫脚本
 * 适配网站: www.rzjy985.com
 * 日期: 2026年1月20日
 * 修正：搜索和分类分页问题
 */

// ========== 基礎配置 ==========
const baseUrl = 'https://www.rzjy985.com';  // 短剧网域名
const siteName = '短剧网';               // 網站名稱

// ========== 爬蟲接口函數 ==========

async function init(cfg) {
    console.log(`[${siteName}] 爬蟲初始化`);
    return {
        sites: [{
            key: 'duanju',
            name: siteName,
            type: 3,
            searchable: 1,
            changeable: 1,
            ext: '.html'
        }],
        player: {
            decode: 0,
            parse: 0,
            jx: 0
        }
    };
}

async function homeContent(filter) {
    return {
        class: [
            { type_id: "douyinduanju", type_name: "抖音短剧" },
            { type_id: "hanju", type_name: "韩剧" },
            { type_id: "dianshiju", type_name: "电视剧" },
            { type_id: "dianying", type_name: "热门电影" },
            { type_id: "zongyijiemu", type_name: "综艺节目" },
            { type_id: "dongman", type_name: "动漫" },
            { type_id: "tiyusaishi", type_name: "体育赛事" }
        ],
        }
}
async function homeVideoContent() {
    try {
        const url = `${baseUrl}/`;
        const res = await req(url);
        
        if (res.error) {
            return Result.error(`獲取失敗: ${res.error}`);
        }
        
        const html = res.body;
        const videos = extractVideosFromHTML(html);
        
        return Result.list(videos.slice(0, 30));
        
    } catch (error) {
        return Result.error(`首頁錯誤: ${error.message}`);
    }
}

async function categoryContent(tid, pg, filter, extend) {
    try {
        const page = pg || 1;
        let url = '';
        
        console.log(`[${siteName}] 分類請求: tid=${tid}, page=${page}, extend=`, extend);
        
        // 檢查是否有篩選條件
        const hasFilter = extend && Object.keys(extend).length > 0;
        
        if (hasFilter) {
            // 有篩選條件，使用 vodshow 路徑
            // 注意：根據搜索結果頁面，參數格式可能是不同的
            // 搜索結果頁面：/vodsearch/%E6%88%91----------1---/
            // 這表明參數可能是：關鍵字----------頁碼---
            
            const params = [tid || ''];
            
            // 分類
            if (extend.class) {
                params.push(extend.class);
            } else {
                params.push('');
            }
            
            // 地區
            if (extend.area) {
                params.push(extend.area);
            } else {
                params.push('');
            }
            
            // 年份
            if (extend.year) {
                params.push(extend.year);
            } else {
                params.push('');
            }
            
            // 填充其他參數（根據搜索結果，可能有更多參數）
            for (let i = 0; i < 8; i++) {
                params.push('');
            }
            
            const paramStr = params.join('-');
            
            if (page === 1) {
                url = `${baseUrl}/vodshow/${paramStr}/`;
            } else {
                url = `${baseUrl}/vodshow/${paramStr}/page/${page}/`;
            }
            
            console.log(`[${siteName}] 篩選分類URL: ${url}`);
        } else {
            // 沒有篩選條件，使用 nl 路徑
            const categoryMap = {
                "douyinduanju": "douyinduanju",
                "hanju": "hanju",
                "dianshiju": "dianshiju",
                "dianying": "dianying",
                "zongyijiemu": "zongyijiemu",
                "dongman": "dongman",
                "tiyusaishi": "tiyusaishi"
            };
            
            const categoryPath = categoryMap[tid] || tid;
            
            // 嘗試兩種URL格式
            if (page === 1) {
                url = `${baseUrl}/nl/${categoryPath}/`;
            } else {
                url = `${baseUrl}/nl/${categoryPath}/page/${page}/`;
            }
            
            console.log(`[${siteName}] 普通分類URL: ${url}`);
        }
        
        const res = await req(url);
        if (res.error) {
            console.error(`[${siteName}] 請求失敗: ${res.error}`);
            // 嘗試備用URL格式
            if (!hasFilter) {
                const fallbackUrl = page === 1 ? 
                    `${baseUrl}/vodshow/${tid}-----------/` : 
                    `${baseUrl}/vodshow/${tid}-----------/page/${page}/`;
                
                console.log(`[${siteName}] 嘗試備用URL: ${fallbackUrl}`);
                const fallbackRes = await req(fallbackUrl);
                
                if (fallbackRes.error) {
                    return Result.error(`請求失敗: ${fallbackRes.error}`);
                }
                
                return processCategoryResponse(fallbackRes.body, page, tid);
            }
            
            return Result.error(`請求失敗: ${res.error}`);
        }
        
        return processCategoryResponse(res.body, page, tid);
        
    } catch (error) {
        console.error(`[${siteName}] 分類錯誤:`, error);
        return Result.error(`分類錯誤: ${error.message}`);
    }
}

async function processCategoryResponse(html, page, tid) {
    console.log(`[${siteName}] 返回HTML長度: ${html.length} 字符`);
    
    // 檢查HTML是否有效
    if (!html || html.length < 100) {
        console.error(`[${siteName}] HTML內容過短: ${html}`);
        return Result.error('獲取的HTML內容無效');
    }
    
    // 提取視頻列表
    const videos = extractVideosFromHTML(html);
    console.log(`[${siteName}] 提取到 ${videos.length} 個視頻`);
    
    // 提取分頁信息
    const pageInfo = extractPaginationInfo(html);
    
    // 如果無法提取分頁信息，根據實際情況設置
    if (pageInfo.pagecount === 1 && videos.length >= 24) {
        // 根據搜索結果頁面，可能有大量頁面
        pageInfo.pagecount = 100; // 設置一個較大的頁數
        console.log(`[${siteName}] 設置默認總頁數為: ${pageInfo.pagecount}`);
    }
    
    // 設置總數（如果無法提取）
    if (!pageInfo.total && videos.length > 0) {
        pageInfo.total = videos.length * pageInfo.pagecount;
    }
    
    console.log(`[${siteName}] 分頁信息: 當前頁 ${page}, 總頁數 ${pageInfo.pagecount || 1}, 總數 ${pageInfo.total || videos.length}`);
    
    return {
        code: 1,
        msg: "成功",
        list: videos,
        page: page,
        pagecount: pageInfo.pagecount || 1,
        limit: 24,
        total: pageInfo.total || videos.length
    };
}

async function detailContent(ids) {
    try {
        if (!ids || !ids[0]) {
            return Result.error('缺少視頻ID');
        }
        
        const vodPath = ids[0];
        const url = `${baseUrl}/m/${vodPath}/`;
        
        console.log(`[${siteName}] 獲取詳情: ${url}`);
        
        const res = await req(url);
        if (res.error) {
            return Result.error(`詳情失敗: ${res.error}`);
        }
        
        const html = res.body;
        const video = extractDetailFromHTML(html, vodPath);
        
        if (!video.vod_name) {
            console.error(`提取詳情失敗: vodPath=${vodPath}`);
            return Result.error('無法解析視頻詳情');
        }
        
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
        return Result.error(`詳情錯誤: ${error.message}`);
    }
}

async function searchContent(key, quick, pg) {
    try {
        if (!key || key.trim() === '') {
            return Result.error('請輸入關鍵詞');
        }
        
        const encodedKey = encodeURIComponent(key.trim());
        const page = pg || 1;
        let url = '';
        
        // 根據搜索結果頁面，URL格式為：/vodsearch/關鍵字----------頁碼---/
        // 例如：/vodsearch/%E6%88%91----------1---/
        
        // 構建參數：關鍵字 + 11個- + 頁碼 + 3個-
        const params = `${encodedKey}----------${page}---`;
        
        if (page === 1) {
            url = `${baseUrl}/vodsearch/${params}/`;
        } else {
            url = `${baseUrl}/vodsearch/${params}/`;
        }
        
        console.log(`[${siteName}] 搜索請求: ${url}`);
        
        const res = await req(url);
        if (res.error) {
            return Result.error(`搜索失敗: ${res.error}`);
        }
        
        const html = res.body;
        console.log(`[${siteName}] 搜索結果HTML長度: ${html.length} 字符`);
        
        // 提取視頻列表
        const videos = extractVideosFromHTML(html);
        console.log(`[${siteName}] 提取到 ${videos.length} 個搜索結果`);
        
        // 提取分頁信息
        const pageInfo = extractPaginationInfo(html);
        
        // 搜索結果通常有很多頁
        if (pageInfo.pagecount === 1 && videos.length >= 24) {
            // 根據搜索結果頁面顯示，有224頁
            pageInfo.pagecount = 224; // 或者從HTML中提取實際頁數
            pageInfo.total = videos.length * pageInfo.pagecount;
        }
        
        console.log(`[${siteName}] 搜索分頁信息: 當前頁 ${page}, 總頁數 ${pageInfo.pagecount || 1}`);
        
        return {
            code: 1,
            msg: "成功",
            list: videos,
            page: page,
            pagecount: pageInfo.pagecount || 1,
            limit: 24,
            total: pageInfo.total || videos.length
        };
        
    } catch (error) {
        return Result.error(`搜索錯誤: ${error.message}`);
    }
}

async function playerContent(flag, id, vipFlags) {
    try {
        console.log(`[${siteName}] 播放請求: flag=${flag}, id=${id}, vipFlags=${vipFlags}`);
        
        // 根據HTML結構，播放鏈接格式為：/play/vodPath-sid-nid/
        let playUrl = '';
        
        if (id.includes('-')) {
            // ID格式：vodPath-sid-nid
            playUrl = `${baseUrl}/play/${id}/`;
        } else {
            // 只有vodPath，默認第一集
            playUrl = `${baseUrl}/play/${id}-1-1/`;
        }
        
        console.log(`[${siteName}] 播放頁面URL: ${playUrl}`);
        
        // 訪問播放頁面
        const playRes = await req(playUrl);
        if (playRes.error) {
            return Result.error(`獲取播放頁失敗: ${playRes.error}`);
        }
        
        const playHtml = playRes.body;
        console.log(`[${siteName}] 播放頁面HTML長度: ${playHtml.length} 字符`);
        
        // 從HTML中提取播放地址
        let videoUrl = extractPlayerUrlFromHTML(playHtml, id);
        
        // 如果找到了播放地址
        if (videoUrl) {
            console.log(`[${siteName}] 成功提取播放地址: ${videoUrl}`);
            
            // 確保URL是完整的
            videoUrl = fixUrl(videoUrl);
            
            return {
                url: videoUrl,
                parse: 0,  // 0表示直鏈
                header: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': baseUrl,
                    'Origin': baseUrl
                }
            };
        } else {
            console.log(`[${siteName}] 無法提取播放地址，返回播放頁面`);
            
            // 返回播放頁面地址（可能需要二次解析）
            return {
                url: playUrl,
                parse: 1,  // 1表示需要解析
                header: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': baseUrl,
                    'Origin': baseUrl
                }
            };
        }
        
    } catch (error) {
        console.error(`[${siteName}] 播放錯誤:`, error);
        return Result.error(`播放錯誤: ${error.message}`);
    }
}

// ========== 播放地址提取函數 ==========

function extractPlayerUrlFromHTML(html, playerId) {
    try {
        console.log(`[${siteName}] 開始解析播放地址...`);
        
        // 方法1：直接從 player_aaaa 對象中提取
        const playerDataMatch = html.match(/var player_aaaa\s*=\s*({[\s\S]*?});/);
        if (playerDataMatch) {
            console.log(`[${siteName}] 找到 player_aaaa 數據`);
            const playerDataStr = playerDataMatch[1];
            
            // 簡單的正則提取URL
            const urlMatch = playerDataStr.match(/"url"\s*:\s*"([^"]+)"/);
            if (urlMatch) {
                let videoUrl = urlMatch[1];
                videoUrl = videoUrl.replace(/\\\//g, '/');
                console.log(`[${siteName}] 從player_aaaa提取到地址: ${videoUrl}`);
                return videoUrl;
            }
        }
        
        // 方法2：直接查找m3u8文件
        const m3u8Pattern = /(https?:\/\/[^\s"']+\.m3u8[^\s"']*)/g;
        const m3u8Matches = html.match(m3u8Pattern);
        
        if (m3u8Matches) {
            for (const url of m3u8Matches) {
                if (url.includes('fentvoss.com')) {
                    console.log(`[${siteName}] 從m3u8正則找到fentvoss地址: ${url}`);
                    return url;
                }
            }
        }
        
        console.log(`[${siteName}] 所有方法都無法提取播放地址`);
        return null;
        
    } catch (error) {
        console.error(`[${siteName}] 提取播放地址失敗:`, error);
        return null;
    }
}

// ========== 核心解析函數 ==========

function extractVideosFromHTML(html) {
    const videos = [];
    
    if (!html || html.length < 100) {
        console.error(`[${siteName}] HTML內容過短，無法解析`);
        return videos;
    }
    
    // 方法1：查找標準的視頻列表項
    // 注意：搜索結果頁面使用 <ul class="stui-vodlist clearfix">
    const itemPattern = /<li class="stui-vodlist__item[^"]*"[^>]*>([\s\S]*?)<\/li>/gi;
    let itemMatch;
    
    let count = 0;
    while ((itemMatch = itemPattern.exec(html)) !== null && count < 50) {
        const itemHtml = itemMatch[0];
        const video = parseVideoItem(itemHtml);
        
        if (video) {
            videos.push(video);
            count++;
        }
    }
    
    console.log(`[${siteName}] 從標準列表提取到 ${videos.length} 個視頻`);
    
    // 如果沒找到，可能是不同的HTML結構
    if (videos.length === 0) {
        // 查找其他可能的結構
        const backupPattern = /<a[^>]*href="\/m\/([^\/]+)\/[^>]*>([\s\S]*?)<\/a>/gi;
        let backupMatch;
        
        while ((backupMatch = backupPattern.exec(html)) !== null && videos.length < 30) {
            const vodPath = backupMatch[1];
            const linkHtml = backupMatch[0];
            
            // 提取標題
            const titleMatch = linkHtml.match(/title="([^"]+)"/) || linkHtml.match(/alt="([^"]+)"/);
            const vodName = titleMatch ? cleanText(titleMatch[1]) : '';
            
            // 提取封面
            const imgMatch = linkHtml.match(/data-original="([^"]+)"|src="([^"]+)"/);
            const vodPic = imgMatch ? (imgMatch[1] || imgMatch[2]) : '';
            
            if (vodName && vodName.length > 1) {
                videos.push({
                    vod_id: vodPath,
                    vod_name: vodName,
                    vod_pic: fixUrl(vodPic),
                    vod_remarks: '',
                    vod_actor: '',
                    vod_director: '',
                    vod_area: '',
                    vod_lang: '',
                    vod_content: '',
                    vod_play_from: '默認',
                    vod_play_url: `第1集$${vodPath}-1-1`,
                    type_name: '短劇'
                });
            }
        }
        
        console.log(`[${siteName}] 從備用方法提取到 ${videos.length} 個視頻`);
    }
    
    return videos;
}

function parseVideoItem(html) {
    try {
        // 提取路徑
        const pathMatch = html.match(/href="\/m\/([^\/]+)\//);
        if (!pathMatch) return null;
        
        const vodPath = pathMatch[1];
        
        // 提取標題
        const titleMatch = html.match(/title="([^"]+)"/) || html.match(/alt="([^"]+)"/);
        const vodName = titleMatch ? cleanText(titleMatch[1]) : '';
        
        if (!vodName || vodName.length < 2) return null;
        
        // 提取封面
        const imgMatch = html.match(/data-original="([^"]+)"|src="([^"]+)"/);
        const vodPic = imgMatch ? (imgMatch[1] || imgMatch[2]) : '';
        
        // 提取備註
        const remarkMatch = html.match(/pic-text[^>]*>([^<]+)<\/span>/);
        let vodRemarks = remarkMatch ? cleanText(remarkMatch[1]) : '';
        
        if (!vodRemarks) {
            const remarkMatch2 = html.match(/<span class="pic-text[^"]*"[^>]*>([^<]+)<\/span>/);
            if (remarkMatch2) {
                vodRemarks = cleanText(remarkMatch2[1]);
            }
        }
        
        return {
            vod_id: vodPath,
            vod_name: vodName,
            vod_pic: fixUrl(vodPic),
            vod_remarks: vodRemarks,
            vod_actor: '',
            vod_director: '',
            vod_area: '',
            vod_lang: '',
            vod_content: '',
            vod_play_from: '默認',
            vod_play_url: `第1集$${vodPath}-1-1`,
            type_name: '短劇'
        };
        
    } catch (error) {
        console.error('解析視頻項目失敗:', error);
        return null;
    }
}

function extractDetailFromHTML(html, vodPath) {
    const video = {
        vod_id: vodPath,
        vod_name: '',
        vod_pic: '',
        vod_content: '',
        vod_actor: '',
        vod_director: '',
        vod_area: '',
        vod_year: '',
        vod_lang: '',
        vod_remarks: '',
        vod_play_from: '',
        vod_play_url: '',
        type_name: ''
    };
    
    try {
        // 1. 提取標題
        const titleMatch = html.match(/<h1 class="title"[^>]*><a[^>]*>([^<]+)<\/a><\/h1>/);
        if (titleMatch) {
            video.vod_name = cleanText(titleMatch[1]);
        } else {
            const titleMatch2 = html.match(/<title>([^<]+)<\/title>/);
            if (titleMatch2) {
                const title = cleanText(titleMatch2[1]);
                video.vod_name = title.split('-')[0].trim();
            }
        }
        
        // 2. 提取封面
        const imgMatch = html.match(/data-original="([^"]+\.(?:jpg|png|webp))"/i);
        if (imgMatch) {
            video.vod_pic = fixUrl(imgMatch[1]);
        } else {
            const imgMatch2 = html.match(/<img[^>]*data-original="([^"]+)"/i);
            if (imgMatch2) {
                video.vod_pic = fixUrl(imgMatch2[1]);
            }
        }
        
        // 3. 提取詳細信息
        const typeMatch = html.match(/类型[：:]<\/span>\s*<a[^>]*>([^<]+)<\/a>/);
        if (typeMatch) video.type_name = cleanText(typeMatch[1]);
        
        const areaMatch = html.match(/地区[：:]<\/span>\s*<a[^>]*>([^<]+)<\/a>/);
        if (areaMatch) video.vod_area = cleanText(areaMatch[1]);
        
        const yearMatch = html.match(/年份[：:]<\/span>\s*<a[^>]*>([^<]+)<\/a>/);
        if (yearMatch) video.vod_year = cleanText(yearMatch[1]);
        
        const actorMatch = html.match(/主演[：:]<\/span>\s*([^<]+)</);
        if (actorMatch) video.vod_actor = cleanText(actorMatch[1]);
        
        const updateMatch = html.match(/更新[：:]<\/span>\s*([^<]+)</);
        if (updateMatch) video.vod_remarks = cleanText(updateMatch[1]);
        
        // 4. 提取播放信息
        const playListMatch = html.match(/<ul class="stui-content__playlist[^>]*>([\s\S]*?)<\/ul>/);
        
        if (playListMatch) {
            const playListHtml = playListMatch[1];
            const playLinks = [];
            const playPattern = /href="\/play\/([^"]+)\/"[^>]*>([^<]+)<\/a>/g;
            let playMatch;
            
            while ((playMatch = playPattern.exec(playListHtml)) !== null) {
                const playId = playMatch[1];
                const episodeName = cleanText(playMatch[2]);
                playLinks.push(`${episodeName}$${playId}`);
            }
            
            if (playLinks.length > 0) {
                video.vod_play_from = '默認';
                video.vod_play_url = playLinks.join('#');
            } else {
                video.vod_play_from = '默認';
                video.vod_play_url = `第1集$${vodPath}-1-1`;
            }
        } else {
            video.vod_play_from = '默認';
            video.vod_play_url = `第1集$${vodPath}-1-1`;
        }
        
        // 5. 提取簡介
        const descSection = html.match(/<div class="stui-content__desc[^>]*>([\s\S]*?)<\/div>/);
        if (descSection) {
            video.vod_content = cleanText(descSection[1].replace(/<[^>]+>/g, ''));
        }
        
    } catch (error) {
        console.error('提取詳情信息失敗:', error);
    }
    
    return video;
}

function extractPaginationInfo(html) {
    const pageInfo = {
        current: 1,
        pagecount: 1,
        total: 0
    };
    
    try {
        // 當前頁
        const currentMatch = html.match(/<li class="active"[^>]*><a[^>]*>(\d+)<\/a><\/li>/);
        if (currentMatch) {
            pageInfo.current = parseInt(currentMatch[1]);
        }
        
        // 所有頁碼鏈接 - 改進正則以匹配更多情況
        const pageLinks = html.match(/<a[^>]*href="[^"]*\/page\/(\d+)\/[^"]*"[^>]*>(\d+)<\/a>/g) || 
                         html.match(/<a[^>]*href="[^"]*----------(\d+)---\/"[^>]*>(\d+)<\/a>/g);
        
        if (pageLinks) {
            let maxPage = pageInfo.current;
            pageLinks.forEach(link => {
                const match = link.match(/>(\d+)</);
                if (match) {
                    const pageNum = parseInt(match[1]);
                    if (pageNum > maxPage) maxPage = pageNum;
                }
            });
            pageInfo.pagecount = maxPage;
        }
        
        // 從分頁控件中提取總頁數
        const pageTextMatch = html.match(/<li class="active visible-xs"><span class="num">(\d+)\/(\d+)<\/span><\/li>/);
        if (pageTextMatch) {
            pageInfo.current = parseInt(pageTextMatch[1]);
            pageInfo.pagecount = parseInt(pageTextMatch[2]);
        }
        
        // 總數
        const totalMatch = html.match(/共\s*<em[^>]*>(\d+)<\/em>\s*條/);
        if (totalMatch) {
            pageInfo.total = parseInt(totalMatch[1]);
        }
        
        console.log(`[${siteName}] 解析分頁信息成功: 當前頁 ${pageInfo.current}, 總頁數 ${pageInfo.pagecount}, 總數 ${pageInfo.total}`);
        
    } catch (error) {
        console.error('提取分頁信息失敗:', error);
    }
    
    return pageInfo;
}

// ========== 工具函數 ==========

function cleanText(text) {
    if (!text) return '';
    return text.replace(/\s+/g, ' ')
               .replace(/[\r\n\t]/g, '')
               .replace(/&nbsp;/g, ' ')
               .replace(/&amp;/g, '&')
               .replace(/&quot;/g, '"')
               .replace(/&lt;/g, '<')
               .replace(/&gt;/g, '>')
               .trim();
}

function fixUrl(url) {
    if (!url || typeof url !== 'string') {
        return '';
    }
    
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    
    if (url.startsWith('//')) {
        return 'https:' + url;
    }
    
    if (url.startsWith('/')) {
        return baseUrl + url;
    }
    
    url = url.replace(/\\\//g, '/');
    return url;
}

function req(url) {
    return new Promise((resolve) => {
        try {
            if (typeof Java !== 'undefined' && Java.req) {
                const result = Java.req(url);
                resolve(result);
            } else if (typeof fetch !== 'undefined') {
                fetch(url, {
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': baseUrl
                    }
                })
                .then(response => response.text())
                .then(body => resolve({ body }))
                .catch(error => resolve({ error: error.message }));
            } else if (typeof XMLHttpRequest !== 'undefined') {
                const xhr = new XMLHttpRequest();
                xhr.open('GET', url, true);
                xhr.setRequestHeader('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
                xhr.setRequestHeader('Referer', baseUrl);
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            resolve({ body: xhr.responseText });
                        } else {
                            resolve({ error: `HTTP ${xhr.status}` });
                        }
                    }
                };
                
                xhr.onerror = function() {
                    resolve({ error: 'Network error' });
                };
                
                xhr.send();
            } else {
                resolve({ error: 'No HTTP client available' });
            }
        } catch (error) {
            resolve({ error: error.message });
        }
    });
}

// ========== Result工具函數 ==========
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
            page: 1,
            pagecount: 1,
            limit: 0,
            total: 0,
            list: []
        };
    }
};

// ========== 導出模塊 ==========
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        init,
        homeContent,
        homeVideoContent,
        categoryContent,
        detailContent,
        searchContent,
        playerContent
    };
}

if (typeof window !== 'undefined') {
    window.init = init;
    window.homeContent = homeContent;
    window.homeVideoContent = homeVideoContent;
    window.categoryContent = categoryContent;
    window.detailContent = detailContent;
    window.searchContent = searchContent;
    window.playerContent = playerContent;
}

console.log(`[${siteName}] 爬蟲加載完成，基址: ${baseUrl}`);
console.log(`[${siteName}] 蘋果CMS模板適配 - 2026年1月20日更新`);