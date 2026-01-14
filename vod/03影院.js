/*
@header({
  searchable: 1,
  filterable: 1,
  quickSearch: 1,
  title: '03影视',
  author: '小可乐/250915/第一版',
  '类型': '影视',
  lang: 'dr2'
})
*/

var rule = {
    author: '小可乐/250915/第一版',
    title: '03影视',
    类型: '影视',
    host: 'https://www.03yy.live',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.03yy.live/',
        'Sec-Ch-Ua': '"Chromium";v="128", "Not;A=Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    },
    编码: 'utf-8',
    timeout: 10000,
    url: '/type/indexfyclass-fypage.html',
    searchUrl: '/search.php?searchword=**&page=fypage',
    searchable: 1,
    quickSearch: 1,
    filterable: 1,

    class_name: '电影&电视剧&综艺&动漫',
    class_url: '1&2&3&4',
    
    // 添加分类筛选器，类似3Q影视的filter配置
    filter_def: {
        "电影": [
            { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"动作",v:"动作"}, {n:"喜剧",v:"喜剧"}, {n:"爱情",v:"爱情"}, {n:"科幻",v:"科幻"}, {n:"恐怖",v:"恐怖"}, {n:"悬疑",v:"悬疑"}, {n:"犯罪",v:"犯罪"} ] },
            { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"大陆",v:"大陆"}, {n:"香港",v:"香港"}, {n:"台湾",v:"台湾"}, {n:"美国",v:"美国"}, {n:"韩国",v:"韩国"}, {n:"日本",v:"日本"} ] },
            { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"} ] }
        ],
        "电视剧": [
            { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"爱情",v:"爱情"}, {n:"古装",v:"古装"}, {n:"悬疑",v:"悬疑"}, {n:"犯罪",v:"犯罪"}, {n:"家庭",v:"家庭"}, {n:"喜剧",v:"喜剧"} ] },
            { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"大陆",v:"大陆"}, {n:"韩国",v:"韩国"}, {n:"日本",v:"日本"}, {n:"美国",v:"美国"}, {n:"英国",v:"英国"} ] },
            { key: "year", name: "年份", value: [ {n:"全部",v:"""}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"} ] }
        ]
    },

    预处理: $js.toString(() => {
        try {
            console.log('开始预处理，获取初始Cookie...');
            
            const res = request(HOST, {
                headers: {
                    'User-Agent': rule.headers['User-Agent'],
                    'Accept': rule.headers['Accept']
                },
                withHeaders: true,
                method: 'GET',
                timeout: rule.timeout
            });

            if (!res) {
                console.error('预处理请求失败: 无响应');
                return;
            }

            let headers = {};
            if (typeof res === 'string') {
                try {
                    headers = JSON.parse(res);
                } catch (e) {
                    console.error('解析响应失败:', e.message);
                    return;
                }
            } else {
                headers = res;
            }

            // 提取set-cookie头
            let setCookie = headers['set-cookie'] || headers['Set-Cookie'] || '';
            
            if (setCookie) {
                console.log('原始Set-Cookie:', setCookie);
                
                let cookiesArray = [];
                if (Array.isArray(setCookie)) {
                    cookiesArray = setCookie;
                } else {
                    cookiesArray = [setCookie];
                }

                // 处理每个cookie
                let validCookies = [];
                cookiesArray.forEach(cookie => {
                    if (cookie && typeof cookie === 'string') {
                        // 只取第一个分号前的部分
                        const cookiePart = cookie.split(';')[0].trim();
                        if (cookiePart) {
                            validCookies.push(cookiePart);
                        }
                    }
                });

                if (validCookies.length > 0) {
                    const newCookie = validCookies.join('; ');
                    console.log('提取的有效Cookie:', newCookie);
                    
                    // 更新headers
                    if (rule.headers['cookie']) {
                        rule.headers['cookie'] += '; ' + newCookie;
                    } else {
                        rule.headers['cookie'] = newCookie;
                    }
                    
                    // 更新全局fetch参数
                    if (typeof rule_fetch_params !== 'undefined') {
                        rule_fetch_params.headers = Object.assign({}, rule.headers);
                    }
                    
                    console.log('最终Cookie设置完成');
                }
            } else {
                console.log('未找到Set-Cookie头');
            }
        } catch (error) {
            console.error('预处理出错:', error.message);
        }
    }),

    play_parse: true,
    
    lazy: $js.toString(() => {
        try {
            console.log('开始解析播放地址, input:', input);
            
            if (!input) {
                console.error('输入为空');
                return { parse: 0, url: '' };
            }

            let html = request(input, {
                headers: rule.headers,
                method: 'GET',
                timeout: rule.timeout,
                redirect: false
            });

            if (!html) {
                console.error('获取播放页失败');
                return { parse: 0, url: '' };
            }

            // 处理转义字符
            html = html.replace(/\\"/g, '"').replace(/\\\//g, '/');

            // 1. 尝试直接匹配now变量
            let nowMatch = html.match(/var\s+now\s*=\s*["']([^"']+)["']/);
            if (!nowMatch) {
                nowMatch = html.match(/var\s+now\s*=\s*base64decode\s*\(\s*["']([^"']+)["']\s*\)/);
            }

            if (!nowMatch || !nowMatch[1]) {
                console.error('未找到now变量');
                // 尝试直接提取m3u8链接
                const m3u8Match = html.match(/(https?:\/\/[^\s"']+\.(m3u8|mp4|mkv|flv|avi))/i);
                if (m3u8Match) {
                    console.log('直接找到视频链接:', m3u8Match[1]);
                    return { parse: 0, url: m3u8Match[1] };
                }
                return { parse: 0, url: '' };
            }

            let now = nowMatch[1];
            console.log('原始now值:', now);

            // 如果是base64编码则解码
            if (now.includes('base64decode') || /^[A-Za-z0-9+/]+=*$/.test(now) && now.length % 4 === 0) {
                try {
                    now = base64Decode(now);
                    console.log('base64解码后:', now);
                } catch (e) {
                    console.log('base64解码失败，使用原始值');
                }
            }

            // 检查是否是直接视频链接
            if (/\.(m3u8|mp4|mkv|flv|avi|jpg|png|webp)/i.test(now)) {
                console.log('now是直接视频链接:', now);
                return { parse: 0, url: now };
            }

            // 提取prePage和nextPage
            const prePageMatch = html.match(/var\s+prePage\s*=\s*["']([^"']+)["']/);
            const nextPageMatch = html.match(/var\s+nextPage\s*=\s*["']([^"']+)["']/);
            
            const prePage = prePageMatch ? prePageMatch[1] : HOST;
            const nextPage = nextPageMatch ? nextPageMatch[1] : '';
            
            console.log('prePage:', prePage);
            console.log('nextPage:', nextPage);

            // 构建API请求URL
            const jxUrl = `${HOST}/api/dplayer.php?url=${encodeURIComponent(now)}&ref=${encodeURIComponent(prePage)}`;
            if (nextPage) {
                jxUrl += `&next=${encodeURIComponent(nextPage)}`;
            }
            
            console.log('请求解析API:', jxUrl);

            // 请求解析API
            let videohtml = request(jxUrl, {
                headers: rule.headers,
                method: 'GET',
                timeout: rule.timeout
            });

            if (!videohtml) {
                console.error('解析API返回空');
                return { parse: 0, url: '' };
            }

            console.log('API返回长度:', videohtml.length);

            // 方法1: 尝试解析mediaInfo
            const mediaInfoRegex = /mediaInfo\s*=\s*(\[.*?\]);/gis;
            const mediaInfoMatch = mediaInfoRegex.exec(videohtml);
            
            if (mediaInfoMatch && mediaInfoMatch[1]) {
                try {
                    const mediaInfoContent = mediaInfoMatch[1];
                    console.log('找到mediaInfo内容');
                    
                    // 提取所有URL
                    const urlMatches = mediaInfoContent.match(/["']?(https?:\/\/[^\s"']+)["']?/gi);
                    if (urlMatches && urlMatches.length > 0) {
                        // 按清晰度排序
                        const qualityUrls = {};
                        urlMatches.forEach(url => {
                            const cleanUrl = url.replace(/["']/g, '').replace(/\\\\\//g, '/');
                            if (cleanUrl.includes('.m3u8') || cleanUrl.includes('.mp4')) {
                                // 检测清晰度
                                let quality = '标清';
                                if (cleanUrl.includes('1080')) quality = '超清';
                                else if (cleanUrl.includes('720')) quality = '高清';
                                else if (cleanUrl.includes('540')) quality = '清晰';
                                else if (cleanUrl.includes('360')) quality = '流畅';
                                
                                qualityUrls[quality] = cleanUrl;
                            }
                        });

                        // 转换为数组格式
                        if (Object.keys(qualityUrls).length > 0) {
                            const result = [];
                            for (const [quality, url] of Object.entries(qualityUrls)) {
                                result.push(quality, url);
                            }
                            console.log('成功提取多清晰度视频:', result);
                            return { parse: 0, url: result };
                        }
                    }
                } catch (e) {
                    console.error('解析mediaInfo失败:', e.message);
                }
            }

            // 方法2: 尝试直接提取视频链接
            const directUrlMatch = videohtml.match(/(https?:\/\/[^\s"']+\.(m3u8|mp4|mkv|flv))/i);
            if (directUrlMatch) {
                console.log('直接提取到视频链接:', directUrlMatch[1]);
                return { parse: 0, url: directUrlMatch[1] };
            }

            // 方法3: 尝试JSON解析
            try {
                const jsonData = JSON.parse(videohtml);
                if (jsonData.url) {
                    console.log('JSON解析成功:', jsonData.url);
                    return { parse: 0, url: jsonData.url };
                }
            } catch (e) {
                console.log('不是JSON格式');
            }

            console.error('无法解析播放地址');
            return { parse: 0, url: '' };

        } catch (error) {
            console.error('解析播放地址出错:', error.message);
            return { parse: 0, url: '' };
        }
    }),

    limit: 20,
    double: true,
    
    // 推荐视频选择器
    推荐: '.Pic-list&&.pic-content;a&&title;img&&src;span&&Text;a&&href',
    
    // 一级分类选择器
    一级: '.type-box&&.pic-height-a;a&&title;img&&src;.pic-text&&Text;a&&href',
    
    // 二级详情页选择器 - 优化版
    二级: {
        title: 'h2&&Text',
        img: '.img-responsive&&src',
        desc: '.m-content&&ul&&li:eq(0)&&Text;;.m-content&&ul&&li:eq(1)&&Text;.m-content&&ul&&li:eq(2)&&Text;.m-content&&ul&&li:eq(3)&&Text;.m-content&&ul&&li:eq(4)&&Text',
        content: '.m-intro&&Text',
        tabs: '#playlist&&li',
        tab_text: '&&Text',
        lists: '.play_list:eq(#id)&&li',
        list_text: 'a&&Text',
        list_url: 'a&&href'
    },
    
    // 搜索选择器 - 优化版
    搜索: '.Pic-list&&.pic-content;a&&title;img&&src;.pic-text&&Text;a&&href',
    
    // 新增：搜索结果处理函数
    search: $js.toString(() => {
        try {
            const searchword = KEY;
            const page = parseInt(PAGE) || 1;
            
            if (!searchword || searchword.trim() === '') {
                return { list: [] };
            }
            
            const searchUrl = `${HOST}/search.php?searchword=${encodeURIComponent(searchword)}&page=${page}`;
            console.log('搜索URL:', searchUrl);
            
            const html = request(searchUrl, {
                headers: rule.headers,
                method: 'GET',
                timeout: rule.timeout
            });
            
            if (!html) {
                console.error('搜索请求失败');
                return { list: [] };
            }
            
            const items = parseSearchResults(html);
            const total = items.length;
            const pagecount = Math.ceil(total / rule.limit) || 1;
            
            return {
                list: items,
                page: page,
                pagecount: pagecount,
                limit: rule.limit,
                total: total
            };
            
        } catch (error) {
            console.error('搜索出错:', error.message);
            return { list: [] };
        }
    })
};

// 辅助函数
function parseSearchResults(html) {
    const items = [];
    const doc = new DOMParser().parseFromString(html, 'text/html');
    
    // 多个可能的选择器
    const selectors = [
        '.Pic-list .pic-content',
        '.type-box .pic-height-a',
        '.stui-vodlist__box',
        '.item'
    ];
    
    let elements = [];
    for (const selector of selectors) {
        const found = doc.querySelectorAll(selector);
        if (found.length > 0) {
            elements = found;
            break;
        }
    }
    
    elements.forEach(element => {
        try {
            const link = element.querySelector('a');
            const img = element.querySelector('img');
            const titleElem = element.querySelector('a[title]') || link;
            const remarkElem = element.querySelector('.pic-text, .text, span, .remarks');
            
            if (!link || !titleElem) return;
            
            const href = link.getAttribute('href') || '';
            const vod_id = href.match(/\/(\d+)\.html/)?.[1] || 
                          href.match(/id=(\d+)/)?.[1] || '';
            
            const vod_name = titleElem.getAttribute('title') || 
                           titleElem.textContent.trim() || '';
            
            const vod_pic = img ? (img.getAttribute('data-original') || 
                                 img.getAttribute('src') || '') : '';
            
            const vod_remarks = remarkElem ? remarkElem.textContent.trim() : '';
            
            if (vod_id && vod_name) {
                items.push({
                    vod_id: vod_id,
                    vod_name: vod_name,
                    vod_pic: vod_pic ? (vod_pic.startsWith('http') ? vod_pic : HOST + vod_pic) : '',
                    vod_remarks: vod_remarks
                });
            }
        } catch (e) {
            console.error('解析搜索项出错:', e.message);
        }
    });
    
    return items;
}