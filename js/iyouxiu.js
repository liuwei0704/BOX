var siteConfig = {
    author: 'DOVE',
    title: '硬核影视',
    host: 'https://www.iyouxiu.com',
    url: '/vodshow/fyfilter',
    searchUrl: '/vodsearch/page/fypage/wd/**/',
    filter_url: '{{fl.cateId}}-{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}-{{fl.letter}}---fypage---{{fl.year}}/',
    class: {
        parseElement: '.navbar-items li',
        type_idRegex: '/vodtype/(.*?)/',
        type_nameElement: 'a&&Text',
        excludeNames: ['首页', '留言', '今日更新', '热榜', 'NBA直播','体育赛事'],
    },
    staticClass: {
        class_name: ['电影', '电视剧', '综艺', '动漫'],
        class_url: ['dianying', 'dsj', 'zongyi', 'dongman'],
    },
    dynamicClass: true, // 是否使用动态分类
    dynamicFilter: true, // 是否使用动态筛选
    useStaticFilterDef: false, // 是否使用静态筛选默认值
    keyMap: {
        '类型': 'cateId',
        '剧情': 'class',
        '地区': 'area',
        '年份': 'year',
        '语言': 'lang',
        '字母': 'letter',
        '排序': 'by',
    },
    excludeFilterNames: ['语言',],
    filter: {
        urlPattern: '/vodshow/{type_id}-----------/',
        cateIdRegex: 'vodshow/(.*?)-----------/',
        classRegex: '---(.*?)--------',
        areaRegex: '-(.*?)----------',
        yearRegex: '-----------(.*?)/',
        byRegex: '--(.*?)---------',
        filterElement: '.module-main .module-class-items',
        moduleItemTitle: 'div.module-item-title&&Text',
        filterItem: '.module-item-box a'
    },
    useCustomRecommend: true,
    recommend: {
        element: '.module-items a',
        titleElement: 'a&&title',
        picUrlElement: '.lazyload&&data-original',
        descElement: '.module-item-note&&Text',
        urlElement: 'a&&href',
        detailsElement: ''
    },
    level1: {
        element: '.module-items.module-poster-items-base a',
        titleElement: 'a&&title',
        picUrlElement: '.lazyload&&data-original',
        descElement: '.module-item-note&&Text',
        urlElement: 'a&&href',
        detailsElement: ''
    },
    level2: {
        vodNameElement: 'h1&&Text',
        typeNameElement: '.module-info-tag-link:eq(-1)&&Text',
        vodRemarksElement: '.module-info-item:eq(-2)&&Text',
        vodYearElement: '.module-info-tag-link&&Text',
        vodAreaElement: '.module-info-tag-link:eq(1)&&Text',
        vodActorElement: '.module-info-item:eq(2)&&Text',
        vodDirectorElement: '.module-info-item:eq(1)&&Text',
        vodContentElement: '.module-info-introduction-content&&Text',
        playlistElement: '.module-play-list-content',
        tabsElement: '.module-tab-item',
        playFromTextElement: 'Text',
        playListElement: 'body&&a:not(:contains(简介))',
        playTitleElement: 'a&&Text',
        playUrlElement: 'a&&href'
    },
    search: {
        element: '.module-items .module-card-item',
        titleElement: '.module-card-item-title&&Text',
        picUrlElement: '.lazyload&&data-original',
        descElement: '.module-item-note&&Text',
        urlElement: 'a&&href',
        contentElement: '.module-info-item-content&&Text'
    },
    headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    },
    other: {
        searchable: 1,
        quickSearch: 1,
        filterable: 1,
        play_parse: true,
        limit: 6,
        double: true
    },
    staticFilter: {
        dianying: [
            {
                key: "class",
                name: "剧情",
                value: [
                    { n: "全部", v: "" },
                    { n: "喜剧", v: "喜剧" },
                    { n: "爱情", v: "爱情" },
                    { n: "恐怖", v: "恐怖" },
                    { n: "农村", v: "农村" },
                    { n: "儿童", v: "儿童" },
                    { n: "网络电影", v: "网络电影" }
                ]
            },
            {
                key: "area",
                name: "地区",
                value: [
                    { n: "全部", v: "" },
                    { n: "大陆", v: "大陆" },
                    { n: "香港", v: "香港" },
                    { n: "台湾", v: "台湾" },
                    { n: "美国", v: "美国" },
                    { n: "法国", v: "法国" },
                    { n: "英国", v: "英国" },
                    { n: "其他", v: "其他" }
                ]
            },
            {
                key: "lang",
                name: "语言",
                value: [
                    { n: "全部", v: "" },
                    { n: "国语", v: "国语" },
                    { n: "英语", v: "英语" },
                    { n: "粤语", v: "粤语" },
                    { n: "其它", v: "其它" }
                ]
            },
            {
                key: "year",
                name: "年份",
                value: [
                    { n: "全部", v: "" },
                    { n: "2024", v: "2024" },
                    { n: "2023", v: "2023" },
                    { n: "2022", v: "2022" },
                    { n: "2021", v: "2021" }
                ]
            },
            {
                key: "by",
                name: "排序",
                value: [
                    { n: "全部", v: "" },
                    { n: "时间", v: "time" },
                    { n: "人气", v: "hits" },
                    { n: "评分", v: "score" }
                ]
            }
        ],
        dsj: [
            // 电视剧的筛选项配置
        ],
        zongyi: [
            // 综艺的筛选项配置
        ],
        dongman: [
            // 动漫的筛选项配置
        ]
    },
    staticFilter_def: {
        dianying: { class: '儿童' },
        dsj: { cateId: '2' },
        zongyi: { cateId: '3' },
        dongman: { cateId: '4' }
    },
};

var rule = {
    author: siteConfig.author,
    title: siteConfig.title,
    host: siteConfig.host,
    hostJs: siteConfig.hostJs,
    url: siteConfig.url,
    filter_url: siteConfig.filter_url,
    searchable: siteConfig.other.searchable,
    quickSearch: siteConfig.other.quickSearch,
    filterable: siteConfig.other.filterable,
    headers: siteConfig.headers,
    play_parse: siteConfig.other.play_parse,
    limit: siteConfig.other.limit,
    double: siteConfig.other.double,
    filter: siteConfig.staticFilter,
    filter_def: siteConfig.staticFilter_def,
    lazy: async function () {
        let {
            input,
            pdfa,
            pdfh,
            pd
        } = this;
        const html = JSON.parse((await req(input)).content.match(/r player_.*?=(.*?)</)[1]);
        let url = html.url;
        if (html.encrypt == "1") {
            url = unescape(url);
            return {
                parse: 0,
                url: url
            };
        } else if (html.encrypt == "2") {
            url = unescape(base64Decode(url));
            return {
                parse: 0,
                url: url
            };
        }
        if (/m3u8|mp4/.test(url)) {
            input = url;
            return {
                parse: 0,
                url: input
            };
        } else {
            return {
                parse: 1,
                url: input
            };
        }
    },
    class_parse: async function () {
        const { input, pdfa, pdfh, pd } = this;
        const filters = {};

        if (!siteConfig.dynamicClass) {
            const classes = siteConfig.staticClass.class_name.map((name, index) => {
                return {
                    type_id: siteConfig.staticClass.class_url[index],
                    type_name: name
                };
            });

            // 初始化 filter_def
            this.filter_def = classes.reduce((acc, { type_id, type_name }) => {
                acc[type_id] = {
                    cateId: type_id,
                    type_name: type_name
                };
                return acc;
            }, {});

            if (siteConfig.useStaticFilterDef) {
                // 使用静态筛选的默认值
                classes.forEach(item => {
                    if (siteConfig.staticFilter_def[item.type_id]) {
                        this.filter_def[item.type_id] = siteConfig.staticFilter_def[item.type_id];
                    }
                });
            }

            if (!siteConfig.dynamicFilter) {
                // 动态获取分类的 type_id 并赋值对应的静态筛选项
                classes.forEach(item => {
                    if (siteConfig.staticFilter[item.type_id]) {
                        filters[item.type_id] = siteConfig.staticFilter[item.type_id];
                    }
                });
            } else {
                const htmlUrl = classes.map((item) => ({
                    url: `${this.host}${siteConfig.filter.urlPattern.replace('{type_id}', item.type_id)}`,
                    options: { timeout: this.timeout, headers: this.headers },
                }));
                const htmlArr = await batchFetch(htmlUrl);

                if (!htmlArr || htmlArr.length === 0) {
                    return { class: classes, filters: {} };
                }

                const keyRegexMap = Object.entries(siteConfig.filter).reduce((acc, [key, value]) => {
                    if (key.endsWith('Regex')) {
                        const regexKey = key.replace('Regex', '');
                        acc[regexKey] = value;
                    }
                    return acc;
                }, {});

                htmlArr.forEach((htmlContent, i) => {
                    const type_id = classes[i].type_id;
                    const data = pdfa(htmlContent, siteConfig.filter.filterElement);
                    const categories = [];
                    const moduleTitles = [...new Set(data.map(item => pdfh(item, siteConfig.filter.moduleItemTitle).trim()))];

                    moduleTitles.forEach(title => {
                        if (title) {
                            if (siteConfig.excludeFilterNames.includes(title)) {
                                return;
                            }
                            const key = siteConfig.keyMap[title] || title.toLowerCase().replace(/[^a-zA-Z]/g, '');
                            categories.push({
                                key: key,
                                name: title,
                            });
                        }
                    });

                    filters[type_id] = categories
                        .map((category) => {
                            const filteredData = data.filter((item) =>
                                pdfh(item, siteConfig.filter.moduleItemTitle).trim() === category.name
                            )[0] || [];

                            if (filteredData.length === 0) return null;

                            const values = pdfa(filteredData, siteConfig.filter.filterItem)
                                .map((it) => {
                                    const href = pdfh(it, 'a&&href');
                                    const text = pdfh(it, 'a&&Text').trim().replace(/^"|"$/g, '');
                                    let v = '';

                                    const regex = keyRegexMap[category.key];
                                    if (regex) {
                                        const match = href.match(regex);
                                        if (match) {
                                            v = decodeURIComponent(match[1]);
                                        }
                                    } else {
                                        v = text;
                                    }

                                    return {
                                        n: text,
                                        v: v === '全部' ? '' : v,
                                    };
                                })
                                .filter(Boolean);

                            if (values.length === 0) return null;

                            return { key: category.key, name: category.name, value: values };
                        })
                        .filter(Boolean);
                });
            }

            return { class: classes, filters };
        } else {
            const html = await request(input, { headers: this.headers });
            const data = pdfa(html, siteConfig.class.parseElement);
            const classes = data
                .map((it) => {
                    const href = pdfh(it, 'a&&href');
                    const type_idMatch = href.match(siteConfig.class.type_idRegex);
                    const type_name = pdfh(it, siteConfig.class.type_nameElement);

                    if (!type_idMatch || siteConfig.class.excludeNames.includes(type_name)) return null;
                    const type_id = type_idMatch[1];
                    return { type_id, type_name };
                })
                .filter(Boolean);

            if (classes.length === 0) {
                return { class: [], filters: {} };
            }

            this.filter_def = classes.reduce((acc, { type_id, type_name }) => {
                acc[type_id] = { cateId: type_id, type_name: type_name };
                return acc;
            }, {});

            if (siteConfig.useStaticFilterDef) {
                // 使用静态筛选的默认值
                classes.forEach(item => {
                    if (siteConfig.staticFilter_def[item.type_id]) {
                        this.filter_def[item.type_id] = siteConfig.staticFilter_def[item.type_id];
                    }
                });
            }

            if (!siteConfig.dynamicFilter) {
                classes.forEach(item => {
                    if (siteConfig.staticFilter[item.type_id]) {
                        filters[item.type_id] = siteConfig.staticFilter[item.type_id];
                    }
                });
            } else {
            const htmlUrl = classes.map((item) => ({
                url: `${this.host}${siteConfig.filter.urlPattern.replace('{type_id}', item.type_id)}`,
                options: { timeout: this.timeout, headers: this.headers },
            }));
            const htmlArr = await batchFetch(htmlUrl);

            if (!htmlArr || htmlArr.length === 0) {
                return { class: classes, filters: {} };
            }

            const keyRegexMap = Object.entries(siteConfig.filter).reduce((acc, [key, value]) => {
                if (key.endsWith('Regex')) {
                    const regexKey = key.replace('Regex', '');
                    acc[regexKey] = value;
                }
                return acc;
            }, {});

            htmlArr.forEach((htmlContent, i) => {
                const type_id = classes[i].type_id;
                const data = pdfa(htmlContent, siteConfig.filter.filterElement);
                const categories = [];
                const moduleTitles = [...new Set(data.map(item => pdfh(item, siteConfig.filter.moduleItemTitle).trim()))];

                moduleTitles.forEach(title => {
                    if (title) {
                        if (siteConfig.excludeFilterNames.includes(title)) {
                            return;
                        }
                        const key = siteConfig.keyMap[title] || title.toLowerCase().replace(/[^a-zA-Z]/g, '');
                        categories.push({
                            key: key,
                            name: title,
                        });
                    }
                });

                filters[type_id] = categories
                    .map((category) => {
                        const filteredData = data.filter((item) =>
                            pdfh(item, siteConfig.filter.moduleItemTitle).trim() === category.name
                        )[0] || [];

                        if (filteredData.length === 0) return null;

                        const values = pdfa(filteredData, siteConfig.filter.filterItem)
                            .map((it) => {
                                const href = pdfh(it, 'a&&href');
                                const text = pdfh(it, 'a&&Text').trim().replace(/^"|"$/g, '');
                                let v = '';

                                const regex = keyRegexMap[category.key];
                                if (regex) {
                                    const match = href.match(regex);
                                    if (match) {
                                        v = decodeURIComponent(match[1]);
                                    }
                                } else {
                                    v = text;
                                }

                                return {
                                    n: text,
                                    v: v === '全部' ? '' : v,
                                };
                            })
                            .filter(Boolean);

                        if (values.length === 0) return null;

                        return { key: category.key, name: category.name, value: values };
                    })
                    .filter(Boolean);
            });
            }

            return { class: classes, filters };
        }
    },

    推荐: async function (tid, pg, filter, extend) {
        if (siteConfig.useCustomRecommend) {
            let { input, pdfa, pdfh, pd } = this;
            let html = await request(input);
            let d = [];
            let data = pdfa(html, siteConfig.recommend.element);
            data.forEach((it) => {
                d.push({
                    title: pdfh(it, siteConfig.recommend.titleElement),
                    pic_url: pd(it, siteConfig.recommend.picUrlElement),
                    desc: pdfh(it, siteConfig.recommend.descElement),
                    url: pd(it, siteConfig.recommend.urlElement),
                    details: pdfh(it, siteConfig.recommend.detailsElement),
                });
            });
            return setResult(d);
        } else {
            return this.一级();
        }
    },

    一级: async function (tid, pg, filter, extend) {
        let { input, pdfa, pdfh, pd } = this;
        let html = await request(input);
        let d = [];
        let data = pdfa(html, siteConfig.level1.element);
        data.forEach((it) => {
            d.push({
                title: pdfh(it, siteConfig.level1.titleElement),
                pic_url: pd(it, siteConfig.level1.picUrlElement),
                desc: pdfh(it, siteConfig.level1.descElement),
                url: pd(it, siteConfig.level1.urlElement),
                details: pdfh(it, siteConfig.recommend.detailsElement),
            });
        });
        return setResult(d);
    },

    二级: async function (ids) {
        let { input, pdfa, pdfh, pd } = this;
        let html = await request(input);
        let VOD = {};
        VOD.vod_name = pdfh(html, siteConfig.level2.vodNameElement);
        VOD.type_name = pdfh(html, siteConfig.level2.typeNameElement);
        VOD.vod_remarks = pdfh(html, siteConfig.level2.vodRemarksElement);
        VOD.vod_year = pdfh(html, siteConfig.level2.vodYearElement);
        VOD.vod_area = pdfh(html, siteConfig.level2.vodAreaElement);
        VOD.vod_actor = pdfh(html, siteConfig.level2.vodActorElement);
        VOD.vod_director = pdfh(html, siteConfig.level2.vodDirectorElement);
        VOD.vod_content = pdfh(html, siteConfig.level2.vodContentElement);

        let playlist = pdfa(html, siteConfig.level2.playlistElement);
        let tabs = pdfa(html, siteConfig.level2.tabsElement);
        let playmap = {};
        tabs.forEach((item, i) => {
            const form = pdfh(item, siteConfig.level2.playFromTextElement);
            const list = playlist[i];
            const a = pdfa(list, siteConfig.level2.playListElement);
            a.forEach((it) => {
                let title = pdfh(it, siteConfig.level2.playTitleElement);
                let urls = pd(it, siteConfig.level2.playUrlElement, input);
                if (!playmap.hasOwnProperty(form)) {
                    playmap[form] = [];
                }
                playmap[form].push(title + "$" + urls);
            });
        });
        VOD.vod_play_from = Object.keys(playmap).join('$$$');
        const urls = Object.values(playmap);
        const playUrls = urls.map((urllist) => {
            return urllist.join("#");
        });
        VOD.vod_play_url = playUrls.join('$$$');
        return VOD;
    },

    搜索: async function (wd, quick, pg) {
        let { input, pdfa, pdfh, pd } = this;
        let html = await request(input);
        let d = [];
        let data = pdfa(html, siteConfig.search.element);
        data.forEach((it) => {
            d.push({
                title: pdfh(it, siteConfig.search.titleElement),
                pic_url: pd(it, siteConfig.search.picUrlElement),
                desc: pdfh(it, siteConfig.search.descElement),
                url: pd(it, siteConfig.search.urlElement),
                content: pdfh(it, siteConfig.search.contentElement),
            });
        });
        return setResult(d);
    }
};

// 示例：调用class_parse函数获取分类和筛选项
(async function () {
    try {
        const result = await rule.class_parse();
        console.log('是否使用动态分类:', siteConfig.dynamicClass);
        console.log('是否启用动态筛选:', siteConfig.dynamicFilter);
        console.log('是否使用静态筛选默认值:', siteConfig.useStaticFilterDef);
        console.log('排除的筛选分类:', siteConfig.excludeFilterNames);
        console.log('是否使用自定义推荐:', siteConfig.useCustomRecommend);
        console.log('分类和筛选项:', result);
    } catch (error) {
        console.error('错误:', error);
    }
})();
