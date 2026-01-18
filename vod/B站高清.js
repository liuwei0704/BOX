/**
 * 哔哩哔哩 - 猫影视/TVBox JS爬虫格式
 * 调用壳子超级解析功能
 * 支持沙雕动画搜索 - 已修复无图问题
 */

class Spider extends BaseSpider {
    
    constructor() {
        super();
        this.host = 'https://www.bilibili.com';
        
        // 基础请求头
        this.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': ''  // 留空，用户可自行配置
        };
        
        // 分类配置 - 新增沙雕动画分类
        this.classes = [
            { type_id: '沙雕仙逆', type_name: '沙雕仙逆' },
            { type_id: '沙雕动画', type_name: '沙雕动画' },
            { type_id: '搞笑动画', type_name: '搞笑动画' },
            { type_id: '全部', type_name: '全部' },
            { type_id: '1', type_name: '番剧' },
            { type_id: '4', type_name: '国创' },
            { type_id: '2', type_name: '电影' },
            { type_id: '5', type_name: '电视剧' },
            { type_id: '3', type_name: '纪录片' },
            { type_id: '7', type_name: '综艺' },
            { type_id: '追番', type_name: '追番' },
            { type_id: '追剧', type_name: '追剧' },
            { type_id: '时间表', type_name: '时间表' }
        ];
        
        // 筛选配置
        this.filters = {
            '全部': [
                {
                    key: 'tid',
                    name: '分类',
                    value: [
                        { n: '沙雕仙逆', v: '沙雕仙逆' },
                        { n: '番剧', v: '1' },
                        { n: '国创', v: '4' },
                        { n: '电影', v: '2' },
                        { n: '电视剧', v: '5' },
                        { n: '记录片', v: '3' },
                        { n: '综艺', v: '7' }
                    ]
                },
                {
                    key: 'order',
                    name: '排序',
                    value: [
                        { n: '播放数量', v: '2' },
                        { n: '更新时间', v: '0' },
                        { n: '最高评分', v: '4' },
                        { n: '弹幕数量', v: '1' },
                        { n: '追看人数', v: '3' },
                        { n: '开播时间', v: '5' },
                        { n: '上映时间', v: '6' }
                    ]
                },
                {
                    key: 'season_status',
                    name: '付费',
                    value: [
                        { n: '全部', v: '-1' },
                        { n: '免费', v: '1' },
                        { n: '付费', v: '2%2C6' },
                        { n: '大会员', v: '4%2C6' }
                    ]
                }
            ],
            '时间表': [
                {
                    key: 'tid',
                    name: '分类',
                    value: [
                        { n: '番剧', v: '1' },
                        { n: '国创', v: '4' }
                    ]
                }
            ]
        };
        
        // 自定义搜索关键词配置
        this.customSearchKeywords = {
            '沙雕仙逆': ['仙逆', '沙雕仙逆', '仙逆搞笑', '仙逆改编', '王林搞笑'],
            '沙雕动画': ['沙雕动画', '搞笑动画', '动漫搞笑', '动漫沙雕', '动画搞笑', '沙雕'],
            '搞笑动画': ['搞笑动漫', '搞笑番剧', '喜剧动画', '幽默动画', '爆笑动画']
        };
        
        // ============ 线路配置 ============
        this.playLines = [
            { name: '壳子超级解析', id: 'super_parse', type: 'parse', priority: 10 },
            { name: '官方直连(需Cookie)', id: 'official', type: 'direct', priority: 5 },
            { name: 'B站分享链接', id: 'share', type: 'share', priority: 3 }
        ];
        
        // 线路状态管理（记忆功能）
        this.lineStats = {};
        
        // 初始化线路统计
        this.initLineStats();
    }
    
    init(extend = '') {
        // 尝试从extend中恢复线路状态
        if (extend) {
            try {
                const config = JSON.parse(extend);
                if (config.lineStats) {
                    this.lineStats = config.lineStats;
                }
            } catch (e) {
                // 解析失败，使用默认配置
            }
        }
        return '';
    }
    
    getName() {
        return '哔哩哔哩(沙雕动画版)';
    }
    
    isVideoFormat(url) {
        return true;
    }
    
    manualVideoCheck() {
        return false;
    }
    
    destroy() {
        // 清理资源
    }
    
    homeContent(filter) {
        const result = {
            class: this.classes,
            filters: this.filters
        };
        
        return result;
    }
    
    async homeVideoContent() {
        try {
            const videos = [];
            
            // 获取番剧排行榜
            const bangumiList = await this.getRankList(1, 1);
            videos.push(...bangumiList.slice(0, 5));
            
            // 获取其他分类排行榜
            const categories = [4, 2, 5, 3, 7];
            for (const cat of categories) {
                const list = await this.getRankList(cat, 1);
                videos.push(...list.slice(0, 3));
            }
            
            // 过滤预告片
            const filteredVideos = videos.filter(item => 
                !item.vod_name?.includes('预告') && 
                !item.vod_remarks?.includes('预告')
            );
            
            return { list: filteredVideos };
            
        } catch (error) {
            console.error(`homeVideoContent error: ${error.message}`);
            return { list: [] };
        }
    }
    
    async categoryContent(tid, pg, filter, extend) {
        try {
            const page = parseInt(pg) || 1;
            let videos = [];
            
            // 解析筛选参数
            let filterObj = {};
            if (extend) {
                if (typeof extend === 'string') {
                    try {
                        filterObj = JSON.parse(extend);
                    } catch (e) {
                        // 如果不是JSON，尝试解析为key=value格式
                        extend.split('&').forEach(item => {
                            const [key, value] = item.split('=');
                            if (key && value) {
                                filterObj[key] = value;
                            }
                        });
                    }
                } else if (typeof extend === 'object') {
                    filterObj = extend;
                }
            }
            
            // 处理自定义搜索分类
            if (this.customSearchKeywords[tid]) {
                // 获取该分类的关键词
                const keywords = this.customSearchKeywords[tid];
                // 使用第一个关键词进行搜索
                videos = await this.searchCustomContent(keywords[0], page);
            } else if (tid === '1') { // 番剧
                videos = await this.getRankList(1, page);
            } else if (['2', '3', '4', '5', '7'].includes(tid)) {
                videos = await this.getRankList(parseInt(tid), page);
            } else if (tid === '全部') {
                const seasonType = filterObj.tid || '1';
                const order = filterObj.order || '2';
                const seasonStatus = filterObj.season_status || '-1';
                videos = await this.getAllList(seasonType, page, order, seasonStatus);
            } else if (tid === '时间表') {
                const seasonType = filterObj.tid || '1';
                videos = await this.getTimeline(seasonType);
            }
            
            // 过滤预告片
            const filteredVideos = videos.filter(item => 
                !item.vod_name?.includes('预告') && 
                !item.vod_remarks?.includes('预告')
            );
            
            return {
                list: filteredVideos,
                page: page,
                pagecount: 9999,
                limit: 20,
                total: 999999
            };
            
        } catch (error) {
            console.error(`categoryContent error: ${error.message}`);
            return {
                list: [],
                page: pg,
                pagecount: 0,
                limit: 20,
                total: 0
            };
        }
    }
    
    async detailContent(ids) {
        try {
            const id = ids[0];
            
            // 检查ID类型（BV号/av号还是season_id）
            if (id.startsWith('BV') || id.startsWith('av')) {
                // 处理视频ID（用户创作的沙雕视频）
                return await this.getVideoDetail(id);
            } else {
                // 处理番剧/影视ID
                return await this.getSeasonDetail(id);
            }
            
        } catch (error) {
            console.error(`detailContent error: ${error.message}`);
            return { list: [] };
        }
    }
    
    async searchContent(key, quick, pg = '1') {
        try {
            const page = parseInt(pg) || 1;
            const encodedKeyword = encodeURIComponent(key);
            
            const videos = [];
            
            // 主要搜索视频类型（修复图片问题）
            const searchTypes = ['video']; // 主要搜索video类型，获取完整的图片信息
            
            for (const searchType of searchTypes) {
                try {
                    const url = `https://api.bilibili.com/x/web-interface/search/type?search_type=${searchType}&keyword=${encodedKeyword}&page=${page}`;
                    const response = await fetch(url, { headers: this.headers });
                    
                    if (!response.ok) continue;
                    
                    const data = await response.json();
                    
                    if (data.code === 0 && data.data?.result) {
                        data.data.result.forEach(vod => {
                            if (!vod.title?.includes('预告')) {
                                // 获取视频ID
                                let videoId = '';
                                if (vod.bvid) {
                                    videoId = vod.bvid;
                                } else if (vod.aid) {
                                    videoId = 'av' + vod.aid;
                                }
                                
                                if (videoId) {
                                    // 修复图片问题：优先使用pic字段，它有完整的URL
                                    const coverUrl = this.fixCoverUrl(vod.pic || vod.cover || '');
                                    
                                    videos.push({
                                        vod_id: videoId,
                                        vod_name: this.cleanHtml(vod.title || '').trim(),
                                        vod_pic: coverUrl,
                                        vod_remarks: this.cleanHtml(vod.description || vod.desc || '').substring(0, 30) + '...'
                                    });
                                }
                            }
                        });
                    }
                } catch (e) {
                    console.error(`搜索类型 ${searchType} 失败:`, e.message);
                }
            }
            
            // 如果没有搜索结果，尝试搜索番剧
            if (videos.length === 0) {
                const bangumiVideos = await this.searchBangumiContent(key, page);
                videos.push(...bangumiVideos);
            }
            
            return {
                list: videos,
                page: page,
                pagecount: 10,
                limit: 20,
                total: videos.length
            };
            
        } catch (error) {
            console.error(`searchContent error: ${error.message}`);
            return {
                list: [],
                page: pg,
                pagecount: 0,
                limit: 20,
                total: 0
            };
        }
    }
    
    // 专门搜索番剧内容
    async searchBangumiContent(keyword, page = 1) {
        try {
            const encodedKeyword = encodeURIComponent(keyword);
            const videos = [];
            
            const url1 = `https://api.bilibili.com/x/web-interface/search/type?search_type=media_bangumi&keyword=${encodedKeyword}&page=${page}`;
            const url2 = `https://api.bilibili.com/x/web-interface/search/type?search_type=media_ft&keyword=${encodedKeyword}&page=${page}`;
            
            // 搜索番剧
            try {
                const response1 = await fetch(url1, { headers: this.headers });
                if (response1.ok) {
                    const data1 = await response1.json();
                    if (data1.code === 0 && data1.data?.result) {
                        data1.data.result.forEach(vod => {
                            if (!vod.title?.includes('预告')) {
                                videos.push({
                                    vod_id: String(vod.season_id || '').trim(),
                                    vod_name: this.cleanHtml(vod.title || '').trim(),
                                    vod_pic: this.fixCoverUrl(vod.cover || ''),
                                    vod_remarks: this.cleanHtml(vod.index_show || '').trim()
                                });
                            }
                        });
                    }
                }
            } catch (e) {
                console.error('番剧搜索失败:', e.message);
            }
            
            // 搜索影视
            try {
                const response2 = await fetch(url2, { headers: this.headers });
                if (response2.ok) {
                    const data2 = await response2.json();
                    if (data2.code === 0 && data2.data?.result) {
                        data2.data.result.forEach(vod => {
                            if (!vod.title?.includes('预告')) {
                                videos.push({
                                    vod_id: String(vod.season_id || '').trim(),
                                    vod_name: this.cleanHtml(vod.title || '').trim(),
                                    vod_pic: this.fixCoverUrl(vod.cover || ''),
                                    vod_remarks: this.cleanHtml(vod.index_show || '').trim()
                                });
                            }
                        });
                    }
                }
            } catch (e) {
                console.error('影视搜索失败:', e.message);
            }
            
            return videos;
            
        } catch (error) {
            console.error(`searchBangumiContent error: ${error.message}`);
            return [];
        }
    }
    
    async playerContent(flag, id, vipFlags) {
        try {
            // 根据线路类型返回不同的播放参数
            if (flag === '壳子超级解析') {
                // 调用壳子超级解析
                return {
                    parse: 1,           // 必须为1，表示需要解析
                    jx: 1,              // 必须为1，启用解析
                    play_parse: true,   // 启用播放解析
                    parse_type: '壳子超级解析',
                    parse_source: '哔哩哔哩',
                    url: id,            // B站分享链接
                    header: JSON.stringify({
                        'User-Agent': this.headers['User-Agent'],
                        'Referer': 'https://www.bilibili.com',
                        'Origin': 'https://www.bilibili.com'
                    })
                };
                
            } else if (flag === '官方直连(需Cookie)') {
                // 解析官方ID格式
                const parts = id.split('_');
                if (parts.length >= 3) {
                    const season_id = parts[0];
                    const epId = parts[1];
                    const cid = parts[2];
                    
                    // 返回官方播放地址（需要壳子支持Cookie）
                    return {
                        parse: 0,
                        url: `https://api.bilibili.com/pgc/player/web/playurl?cid=${cid}&ep_id=${epId}&qn=80&fnval=1&fnver=0&fourk=0`,
                        header: JSON.stringify(this.headers)
                    };
                }
                // 如果不是官方ID格式，回退到壳子解析
                return {
                    parse: 1,
                    jx: 1,
                    play_parse: true,
                    parse_type: '壳子超级解析',
                    parse_source: '哔哩哔哩',
                    url: id,
                    header: JSON.stringify(this.headers)
                };
                
            } else if (flag === 'B站分享链接') {
                // 直接返回分享链接，让壳子处理
                return {
                    parse: 1,
                    jx: 1,
                    play_parse: true,
                    parse_type: '壳子自动解析',
                    parse_source: '哔哩哔哩',
                    url: id,
                    header: JSON.stringify({
                        'User-Agent': this.headers['User-Agent'],
                        'Referer': 'https://www.bilibili.com',
                        'Origin': 'https://www.bilibili.com'
                    })
                };
            }
            
            // 默认使用壳子超级解析
            return {
                parse: 1,
                jx: 1,
                play_parse: true,
                parse_type: '壳子超级解析',
                parse_source: '哔哩哔哩',
                url: id,
                header: JSON.stringify(this.headers)
            };
            
        } catch (error) {
            console.error(`playerContent error: ${error.message}`);
            // 即使出错也返回超级解析参数，让壳子处理
            return {
                parse: 1,
                jx: 1,
                play_parse: true,
                parse_type: '壳子超级解析',
                parse_source: '哔哩哔哩',
                url: id,
                header: JSON.stringify(this.headers)
            };
        }
    }
    
    localProxy(param) {
        return null;
    }
    
    // ============ 辅助方法 ============
    
    // 初始化线路统计
    initLineStats() {
        this.playLines.forEach(line => {
            if (!this.lineStats[line.id]) {
                this.lineStats[line.id] = {
                    success: 0,
                    fail: 0,
                    score: line.priority || 0,
                    lastUsed: 0
                };
            }
        });
    }
    
    // 记录线路成功
    markLineSuccess(lineId) {
        if (this.lineStats[lineId]) {
            this.lineStats[lineId].success++;
            this.lineStats[lineId].score += 2;
            this.lineStats[lineId].lastUsed = Date.now();
        }
    }
    
    // 记录线路失败
    markLineFail(lineId) {
        if (this.lineStats[lineId]) {
            this.lineStats[lineId].fail++;
            this.lineStats[lineId].score -= 1;
            this.lineStats[lineId].lastUsed = Date.now();
        }
    }
    
    // 获取最佳线路
    getBestLine() {
        let bestLine = this.playLines[0];
        let bestScore = -Infinity;
        
        this.playLines.forEach(line => {
            const stats = this.lineStats[line.id] || { score: 0 };
            if (stats.score > bestScore) {
                bestScore = stats.score;
                bestLine = line;
            }
        });
        
        return bestLine;
    }
    
    // ============ 修复图片URL ============
    fixCoverUrl(url) {
        if (!url) {
            // 返回一个默认的B站占位图
            return 'https://i0.hdslb.com/bfs/archive/9e5ff5a6e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5.jpg';
        }
        
        // 如果URL是相对路径，添加协议
        if (url.startsWith('//')) {
            return 'https:' + url;
        }
        
        // 如果URL没有协议，添加https
        if (!url.startsWith('http')) {
            // 检查是否是B站图片路径
            if (url.includes('hdslb.com') || url.includes('bilivideo.com')) {
                return 'https:' + url;
            }
            return 'https://' + url;
        }
        
        return url;
    }
    
    // ============ 自定义内容搜索 ============
    async searchCustomContent(keyword, page = 1) {
        try {
            const encodedKeyword = encodeURIComponent(keyword);
            const videos = [];
            
            // 主要搜索视频类型，因为用户上传的沙雕视频都在这里
            const searchTypes = ['video'];
            
            for (const searchType of searchTypes) {
                try {
                    const url = `https://api.bilibili.com/x/web-interface/search/type?search_type=${searchType}&keyword=${encodedKeyword}&page=${page}`;
                    const response = await fetch(url, { headers: this.headers });
                    
                    if (!response.ok) continue;
                    
                    const data = await response.json();
                    
                    if (data.code === 0 && data.data?.result) {
                        data.data.result.forEach(vod => {
                            // 筛选相关视频
                            const title = this.cleanHtml(vod.title || '').toLowerCase();
                            
                            if (this.isRelatedContent(title, keyword)) {
                                // 获取视频ID
                                let videoId = '';
                                if (vod.bvid) {
                                    videoId = vod.bvid;
                                } else if (vod.aid) {
                                    videoId = 'av' + vod.aid;
                                }
                                
                                if (videoId) {
                                    // 修复图片URL
                                    const coverUrl = this.fixCoverUrl(vod.pic || '');
                                    
                                    // 生成备注信息
                                    let remark = '';
                                    if (vod.duration) {
                                        const minutes = Math.floor(vod.duration / 60);
                                        const seconds = vod.duration % 60;
                                        remark += `${minutes}:${seconds.toString().padStart(2, '0')} `;
                                    }
                                    if (vod.pubdate) {
                                        const date = new Date(vod.pubdate * 1000);
                                        remark += date.toLocaleDateString();
                                    }
                                    
                                    videos.push({
                                        vod_id: videoId,
                                        vod_name: this.cleanHtml(vod.title || '').trim(),
                                        vod_pic: coverUrl,
                                        vod_remarks: remark || '沙雕动画'
                                    });
                                }
                            }
                        });
                    }
                } catch (e) {
                    console.error(`搜索类型 ${searchType} 失败:`, e.message);
                }
            }
            
            // 去重
            const uniqueVideos = [];
            const seenIds = new Set();
            
            for (const video of videos) {
                if (!seenIds.has(video.vod_id)) {
                    seenIds.add(video.vod_id);
                    uniqueVideos.push(video);
                }
            }
            
            return uniqueVideos;
            
        } catch (error) {
            console.error(`searchCustomContent error: ${error.message}`);
            return [];
        }
    }
    
    // 获取视频详情（用户创作的沙雕视频）
    async getVideoDetail(videoId) {
        try {
            let url = '';
            let isAid = false;
            
            if (videoId.startsWith('BV')) {
                url = `https://api.bilibili.com/x/web-interface/view?bvid=${videoId}`;
            } else if (videoId.startsWith('av')) {
                const aid = videoId.replace('av', '');
                url = `https://api.bilibili.com/x/web-interface/view?aid=${aid}`;
                isAid = true;
            } else {
                return { list: [] };
            }
            
            const response = await fetch(url, { 
                headers: this.headers 
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code !== 0 || !data.data) {
                console.log('视频详情接口返回错误:', data.message);
                return { list: [] };
            }
            
            const videoData = data.data;
            
            // 格式化数字
            const formatNumber = (num) => {
                if (!num) return '0';
                if (num > 1e8) return (num / 1e8).toFixed(2) + '亿';
                if (num > 1e4) return (num / 1e4).toFixed(2) + '万';
                return num.toString();
            };
            
            const vod = {
                vod_id: videoId,
                vod_name: videoData.title || '',
                vod_pic: this.fixCoverUrl(videoData.pic || ''),
                type_name: '沙雕动画',
                vod_year: new Date(videoData.pubdate * 1000).getFullYear() || '',
                vod_area: '中国',
                vod_remarks: `播放:${formatNumber(videoData.stat?.view)}`,
                vod_actor: `UP主: ${videoData.owner?.name || ''}`,
                vod_director: `点赞:${formatNumber(videoData.stat?.like)} 投币:${formatNumber(videoData.stat?.coin)}`,
                vod_content: this.cleanHtml(videoData.desc || ''),
                vod_play_from: '',
                vod_play_url: ''
            };

            // 构建播放线路
            const shareUrl = `https://www.bilibili.com/video/${videoId}`;
            const playFrom = [];
            const playUrl = [];
            
            // 壳子超级解析线路
            playFrom.push('壳子超级解析');
            playUrl.push(`正片$${shareUrl}`);
            
            // B站分享链接线路（备用）
            playFrom.push('B站分享链接');
            playUrl.push(`正片$${shareUrl}`);

            vod.vod_play_from = playFrom.join('$$$');
            vod.vod_play_url = playUrl.join('$$$');

            return { list: [vod] };
            
        } catch (error) {
            console.error(`getVideoDetail error: ${error.message}`);
            return { list: [] };
        }
    }
    
    // 获取番剧详情（原有逻辑）
    async getSeasonDetail(seasonId) {
        try {
            const url = 'https://api.bilibili.com/pgc/view/web/season';
            
            const response = await fetch(`${url}?season_id=${seasonId}`, { 
                headers: this.headers 
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code !== 0 || !data.result) {
                console.log('详情接口返回错误:', data.message);
                return { list: [] };
            }
            
            const jo = data.result;
            const stat = jo.stat || {};
            const rating = jo.rating || {};
            
            // 格式化数字
            const formatNumber = (num) => {
                if (!num) return '0';
                if (num > 1e8) return (num / 1e8).toFixed(2) + '亿';
                if (num > 1e4) return (num / 1e4).toFixed(2) + '万';
                return num.toString();
            };
            
            const vod = {
                vod_id: seasonId,
                vod_name: jo.title || '',
                vod_pic: this.fixCoverUrl(jo.cover || ''),
                type_name: jo.share_sub_title || '',
                vod_year: jo.publish?.pub_time?.substr(0, 4) || '',
                vod_area: jo.areas?.[0]?.name || '',
                vod_remarks: jo.new_ep?.desc || '',
                vod_actor: `弹幕: ${formatNumber(stat.danmakus)}　点赞: ${formatNumber(stat.likes)}　投币: ${formatNumber(stat.coins)}`,
                vod_director: rating.score ? `评分: ${rating.score}　${jo.subtitle || ''}` : `暂无评分　${jo.subtitle || ''}`,
                vod_content: this.cleanHtml(jo.evaluate || ''),
                vod_play_from: '',
                vod_play_url: ''
            };

            // 处理剧集
            const episodes = jo.episodes || [];
            const filteredEpisodes = episodes.filter(ep => 
                !ep.title?.includes('预告') && 
                !(ep.badge && ep.badge.includes('预告'))
            );

            if (filteredEpisodes.length > 0) {
                const playFrom = [];
                const playUrl = [];

                // 壳子超级解析线路
                const superParseItems = [];
                
                // 官方直连线路（需要Cookie）
                const officialItems = [];
                
                // B站分享链接线路
                const shareItems = [];

                filteredEpisodes.forEach(ep => {
                    // B站分享链接
                    const shareUrl = ep.share_url || `https://www.bilibili.com/bangumi/play/ep${ep.id}`;
                    let part = `${ep.title || ''} ${ep.long_title || ''}`.trim();
                    
                    // 清理标题
                    part = part
                        .replace(/#/g, '-')
                        .replace(/\[预告\]/g, '')
                        .replace(/预告/g, '')
                        .replace(/\s+/g, ' ')
                        .trim();
                    
                    if (!part) {
                        part = `第${ep.order || '?'}集`;
                    }
                    
                    // 壳子超级解析使用分享链接
                    superParseItems.push(`${part}$${shareUrl}`);
                    
                    // 官方线路使用ID格式（需要Cookie）
                    const officialId = `${seasonId}_${ep.id}_${ep.cid}`;
                    officialItems.push(`${part}$${officialId}`);
                    
                    // B站分享链接
                    shareItems.push(`${part}$${shareUrl}`);
                });

                if (superParseItems.length > 0) {
                    playFrom.push('壳子超级解析');
                    playUrl.push(superParseItems.join('#'));
                }
                
                if (officialItems.length > 0) {
                    playFrom.push('官方直连(需Cookie)');
                    playUrl.push(officialItems.join('#'));
                }
                
                if (shareItems.length > 0) {
                    playFrom.push('B站分享链接');
                    playUrl.push(shareItems.join('#'));
                }

                if (playFrom.length > 0) {
                    vod.vod_play_from = playFrom.join('$$$');
                    vod.vod_play_url = playUrl.join('$$$');
                }
            }

            return { list: [vod] };
            
        } catch (error) {
            console.error(`getSeasonDetail error: ${error.message}`);
            return { list: [] };
        }
    }
    
    // 检查内容是否相关
    isRelatedContent(title, keyword) {
        const titleLower = title.toLowerCase();
        const keywordLower = keyword.toLowerCase();
        
        // 沙雕仙逆的相关词
        if (keyword.includes('仙逆') || keyword.includes('王林')) {
            return titleLower.includes('仙逆') || 
                   titleLower.includes('王林') ||
                   titleLower.includes('修真') ||
                   titleLower.includes('耳根') ||
                   titleLower.includes('修仙') ||
                   titleLower.includes('逆仙') ||
                   titleLower.includes('凡人修仙') ||
                   titleLower.includes('仙侠');
        }
        
        // 沙雕动画的相关词
        if (keyword.includes('沙雕') || keyword.includes('搞笑')) {
            return titleLower.includes('搞笑') || 
                   titleLower.includes('沙雕') ||
                   titleLower.includes('幽默') ||
                   titleLower.includes('喜剧') ||
                   titleLower.includes('恶搞') ||
                   titleLower.includes('整活') ||
                   titleLower.includes('爆笑') ||
                   titleLower.includes('逗比') ||
                   titleLower.includes('笑死') ||
                   titleLower.includes('有趣');
        }
        
        // 通用匹配
        return titleLower.includes(keywordLower);
    }
    
    // 清理HTML标签
    cleanHtml(text) {
        if (!text) return '';
        return text.replace(/<[^>]+>/g, '').replace(/&quot;/g, '"').replace(/&amp;/g, '&');
    }
    
    // 获取排行榜数据
    async getRankList(seasonType, page = 1) {
        try {
            const url = `https://api.bilibili.com/pgc/web/rank/list?season_type=${seasonType}&pagesize=20&page=${page}&day=3`;
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code === 0) {
                const items = data.result?.list || data.data?.list || [];
                return items.map(item => ({
                    vod_id: String(item.season_id || '').trim(),
                    vod_name: item.title?.trim() || '',
                    vod_pic: this.fixCoverUrl(item.cover || ''),
                    vod_remarks: item.new_ep?.index_show || item.index_show || ''
                }));
            }
            
            return [];
            
        } catch (error) {
            console.error(`getRankList error: ${error.message}`);
            return [];
        }
    }
    
    // 获取全部分类数据
    async getAllList(tid, page = 1, order = '2', seasonStatus = '-1') {
        try {
            const url = `https://api.bilibili.com/pgc/season/index/result?order=${order}&pagesize=20&type=1&season_type=${tid}&page=${page}&season_status=${seasonStatus}`;
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code === 0) {
                const items = data.data?.list || [];
                return items.map(item => ({
                    vod_id: String(item.season_id || '').trim(),
                    vod_name: item.title?.trim() || '',
                    vod_pic: this.fixCoverUrl(item.cover || ''),
                    vod_remarks: item.index_show || ''
                }));
            }
            
            return [];
            
        } catch (error) {
            console.error(`getAllList error: ${error.message}`);
            return [];
        }
    }
    
    // 获取时间表数据
    async getTimeline(tid) {
        try {
            const url = `https://api.bilibili.com/pgc/web/timeline/v2?season_type=${tid}&day_before=2&day_after=4`;
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            const videos = [];
            
            if (data.code === 0 && data.result) {
                const result = data.result;
                
                // 最新更新
                const latestList = result.latest || [];
                latestList.forEach(vod => {
                    if (!vod.title?.includes('预告')) {
                        videos.push({
                            vod_id: String(vod.season_id || '').trim(),
                            vod_name: vod.title?.trim() || '',
                            vod_pic: this.fixCoverUrl(vod.cover || ''),
                            vod_remarks: (vod.pub_index || '') + '　' + (vod.follows || '').replace('系列', '')
                        });
                    }
                });
                
                // 时间表
                for (let i = 0; i < 7; i++) {
                    const dayList = result.timeline?.[i]?.episodes || [];
                    dayList.forEach(vod => {
                        if (String(vod.published) === '0' && !vod.title?.includes('预告')) {
                            videos.push({
                                vod_id: String(vod.season_id || '').trim(),
                                vod_name: vod.title?.trim() || '',
                                vod_pic: this.fixCoverUrl(vod.cover || ''),
                                vod_remarks: (vod.pub_ts || '') + '   ' + (vod.pub_index || '')
                            });
                        }
                    });
                }
            }
            
            return videos;
            
        } catch (error) {
            console.error(`getTimeline error: ${error.message}`);
            return [];
        }
    }
}

// 导出 Spider 类
module.exports = Spider;