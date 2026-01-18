/**
 * 电影天堂 - 猫影视/TVBox JS爬虫格式（优酷模板风格）- 修复版
 */

class Spider extends BaseSpider {
    
    constructor() {
        super();
        this.host = 'http://caiji.dyttzyapi.com';
        
        this.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://caiji.dyttzyapi.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        };
        
        this.baseURL = "http://caiji.dyttzyapi.com/api.php/provide/vod/from/dyttm3u8/at/json/";
        
        // 预定义分类（根据电影天堂API的实际分类ID）
        this.predefinedCategories = [
            {"type_id":2,"type_pid":1,"type_name":"连续剧"},{"type_id":6,"type_pid":1,"type_name":"动作片"},{"type_id":7,"type_pid":1,"type_name":"喜剧片"},{"type_id":8,"type_pid":1,"type_name":"爱情片"},{"type_id":9,"type_pid":1,"type_name":"科幻片"},{"type_id":10,"type_pid":1,"type_name":"恐怖片"},{"type_id":11,"type_pid":1,"type_name":"剧情片"},{"type_id":12,"type_pid":1,"type_name":"战争片"},{"type_id":13,"type_pid":2,"type_name":"国产剧"},{"type_id":14,"type_pid":2,"type_name":"香港剧"},{"type_id":15,"type_pid":2,"type_name":"韩国剧"},{"type_id":16,"type_pid":2,"type_name":"欧美剧"},{"type_id":20,"type_pid":1,"type_name":"记录片"},{"type_id":21,"type_pid":2,"type_name":"台湾剧"},{"type_id":22,"type_pid":2,"type_name":"日本剧"},{"type_id":23,"type_pid":2,"type_name":"海外剧"},{"type_id":24,"type_pid":2,"type_name":"泰国剧"},{"type_id":25,"type_pid":3,"type_name":"大陆综艺"},{"type_id":26,"type_pid":3,"type_name":"港台综艺"},{"type_id":27,"type_pid":3,"type_name":"日韩综艺"},{"type_id":28,"type_pid":3,"type_name":"欧美综艺"},{"type_id":29,"type_pid":4,"type_name":"国产动漫"},{"type_id":30,"type_pid":4,"type_name":"日韩动漫"},{"type_id":31,"type_pid":4,"type_name":"欧美动漫"},{"type_id":32,"type_pid":4,"type_name":"港台动漫"},{"type_id":34,"type_pid":1,"type_name":"伦理片"},{"type_id":36,"type_pid":2,"type_name":"短剧"},{"type_id":37,"type_pid":1,"type_name":"动画片"}
        ];
    }
    
    init(extend = '') {
        return '';
    }
    
    getName() {
        return '电影天堂修复版';
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
    
    // 修复1：首页必须返回分类列表
    homeContent(filter) {
        return {
            class: this.predefinedCategories
        };
    }
    
    async homeVideoContent() {
        try {
            // 获取推荐视频
            const url = `${this.baseURL}?ac=detail&pg=1`;
            const response = await this.fetch(url, {}, this.headers);
            const data = response.data;
            
            const videos = [];
            if (data.list && Array.isArray(data.list)) {
                data.list.slice(0, 20).forEach((i) => {
                    videos.push({
                        vod_id: i.vod_id || '',
                        vod_name: i.vod_name || '',
                        vod_pic: i.vod_pic || '',
                        vod_remarks: i.vod_remarks || '',
                        vod_year: i.vod_year || '',
                        type_name: i.type_name || ''
                    });
                });
            }
            
            return { list: videos };
        } catch (error) {
            console.error(`homeVideoContent error: ${error.message}`);
            return { list: [] };
        }
    }
    
    async categoryContent(tid, pg, filter, extend) {
        try {
            const page = parseInt(pg) || 1;
            const typeId = parseInt(tid) || 0;
            
            // 修复2：确保type_id正确传递
            const params = {
                ac: 'detail',
                t: typeId,
                pg: page
            };
            
            // 如果有筛选条件
            if (extend && typeof extend === 'object') {
                Object.assign(params, extend);
            }
            
            const url = `${this.baseURL}?${new URLSearchParams(params).toString()}`;
            
            const response = await this.fetch(url, {}, this.headers);
            const data = response.data;
            
            const videos = [];
            if (data.list && Array.isArray(data.list)) {
                data.list.forEach((i) => {
                    videos.push({
                        vod_id: i.vod_id || '',
                        vod_name: i.vod_name || '',
                        vod_pic: i.vod_pic || '',
                        vod_remarks: i.vod_remarks || '',
                        vod_year: i.vod_year || '',
                        type_name: i.type_name || ''
                    });
                });
            }
            
            return {
                list: videos,
                page: page,
                pagecount: data.pagecount || 1,
                limit: data.limit || 20,
                total: data.total || 0
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
            
            const url = `${this.baseURL}?ac=detail&ids=${id}`;
            
            const response = await this.fetch(url, {}, this.headers);
            const data = response.data;
            
            if (!data || !data.list || !Array.isArray(data.list) || data.list.length === 0) {
                return { list: [] };
            }
            
            const item = data.list[0];
            
            const vod = {
                vod_id: item.vod_id || id,
                vod_name: item.vod_name || '',
                type_name: item.type_name || '',
                vod_year: item.vod_year || '',
                vod_area: item.vod_area || '',
                vod_remarks: item.vod_remarks || '',
                vod_actor: item.vod_actor || '',
                vod_director: item.vod_director || '',
                vod_content: item.vod_content || '',
                vod_pic: item.vod_pic || '',
                vod_play_from: item.vod_play_from || '',
                vod_play_url: item.vod_play_url || ''
            };
            
            return { list: [vod] };
            
        } catch (error) {
            console.error(`detailContent error: ${error.message}`);
            return { list: [] };
        }
    }
    
    async searchContent(key, quick, pg = '1') {
        try {
            const page = parseInt(pg) || 1;
            
            const params = {
                ac: 'detail',
                wd: key,
                pg: page
            };
            
            const url = `${this.baseURL}?${new URLSearchParams(params).toString()}`;
            
            const response = await this.fetch(url, {}, this.headers);
            const data = response.data;
            
            const videos = [];
            if (data.list && Array.isArray(data.list)) {
                data.list.forEach((i) => {
                    videos.push({
                        vod_id: i.vod_id || '',
                        vod_name: i.vod_name || '',
                        vod_pic: i.vod_pic || '',
                        vod_remarks: i.vod_remarks || '',
                        vod_year: i.vod_year || '',
                        type_name: i.type_name || ''
                    });
                });
            }
            
            return {
                list: videos,
                page: page,
                pagecount: data.pagecount || 1,
                limit: data.limit || 20,
                total: data.total || 0
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
    
    async playerContent(flag, id, vipFlags) {
        try {
            // 直接播放地址
            if (/\.(m3u8|mp4|rmvb|avi|wmv|flv|mkv|webm|mov|m3u)(?!\w)/i.test(id)) {
                return {
                    url: id,
                    jx: 0,
                    parse: 0,
                };
            }
            
            // 调用壳子解析
            return {
                parse: 1,
                jx: 1,
                play_parse: true,
                parse_type: '壳子超级解析',
                parse_source: '电影天堂',
                url: id,
                header: JSON.stringify({
                    'User-Agent': this.headers['User-Agent'],
                    'Referer': this.host,
                    'Origin': this.host
                })
            };
            
        } catch (error) {
            console.error(`playerContent error: ${error.message}`);
            return {
                parse: 1,
                jx: 1,
                play_parse: true,
                parse_type: '壳子超级解析',
                parse_source: '电影天堂',
                url: id,
                header: JSON.stringify(this.headers)
            };
        }
    }
    
    localProxy(param) {
        return null;
    }
}

// 导出 Spider 类
module.exports = Spider;