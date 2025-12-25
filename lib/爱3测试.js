var rule = {
    title: '爱壹帆',
    host: 'https://www.iyf.lv',
    // homeUrl: '/',
    url: '/t/fyclass/', // 简单的URL格式
    searchUrl: '/s/**-------------/', // 搜索URL格式
    searchable: 2, // 启用全局搜索
    quickSearch: 0, // 不启用快速搜索
    filterable: 0, // 不启用分类筛选
    headers: {
        'User-Agent': 'MOBILE_UA',
        'Referer': 'https://www.iyf.lv/',
        'Origin': 'https://www.iyf.lv'
    },
    timeout: 5000,
    
    // 只保留能正常工作的四个分类
    class_name: '电影&剧集&综艺&动漫',
    class_url: '1&2&3&4',
    
    play_parse: true,
    lazy: `js:
        let html = request(input);
        // 尝试从页面中提取m3u8地址
        let m3u8_match = html.match(/(https?:\\/\\/[^\\s"\'<>]+\\.m3u8[^\\s"\'<>]*)/);
        if (m3u8_match) {
            input = {
                parse: 0,
                jx: 0,
                url: m3u8_match[1]
            };
        } else {
            // 如果没有找到m3u8，尝试其他视频格式
            let mp4_match = html.match(/(https?:\\/\\/[^\\s"\'<>]+\\.(mp4|m4a|m3u8)[^\\s"\'<>]*)/);
            if (mp4_match) {
                input = {
                    parse: 0,
                    jx: 0,
                    url: mp4_match[1]
                };
            } else {
                // 如果都没有找到，保持原URL让播放器尝试解析
                input;
            }
        }`,
    limit: 20,
    double: true, // 推荐内容是否双层定位
    
    // 推荐规则
    推荐: '.tab-list.active;a.module-poster-item.module-item;.module-poster-item-title&&Text;.lazyload&&data-original;.module-item-note&&Text;a&&href',
    
    // 一级规则 - 分类页
    一级: 'body a.module-poster-item.module-item;a&&title;.lazyload&&data-original;.module-item-note&&Text;a&&href',
    
    // 二级规则 - 详情页
    二级: {
        title: 'h1&&Text;.module-info-tag-link:eq(-1)&&Text',
        img: '.lazyload&&data-original',
        desc: '.module-info-item:eq(-2)&&Text;.module-info-tag-link&&Text;.module-info-tag-link:eq(1)&&Text;.module-info-item:eq(2)&&Text;.module-info-item:eq(1)&&Text',
        content: '.module-info-introduction&&Text',
        tabs: '.module-tab-item',
        lists: '.module-play-list:eq(#id) a',
        tab_text: 'div&&Text'
    },
    
    // 搜索规则
    搜索: 'body .module-item;.module-card-item-title&&Text;.lazyload&&data-original;.module-item-note&&Text;a&&href;.module-info-item-content&&Text'
};

// 导出规则
if (typeof module !== 'undefined' && module.exports) {
    module.exports = rule;
}