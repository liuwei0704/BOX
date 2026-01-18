/**
 * 華人影視（HRTV）
 * 播放問題已修復 - 2026年1月18日更新
 */

// ========== 基礎配置 ==========
const baseUrl = 'https://www.men.cc';  // 華人影視域名
const siteName = 'HRTV';               // 網站名稱

// ========== 爬蟲接口函數 ==========

async function init(cfg) {
    console.log(`[${siteName}] 爬蟲初始化`);
    return {
        sites: [{
            key: 'hrtv',
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
            { type_id: "1", type_name: "電影" },
            { type_id: "2", type_name: "連續劇" },
            { type_id: "4", type_name: "動漫" },
            { type_id: "31", type_name: "紀錄片" },
            { type_id: "6", type_name: "喜劇" },
            { type_id: "7", type_name: "愛情" },
            { type_id: "9", type_name: "動作" },
            { type_id: "10", type_name: "科幻" },
            { type_id: "8", type_name: "恐怖" },
            { type_id: "11", type_name: "劇情" }
        ],
        filters: {
            "1": [
                {
                    key: "area",
                    name: "地區",
                    value: [
                        { n: "全部", v: "" },
                        { n: "大陸", v: "大陸" },
                        { n: "香港", v: "香港" },
                        { n: "台灣", v: "台灣" },
                        { n: "美國", v: "美國" },
                        { n: "日本", v: "日本" },
                        { n: "韓國", v: "韓國" }
                    ]
                },
                {
                    key: "year",
                    name: "年份",
                    value: [
                        { n: "全部", v: "" },
                        { n: "2025", v: "2025" },
                        { n: "2024", v: "2024" },
                        { n: "2023", v: "2023" }
                    ]
                }
            ]
        }
    };
}

async function homeVideoContent() {
    try {
        const url = `${baseUrl}/index.php/vod/show/id/1.html`;
        const res = await req(url);
        
        if (res.error) {
            return Result.error(`獲取失敗: ${res.error}`);
        }
        
        const html = res.body;
        const videos = extractVideosFromHTML(html);
        
        return Result.list(videos.slice(0, 20));
        
    } catch (error) {
        return Result.error(`首頁錯誤: ${error.message}`);
    }
}

async function categoryContent(tid, pg, filter, extend) {
    try {
        const page = pg || 1;
        let url = '';
        
        if (extend && Object.keys(extend).length > 0) {
            const params = [];
            params.push(`id/${tid}`);
            
            if (extend.area) {
                params.push(`area/${encodeURIComponent(extend.area)}`);
            }
            
            if (extend.year) {
                params.push(`year/${extend.year}`);
            }
            
            const sortBy = extend.sort || 'time';
            params.push(`by/${sortBy}`);
            params.push(`page/${page}`);
            
            url = `${baseUrl}/index.php/vod/show/${params.join('/')}.html`;
        } else {
            if (page === 1) {
                url = `${baseUrl}/index.php/vod/type/id/${tid}.html`;
            } else {
                url = `${baseUrl}/index.php/vod/type/id/${tid}/page/${page}.html`;
            }
        }
        
        const res = await req(url);
        if (res.error) {
            return Result.error(`請求失敗: ${res.error}`);
        }
        
        const html = res.body;
        const videos = extractVideosFromHTML(html);
        const pageInfo = extractPaginationInfo(html);
        
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
        return Result.error(`分類錯誤: ${error.message}`);
    }
}

async function detailContent(ids) {
    try {
        if (!ids || !ids[0]) {
            return Result.error('缺少視頻ID');
        }
        
        const vodId = ids[0];
        const url = `${baseUrl}/index.php/vod/detail/id/${vodId}.html`;
        
        console.log(`[${siteName}] 獲取詳情: ${url}`);
        
        const res = await req(url);
        if (res.error) {
            return Result.error(`詳情失敗: ${res.error}`);
        }
        
        const html = res.body;
        const video = extractDetailFromHTML(html, vodId);
        
        if (!video.vod_name) {
            console.error(`提取詳情失敗: vodId=${vodId}`);
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
        
        if (page === 1) {
            url = `${baseUrl}/index.php/vod/search/wd/${encodedKey}.html`;
        } else {
            url = `${baseUrl}/index.php/vod/search/wd/${encodedKey}/page/${page}.html`;
        }
        
        const res = await req(url);
        if (res.error) {
            return Result.error(`搜索失敗: ${res.error}`);
        }
        
        const html = res.body;
        const videos = extractVideosFromHTML(html);
        const pageInfo = extractPaginationInfo(html);
        
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

/**
 * 播放內容 - 支援多集劇集（已修復播放問題）
 */
async function playerContent(flag, id, vipFlags) {
    try {
        console.log(`[${siteName}] 播放請求: flag=${flag}, id=${id}, vipFlags=${vipFlags}`);
        
        // 解析ID格式：vodId-sid-nid 或 vodId-nid
        let vodId, sid = "1", nid = "1";
        
        if (id.includes('-')) {
            const parts = id.split('-');
            if (parts.length === 3) {
                // 格式: vodId-sid-nid
                vodId = parts[0];
                sid = parts[1];
                nid = parts[2];
            } else if (parts.length === 2) {
                // 格式: vodId-nid
                vodId = parts[0];
                nid = parts[1];
            } else {
                // 格式: vodId-episodeIndex
                vodId = parts[0];
                nid = parts[1] || "1";
            }
        } else {
            vodId = id;
        }
        
        // 構造播放頁面URL
        const playUrl = `${baseUrl}/index.php/vod/play/id/${vodId}/sid/${sid}/nid/${nid}.html`;
        console.log(`[${siteName}] 播放頁面URL: ${playUrl}`);
        
        // 直接訪問播放頁面
        const playRes = await req(playUrl);
        if (playRes.error) {
            return Result.error(`獲取播放頁失敗: ${playRes.error}`);
        }
        
        const playHtml = playRes.body;
        console.log(`[${siteName}] 播放頁面HTML長度: ${playHtml.length} 字符`);
        
        // 從HTML中提取播放地址 - 專為華人影視優化
        let videoUrl = extractPlayerUrlFromHTML(playHtml);
        
        if (!videoUrl) {
            console.log(`[${siteName}] 無法提取播放地址，嘗試備用方法`);
            videoUrl = extractVideoUrlFromJavaScript(playHtml);
        }
        
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

// ========== 播放地址提取函數（已修復）==========

/**
 * 從HTML提取播放地址（專為華人影視優化）
 */
function extractPlayerUrlFromHTML(html) {
    try {
        console.log(`[${siteName}] 開始解析播放地址...`);
        
        // 方法1：直接從player_aaaa變量中提取（華人影視專用）
        const playerVarMatch = html.match(/var\s+player_aaaa\s*=\s*({[\s\S]*?});/);
        if (playerVarMatch) {
            console.log(`[${siteName}] 找到player_aaaa變量，嘗試提取...`);
            
            const playerDataStr = playerVarMatch[1];
            
            // 嘗試解析JSON
            try {
                // 先清理字符串
                let cleanStr = playerDataStr
                    .replace(/\n/g, '')
                    .replace(/\t/g, '')
                    .replace(/\\\//g, '/');
                
                // 解析JSON
                const playerData = JSON.parse(cleanStr);
                
                if (playerData && playerData.url) {
                    const videoUrl = playerData.url;
                    console.log(`[${siteName}] 從player_aaaa JSON提取到地址: ${videoUrl}`);
                    return videoUrl;
                }
            } catch (jsonError) {
                console.warn(`[${siteName}] JSON解析失敗，嘗試其他方法:`, jsonError.message);
            }
            
            // 如果JSON解析失敗，嘗試正則提取
            const urlMatch = playerDataStr.match(/"url"\s*:\s*"([^"]+)"/);
            if (urlMatch) {
                let videoUrl = urlMatch[1];
                videoUrl = videoUrl.replace(/\\\//g, '/');
                console.log(`[${siteName}] 從player_aaaa正則提取到地址: ${videoUrl}`);
                return videoUrl;
            }
        }
        
        // 方法2：查找url字段
        const urlPatterns = [
            /"url"\s*:\s*"([^"]+)"/,
            /'url'\s*:\s*'([^']+)'/,
            /url\s*:\s*"([^"]+)"/,
            /url\s*:\s*'([^']+)'/,
            /var\s+url\s*=\s*"([^"]+)"/,
            /var\s+url\s*=\s*'([^']+)'/
        ];
        
        for (const pattern of urlPatterns) {
            const matches = html.match(pattern);
            if (matches) {
                let videoUrl = matches[1];
                videoUrl = videoUrl.replace(/\\\//g, '/');
                
                // 檢查是否是m3u8地址
                if (videoUrl.includes('.m3u8')) {
                    console.log(`[${siteName}] 從正則匹配找到m3u8地址: ${videoUrl}`);
                    return videoUrl;
                }
            }
        }
        
        // 方法3：查找m3u8文件
        const m3u8Pattern = /(https?:\/\/[^\s"']+\.m3u8[^\s"']*)/g;
        const m3u8Matches = html.match(m3u8Pattern);
        
        if (m3u8Matches) {
            for (const url of m3u8Matches) {
                // 過濾掉廣告和統計鏈接
                if (!url.includes('google') && !url.includes('baidu') && 
                    !url.includes('analytics') && !url.includes('ad.') &&
                    !url.includes('stat.') && !url.includes('track')) {
                    console.log(`[${siteName}] 從m3u8正則找到地址: ${url}`);
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

/**
 * 從JavaScript提取視頻地址（備用方法）
 */
function extractVideoUrlFromJavaScript(html) {
    try {
        // 查找所有JavaScript代碼塊
        const scriptPattern = /<script[^>]*>([\s\S]*?)<\/script>/gi;
        const scripts = [];
        let match;
        
        while ((match = scriptPattern.exec(html)) !== null) {
            scripts.push(match[1]);
        }
        
        // 在每個JavaScript塊中查找播放地址
        for (const script of scripts) {
            // 常見的播放地址模式
            const patterns = [
                // m3u8地址
                /(https?:\/\/[^"'`{}]+\.m3u8[^"'`{}]*)/gi,
                // 通用視頻地址
                /url\s*[=:]\s*["']([^"']+)["']/i,
                /src\s*[=:]\s*["']([^"']+)["']/i,
                /file\s*[=:]\s*["']([^"']+)["']/i,
                /video_url\s*[=:]\s*["']([^"']+)["']/i,
                /videoUrl\s*[=:]\s*["']([^"']+)["']/i
            ];
            
            for (const pattern of patterns) {
                const matches = script.match(pattern);
                if (matches) {
                    let url = matches[1] || matches[0];
                    url = url.trim();
                    
                    // 解碼轉義字符
                    url = url.replace(/\\\//g, '/');
                    
                    // 過濾無效的URL
                    if (url && !url.includes('//comment') && !url.includes('//ad.') && 
                        (url.includes('http') || url.startsWith('//'))) {
                        
                        console.log(`[${siteName}] 從JavaScript找到地址: ${url}`);
                        
                        // 檢查是否是視頻地址
                        if (url.includes('.m3u8') || url.includes('.mp4') || 
                            url.includes('.flv') || url.includes('video') ||
                            url.includes('player') || url.includes('play')) {
                            return url;
                        }
                    }
                }
            }
        }
        
        return null;
    } catch (error) {
        console.error('從JavaScript提取地址失敗:', error);
        return null;
    }
}

/**
 * 從iframe提取視頻地址
 */
function extractVideoUrlFromIframe(html) {
    try {
        // 查找iframe標籤
        const iframeRegex = /<iframe[^>]*src=["']([^"']+)["'][^>]*>/gi;
        const match = iframeRegex.exec(html);
        
        if (match) {
            let iframeSrc = match[1];
            
            // 修復URL
            iframeSrc = fixUrl(iframeSrc);
            
            console.log(`[${siteName}] 找到iframe地址: ${iframeSrc}`);
            
            // 檢查是否是視頻地址
            if (iframeSrc.includes('.m3u8') || iframeSrc.includes('.mp4') || 
                iframeSrc.includes('.flv') || iframeSrc.includes('video')) {
                return iframeSrc;
            }
            
            // 如果是常見的視頻播放器域名
            const videoDomains = [
                'player.', 'play.', 'video.', 'vod.', 'cloud.', 
                'cdn.', 'stream.', 'm3u8.', 'hls.'
            ];
            
            for (const domain of videoDomains) {
                if (iframeSrc.includes(domain)) {
                    return iframeSrc;
                }
            }
        }
        
        return null;
    } catch (error) {
        console.error('提取iframe地址失敗:', error);
        return null;
    }
}

/**
 * 從embed標籤提取視頻地址
 */
function extractVideoUrlFromEmbed(html) {
    try {
        // 查找embed或object標籤
        const embedRegex = /<(embed|object)[^>]*>[\s\S]*?<param[^>]*value=["']([^"']+)["'][^>]*>/gi;
        const match = embedRegex.exec(html);
        
        if (match) {
            let url = match[2];
            url = fixUrl(url);
            
            if (url.includes('.m3u8') || url.includes('.mp4') || url.includes('.flv')) {
                console.log(`[${siteName}] 從embed找到地址: ${url}`);
                return url;
            }
        }
        
        return null;
    } catch (error) {
        console.error('提取embed地址失敗:', error);
        return null;
    }
}

// ========== 核心解析函數 ==========

/**
 * 從HTML提取視頻列表
 */
function extractVideosFromHTML(html) {
    const videos = [];
    
    // 正則表達式提取視頻項目
    const itemPattern = /<li class="hl-list-item[^"]*"[^>]*>([\s\S]*?)<\/li>/gi;
    let itemMatch;
    
    while ((itemMatch = itemPattern.exec(html)) !== null) {
        const itemHtml = itemMatch[0];
        const video = parseVideoItem(itemHtml);
        
        if (video) {
            videos.push(video);
        }
    }
    
    return videos;
}

/**
 * 解析單個視頻項目
 */
function parseVideoItem(html) {
    try {
        // 提取ID
        const idMatch = html.match(/\/id\/(\d+)\.html/);
        if (!idMatch) return null;
        
        const vodId = idMatch[1];
        
        // 提取標題
        const titleMatch = html.match(/title="([^"]+)"/);
        const vodName = titleMatch ? cleanText(titleMatch[1]) : '';
        
        // 提取封面
        const imgMatch = html.match(/data-original="([^"]+)"|src="([^"]+)"|data-src="([^"]+)"/);
        const vodPic = imgMatch ? (imgMatch[1] || imgMatch[2] || imgMatch[3]) : '';
        
        // 提取備註
        const remarkMatch = html.match(/class="[^"]*remarks[^"]*"[^>]*>([^<]+)<\/span>/);
        const vodRemarks = remarkMatch ? cleanText(remarkMatch[1]) : '';
        
        // 提取描述信息
        const descMatch = html.match(/class="hl-item-sub[^"]*"[^>]*>([\s\S]*?)<\/div>/);
        let vodActor = '';
        
        if (descMatch) {
            const descHtml = descMatch[1];
            const scoreMatch = descHtml.match(/<span[^>]*score[^"]*"[^>]*>([\d.]+)<\/span>/);
            if (scoreMatch) {
                vodActor = descHtml.replace(scoreMatch[0], '').trim();
            } else {
                vodActor = descHtml;
            }
            vodActor = vodActor.replace(/<[^>]+>/g, '').trim();
        }
        
        // 默認播放信息（在詳情頁會重新解析）
        const playFrom = '暴風資源';
        const playUrl = `第1集$${vodId}-1-1`;
        
        return {
            vod_id: vodId,
            vod_name: vodName,
            vod_pic: fixUrl(vodPic),
            vod_remarks: vodRemarks,
            vod_actor: vodActor.substring(0, 100),
            vod_director: '',
            vod_area: '',
            vod_lang: '',
            vod_content: '',
            vod_play_from: playFrom,
            vod_play_url: playUrl,
            type_name: '電影'
        };
        
    } catch (error) {
        console.error('解析視頻項目失敗:', error);
        return null;
    }
}

/**
 * 從HTML提取詳情信息（支援多集劇集）
 */
function extractDetailFromHTML(html, vodId) {
    const video = {
        vod_id: vodId,
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
        const titleMatch = html.match(/<h2 class="hl-dc-title[^>]*>([^<]+)<\/h2>/);
        if (titleMatch) {
            video.vod_name = cleanText(titleMatch[1]);
        } else {
            const metaTitleMatch = html.match(/<title>《([^》]+)》/);
            if (metaTitleMatch) {
                video.vod_name = cleanText(metaTitleMatch[1]);
            }
        }
        
        // 2. 提取封面
        const imgMatch = html.match(/data-original="([^"]+\.jpg)"/);
        if (imgMatch) {
            video.vod_pic = fixUrl(imgMatch[1]);
        }
        
        // 3. 提取詳細信息
        const dataMatch = html.match(/<div class="hl-vod-data[^>]*>([\s\S]*?)<\/div>/);
        if (dataMatch) {
            const dataHtml = dataMatch[0];
            
            // 提取狀態
            const statusMatch = dataHtml.match(/<span class="[^"]*hl-text-conch[^"]*"[^>]*>([^<]+)<\/span>/);
            if (statusMatch) {
                video.vod_remarks = cleanText(statusMatch[1]);
            }
            
            // 提取演員
            const actorMatch = dataHtml.match(/主演：<\/em>([\s\S]*?)<\/li>/);
            if (actorMatch) {
                let actorHtml = actorMatch[1];
                actorHtml = actorHtml.replace(/<[^>]+>/g, '');
                actorHtml = actorHtml.replace(/&amp;/g, '&');
                video.vod_actor = cleanText(actorHtml);
            }
            
            // 提取導演
            const directorMatch = dataHtml.match(/導演：<\/em>([\s\S]*?)<\/li>/);
            if (directorMatch) {
                let directorHtml = directorMatch[1];
                directorHtml = directorHtml.replace(/<[^>]+>/g, '');
                video.vod_director = cleanText(directorHtml);
            }
            
            // 提取年份
            const yearMatch = dataHtml.match(/年份：<\/em>([^<]+)<\/li>/);
            if (yearMatch) {
                video.vod_year = cleanText(yearMatch[1]);
            }
            
            // 提取地區
            const areaMatch = dataHtml.match(/地區：<\/em>([^<]+)<\/li>/);
            if (areaMatch) {
                video.vod_area = cleanText(areaMatch[1]);
            }
            
            // 提取類型
            const typeMatch = dataHtml.match(/類型：<\/em>([\s\S]*?)<\/li>/);
            if (typeMatch) {
                let typeHtml = typeMatch[1];
                typeHtml = typeHtml.replace(/<[^>]+>/g, '');
                // 只提取第一個類型
                const typeParts = typeHtml.split('/');
                video.type_name = cleanText(typeParts[0]);
            }
            
            // 提取語言
            const langMatch = dataHtml.match(/語言：<\/em>([^<]+)<\/li>/);
            if (langMatch) {
                video.vod_lang = cleanText(langMatch[1]);
            }
            
            // 提取簡介
            const descMatch = dataHtml.match(/簡介：<\/em>([^<]+)<\/li>/);
            if (descMatch) {
                video.vod_content = cleanText(descMatch[1]);
            } else {
                const contentMatch = html.match(/<span class="hl-content-text"[^>]*><em>([^<]+)<\/em>/);
                if (contentMatch) {
                    video.vod_content = cleanText(contentMatch[1]);
                }
            }
        }
        
        // 4. 提取播放信息（重點：支援多集劇集）
        const playInfo = extractPlayInfoFromHTML(html, vodId);
        video.vod_play_from = playInfo.playFrom;
        video.vod_play_url = playInfo.playUrl;
        
        // 5. 如果沒有提取到類型，默認為動漫
        if (!video.type_name) {
            video.type_name = '動漫';
        }
        
        console.log(`[${siteName}] 提取到的視頻詳情:`, {
            name: video.vod_name,
            actor: video.vod_actor.substring(0, 50) + '...',
            year: video.vod_year,
            area: video.vod_area,
            episodes: playInfo.episodeCount
        });
        
    } catch (error) {
        console.error('提取詳情信息失敗:', error);
    }
    
    return video;
}

/**
 * 從HTML提取播放信息（支援多集劇集）
 */
function extractPlayInfoFromHTML(html, vodId) {
    let playFrom = '暴風資源';
    let playUrl = '';
    
    try {
        // 提取播放來源
        const sourceMatch = html.match(/<span class="hl-from-bfzym3u8[^>]*>([^<]+)<\/span>/);
        if (sourceMatch) {
            playFrom = cleanText(sourceMatch[1]);
        }
        
        // 提取播放列表
        const playListMatch = html.match(/<ul class="hl-plays-list[^>]*>([\s\S]*?)<\/ul>/);
        if (playListMatch) {
            const playListHtml = playListMatch[1];
            
            // 提取所有劇集鏈接
            const episodePattern = /href="\/index\.php\/vod\/play\/id\/\d+\/sid\/(\d+)\/nid\/(\d+)\.html"[^>]*>([^<]+)<\/a>/g;
            const episodes = [];
            let episodeMatch;
            let episodeCount = 0;
            
            while ((episodeMatch = episodePattern.exec(playListHtml)) !== null) {
                const sid = episodeMatch[1];
                const nid = episodeMatch[2];
                const episodeName = cleanText(episodeMatch[3]);
                
                // 構建劇集格式：劇集名$vodId-sid-nid
                episodes.push(`${episodeName}$${vodId}-${sid}-${nid}`);
                episodeCount++;
            }
            
            // 如果有劇集，構建播放URL
            if (episodes.length > 0) {
                playUrl = episodes.join('#');
                console.log(`[${siteName}] 找到${episodeCount}個劇集`);
            } else {
                // 默認只有一集
                playUrl = `第1集$${vodId}-1-1`;
            }
        } else {
            // 如果沒有播放列表，默認只有一集
            playUrl = `第1集$${vodId}-1-1`;
        }
        
    } catch (error) {
        console.error('提取播放信息失敗:', error);
        playFrom = '暴風資源';
        playUrl = `第1集$${vodId}-1-1`;
    }
    
    return {
        playFrom: playFrom,
        playUrl: playUrl
    };
}

/**
 * 提取分頁信息
 */
function extractPaginationInfo(html) {
    const pageInfo = {
        current: 1,
        pagecount: 1,
        total: 0
    };
    
    try {
        const currentMatch = html.match(/class="[^"]*active[^"]*"[^>]*>(\d+)<\/a>/);
        if (currentMatch) {
            pageInfo.current = parseInt(currentMatch[1]);
        }
        
        const pageLinks = html.match(/<a[^>]*href="[^"]*\/page\/(\d+)\.html"[^>]*>/g);
        if (pageLinks) {
            let maxPage = pageInfo.current;
            pageLinks.forEach(link => {
                const match = link.match(/\/page\/(\d+)\.html/);
                if (match) {
                    const pageNum = parseInt(match[1]);
                    if (pageNum > maxPage) maxPage = pageNum;
                }
            });
            pageInfo.pagecount = maxPage;
        }
        
        const totalMatch = html.match(/共[^<]*<em[^>]*>(\d+)<\/em>[^<]*個/);
        if (totalMatch) {
            pageInfo.total = parseInt(totalMatch[1]);
        }
        
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
               .trim();
}

function fixUrl(url) {
    if (!url || typeof url !== 'string') {
        console.warn(`[${siteName}] fixUrl收到無效URL:`, url);
        return '';
    }
    
    // 如果已經是完整URL，直接返回
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    
    if (url.startsWith('//')) {
        return 'https:' + url;
    }
    
    if (url.startsWith('/')) {
        return baseUrl + url;
    }
    
    // 解碼轉義字符
    url = url.replace(/\\\//g, '/');
    
    return url;
}

function req(url) {
    return new Promise((resolve) => {
        try {
            // 蜂蜜影視環境使用Java.req
            if (typeof Java !== 'undefined' && Java.req) {
                const result = Java.req(url);
                resolve(result);
            } 
            // 瀏覽器環境使用fetch
            else if (typeof fetch !== 'undefined') {
                fetch(url, {
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': baseUrl
                    }
                })
                .then(response => response.text())
                .then(body => resolve({ body }))
                .catch(error => resolve({ error: error.message }));
            }
            // XMLHttpRequest備用
            else if (typeof XMLHttpRequest !== 'undefined') {
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
            }
            // 都不支持
            else {
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
console.log(`[${siteName}] 播放功能已修復 - 2026年1月18日更新`);