async function categoryContent(tid, pg, filter, extend) {
    const link = `${baseUrl}/index.php/vod/show/id/${tid}/page/${pg}.html`;
    const html = await request(link); // 假設你已有封裝好的 request 函數
    const $ = cheerio.load(html);
    
    let videos = [];
    $('.hl-vod-list > li.hl-list-item').each((i, el) => {
        const a = $(el).find('a.hl-item-thumb');
        const title = a.attr('title');
        const href = a.attr('href');
        const img = a.attr('data-original');
        const remarks = $(el).find('.remarks').text();
        
        // 提取 ID：從 /index.php/vod/detail/id/9944.html 中匹配數字
        const idMatch = href.match(/id\/(\d+)\.html/);
        const id = idMatch ? idMatch[1] : "";

        videos.push({
            vod_id: id,
            vod_name: title,
            vod_pic: img,
            vod_remarks: remarks
        });
    });

    // 提取總頁數：從 "1 / 836頁" 中解析
    const pageText = $('.hl-page-total').text();
    const pageCountMatch = pageText.match(/\/ *(\d+)頁/);
    const pageCount = pageCountMatch ? parseInt(pageCountMatch[1]) : pg;

    return {
        page: parseInt(pg),
        pagecount: pageCount,
        limit: videos.length,
        total: videos.length * pageCount, // 估算總數
        list: videos
    };
}
