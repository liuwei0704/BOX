var rule = {
    author: 'Jack',
    title: '影视狗',
    类型: '影视',
    host: 'https://www.yingshi.dog',
    headers: {
    'User-Agent': 'MOBILE_UA',
    'Referer': '',
     'Cookie': ''
       },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: '/',
//  filter_url: '{{fl.cateId}}-{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}-{{fl.letter}}---fypage---{{fl.year}}',
//filter_url: '{{fl.area}}{{fl.by}}{{fl.class}}/id/{{fl.cateId}}{{fl.lang}}{{fl.letter}}/page/fypage{{fl.year}}',
//https://m.jngcxy.cn/show/7-大陆-------2---.html 
      url: 'https://www.yingshi.dog/vodshow/fyfilter.html',
   filter_url: '{{fl.area}}{{fl.by}}{{fl.class}}/id/{{fl.cateId}}{{fl.lang}}{{fl.letter}}/page/fypage{{fl.year}}',
    detailUrl: 'https://www.yingshi.dog/voddetail/fyid.html',
  
 searchUrl: 'https://www.yingshi.dog/vodsearch/page/fypage/wd/**.html',

  搜索: '.module-card-item.module-item;.lazyload&&alt;.lazyload&&data-original;.module-item-note&&Text;a&&href',

 // searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',

    //搜索: 'json:list;name;pic;en;id',  

    searchable: 2,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '电影&电视剧&综艺&动漫&短剧',
    //静态分类值
    class_url: '1&2&3&4&47',
    
    filter_def: {
        1: {
            cateId: '1'
        },
        2: {
            cateId: '2'
        },
        3: {
            cateId: '3'
        },
        4: {
            cateId: '4'
        },
        
     47: {
            cateId: '47'
        },
    },
    推荐: '*',
    一级: $js.toString(() => {
    let klist = pdfa(request(input), 'a:has(.module-item-pic)');
    let k = klist.map(it => ({
        title: pdfh(it, 'a&&title'),
        //pic_url: 'https://xsc.jngcxy.cn/' + pdfh(it, 'img&&data-original'),
        pic_url: pdfh(it, '.lazyload&&data-original'),
        desc: pdfh(it, '.module-item-note&&Text'),
        url: pdfh(it, 'a&&href'),
        content: ''
    }));
    setResult(k);
}),
      
    二级: $js.toString(() => {
    let html = request(input);
  VOD = {
    vod_id: input,
    vod_name: pdfh(html, '.vod-title-main&&Text') || '',
    type_name: (pdfh(html, '.vod-title-meta&&Text') || '').replace(/年·|剧/g, ''),
    vod_pic: pd(html, '.module-item-pic img&&data-original', input) || '',
    vod_remarks: pdfh(html, '.module-info-item:contains(进度) .module-info-item-content:last-child&&Text') || '',
    vod_year: (pdfh(html, '.vod-title-meta&&Text') || '').match(/\d{4}/)?.[0] || '',
    vod_area: pdfh(html, '.module-info-tag-link a:contains(日本)&&Text') || '',
    vod_director: pdfh(html, '.module-info-item:contains(导演) .module-info-item-content&&Text') || '',
    vod_actor: pdfh(html, '.module-info-item:contains(主演) .module-info-item-content&&Text') || '',
    vod_content: pdfh(html, '.module-info-introduction-content p&&Text') || ''

}; 
    // 播放源和剧集列表
    
    let jinput = pd(html, '.module-play-list-link&&a&&href', HOST); 
 let r_ktabs = pdfa(request(jinput),'.module-tab-item.tab-item');
 let ktabs = r_ktabs.map(it => pdfh(it, 'span&&Text'));
 VOD.vod_play_from = ktabs.join('$$$');
 
    
    let klists = [];
 let r_plists = pdfa(request(jinput), '.module-play-list-content');
 r_plists.forEach((rp) => {
     let klist = pdfa(rp, 'a').map((it) => {
     return pdfh(it, 'span&&Text') + '$' + pd(it, 'a&&href', input);
     });
     klist = klist.join('#');
     klists.push(klist);
 });
 VOD.vod_play_url = klists.join('$$$')
}),
//是否启用辅助嗅探: 1,0
    sniffer: 0,
    // 辅助嗅探规则
    isVideo: 'http((?!http).){26,}\\.(m3u8|mp4|flv|avi|mkv|wmv|mpg|mpeg|mov|ts|3gp|rm|rmvb|asf|m4a|mp3|wma)',

  play_parse: true,
    //播放地址通用解析
   lazy: $js.toString(() => {
let kcode = JSON.parse(fetch(input).split('aaaa=')[1].split('<')[0]);
let kurl = kcode.url;
if (/\.(m3u8|mp4)/.test(kurl)) {
    input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
} else {
    input = { jx: 0, parse: 1, url: input }
}
}),
"filter": {
    "1": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "动作片", "v": "9"},
          {"n": "喜剧片", "v": "10"},
          {"n": "爱情片", "v": "11"},
          {"n": "犯罪片", "v": "13"},
          {"n": "恐怖片", "v": "14"},
          {"n": "科幻片", "v": "12"},
          {"n": "悬疑片", "v": "15"},
          {"n": "剧情片", "v": "18"},
          {"n": "动画片", "v": "19"},
          {"n": "战争片", "v": "20"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "喜剧", "v": "/class/喜剧"},
          {"n": "爱情", "v": "/class/爱情"},
          {"n": "恐怖", "v": "/class/恐怖"},
          {"n": "动作", "v": "/class/动作"},
          {"n": "科幻", "v": "/class/科幻"},
          {"n": "剧情", "v": "/class/剧情"},
          {"n": "战争", "v": "/class/战争"},
          {"n": "犯罪", "v": "/class/犯罪"},
          {"n": "动画", "v": "/class/动画"},
          {"n": "奇幻", "v": "/class/奇幻"},
          {"n": "武侠", "v": "/class/武侠"},
          {"n": "冒险", "v": "/class/冒险"},
          {"n": "悬疑", "v": "/class/悬疑"},
          {"n": "惊悚", "v": "/class/惊悚"},
          {"n": "经典", "v": "/class/经典"},
          {"n": "古装", "v": "/class/古装"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "中国", "v": "/area/中国"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "美国", "v": "/area/美国"},
          {"n": "韩国", "v": "/area/韩国"},
          {"n": "法国", "v": "/area/法国"},
          {"n": "英国", "v": "/area/英国"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "德国", "v": "/area/德国"},
          {"n": "泰国", "v": "/area/泰国"},
          {"n": "印度", "v": "/area/印度"},
          {"n": "意大利", "v": "/area/意大利"},
          {"n": "西班牙", "v": "/area/西班牙"},
          {"n": "加拿大", "v": "/area/加拿大"},
          {"n": "其它", "v": "/area/其它"}
        ]
      },
      {
        "key": "lang",
        "name": "语言",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "普通话", "v": "/lang/普通话"},
          {"n": "英语", "v": "/lang/英语"},
          {"n": "粤语", "v": "/lang/粤语"},
          {"n": "闽南语", "v": "/lang/闽南语"},
          {"n": "韩语", "v": "/lang/韩语"},
          {"n": "日语", "v": "/lang/日语"},
          {"n": "法语", "v": "/lang/法语"},
          {"n": "德语", "v": "/lang/德语"},
          {"n": "其它", "v": "/lang/其它"}
        ]
      },
      {
        "key": "year",
        "name": "年份",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "2025", "v": "/year/2025"},
          {"n": "2024", "v": "/year/2024"},
          {"n": "2023", "v": "/year/2023"},
          {"n": "2022", "v": "/year/2022"},
          {"n": "2021", "v": "/year/2021"},
          {"n": "2020", "v": "/year/2020"},
          {"n": "2019", "v": "/year/2019"},
          {"n": "2018", "v": "/year/2018"},
          {"n": "2017", "v": "/year/2017"},
          {"n": "2016", "v": "/year/2016"},
          {"n": "2015", "v": "/year/2015"},
          {"n": "2014", "v": "/year/2014"},
          {"n": "2013", "v": "/year/2013"},
          {"n": "2012", "v": "/year/2012"},
          {"n": "2011", "v": "/year/2011"},
          {"n": "2010", "v": "/year/2010"},
          {"n": "2009", "v": "/year/2009"},
          {"n": "2008", "v": "/year/2008"}
        ]
      },
      {
        "key": "letter",
        "name": "字母",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "A", "v": "/letter/A"},
          {"n": "B", "v": "/letter/B"},
          {"n": "C", "v": "/letter/C"},
          {"n": "D", "v": "/letter/D"},
          {"n": "E", "v": "/letter/E"},
          {"n": "F", "v": "/letter/F"},
          {"n": "G", "v": "/letter/G"},
          {"n": "H", "v": "/letter/H"},
          {"n": "I", "v": "/letter/I"},
          {"n": "J", "v": "/letter/J"},
          {"n": "K", "v": "/letter/K"},
          {"n": "L", "v": "/letter/L"},
          {"n": "M", "v": "/letter/M"},
          {"n": "N", "v": "/letter/N"},
          {"n": "O", "v": "/letter/O"},
          {"n": "P", "v": "/letter/P"},
          {"n": "Q", "v": "/letter/Q"},
          {"n": "R", "v": "/letter/R"},
          {"n": "S", "v": "/letter/S"},
          {"n": "T", "v": "/letter/T"},
          {"n": "U", "v": "/letter/U"},
          {"n": "V", "v": "/letter/V"},
          {"n": "W", "v": "/letter/W"},
          {"n": "X", "v": "/letter/X"},
          {"n": "Y", "v": "/letter/Y"},
          {"n": "Z", "v": "/letter/Z"},
          {"n": "0-9", "v": "/letter/0-9"}
        ]
      },
      {
        "key": "by",
        "name": "排序",
        "value": [
          {"n": "更新时间", "v": "/by/time"},
          {"n": "最多播放", "v": "/by/hits"},
          {"n": "实时热播", "v": "/by/hits_day"},
          {"n": "本周热播", "v": "/by/hits_week"},
          {"n": "本月热播", "v": "/by/hits_month"},
          {"n": "新片上线", "v": "/by/time_add"}
        ]
      }
    ],


    "2": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国产剧", "v": "22"},
          {"n": "香港剧", "v": "23"},
          {"n": "台湾剧", "v": "24"},
          {"n": "欧美剧", "v": "25"},
          {"n": "日本剧", "v": "27"},
          {"n": "韩国剧", "v": "28"},
          {"n": "东南亚", "v": "29"},
          {"n": "其他剧", "v": "30"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "爱情", "v": "/class/爱情"},
          {"n": "古装", "v": "/class/古装"},
          {"n": "战争", "v": "/class/战争"},
          {"n": "青春", "v": "/class/青春"},
          {"n": "偶像", "v": "/class/偶像"},
          {"n": "喜剧", "v": "/class/喜剧"},
          {"n": "家庭", "v": "/class/家庭"},
          {"n": "犯罪", "v": "/class/犯罪"},
          {"n": "动作", "v": "/class/动作"},
          {"n": "奇幻", "v": "/class/奇幻"},
          {"n": "剧情", "v": "/class/剧情"},
          {"n": "历史", "v": "/class/历史"},
          {"n": "经典", "v": "/class/经典"},
          {"n": "其它", "v": "/class/其它"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "中国", "v": "/area/中国"},
          {"n": "韩国", "v": "/area/韩国"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "美国", "v": "/area/美国"},
          {"n": "泰国", "v": "/area/泰国"},
          {"n": "英国", "v": "/area/英国"},
          {"n": "新加坡", "v": "/area/新加坡"},
          {"n": "其它", "v": "/area/其它"}
        ]
      },
      {
        "key": "lang",
        "name": "语言",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "普通话", "v": "/lang/普通话"},
          {"n": "英语", "v": "/lang/英语"},
          {"n": "粤语", "v": "/lang/粤语"},
          {"n": "闽南语", "v": "/lang/闽南语"},
          {"n": "韩语", "v": "/lang/韩语"},
          {"n": "日语", "v": "/lang/日语"},
          {"n": "其它", "v": "/lang/其它"}
        ]
      },
      {
        "key": "year",
        "name": "年份",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "2025", "v": "/year/2025"},
          {"n": "2024", "v": "/year/2024"},
          {"n": "2023", "v": "/year/2023"},
          {"n": "2022", "v": "/year/2022"},
          {"n": "2021", "v": "/year/2021"},
          {"n": "2020", "v": "/year/2020"},
          {"n": "2019", "v": "/year/2019"},
          {"n": "2018", "v": "/year/2018"},
          {"n": "2017", "v": "/year/2017"},
          {"n": "2016", "v": "/year/2016"},
          {"n": "2015", "v": "/year/2015"},
          {"n": "2014", "v": "/year/2014"},
          {"n": "2013", "v": "/year/2013"},
          {"n": "2012", "v": "/year/2012"},
          {"n": "2011", "v": "/year/2011"},
          {"n": "2010", "v": "/year/2010"},
          {"n": "2009", "v": "/year/2009"},
          {"n": "2008", "v": "/year/2008"}
        ]
      },
      {
        "key": "letter",
        "name": "字母",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "A", "v": "/letter/A"},
          {"n": "B", "v": "/letter/B"},
          {"n": "C", "v": "/letter/C"},
          {"n": "D", "v": "/letter/D"},
          {"n": "E", "v": "/letter/E"},
          {"n": "F", "v": "/letter/F"},
          {"n": "G", "v": "/letter/G"},
          {"n": "H", "v": "/letter/H"},
          {"n": "I", "v": "/letter/I"},
          {"n": "J", "v": "/letter/J"},
          {"n": "K", "v": "/letter/K"},
          {"n": "L", "v": "/letter/L"},
          {"n": "M", "v": "/letter/M"},
          {"n": "N", "v": "/letter/N"},
          {"n": "O", "v": "/letter/O"},
          {"n": "P", "v": "/letter/P"},
          {"n": "Q", "v": "/letter/Q"},
          {"n": "R", "v": "/letter/R"},
          {"n": "S", "v": "/letter/S"},
          {"n": "T", "v": "/letter/T"},
          {"n": "U", "v": "/letter/U"},
          {"n": "V", "v": "/letter/V"},
          {"n": "W", "v": "/letter/W"},
          {"n": "X", "v": "/letter/X"},
          {"n": "Y", "v": "/letter/Y"},
          {"n": "Z", "v": "/letter/Z"},
          {"n": "0-9", "v": "/letter/0-9"}
        ]
      },
      {
        "key": "by",
        "name": "排序",
        "value": [
          {"n": "更新时间", "v": "/by/time"},
          {"n": "最多播放", "v": "/by/hits"},
          {"n": "实时热播", "v": "/by/hits_day"},
          {"n": "本周热播", "v": "/by/hits_week"},
          {"n": "本月热播", "v": "/by/hits_month"},
          {"n": "新片上线", "v": "/by/time_add"}
        ]
      }
    ],

    "3": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "大陆综艺", "v": "31"},
          {"n": "港台综艺", "v": "32"},
          {"n": "日韩综艺", "v": "34"},
          {"n": "欧美综艺", "v": "36"},
          {"n": "其他综艺", "v": "37"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "选秀", "v": "/class/选秀"},
          {"n": "情感", "v": "/class/情感"},
          {"n": "访谈", "v": "/class/访谈"},
          {"n": "播报", "v": "/class/播报"},
          {"n": "旅游", "v": "/class/旅游"},
          {"n": "音乐", "v": "/class/音乐"},
          {"n": "美食", "v": "/class/美食"},
          {"n": "纪实", "v": "/class/纪实"},
          {"n": "曲艺", "v": "/class/曲艺"},
          {"n": "生活", "v": "/class/生活"},
          {"n": "游戏互动", "v": "/class/游戏互动"},
          {"n": "财经", "v": "/class/财经"},
          {"n": "求职", "v": "/class/求职"},
          {"n": "其它", "v": "/class/其它"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "中国", "v": "/area/中国"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "韩国", "v": "/area/韩国"},
          {"n": "欧美", "v": "/area/欧美"},
          {"n": "其它", "v": "/area/其它"}
        ]
      },
    
      {
        "key": "year",
        "name": "年份",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "2025", "v": "/year/2025"},
          {"n": "2024", "v": "/year/2024"},
          {"n": "2023", "v": "/year/2023"},
          {"n": "2022", "v": "/year/2022"},
          {"n": "2021", "v": "/year/2021"},
          {"n": "2020", "v": "/year/2020"},
          {"n": "2019", "v": "/year/2019"},
          {"n": "2018", "v": "/year/2018"},
          {"n": "2017", "v": "/year/2017"},
          {"n": "2016", "v": "/year/2016"},
          {"n": "2015", "v": "/year/2015"},
          {"n": "2014", "v": "/year/2014"},
          {"n": "2013", "v": "/year/2013"},
          {"n": "2012", "v": "/year/2012"},
          {"n": "2011", "v": "/year/2011"},
          {"n": "2010", "v": "/year/2010"},
          {"n": "2009", "v": "/year/2009"},
          {"n": "2008", "v": "/year/2008"}
        ]
      },
      {
        "key": "letter",
        "name": "字母",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "A", "v": "/letter/A"},
          {"n": "B", "v": "/letter/B"},
          {"n": "C", "v": "/letter/C"},
          {"n": "D", "v": "/letter/D"},
          {"n": "E", "v": "/letter/E"},
          {"n": "F", "v": "/letter/F"},
          {"n": "G", "v": "/letter/G"},
          {"n": "H", "v": "/letter/H"},
          {"n": "I", "v": "/letter/I"},
          {"n": "J", "v": "/letter/J"},
          {"n": "K", "v": "/letter/K"},
          {"n": "L", "v": "/letter/L"},
          {"n": "M", "v": "/letter/M"},
          {"n": "N", "v": "/letter/N"},
          {"n": "O", "v": "/letter/O"},
          {"n": "P", "v": "/letter/P"},
          {"n": "Q", "v": "/letter/Q"},
          {"n": "R", "v": "/letter/R"},
          {"n": "S", "v": "/letter/S"},
          {"n": "T", "v": "/letter/T"},
          {"n": "U", "v": "/letter/U"},
          {"n": "V", "v": "/letter/V"},
          {"n": "W", "v": "/letter/W"},
          {"n": "X", "v": "/letter/X"},
          {"n": "Y", "v": "/letter/Y"},
          {"n": "Z", "v": "/letter/Z"},
          {"n": "0-9", "v": "/letter/0-9"}
        ]
      },


      {
        "key": "by",
        "name": "排序",
        "value": [
          {"n": "更新时间", "v": "/by/time"},
          {"n": "最多播放", "v": "/by/hits"},
          {"n": "实时热播", "v": "/by/hits_day"},
          {"n": "本周热播", "v": "/by/hits_week"},
          {"n": "本月热播", "v": "/by/hits_month"},
          {"n": "新片上线", "v": "/by/time_add"}
        ]
      }
    ],

    "4": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国产动漫", "v": "38"},
          {"n": "日韩动漫", "v": "39"},
          {"n": "欧美动漫", "v": "40"},
          {"n": "其他动漫", "v": "41"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "科幻", "v": "/class/科幻"},
          {"n": "热血", "v": "/class/热血"},
          {"n": "推理", "v": "/class/推理"},
          {"n": "搞笑", "v": "/class/搞笑"},
          {"n": "冒险", "v": "/class/冒险"},
          {"n": "校园", "v": "/class/校园"},
          {"n": "动作", "v": "/class/动作"},
          {"n": "机战", "v": "/class/机战"},
          {"n": "运动", "v": "/class/运动"},
          {"n": "战争", "v": "/class/战争"},
          {"n": "少年", "v": "/class/少年"},
          {"n": "少女", "v": "/class/少女"},
          {"n": "社会", "v": "/class/社会"},
          {"n": "原创", "v": "/class/原创"},
          {"n": "亲子", "v": "/class/亲子"},
          {"n": "益智", "v": "/class/益智"},
          {"n": "励志", "v": "/class/励志"},
          {"n": "其它", "v": "/class/其它"}
        ]
      },
    
  

      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "中国", "v": "/area/中国"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "美国", "v": "/area/美国"},
          {"n": "韩国", "v": "/area/韩国"},
          {"n": "法国", "v": "/area/法国"},
          {"n": "英国", "v": "/area/英国"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "德国", "v": "/area/德国"},
          {"n": "泰国", "v": "/area/泰国"},
          {"n": "印度", "v": "/area/印度"},
          {"n": "意大利", "v": "/area/意大利"},
          {"n": "西班牙", "v": "/area/西班牙"},
          {"n": "加拿大", "v": "/area/加拿大"},
          {"n": "其它", "v": "/area/其它"}
        ]
      },
      {
        "key": "lang",
        "name": "语言",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "普通话", "v": "/lang/普通话"},
          {"n": "英语", "v": "/lang/英语"},
          {"n": "粤语", "v": "/lang/粤语"},
          {"n": "闽南语", "v": "/lang/闽南语"},
          {"n": "韩语", "v": "/lang/韩语"},
          {"n": "日语", "v": "/lang/日语"},
          {"n": "法语", "v": "/lang/法语"},
          {"n": "德语", "v": "/lang/德语"},
          {"n": "其它", "v": "/lang/其它"}
        ]
      },
      {
        "key": "year",
        "name": "年份",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "2025", "v": "/year/2025"},
          {"n": "2024", "v": "/year/2024"},
          {"n": "2023", "v": "/year/2023"},
          {"n": "2022", "v": "/year/2022"},
          {"n": "2021", "v": "/year/2021"},
          {"n": "2020", "v": "/year/2020"},
          {"n": "2019", "v": "/year/2019"},
          {"n": "2018", "v": "/year/2018"},
          {"n": "2017", "v": "/year/2017"},
          {"n": "2016", "v": "/year/2016"},
          {"n": "2015", "v": "/year/2015"},
          {"n": "2014", "v": "/year/2014"},
          {"n": "2013", "v": "/year/2013"},
          {"n": "2012", "v": "/year/2012"},
          {"n": "2011", "v": "/year/2011"},
          {"n": "2010", "v": "/year/2010"},
          {"n": "2009", "v": "/year/2009"},
          {"n": "2008", "v": "/year/2008"}
        ]
      },
      {
        "key": "letter",
        "name": "字母",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "A", "v": "/letter/A"},
          {"n": "B", "v": "/letter/B"},
          {"n": "C", "v": "/letter/C"},
          {"n": "D", "v": "/letter/D"},
          {"n": "E", "v": "/letter/E"},
          {"n": "F", "v": "/letter/F"},
          {"n": "G", "v": "/letter/G"},
          {"n": "H", "v": "/letter/H"},
          {"n": "I", "v": "/letter/I"},
          {"n": "J", "v": "/letter/J"},
          {"n": "K", "v": "/letter/K"},
          {"n": "L", "v": "/letter/L"},
          {"n": "M", "v": "/letter/M"},
          {"n": "N", "v": "/letter/N"},
          {"n": "O", "v": "/letter/O"},
          {"n": "P", "v": "/letter/P"},
          {"n": "Q", "v": "/letter/Q"},
          {"n": "R", "v": "/letter/R"},
          {"n": "S", "v": "/letter/S"},
          {"n": "T", "v": "/letter/T"},
          {"n": "U", "v": "/letter/U"},
          {"n": "V", "v": "/letter/V"},
          {"n": "W", "v": "/letter/W"},
          {"n": "X", "v": "/letter/X"},
          {"n": "Y", "v": "/letter/Y"},
          {"n": "Z", "v": "/letter/Z"},
          {"n": "0-9", "v": "/letter/0-9"}
        ]
      },
      {
        "key": "by",
        "name": "排序",
        "value": [
          {"n": "更新时间", "v": "/by/time"},
          {"n": "最多播放", "v": "/by/hits"},
          {"n": "实时热播", "v": "/by/hits_day"},
          {"n": "本周热播", "v": "/by/hits_week"},
          {"n": "本月热播", "v": "/by/hits_month"},
          {"n": "新片上线", "v": "/by/time_add"}
        ]
      }
    ],
  
 
    "47": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "女频恋爱", "v": "53"},
          {"n": "反转爽剧", "v": "54"},
          {"n": "脑洞悬疑", "v": "55"},
          {"n": "年代穿越", "v": "56"},
          {"n": "古装仙侠", "v": "57"},
          {"n": "现代都市", "v": "58"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "爱情", "v": "/class/爱情"},
          {"n": "女尊", "v": "/class/女尊"},
          {"n": "古装", "v": "/class/古装"},
          {"n": "重生", "v": "/class/重生"},
          {"n": "穿越", "v": "/class/穿越"},
          {"n": "逆袭", "v": "/class/逆袭"},
          {"n": "恋爱", "v": "/class/恋爱"},
          {"n": "悬疑", "v": "/class/悬疑"},
          {"n": "现代", "v": "/class/现代"}
        ]
      },{
        "key": "by",
        "name": "排序",
        "value": [
          {"n": "更新时间", "v": "/by/time"},
          {"n": "最多播放", "v": "/by/hits"},
          {"n": "实时热播", "v": "/by/hits_day"},
          {"n": "本周热播", "v": "/by/hits_week"},
          {"n": "本月热播", "v": "/by/hits_month"},
          {"n": "新片上线", "v": "/by/time_add"}
        ]
      }
    
    ]
  
  }
}

    