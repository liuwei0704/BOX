<?php
// B站爬虫模板 - 单一分类无限细分 + 修复播放URL
//
header('Content-Type: application/json; charset=utf-8');

// 使用Apple CMS标准参数
$ac = $_GET['ac'] ?? 'detail';
$t = $_GET['t'] ?? '';
$pg = $_GET['pg'] ?? '1';
$f = $_GET['f'] ?? '';
$ids = $_GET['ids'] ?? '';
$wd = $_GET['wd'] ?? '';
$flag = $_GET['flag'] ?? '';
$id = $_GET['id'] ?? '';

// B站爬虫类
class BiliBiliSpider {
    private $categories = [];
    private $baseUrl = 'https://api.bilibili.com';
    
    public function __construct() {
        $this->initializeCategories();
    }
    
    // 初始化分类 - 只有B站一个一级分类
    private function initializeCategories() {
        // 只有一个一级分类：B站
        $this->categories = [
            '1' => ['name' => 'B站', 'tid' => 0, 'level' => 1, 'has_children' => true],
        ];

        // 初始化B站所有主要分区作为二级分类
        $this->initializeBilibiliCategories();
    }
    
    // 初始化B站所有分类
    private function initializeBilibiliCategories() {
        // B站主要分区
        $mainCategories = [
            ['id' => '1_1', 'name' => '动画', 'tid' => 1],
            ['id' => '1_2', 'name' => '番剧', 'tid' => 13],
            ['id' => '1_3', 'name' => '国创', 'tid' => 167],
            ['id' => '1_4', 'name' => '音乐', 'tid' => 3],
            ['id' => '1_5', 'name' => '舞蹈', 'tid' => 129],
            ['id' => '1_6', 'name' => '游戏', 'tid' => 4],
            ['id' => '1_7', 'name' => '知识', 'tid' => 36],
            ['id' => '1_8', 'name' => '科技', 'tid' => 188],
            ['id' => '1_9', 'name' => '运动', 'tid' => 234],
            ['id' => '1_10', 'name' => '汽车', 'tid' => 223],
            ['id' => '1_11', 'name' => '生活', 'tid' => 160],
            ['id' => '1_12', 'name' => '美食', 'tid' => 211],
            ['id' => '1_13', 'name' => '动物', 'tid' => 217],
            ['id' => '1_14', 'name' => '鬼畜', 'tid' => 119],
            ['id' => '1_15', 'name' => '时尚', 'tid' => 155],
            ['id' => '1_16', 'name' => '娱乐', 'tid' => 5],
            ['id' => '1_17', 'name' => '影视', 'tid' => 181],
            ['id' => '1_18', 'name' => '纪录片', 'tid' => 177],
            ['id' => '1_19', 'name' => '电影', 'tid' => 23],
            ['id' => '1_20', 'name' => '电视剧', 'tid' => 11],
            ['id' => '1_21', 'name' => '热门推荐', 'tid' => 0],
        ];

        foreach ($mainCategories as $cat) {
            $this->categories[$cat['id']] = [
                'name' => $cat['name'],
                'tid' => $cat['tid'],
                'level' => 2,
                'parent' => '1',
                'has_children' => $this->hasSubCategories($cat['tid'])
            ];
        }

        // 初始化所有子分类
        $this->initializeAllSubCategories();
    }
    
    // 检查是否有子分类
    private function hasSubCategories($tid) {
        $hasSubs = [1, 13, 167, 3, 129, 4, 36, 188, 234, 160, 5, 181];
        return in_array($tid, $hasSubs);
    }
    
    // 初始化所有子分类
    private function initializeAllSubCategories() {
        // 在 initializeAllSubCategories 方法中添加以下代码：

// 热门推荐细分
$this->addSubCategory('1_21', '1_21_1', '今日热门', 'hot_today');
$this->addSubCategory('1_21', '1_21_2', '本周热门', 'hot_week');
$this->addSubCategory('1_21', '1_21_3', '月度热门', 'hot_month');
$this->addSubCategory('1_21', '1_21_4', '年度热门', 'hot_year');
$this->addSubCategory('1_21', '1_21_5', '飙升榜', 'hot_soaring');
$this->addSubCategory('1_21', '1_21_6', '新人榜', 'hot_newcomer');

// 按地区细分
$this->addSubCategory('1', '1_22', '按地区', 'region_all');
$this->addSubCategory('1_22', '1_22_1', '中国大陆', 'region_china');
$this->addSubCategory('1_22', '1_22_2', '日本', 'region_japan');
$this->addSubCategory('1_22', '1_22_3', '韩国', 'region_korea');
$this->addSubCategory('1_22', '1_22_4', '美国', 'region_usa');
$this->addSubCategory('1_22', '1_22_5', '欧洲', 'region_europe');

// 按时间细分
$this->addSubCategory('1', '1_23', '按时间', 'time_all');
$this->addSubCategory('1_23', '1_23_1', '2025年', 'time_2025');
$this->addSubCategory('1_23', '1_23_2', '2024年', 'time_2024');
$this->addSubCategory('1_23', '1_23_3', '2023年', 'time_2023');
$this->addSubCategory('1_23', '1_23_4', '2022年', 'time_2022');
$this->addSubCategory('1_23', '1_23_5', '2021年', 'time_2021');
$this->addSubCategory('1_23', '1_23_6', '经典老番', 'time_classic');

// 按类型细分
$this->addSubCategory('1', '1_24', '按类型', 'genre_all');
$this->addSubCategory('1_24', '1_24_1', '搞笑', 'genre_funny');
$this->addSubCategory('1_24', '1_24_2', '治愈', 'genre_healing');
$this->addSubCategory('1_24', '1_24_3', '热血', 'genre_hotblood');
$this->addSubCategory('1_24', '1_24_4', '恋爱', 'genre_romance');
$this->addSubCategory('1_24', '1_24_5', '悬疑', 'genre_mystery');
$this->addSubCategory('1_24', '1_24_6', '恐怖', 'genre_horror');

// 按UP主细分
$this->addSubCategory('1', '1_25', '知名UP主', 'uper_all');
$this->addSubCategory('1_25', '1_25_1', '老番茄', 'uper_laofanqie');
$this->addSubCategory('1_25', '1_25_2', 'LexBurner', 'uper_lexburner');
$this->addSubCategory('1_25', '1_25_3', '敖厂长', 'uper_aochang');
$this->addSubCategory('1_25', '1_25_4', '王刚', 'uper_wanggang');
$this->addSubCategory('1_25', '1_25_5', '李子柒', 'uper_liziqi');
$this->addSubCategory('1_25', '1_25_6', '罗翔说刑法', 'uper_luoxiang');
        // 动画分区细分
        $this->addSubCategory('1_1', '1_1_1', 'MAD·AMV', 24);
        $this->addSubCategory('1_1', '1_1_2', 'MMD·3D', 25);
        $this->addSubCategory('1_1', '1_1_3', '短片·手书', 47);
        $this->addSubCategory('1_1', '1_1_4', '综合', 27);
        
        // 番剧分区细分
        $this->addSubCategory('1_2', '1_2_1', '连载动画', 33);
        $this->addSubCategory('1_2', '1_2_2', '完结动画', 32);
        $this->addSubCategory('1_2', '1_2_3', '资讯', 51);
        $this->addSubCategory('1_2', '1_2_4', '官方延伸', 152);
        
        // 国创分区细分
        $this->addSubCategory('1_3', '1_3_1', '国产动画', 153);
        $this->addSubCategory('1_3', '1_3_2', '国产原创', 168);
        $this->addSubCategory('1_3', '1_3_3', '布袋戏', 169);
        $this->addSubCategory('1_3', '1_3_4', '动态漫·广播剧', 195);
        
        // 音乐分区细分
        $this->addSubCategory('1_4', '1_4_1', '原创音乐', 28);
        $this->addSubCategory('1_4', '1_4_2', '翻唱', 31);
        $this->addSubCategory('1_4', '1_4_3', 'VOCALOID·UTAU', 30);
        $this->addSubCategory('1_4', '1_4_4', '演奏', 59);
        $this->addSubCategory('1_4', '1_4_5', 'MV', 193);
        $this->addSubCategory('1_4', '1_4_6', '音乐现场', 29);
        $this->addSubCategory('1_4', '1_4_7', '音乐综合', 130);
        
        // 舞蹈分区细分
        $this->addSubCategory('1_5', '1_5_1', '宅舞', 20);
        $this->addSubCategory('1_5', '1_5_2', '街舞', 198);
        $this->addSubCategory('1_5', '1_5_3', '明星舞蹈', 199);
        $this->addSubCategory('1_5', '1_5_4', '中国舞', 200);
        $this->addSubCategory('1_5', '1_5_5', '舞蹈综合', 154);
        
        // 游戏分区细分 - 三级分类
        $this->addSubCategory('1_6', '1_6_1', '单机游戏', 17);
        $this->addSubCategory('1_6', '1_6_2', '电子竞技', 171);
        $this->addSubCategory('1_6', '1_6_3', '手机游戏', 65);
        $this->addSubCategory('1_6', '1_6_4', '网络游戏', 172);
        $this->addSubCategory('1_6', '1_6_5', '桌游棋牌', 173);
        $this->addSubCategory('1_6', '1_6_6', 'GMV', 121);
        $this->addSubCategory('1_6', '1_6_7', '音游', 136);
        $this->addSubCategory('1_6', '1_6_8', 'Mugen', 19);
        
        // 游戏分区 - 四级分类（单机游戏细分）
        $this->addSubCategory('1_6_1', '1_6_1_1', '主机游戏', 17);
        $this->addSubCategory('1_6_1', '1_6_1_2', '独立游戏', 17);
        $this->addSubCategory('1_6_1', '1_6_1_3', 'Steam游戏', 17);
        
        // 知识分区细分
        $this->addSubCategory('1_7', '1_7_1', '科学科普', 201);
        $this->addSubCategory('1_7', '1_7_2', '社科人文', 124);
        $this->addSubCategory('1_7', '1_7_3', '财经', 207);
        $this->addSubCategory('1_7', '1_7_4', '校园学习', 208);
        $this->addSubCategory('1_7', '1_7_5', '职业职场', 209);
        $this->addSubCategory('1_7', '1_7_6', '野生技术协会', 122);
        
        // 生活分区细分
        $this->addSubCategory('1_11', '1_11_1', '搞笑', 138);
        $this->addSubCategory('1_11', '1_11_2', '日常', 21);
        $this->addSubCategory('1_11', '1_11_3', '手工', 161);
        $this->addSubCategory('1_11', '1_11_4', '绘画', 162);
        $this->addSubCategory('1_11', '1_11_5', '运动', 163);
        $this->addSubCategory('1_11', '1_11_6', '其他', 174);
        
        // 娱乐分区细分
        $this->addSubCategory('1_16', '1_16_1', '综艺', 71);
        $this->addSubCategory('1_16', '1_16_2', '明星', 137);
        $this->addSubCategory('1_16', '1_16_3', 'Korea相关', 131);
        
        // 影视分区细分
        $this->addSubCategory('1_17', '1_17_1', '影视杂谈', 182);
        $this->addSubCategory('1_17', '1_17_2', '影视剪辑', 183);
        $this->addSubCategory('1_17', '1_17_3', '短片', 85);
        $this->addSubCategory('1_17', '1_17_4', '预告·资讯', 184);
    // 科技分区细分 - 更多层级
    $this->addSubCategory('1_8', '1_8_1', '数码', 95);
    $this->addSubCategory('1_8', '1_8_2', '软件应用', 230);
    $this->addSubCategory('1_8', '1_8_3', '计算机技术', 231);
    $this->addSubCategory('1_8', '1_8_4', '工业工程', 232);
    $this->addSubCategory('1_8', '1_8_5', '机械', 233);
    $this->addSubCategory('1_8', '1_8_6', '极客DIY', 247);
    
    // 数码细分 - 四级分类
    $this->addSubCategory('1_8_1', '1_8_1_1', '手机测评', 95);
    $this->addSubCategory('1_8_1', '1_8_1_2', '电脑装机', 95);
    $this->addSubCategory('1_8_1', '1_8_1_3', '摄影摄像', 95);
    $this->addSubCategory('1_8_1', '1_8_1_4', '影音智能', 95);
    
    // 软件应用细分
    $this->addSubCategory('1_8_2', '1_8_2_1', '办公软件', 230);
    $this->addSubCategory('1_8_2', '1_8_2_2', '设计剪辑', 230);
    $this->addSubCategory('1_8_2', '1_8_2_3', '编程开发', 230);
    
    // 运动分区细分
    $this->addSubCategory('1_9', '1_9_1', '篮球', 235);
    $this->addSubCategory('1_9', '1_9_2', '足球', 249);
    $this->addSubCategory('1_9', '1_9_3', '健身', 164);
    $this->addSubCategory('1_9', '1_9_4', '竞技体育', 236);
    $this->addSubCategory('1_9', '1_9_5', '运动文化', 237);
    $this->addSubCategory('1_9', '1_9_6', '极限运动', 238);
    
    // 篮球细分
    $this->addSubCategory('1_9_1', '1_9_1_1', 'NBA', 235);
    $this->addSubCategory('1_9_1', '1_9_1_2', 'CBA', 235);
    $this->addSubCategory('1_9_1', '1_9_1_3', '街头篮球', 235);
    $this->addSubCategory('1_9_1', '1_9_1_4', '篮球教学', 235);
    
    // 健身细分
    $this->addSubCategory('1_9_3', '1_9_3_1', '力量训练', 164);
    $this->addSubCategory('1_9_3', '1_9_3_2', '瑜伽普拉提', 164);
    $this->addSubCategory('1_9_3', '1_9_3_3', '有氧运动', 164);
    $this->addSubCategory('1_9_3', '1_9_3_4', '健身餐食', 164);
    
    // 汽车分区细分
    $this->addSubCategory('1_10', '1_10_1', '汽车生活', 176);
    $this->addSubCategory('1_10', '1_10_2', '汽车文化', 224);
    $this->addSubCategory('1_10', '1_10_3', '汽车极客', 225);
    $this->addSubCategory('1_10', '1_10_4', '智能出行', 226);
    $this->addSubCategory('1_10', '1_10_5', '购车攻略', 227);
    
    // 汽车生活细分
    $this->addSubCategory('1_10_1', '1_10_1_1', '改装玩车', 176);
    $this->addSubCategory('1_10_1', '1_10_1_2', '摩托车', 176);
    $this->addSubCategory('1_10_1', '1_10_1_3', '赛车赛事', 176);
    $this->addSubCategory('1_10_1', '1_10_1_4', '自驾旅行', 176);
    
    // 生活分区更多细分
    $this->addSubCategory('1_11', '1_11_7', '亲子', 157);
    $this->addSubCategory('1_11', '1_11_8', '家居', 158);
    $this->addSubCategory('1_11', '1_11_9', '家装', 159);
    $this->addSubCategory('1_11', '1_11_10', '出行', 166);
    
    // 搞笑细分
    $this->addSubCategory('1_11_1', '1_11_1_1', '搞笑剪辑', 138);
    $this->addSubCategory('1_11_1', '1_11_1_2', '恶搞配音', 138);
    $this->addSubCategory('1_11_1', '1_11_1_3', '情景喜剧', 138);
    
    // 日常细分
    $this->addSubCategory('1_11_2', '1_11_2_1', '生活记录', 21);
    $this->addSubCategory('1_11_2', '1_11_2_2', '趣味生活', 21);
    $this->addSubCategory('1_11_2', '1_11_2_3', '旅行记录', 21);
    
    // 美食分区细分
    $this->addSubCategory('1_12', '1_12_1', '美食制作', 76);
    $this->addSubCategory('1_12', '1_12_2', '美食侦探', 212);
    $this->addSubCategory('1_12', '1_12_3', '美食测评', 213);
    $this->addSubCategory('1_12', '1_12_4', '田园美食', 214);
    $this->addSubCategory('1_12', '1_12_5', '美食记录', 215);
    
    // 美食制作细分
    $this->addSubCategory('1_12_1', '1_12_1_1', '中餐烹饪', 76);
    $this->addSubCategory('1_12_1', '1_12_1_2', '西点烘焙', 76);
    $this->addSubCategory('1_12_1', '1_12_1_3', '日韩料理', 76);
    $this->addSubCategory('1_12_1', '1_12_1_4', '街头小吃', 76);
    
    // 动物分区细分
    $this->addSubCategory('1_13', '1_13_1', '喵星人', 218);
    $this->addSubCategory('1_13', '1_13_2', '汪星人', 219);
    $this->addSubCategory('1_13', '1_13_3', '大熊猫', 220);
    $this->addSubCategory('1_13', '1_13_4', '野生动物', 221);
    $this->addSubCategory('1_13', '1_13_5', '爬宠', 222);
    $this->addSubCategory('1_13', '1_13_6', '动物综合', 75);
    
    // 喵星人细分
    $this->addSubCategory('1_13_1', '1_13_1_1', '猫咪日常', 218);
    $this->addSubCategory('1_13_1', '1_13_1_2', '猫咪养护', 218);
    $this->addSubCategory('1_13_1', '1_13_1_3', '猫咪搞笑', 218);
    
    // 鬼畜分区细分
    $this->addSubCategory('1_14', '1_14_1', '鬼畜调教', 22);
    $this->addSubCategory('1_14', '1_14_2', '音MAD', 26);
    $this->addSubCategory('1_14', '1_14_3', '鬼畜剧场', 126);
    $this->addSubCategory('1_14', '1_14_4', '教程演示', 127);
    
    // 鬼畜调教细分
    $this->addSubCategory('1_14_1', '1_14_1_1', '全明星', 22);
    $this->addSubCategory('1_14_1', '1_14_1_2', '明星鬼畜', 22);
    $this->addSubCategory('1_14_1', '1_14_1_3', '动漫鬼畜', 22);
    
    // 时尚分区细分
    $this->addSubCategory('1_15', '1_15_1', '美妆', 157);
    $this->addSubCategory('1_15', '1_15_2', '服饰', 158);
    $this->addSubCategory('1_15', '1_15_3', '时尚潮流', 159);
    $this->addSubCategory('1_15', '1_15_4', '仿妆', 192);
    $this->addSubCategory('1_15', '1_15_5', '穿搭', 189);
    
    // 美妆细分
    $this->addSubCategory('1_15_1', '1_15_1_1', '彩妆教程', 157);
    $this->addSubCategory('1_15_1', '1_15_1_2', '护肤心得', 157);
    $this->addSubCategory('1_15_1', '1_15_1_3', '美妆测评', 157);
    $this->addSubCategory('1_15_1', '1_15_1_4', '发型造型', 157);
    
    // 娱乐分区更多细分
    $this->addSubCategory('1_16', '1_16_4', '搞笑娱乐', 138);
    $this->addSubCategory('1_16', '1_16_5', '真人秀', 71);
    $this->addSubCategory('1_16', '1_16_6', '娱乐杂谈', 241);
    
    // 综艺细分
    $this->addSubCategory('1_16_1', '1_16_1_1', '国内综艺', 71);
    $this->addSubCategory('1_16_1', '1_16_1_2', '日韩综艺', 71);
    $this->addSubCategory('1_16_1', '1_16_1_3', '欧美综艺', 71);
    
    // 明星细分
    $this->addSubCategory('1_16_2', '1_16_2_1', '内地明星', 137);
    $this->addSubCategory('1_16_2', '1_16_2_2', '港台明星', 137);
    $this->addSubCategory('1_16_2', '1_16_2_3', '日韩明星', 137);
    $this->addSubCategory('1_16_2', '1_16_2_4', '欧美明星', 137);
    
    // 影视分区更多细分
    $this->addSubCategory('1_17', '1_17_5', '影视解说', 182);
    $this->addSubCategory('1_17', '1_17_6', '幕后花絮', 183);
    $this->addSubCategory('1_17', '1_17_7', '影视混剪', 85);
    
    // 影视解说细分
    $this->addSubCategory('1_17_5', '1_17_5_1', '电影解说', 182);
    $this->addSubCategory('1_17_5', '1_17_5_2', '电视剧解说', 182);
    $this->addSubCategory('1_17_5', '1_17_5_3', '动漫解说', 182);
    
    // 纪录片分区细分
    $this->addSubCategory('1_18', '1_18_1', '人文历史', 37);
    $this->addSubCategory('1_18', '1_18_2', '科学探索', 178);
    $this->addSubCategory('1_18', '1_18_3', '社会纪实', 179);
    $this->addSubCategory('1_18', '1_18_4', '自然生态', 180);
    $this->addSubCategory('1_18', '1_18_5', '旅行纪录片', 196);
    
    // 人文历史细分
    $this->addSubCategory('1_18_1', '1_18_1_1', '中国历史', 37);
    $this->addSubCategory('1_18_1', '1_18_1_2', '世界历史', 37);
    $this->addSubCategory('1_18_1', '1_18_1_3', '考古发现', 37);
    $this->addSubCategory('1_18_1', '1_18_1_4', '文化传承', 37);
    
    // 电影分区细分
    $this->addSubCategory('1_19', '1_19_1', '华语电影', 147);
    $this->addSubCategory('1_19', '1_19_2', '欧美电影', 145);
    $this->addSubCategory('1_19', '1_19_3', '日本电影', 146);
    $this->addSubCategory('1_19', '1_19_4', '韩国电影', 83);
    $this->addSubCategory('1_19', '1_19_5', '其他地区', 82);
    
    // 华语电影细分
    $this->addSubCategory('1_19_1', '1_19_1_1', '大陆电影', 147);
    $this->addSubCategory('1_19_1', '1_19_1_2', '香港电影', 147);
    $this->addSubCategory('1_19_1', '1_19_1_3', '台湾电影', 147);
    
    // 电视剧分区细分
    $this->addSubCategory('1_20', '1_20_1', '国产剧', 185);
    $this->addSubCategory('1_20', '1_20_2', '海外剧', 187);
    
    // 国产剧细分
    $this->addSubCategory('1_20_1', '1_20_1_1', '古装剧', 185);
    $this->addSubCategory('1_20_1', '1_20_1_2', '现代剧', 185);
    $this->addSubCategory('1_20_1', '1_20_1_3', '悬疑剧', 185);
    $this->addSubCategory('1_20_1', '1_20_1_4', '爱情剧', 185);
    $this->addSubCategory('1_20_1', '1_20_1_5', '家庭剧', 185);
    
    // 海外剧细分
    $this->addSubCategory('1_20_2', '1_20_2_1', '美剧', 187);
    $this->addSubCategory('1_20_2', '1_20_2_2', '韩剧', 187);
    $this->addSubCategory('1_20_2', '1_20_2_3', '日剧', 187);
    $this->addSubCategory('1_20_2', '1_20_2_4', '英剧', 187);
    $this->addSubCategory('1_20_2', '1_20_2_5', '泰剧', 187);
    
    // 音乐分区 - 更多深度细分
    $this->addSubCategory('1_4_1', '1_4_1_1', '流行音乐', 28);
    $this->addSubCategory('1_4_1', '1_4_1_2', '摇滚音乐', 28);
    $this->addSubCategory('1_4_1', '1_4_1_3', '电子音乐', 28);
    $this->addSubCategory('1_4_1', '1_4_1_4', '民谣音乐', 28);
    $this->addSubCategory('1_4_1', '1_4_1_5', '说唱音乐', 28);
    $this->addSubCategory('1_4_1', '1_4_1_6', '古风音乐', 28);

    // 翻唱细分
    $this->addSubCategory('1_4_2', '1_4_2_1', '华语翻唱', 31);
    $this->addSubCategory('1_4_2', '1_4_2_2', '日语翻唱', 31);
    $this->addSubCategory('1_4_2', '1_4_2_3', '英语翻唱', 31);
    $this->addSubCategory('1_4_2', '1_4_2_4', '韩语翻唱', 31);
    $this->addSubCategory('1_4_2', '1_4_2_5', 'ACG翻唱', 31);

    // VOCALOID细分
    $this->addSubCategory('1_4_3', '1_4_3_1', '初音未来', 30);
    $this->addSubCategory('1_4_3', '1_4_3_2', '洛天依', 30);
    $this->addSubCategory('1_4_3', '1_4_3_3', '镜音连', 30);
    $this->addSubCategory('1_4_3', '1_4_3_4', '巡音流歌', 30);
    $this->addSubCategory('1_4_3', '1_4_3_5', '言和', 30);

    // 演奏细分
    $this->addSubCategory('1_4_4', '1_4_4_1', '钢琴演奏', 59);
    $this->addSubCategory('1_4_4', '1_4_4_2', '吉他演奏', 59);
    $this->addSubCategory('1_4_4', '1_4_4_3', '小提琴演奏', 59);
    $this->addSubCategory('1_4_4', '1_4_4_4', '古筝演奏', 59);
    $this->addSubCategory('1_4_4', '1_4_4_5', '电子琴演奏', 59);

    // 舞蹈分区 - 更多细分
    $this->addSubCategory('1_5_1', '1_5_1_1', '萌系宅舞', 20);
    $this->addSubCategory('1_5_1', '1_5_1_2', '帅气宅舞', 20);
    $this->addSubCategory('1_5_1', '1_5_1_3', '双人宅舞', 20);
    $this->addSubCategory('1_5_1', '1_5_1_4', '团体宅舞', 20);

    // 街舞细分
    $this->addSubCategory('1_5_2', '1_5_2_1', 'Breaking', 198);
    $this->addSubCategory('1_5_2', '1_5_2_2', 'Popping', 198);
    $this->addSubCategory('1_5_2', '1_5_2_3', 'Locking', 198);
    $this->addSubCategory('1_5_2', '1_5_2_4', 'Hiphop', 198);
    $this->addSubCategory('1_5_2', '1_5_2_5', 'Krump', 198);

    // 中国舞细分
    $this->addSubCategory('1_5_4', '1_5_4_1', '古典舞', 200);
    $this->addSubCategory('1_5_4', '1_5_4_2', '民族舞', 200);
    $this->addSubCategory('1_5_4', '1_5_4_3', '现代舞', 200);
    $this->addSubCategory('1_5_4', '1_5_4_4', '芭蕾舞', 200);

    // 游戏分区 - 电子竞技深度细分
    $this->addSubCategory('1_6_2', '1_6_2_1', '英雄联盟', 171);
    $this->addSubCategory('1_6_2', '1_6_2_2', '王者荣耀', 171);
    $this->addSubCategory('1_6_2', '1_6_2_3', 'CS:GO', 171);
    $this->addSubCategory('1_6_2', '1_6_2_4', 'DOTA2', 171);
    $this->addSubCategory('1_6_2', '1_6_2_5', '守望先锋', 171);
    $this->addSubCategory('1_6_2', '1_6_2_6', 'VALORANT', 171);

    // 英雄联盟细分
    $this->addSubCategory('1_6_2_1', '1_6_2_1_1', 'LPL赛事', 171);
    $this->addSubCategory('1_6_2_1', '1_6_2_1_2', 'LCK赛事', 171);
    $this->addSubCategory('1_6_2_1', '1_6_2_1_3', '世界赛', 171);
    $this->addSubCategory('1_6_2_1', '1_6_2_1_4', '英雄教学', 171);
    $this->addSubCategory('1_6_2_1', '1_6_2_1_5', '赛事集锦', 171);

    // 手机游戏细分
    $this->addSubCategory('1_6_3', '1_6_3_1', '原神', 65);
    $this->addSubCategory('1_6_3', '1_6_3_2', '崩坏：星穹铁道', 65);
    $this->addSubCategory('1_6_3', '1_6_3_3', '明日方舟', 65);
    $this->addSubCategory('1_6_3', '1_6_3_4', '和平精英', 65);
    $this->addSubCategory('1_6_3', '1_6_3_5', '阴阳师', 65);
    $this->addSubCategory('1_6_3', '1_6_3_6', 'Fate/Grand Order', 65);

    // 网络游戏细分
    $this->addSubCategory('1_6_4', '1_6_4_1', '魔兽世界', 172);
    $this->addSubCategory('1_6_4', '1_6_4_2', '最终幻想14', 172);
    $this->addSubCategory('1_6_4', '1_6_4_3', '剑网3', 172);
    $this->addSubCategory('1_6_4', '1_6_4_4', '天涯明月刀', 172);
    $this->addSubCategory('1_6_4', '1_6_4_5', '逆水寒', 172);

    // 知识分区 - 科学科普深度细分
    $this->addSubCategory('1_7_1', '1_7_1_1', '物理学', 201);
    $this->addSubCategory('1_7_1', '1_7_1_2', '化学', 201);
    $this->addSubCategory('1_7_1', '1_7_1_3', '生物学', 201);
    $this->addSubCategory('1_7_1', '1_7_1_4', '天文学', 201);
    $this->addSubCategory('1_7_1', '1_7_1_5', '地理学', 201);
    $this->addSubCategory('1_7_1', '1_7_1_6', '数学', 201);

    // 社科人文细分
    $this->addSubCategory('1_7_2', '1_7_2_1', '历史学', 124);
    $this->addSubCategory('1_7_2', '1_7_2_2', '哲学', 124);
    $this->addSubCategory('1_7_2', '1_7_2_3', '心理学', 124);
    $this->addSubCategory('1_7_2', '1_7_2_4', '社会学', 124);
    $this->addSubCategory('1_7_2', '1_7_2_5', '经济学', 124);

    // 财经细分
    $this->addSubCategory('1_7_3', '1_7_3_1', '股票投资', 207);
    $this->addSubCategory('1_7_3', '1_7_3_2', '基金理财', 207);
    $this->addSubCategory('1_7_3', '1_7_3_3', '宏观经济', 207);
    $this->addSubCategory('1_7_3', '1_7_3_4', '商业分析', 207);
    $this->addSubCategory('1_7_3', '1_7_3_5', '创业指导', 207);

    // 校园学习细分
    $this->addSubCategory('1_7_4', '1_7_4_1', '考研备考', 208);
    $this->addSubCategory('1_7_4', '1_7_4_2', '高考冲刺', 208);
    $this->addSubCategory('1_7_4', '1_7_4_3', '语言学习', 208);
    $this->addSubCategory('1_7_4', '1_7_4_4', '技能培训', 208);
    $this->addSubCategory('1_7_4', '1_7_4_5', '公开课', 208);

    // 科技分区 - 计算机技术深度细分
    $this->addSubCategory('1_8_3', '1_8_3_1', '编程教学', 231);
    $this->addSubCategory('1_8_3', '1_8_3_2', '算法解析', 231);
    $this->addSubCategory('1_8_3', '1_8_3_3', '网络安全', 231);
    $this->addSubCategory('1_8_3', '1_8_3_4', '人工智能', 231);
    $this->addSubCategory('1_8_3', '1_8_3_5', '大数据', 231);

    // 编程教学细分
    $this->addSubCategory('1_8_3_1', '1_8_3_1_1', 'Python', 231);
    $this->addSubCategory('1_8_3_1', '1_8_3_1_2', 'Java', 231);
    $this->addSubCategory('1_8_3_1', '1_8_3_1_3', 'C++', 231);
    $this->addSubCategory('1_8_3_1', '1_8_3_1_4', 'JavaScript', 231);
    $this->addSubCategory('1_8_3_1', '1_8_3_1_5', 'Go语言', 231);

    // 人工智能细分
    $this->addSubCategory('1_8_3_4', '1_8_3_4_1', '机器学习', 231);
    $this->addSubCategory('1_8_3_4', '1_8_3_4_2', '深度学习', 231);
    $this->addSubCategory('1_8_3_4', '1_8_3_4_3', '计算机视觉', 231);
    $this->addSubCategory('1_8_3_4', '1_8_3_4_4', '自然语言处理', 231);

    // 运动分区 - 更多球类细分
    $this->addSubCategory('1_9', '1_9_7', '乒乓球', 235);
    $this->addSubCategory('1_9', '1_9_8', '羽毛球', 235);
    $this->addSubCategory('1_9', '1_9_9', '网球', 235);
    $this->addSubCategory('1_9', '1_9_10', '排球', 235);

    // 足球细分
    $this->addSubCategory('1_9_2', '1_9_2_1', '英超', 249);
    $this->addSubCategory('1_9_2', '1_9_2_2', '西甲', 249);
    $this->addSubCategory('1_9_2', '1_9_2_3', '意甲', 249);
    $this->addSubCategory('1_9_2', '1_9_2_4', '德甲', 249);
    $this->addSubCategory('1_9_2', '1_9_2_5', '法甲', 249);
    $this->addSubCategory('1_9_2', '1_9_2_6', '中超', 249);

    // 生活分区 - 手工深度细分
    $this->addSubCategory('1_11_3', '1_11_3_1', '木工制作', 161);
    $this->addSubCategory('1_11_3', '1_11_3_2', '皮具制作', 161);
    $this->addSubCategory('1_11_3', '1_11_3_3', '金属工艺', 161);
    $this->addSubCategory('1_11_3', '1_11_3_4', '布艺缝纫', 161);
    $this->addSubCategory('1_11_3', '1_11_3_5', '纸艺折纸', 161);

    // 绘画细分
    $this->addSubCategory('1_11_4', '1_11_4_1', '素描', 162);
    $this->addSubCategory('1_11_4', '1_11_4_2', '水彩', 162);
    $this->addSubCategory('1_11_4', '1_11_4_3', '油画', 162);
    $this->addSubCategory('1_11_4', '1_11_4_4', '板绘', 162);
    $this->addSubCategory('1_11_4', '1_11_4_5', '国画', 162);

    // 亲子细分
    $this->addSubCategory('1_11_7', '1_11_7_1', '育儿知识', 157);
    $this->addSubCategory('1_11_7', '1_11_7_2', '亲子游戏', 157);
    $this->addSubCategory('1_11_7', '1_11_7_3', '儿童教育', 157);
    $this->addSubCategory('1_11_7', '1_11_7_4', '母婴用品', 157);

    // 影视分区 - 按国家地区细分
    $this->addSubCategory('1_17', '1_17_8', '华语影视', 181);
    $this->addSubCategory('1_17', '1_17_9', '欧美影视', 181);
    $this->addSubCategory('1_17', '1_17_10', '日韩影视', 181);
    $this->addSubCategory('1_17', '1_17_11', '其他国家', 181);

    // 华语影视细分
    $this->addSubCategory('1_17_8', '1_17_8_1', '大陆影视', 181);
    $this->addSubCategory('1_17_8', '1_17_8_2', '香港影视', 181);
    $this->addSubCategory('1_17_8', '1_17_8_3', '台湾影视', 181);

    // 按评分细分
    $this->addSubCategory('1', '1_26', '按评分', 0);
    $this->addSubCategory('1_26', '1_26_1', '9分以上神作', 0);
    $this->addSubCategory('1_26', '1_26_2', '8-9分佳作', 0);
    $this->addSubCategory('1_26', '1_26_3', '7-8分良作', 0);
    $this->addSubCategory('1_26', '1_26_4', '6-7分普通', 0);

    // 按时长细分
    $this->addSubCategory('1', '1_27', '按时长', 0);
    $this->addSubCategory('1_27', '1_27_1', '5分钟以内', 0);
    $this->addSubCategory('1_27', '1_27_2', '5-15分钟', 0);
    $this->addSubCategory('1_27', '1_27_3', '15-30分钟', 0);
    $this->addSubCategory('1_27', '1_27_4', '30分钟以上', 0);

    // 按系列细分
    $this->addSubCategory('1', '1_28', '热门系列', 0);
    $this->addSubCategory('1_28', '1_28_1', '番剧连载', 0);
    $this->addSubCategory('1_28', '1_28_2', '综艺连载', 0);
    $this->addSubCategory('1_28', '1_28_3', '纪录片系列', 0);
    $this->addSubCategory('1_28', '1_28_4', '教程系列', 0);

    // 特殊分类
    $this->addSubCategory('1', '1_29', 'B站特色', 0);
    $this->addSubCategory('1_29', '1_29_1', '弹幕互动', 0);
    $this->addSubCategory('1_29', '1_29_2', '互动视频', 0);
    $this->addSubCategory('1_29', '1_29_3', '虚拟主播', 0);
    $this->addSubCategory('1_29', '1_29_4', '二创作品', 0);

    // 虚拟主播细分
    $this->addSubCategory('1_29_3', '1_29_3_1', 'A-SOUL', 0);
    $this->addSubCategory('1_29_3', '1_29_3_2', '彩虹社', 0);
    $this->addSubCategory('1_29_3', '1_29_3_3', 'Hololive', 0);
    $this->addSubCategory('1_29_3', '1_29_3_4', '个人势Vup', 0);

    // 按制作水平细分
    $this->addSubCategory('1', '1_30', '按制作', 0);
    $this->addSubCategory('1_30', '1_30_1', '专业制作', 0);
    $this->addSubCategory('1_30', '1_30_2', '个人创作', 0);
    $this->addSubCategory('1_30', '1_30_3', '团队合作', 0);
    $this->addSubCategory('1_30', '1_30_4', '官方出品', 0);
    // 动画分区 - 按题材深度细分
    $this->addSubCategory('1_1', '1_1_5', '按题材', 1);
    $this->addSubCategory('1_1_5', '1_1_5_1', '科幻动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_2', '奇幻动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_3', '校园动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_4', '恋爱动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_5', '热血动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_6', '悬疑动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_7', '治愈动画', 1);
    $this->addSubCategory('1_1_5', '1_1_5_8', '恐怖动画', 1);

    // 按制作公司细分
    $this->addSubCategory('1_1', '1_1_6', '制作公司', 1);
    $this->addSubCategory('1_1_6', '1_1_6_1', '京都动画', 1);
    $this->addSubCategory('1_1_6', '1_1_6_2', '骨头社', 1);
    $this->addSubCategory('1_1_6', '1_1_6_3', 'Production I.G', 1);
    $this->addSubCategory('1_1_6', '1_1_6_4', '扳机社', 1);
    $this->addSubCategory('1_1_6', '1_1_6_5', 'MAPPA', 1);
    $this->addSubCategory('1_1_6', '1_1_6_6', 'A-1 Pictures', 1);
    $this->addSubCategory('1_1_6', '1_1_6_7', 'ufotable', 1);

    // 番剧分区 - 按季度细分
    $this->addSubCategory('1_2', '1_2_5', '2024年番剧', 13);
    $this->addSubCategory('1_2_5', '1_2_5_1', '2024年1月新番', 13);
    $this->addSubCategory('1_2_5', '1_2_5_2', '2024年4月新番', 13);
    $this->addSubCategory('1_2_5', '1_2_5_3', '2024年7月新番', 13);
    $this->addSubCategory('1_2_5', '1_2_5_4', '2024年10月新番', 13);

    $this->addSubCategory('1_2', '1_2_6', '2023年番剧', 13);
    $this->addSubCategory('1_2_6', '1_2_6_1', '2023年1月新番', 13);
    $this->addSubCategory('1_2_6', '1_2_6_2', '2023年4月新番', 13);
    $this->addSubCategory('1_2_6', '1_2_6_3', '2023年7月新番', 13);
    $this->addSubCategory('1_2_6', '1_2_6_4', '2023年10月新番', 13);

    // 音乐分区 - 按乐器深度细分
    $this->addSubCategory('1_4_4', '1_4_4_6', '管乐器', 59);
    $this->addSubCategory('1_4_4_6', '1_4_4_6_1', '萨克斯', 59);
    $this->addSubCategory('1_4_4_6', '1_4_4_6_2', '长笛', 59);
    $this->addSubCategory('1_4_4_6', '1_4_4_6_3', '小号', 59);
    $this->addSubCategory('1_4_4_6', '1_4_4_6_4', '单簧管', 59);

    $this->addSubCategory('1_4_4', '1_4_4_7', '民族乐器', 59);
    $this->addSubCategory('1_4_4_7', '1_4_4_7_1', '二胡', 59);
    $this->addSubCategory('1_4_4_7', '1_4_4_7_2', '琵琶', 59);
    $this->addSubCategory('1_4_4_7', '1_4_4_7_3', '笛子', 59);
    $this->addSubCategory('1_4_4_7', '1_4_4_7_4', '古琴', 59);

    // 舞蹈分区 - 按舞种深度细分
    $this->addSubCategory('1_5', '1_5_6', '现代舞', 129);
    $this->addSubCategory('1_5_6', '1_5_6_1', '当代舞', 129);
    $this->addSubCategory('1_5_6', '1_5_6_2', '爵士舞', 129);
    $this->addSubCategory('1_5_6', '1_5_6_3', '拉丁舞', 129);
    $this->addSubCategory('1_5_6', '1_5_6_4', '踢踏舞', 129);

    // 游戏分区 - 按游戏类型深度细分
    $this->addSubCategory('1_6', '1_6_10', '角色扮演', 4);
    $this->addSubCategory('1_6_10', '1_6_10_1', '日式RPG', 4);
    $this->addSubCategory('1_6_10', '1_6_10_2', '美式RPG', 4);
    $this->addSubCategory('1_6_10', '1_6_10_3', '动作RPG', 4);
    $this->addSubCategory('1_6_10', '1_6_10_4', '策略RPG', 4);

    $this->addSubCategory('1_6', '1_6_11', '动作游戏', 4);
    $this->addSubCategory('1_6_11', '1_6_11_1', '平台动作', 4);
    $this->addSubCategory('1_6_11', '1_6_11_2', '清版动作', 4);
    $this->addSubCategory('1_6_11', '1_6_11_3', '动作冒险', 4);
    $this->addSubCategory('1_6_11', '1_6_11_4', '格斗游戏', 4);

    $this->addSubCategory('1_6', '1_6_12', '策略游戏', 4);
    $this->addSubCategory('1_6_12', '1_6_12_1', '即时战略', 4);
    $this->addSubCategory('1_6_12', '1_6_12_2', '回合策略', 4);
    $this->addSubCategory('1_6_12', '1_6_12_3', '战棋游戏', 4);
    $this->addSubCategory('1_6_12', '1_6_12_4', '模拟经营', 4);

    // 知识分区 - 按学科深度细分
    $this->addSubCategory('1_7', '1_7_7', '语言学', 36);
    $this->addSubCategory('1_7_7', '1_7_7_1', '汉语语言学', 36);
    $this->addSubCategory('1_7_7', '1_7_7_2', '英语语言学', 36);
    $this->addSubCategory('1_7_7', '1_7_7_3', '日语语言学', 36);
    $this->addSubCategory('1_7_7', '1_7_7_4', '法语语言学', 36);

    $this->addSubCategory('1_7', '1_7_8', '艺术学', 36);
    $this->addSubCategory('1_7_8', '1_7_8_1', '美术史', 36);
    $this->addSubCategory('1_7_8', '1_7_8_2', '音乐史', 36);
    $this->addSubCategory('1_7_8', '1_7_8_3', '戏剧学', 36);
    $this->addSubCategory('1_7_8', '1_7_8_4', '电影学', 36);

    // 科技分区 - 按领域深度细分
    $this->addSubCategory('1_8', '1_8_7', '生物技术', 188);
    $this->addSubCategory('1_8_7', '1_8_7_1', '基因工程', 188);
    $this->addSubCategory('1_8_7', '1_8_7_2', '生物制药', 188);
    $this->addSubCategory('1_8_7', '1_8_7_3', '农业科技', 188);
    $this->addSubCategory('1_8_7', '1_8_7_4', '环境科学', 188);

    $this->addSubCategory('1_8', '1_8_8', '材料科学', 188);
    $this->addSubCategory('1_8_8', '1_8_8_1', '纳米材料', 188);
    $this->addSubCategory('1_8_8', '1_8_8_2', '高分子材料', 188);
    $this->addSubCategory('1_8_8', '1_8_8_3', '金属材料', 188);
    $this->addSubCategory('1_8_8', '1_8_8_4', '复合材料', 188);

    // 运动分区 - 按赛事深度细分
    $this->addSubCategory('1_9', '1_9_11', '奥运会', 234);
    $this->addSubCategory('1_9_11', '1_9_11_1', '夏季奥运会', 234);
    $this->addSubCategory('1_9_11', '1_9_11_2', '冬季奥运会', 234);
    $this->addSubCategory('1_9_11', '1_9_11_3', '奥运历史', 234);
    $this->addSubCategory('1_9_11', '1_9_11_4', '奥运项目', 234);

    $this->addSubCategory('1_9', '1_9_12', '亚运会', 234);
    $this->addSubCategory('1_9_12', '1_9_12_1', '杭州亚运会', 234);
    $this->addSubCategory('1_9_12', '1_9_12_2', '雅加达亚运会', 234);
    $this->addSubCategory('1_9_12', '1_9_12_3', '仁川亚运会', 234);

    // 汽车分区 - 按品牌深度细分
    $this->addSubCategory('1_10', '1_10_6', '德系品牌', 223);
    $this->addSubCategory('1_10_6', '1_10_6_1', '奔驰', 223);
    $this->addSubCategory('1_10_6', '1_10_6_2', '宝马', 223);
    $this->addSubCategory('1_10_6', '1_10_6_3', '奥迪', 223);
    $this->addSubCategory('1_10_6', '1_10_6_4', '大众', 223);
    $this->addSubCategory('1_10_6', '1_10_6_5', '保时捷', 223);

    $this->addSubCategory('1_10', '1_10_7', '日系品牌', 223);
    $this->addSubCategory('1_10_7', '1_10_7_1', '丰田', 223);
    $this->addSubCategory('1_10_7', '1_10_7_2', '本田', 223);
    $this->addSubCategory('1_10_7', '1_10_7_3', '日产', 223);
    $this->addSubCategory('1_10_7', '1_10_7_4', '马自达', 223);
    $this->addSubCategory('1_10_7', '1_10_7_5', '斯巴鲁', 223);

    $this->addSubCategory('1_10', '1_10_8', '国产品牌', 223);
    $this->addSubCategory('1_10_8', '1_10_8_1', '比亚迪', 223);
    $this->addSubCategory('1_10_8', '1_10_8_2', '吉利', 223);
    $this->addSubCategory('1_10_8', '1_10_8_3', '长城', 223);
    $this->addSubCategory('1_10_8', '1_10_8_4', '长安', 223);
    $this->addSubCategory('1_10_8', '1_10_8_5', '蔚来', 223);

    // 生活分区 - 按场景深度细分
    $this->addSubCategory('1_11', '1_11_11', '户外生活', 160);
    $this->addSubCategory('1_11_11', '1_11_11_1', '露营', 160);
    $this->addSubCategory('1_11_11', '1_11_11_2', '钓鱼', 160);
    $this->addSubCategory('1_11_11', '1_11_11_3', '登山', 160);
    $this->addSubCategory('1_11_11', '1_11_11_4', '骑行', 160);

    $this->addSubCategory('1_11', '1_11_12', '城市生活', 160);
    $this->addSubCategory('1_11_12', '1_11_12_1', '咖啡文化', 160);
    $this->addSubCategory('1_11_12', '1_11_12_2', '书店探店', 160);
    $this->addSubCategory('1_11_12', '1_11_12_3', '城市漫步', 160);
    $this->addSubCategory('1_11_12', '1_11_12_4', '市集活动', 160);

    // 美食分区 - 按菜系深度细分
    $this->addSubCategory('1_12', '1_12_6', '中华菜系', 211);
    $this->addSubCategory('1_12_6', '1_12_6_1', '川菜', 211);
    $this->addSubCategory('1_12_6', '1_12_6_2', '粤菜', 211);
    $this->addSubCategory('1_12_6', '1_12_6_3', '鲁菜', 211);
    $this->addSubCategory('1_12_6', '1_12_6_4', '苏菜', 211);
    $this->addSubCategory('1_12_6', '1_12_6_5', '浙菜', 211);
    $this->addSubCategory('1_12_6', '1_12_6_6', '湘菜', 211);

    $this->addSubCategory('1_12', '1_12_7', '世界美食', 211);
    $this->addSubCategory('1_12_7', '1_12_7_1', '日本料理', 211);
    $this->addSubCategory('1_12_7', '1_12_7_2', '韩国料理', 211);
    $this->addSubCategory('1_12_7', '1_12_7_3', '意大利菜', 211);
    $this->addSubCategory('1_12_7', '1_12_7_4', '法国菜', 211);
    $this->addSubCategory('1_12_7', '1_12_7_5', '泰国菜', 211);

    // 动物分区 - 按栖息地细分
    $this->addSubCategory('1_13', '1_13_7', '海洋生物', 217);
    $this->addSubCategory('1_13_7', '1_13_7_1', '珊瑚礁生态', 217);
    $this->addSubCategory('1_13_7', '1_13_7_2', '深海生物', 217);
    $this->addSubCategory('1_13_7', '1_13_7_3', '海洋哺乳动物', 217);
    $this->addSubCategory('1_13_7', '1_13_7_4', '海洋鱼类', 217);

    $this->addSubCategory('1_13', '1_13_8', '森林动物', 217);
    $this->addSubCategory('1_13_8', '1_13_8_1', '雨林生态', 217);
    $this->addSubCategory('1_13_8', '1_13_8_2', '温带森林', 217);
    $this->addSubCategory('1_13_8', '1_13_8_3', '寒带森林', 217);

    // 鬼畜分区 - 按素材来源细分
    $this->addSubCategory('1_14', '1_14_5', '影视鬼畜', 119);
    $this->addSubCategory('1_14_5', '1_14_5_1', '电视剧素材', 119);
    $this->addSubCategory('1_14_5', '1_14_5_2', '电影素材', 119);
    $this->addSubCategory('1_14_5', '1_14_5_3', '综艺素材', 119);
    $this->addSubCategory('1_14_5', '1_14_5_4', '广告素材', 119);

    $this->addSubCategory('1_14', '1_14_6', '游戏鬼畜', 119);
    $this->addSubCategory('1_14_6', '1_14_6_1', '游戏CG素材', 119);
    $this->addSubCategory('1_14_6', '1_14_6_2', '游戏实况素材', 119);
    $this->addSubCategory('1_14_6', '1_14_6_3', '游戏角色素材', 119);

    // 时尚分区 - 按风格深度细分
    $this->addSubCategory('1_15', '1_15_6', '时尚风格', 155);
    $this->addSubCategory('1_15_6', '1_15_6_1', '简约风', 155);
    $this->addSubCategory('1_15_6', '1_15_6_2', '复古风', 155);
    $this->addSubCategory('1_15_6', '1_15_6_3', '街头风', 155);
    $this->addSubCategory('1_15_6', '1_15_6_4', '森女系', 155);
    $this->addSubCategory('1_15_6', '1_15_6_5', '职场风', 155);

    // 按平台细分
    $this->addSubCategory('1', '1_31', '按平台', 0);
    $this->addSubCategory('1_31', '1_31_1', 'PC平台', 0);
    $this->addSubCategory('1_31', '1_31_2', '移动平台', 0);
    $this->addSubCategory('1_31', '1_31_3', '主机平台', 0);
    $this->addSubCategory('1_31', '1_31_4', '网页平台', 0);

    // 按语言细分
    $this->addSubCategory('1', '1_32', '按语言', 0);
    $this->addSubCategory('1_32', '1_32_1', '中文配音', 0);
    $this->addSubCategory('1_32', '1_32_2', '日语原声', 0);
    $this->addSubCategory('1_32', '1_32_3', '英语原声', 0);
    $this->addSubCategory('1_32', '1_32_4', '多语言', 0);

    // 按更新状态细分
    $this->addSubCategory('1', '1_33', '更新状态', 0);
    $this->addSubCategory('1_33', '1_33_1', '连载中', 0);
    $this->addSubCategory('1_33', '1_33_2', '已完结', 0);
    $this->addSubCategory('1_33', '1_33_3', '停更', 0);
    $this->addSubCategory('1_33', '1_33_4', '定期更新', 0);

    // 按创作类型细分
    $this->addSubCategory('1', '1_34', '创作类型', 0);
    $this->addSubCategory('1_34', '1_34_1', '原创作品', 0);
    $this->addSubCategory('1_34', '1_34_2', '同人创作', 0);
    $this->addSubCategory('1_34', '1_34_3', '官方授权', 0);
    $this->addSubCategory('1_34', '1_34_4', '粉丝自制', 0);
    // 影视分区 - 按类型深度细分
    $this->addSubCategory('1_17', '1_17_12', '电影类型', 181);
    $this->addSubCategory('1_17_12', '1_17_12_1', '动作电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_2', '喜剧电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_3', '爱情电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_4', '科幻电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_5', '恐怖电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_6', '悬疑电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_7', '文艺电影', 181);
    $this->addSubCategory('1_17_12', '1_17_12_8', '动画电影', 181);

    // 电视剧类型细分
    $this->addSubCategory('1_17', '1_17_13', '电视剧类型', 181);
    $this->addSubCategory('1_17_13', '1_17_13_1', '古装剧', 181);
    $this->addSubCategory('1_17_13', '1_17_13_2', '现代剧', 181);
    $this->addSubCategory('1_17_13', '1_17_13_3', '悬疑剧', 181);
    $this->addSubCategory('1_17_13', '1_17_13_4', '爱情剧', 181);
    $this->addSubCategory('1_17_13', '1_17_13_5', '家庭剧', 181);
    $this->addSubCategory('1_17_13', '1_17_13_6', '职场剧', 181);
    $this->addSubCategory('1_17_13', '1_17_13_7', '历史剧', 181);

    // 纪录片分区 - 按主题深度细分
    $this->addSubCategory('1_18', '1_18_6', '自然地理', 177);
    $this->addSubCategory('1_18_6', '1_18_6_1', '动物世界', 177);
    $this->addSubCategory('1_18_6', '1_18_6_2', '植物王国', 177);
    $this->addSubCategory('1_18_6', '1_18_6_3', '地质奇观', 177);
    $this->addSubCategory('1_18_6', '1_18_6_4', '气候变化', 177);
    $this->addSubCategory('1_18_6', '1_18_6_5', '海洋探索', 177);

    $this->addSubCategory('1_18', '1_18_7', '科学技术', 177);
    $this->addSubCategory('1_18_7', '1_18_7_1', '航天科技', 177);
    $this->addSubCategory('1_18_7', '1_18_7_2', '医学发展', 177);
    $this->addSubCategory('1_18_7', '1_18_7_3', '工程奇迹', 177);
    $this->addSubCategory('1_18_7', '1_18_7_4', '信息技术', 177);

    // 电影分区 - 按年代深度细分
    $this->addSubCategory('1_19', '1_19_6', '经典电影', 23);
    $this->addSubCategory('1_19_6', '1_19_6_1', '80年代电影', 23);
    $this->addSubCategory('1_19_6', '1_19_6_2', '90年代电影', 23);
    $this->addSubCategory('1_19_6', '1_19_6_3', '00年代电影', 23);
    $this->addSubCategory('1_19_6', '1_19_6_4', '10年代电影', 23);
    $this->addSubCategory('1_19_6', '1_19_6_5', '20年代电影', 23);

    // 电视剧分区 - 按长度细分
    $this->addSubCategory('1_20', '1_20_3', '剧集长度', 11);
    $this->addSubCategory('1_20_3', '1_20_3_1', '短剧集', 11);
    $this->addSubCategory('1_20_3', '1_20_3_2', '标准剧集', 11);
    $this->addSubCategory('1_20_3', '1_20_3_3', '长篇剧集', 11);
    $this->addSubCategory('1_20_3', '1_20_3_4', '系列剧集', 11);

    // 娱乐分区 - 按节目类型深度细分
    $this->addSubCategory('1_16', '1_16_7', '真人秀类型', 5);
    $this->addSubCategory('1_16_7', '1_16_7_1', '选秀节目', 5);
    $this->addSubCategory('1_16_7', '1_16_7_2', '竞技节目', 5);
    $this->addSubCategory('1_16_7', '1_16_7_3', '生活观察', 5);
    $this->addSubCategory('1_16_7', '1_16_7_4', '恋爱节目', 5);
    $this->addSubCategory('1_16_7', '1_16_7_5', '职场观察', 5);

    // 按内容形式细分
    $this->addSubCategory('1', '1_35', '内容形式', 0);
    $this->addSubCategory('1_35', '1_35_1', '教程教学', 0);
    $this->addSubCategory('1_35', '1_35_2', '开箱测评', 0);
    $this->addSubCategory('1_35', '1_35_3', '生活VLOG', 0);
    $this->addSubCategory('1_35', '1_35_4', '剧情短片', 0);
    $this->addSubCategory('1_35', '1_35_5', '纪录片', 0);
    $this->addSubCategory('1_35', '1_35_6', '访谈对话', 0);

    // 按视频质量细分
    $this->addSubCategory('1', '1_36', '视频质量', 0);
    $this->addSubCategory('1_36', '1_36_1', '4K超清', 0);
    $this->addSubCategory('1_36', '1_36_2', '1080P高清', 0);
    $this->addSubCategory('1_36', '1_36_3', '720P标清', 0);
    $this->addSubCategory('1_36', '1_36_4', 'HDR视频', 0);
    $this->addSubCategory('1_36', '1_36_5', '杜比视界', 0);

    // 按音频质量细分
    $this->addSubCategory('1', '1_37', '音频质量', 0);
    $this->addSubCategory('1_37', '1_37_1', '无损音质', 0);
    $this->addSubCategory('1_37', '1_37_2', '立体声', 0);
    $this->addSubCategory('1_37', '1_37_3', '环绕声', 0);
    $this->addSubCategory('1_37', '1_37_4', '杜比全景声', 0);

    // 按版权类型细分
    $this->addSubCategory('1', '1_38', '版权类型', 0);
    $this->addSubCategory('1_38', '1_38_1', '独家版权', 0);
    $this->addSubCategory('1_38', '1_38_2', '联合播出', 0);
    $this->addSubCategory('1_38', '1_38_3', '免费观看', 0);
    $this->addSubCategory('1_38', '1_38_4', '会员专享', 0);
    $this->addSubCategory('1_38', '1_38_5', '付费内容', 0);

    // 按互动类型细分
    $this->addSubCategory('1', '1_39', '互动类型', 0);
    $this->addSubCategory('1_39', '1_39_1', '弹幕互动', 0);
    $this->addSubCategory('1_39', '1_39_2', '评论互动', 0);
    $this->addSubCategory('1_39', '1_39_3', '投票互动', 0);
    $this->addSubCategory('1_39', '1_39_4', '抽奖互动', 0);
    $this->addSubCategory('1_39', '1_39_5', '直播互动', 0);

    // 按创作工具细分
    $this->addSubCategory('1', '1_40', '创作工具', 0);
    $this->addSubCategory('1_40', '1_40_1', 'Adobe系列', 0);
    $this->addSubCategory('1_40', '1_40_2', 'Final Cut Pro', 0);
    $this->addSubCategory('1_40', '1_40_3', '达芬奇调色', 0);
    $this->addSubCategory('1_40', '1_40_4', 'Blender制作', 0);
    $this->addSubCategory('1_40', '1_40_5', 'Unity开发', 0);
    $this->addSubCategory('1_40', '1_40_6', 'UE5制作', 0);

    // 按活动类型细分
    $this->addSubCategory('1', '1_41', '活动类型', 0);
    $this->addSubCategory('1_41', '1_41_1', 'BML活动', 0);
    $this->addSubCategory('1_41', '1_41_2', 'BW展会', 0);
    $this->addSubCategory('1_41', '1_41_3', '拜年祭', 0);
    $this->addSubCategory('1_41', '1_41_4', '创作激励', 0);
    $this->addSubCategory('1_41', '1_41_5', '官方赛事', 0);

    // 按合作品牌细分
    $this->addSubCategory('1', '1_42', '合作品牌', 0);
    $this->addSubCategory('1_42', '1_42_1', '官方合作', 0);
    $this->addSubCategory('1_42', '1_42_2', '品牌赞助', 0);
    $this->addSubCategory('1_42', '1_42_3', '跨界联动', 0);
    $this->addSubCategory('1_42', '1_42_4', 'IP授权', 0);

    // 按情感类型细分
    $this->addSubCategory('1', '1_43', '情感类型', 0);
    $this->addSubCategory('1_43', '1_43_1', '欢乐搞笑', 0);
    $this->addSubCategory('1_43', '1_43_2', '感动治愈', 0);
    $this->addSubCategory('1_43', '1_43_3', '紧张刺激', 0);
    $this->addSubCategory('1_43', '1_43_4', '温馨日常', 0);
    $this->addSubCategory('1_43', '1_43_5', '热血沸腾', 0);
    $this->addSubCategory('1_43', '1_43_6', '悬疑惊悚', 0);

    // 按观看场景细分
    $this->addSubCategory('1', '1_44', '观看场景', 0);
    $this->addSubCategory('1_44', '1_44_1', '睡前观看', 0);
    $this->addSubCategory('1_44', '1_44_2', '通勤路上', 0);
    $this->addSubCategory('1_44', '1_44_3', '学习时刻', 0);
    $this->addSubCategory('1_44', '1_44_4', '休闲放松', 0);
    $this->addSubCategory('1_44', '1_44_5', '聚会分享', 0);
    $this->addSubCategory('1_44', '1_44_6', '工作背景', 0);

    // 按难度级别细分
    $this->addSubCategory('1', '1_45', '难度级别', 0);
    $this->addSubCategory('1_45', '1_45_1', '入门级', 0);
    $this->addSubCategory('1_45', '1_45_2', '初级', 0);
    $this->addSubCategory('1_45', '1_45_3', '中级', 0);
    $this->addSubCategory('1_45', '1_45_4', '高级', 0);
    $this->addSubCategory('1_45', '1_45_5', '专家级', 0);

    // 按年龄分级细分
    $this->addSubCategory('1', '1_46', '年龄分级', 0);
    $this->addSubCategory('1_46', '1_46_1', '全年龄', 0);
    $this->addSubCategory('1_46', '1_46_2', '12岁以上', 0);
    $this->addSubCategory('1_46', '1_46_3', '15岁以上', 0);
    $this->addSubCategory('1_46', '1_46_4', '18岁以上', 0);

    // 按文化背景细分
    $this->addSubCategory('1', '1_47', '文化背景', 0);
    $this->addSubCategory('1_47', '1_47_1', '中华文化', 0);
    $this->addSubCategory('1_47', '1_47_2', '日本文化', 0);
    $this->addSubCategory('1_47', '1_47_3', '欧美文化', 0);
    $this->addSubCategory('1_47', '1_47_4', '韩国文化', 0);
    $this->addSubCategory('1_47', '1_47_5', '东南亚文化', 0);

    // 按历史时期细分
    $this->addSubCategory('1', '1_48', '历史时期', 0);
    $this->addSubCategory('1_48', '1_48_1', '古代历史', 0);
    $this->addSubCategory('1_48', '1_48_2', '中世纪', 0);
    $this->addSubCategory('1_48', '1_48_3', '近代历史', 0);
    $this->addSubCategory('1_48', '1_48_4', '现代历史', 0);
    $this->addSubCategory('1_48', '1_48_5', '未来科幻', 0);

    // 按艺术风格细分
    $this->addSubCategory('1', '1_49', '艺术风格', 0);
    $this->addSubCategory('1_49', '1_49_1', '写实风格', 0);
    $this->addSubCategory('1_49', '1_49_2', '卡通风格', 0);
    $this->addSubCategory('1_49', '1_49_3', '像素风格', 0);
    $this->addSubCategory('1_49', '1_49_4', '水彩风格', 0);
    $this->addSubCategory('1_49', '1_49_5', '赛博朋克', 0);
    $this->addSubCategory('1_49', '1_49_6', '蒸汽朋克', 0);

    // 按音乐流派细分
    $this->addSubCategory('1', '1_50', '音乐流派', 0);
    $this->addSubCategory('1_50', '1_50_1', '古典音乐', 0);
    $this->addSubCategory('1_50', '1_50_2', '流行音乐', 0);
    $this->addSubCategory('1_50', '1_50_3', '摇滚音乐', 0);
    $this->addSubCategory('1_50', '1_50_4', '电子音乐', 0);
    $this->addSubCategory('1_50', '1_50_5', '爵士音乐', 0);
    $this->addSubCategory('1_50', '1_50_6', '民族音乐', 0);

    // 按舞蹈风格细分
    $this->addSubCategory('1', '1_51', '舞蹈风格', 0);
    $this->addSubCategory('1_51', '1_51_1', '街舞', 0);
    $this->addSubCategory('1_51', '1_51_2', '现代舞', 0);
    $this->addSubCategory('1_51', '1_51_3', '芭蕾舞', 0);
    $this->addSubCategory('1_51', '1_51_4', '民族舞', 0);
    $this->addSubCategory('1_51', '1_51_5', '交谊舞', 0);

    // 按游戏平台细分
    $this->addSubCategory('1', '1_52', '游戏平台', 0);
    $this->addSubCategory('1_52', '1_52_1', 'Steam平台', 0);
    $this->addSubCategory('1_52', '1_52_2', 'Epic平台', 0);
    $this->addSubCategory('1_52', '1_52_3', 'PlayStation', 0);
    $this->addSubCategory('1_52', '1_52_4', 'Xbox', 0);
    $this->addSubCategory('1_52', '1_52_5', 'Nintendo', 0);

    // 按学习阶段细分
    $this->addSubCategory('1', '1_53', '学习阶段', 0);
    $this->addSubCategory('1_53', '1_53_1', '学前教育', 0);
    $this->addSubCategory('1_53', '1_53_2', '小学阶段', 0);
    $this->addSubCategory('1_53', '1_53_3', '中学阶段', 0);
    $this->addSubCategory('1_53', '1_53_4', '大学阶段', 0);
    $this->addSubCategory('1_53', '1_53_5', '职场提升', 0);

    // 按技术领域细分
    $this->addSubCategory('1', '1_54', '技术领域', 0);
    $this->addSubCategory('1_54', '1_54_1', '前端开发', 0);
    $this->addSubCategory('1_54', '1_54_2', '后端开发', 0);
    $this->addSubCategory('1_54', '1_54_3', '移动开发', 0);
    $this->addSubCategory('1_54', '1_54_4', '数据科学', 0);
    $this->addSubCategory('1_54', '1_54_5', '人工智能', 0);

    // 按运动强度细分
    $this->addSubCategory('1', '1_55', '运动强度', 0);
    $this->addSubCategory('1_55', '1_55_1', '轻度运动', 0);
    $this->addSubCategory('1_55', '1_55_2', '中度运动', 0);
    $this->addSubCategory('1_55', '1_55_3', '高强度运动', 0);
    $this->addSubCategory('1_55', '1_55_4', '专业训练', 0);

    // 按汽车类型细分
    $this->addSubCategory('1', '1_56', '汽车类型', 0);
    $this->addSubCategory('1_56', '1_56_1', '轿车', 0);
    $this->addSubCategory('1_56', '1_56_2', 'SUV', 0);
    $this->addSubCategory('1_56', '1_56_3', '跑车', 0);
    $this->addSubCategory('1_56', '1_56_4', '新能源车', 0);
    $this->addSubCategory('1_56', '1_56_5', '商务车', 0);

    // 按生活场景细分
    $this->addSubCategory('1', '1_57', '生活场景', 0);
    $this->addSubCategory('1_57', '1_57_1', '居家生活', 0);
    $this->addSubCategory('1_57', '1_57_2', '办公场景', 0);
    $this->addSubCategory('1_57', '1_57_3', '旅行出游', 0);
    $this->addSubCategory('1_57', '1_57_4', '社交聚会', 0);
    $this->addSubCategory('1_57', '1_57_5', '运动健身', 0);

    // 按美食场合细分
    $this->addSubCategory('1', '1_58', '美食场合', 0);
    $this->addSubCategory('1_58', '1_58_1', '家常菜', 0);
    $this->addSubCategory('1_58', '1_58_2', '宴客菜', 0);
    $this->addSubCategory('1_58', '1_58_3', '节日美食', 0);
    $this->addSubCategory('1_58', '1_58_4', '快手菜', 0);
    $this->addSubCategory('1_58', '1_58_5', '养生食疗', 0);

    // 按动物习性细分
    $this->addSubCategory('1', '1_59', '动物习性', 0);
    $this->addSubCategory('1_59', '1_59_1', '夜行动物', 0);
    $this->addSubCategory('1_59', '1_59_2', '日行动物', 0);
    $this->addSubCategory('1_59', '1_59_3', '迁徙动物', 0);
    $this->addSubCategory('1_59', '1_59_4', '冬眠动物', 0);
    $this->addSubCategory('1_59', '1_59_5', '群居动物', 0);

    // 按时尚场合细分
    $this->addSubCategory('1', '1_60', '时尚场合', 0);
    $this->addSubCategory('1_60', '1_60_1', '日常穿搭', 0);
    $this->addSubCategory('1_60', '1_60_2', '职场穿搭', 0);
    $this->addSubCategory('1_60', '1_60_3', '约会穿搭', 0);
    $this->addSubCategory('1_60', '1_60_4', '派对穿搭', 0);
    $this->addSubCategory('1_60', '1_60_5', '运动穿搭', 0);
        // 可以继续添加更多细分分类...
    }
    
    // 添加子分类
    private function addSubCategory($parentId, $id, $name, $tid) {
        $this->categories[$id] = [
            'name' => $name,
            'tid' => $tid,
            'level' => $this->categories[$parentId]['level'] + 1,
            'parent' => $parentId,
            'has_children' => false // 默认没有更深层的子分类
        ];
    }
    
    // 获取分类信息
    public function getCategory($categoryId) {
        return $this->categories[$categoryId] ?? null;
    }
    
    // 获取子分类
    public function getChildren($parentId) {
        $children = [];
        foreach ($this->categories as $id => $category) {
            if (isset($category['parent']) && $category['parent'] === $parentId) {
                $children[] = [
                    'id' => $id,
                    'name' => $category['name'],
                    'level' => $category['level'],
                    'has_children' => $category['has_children'],
                    'tid' => $category['tid'] ?? 0
                ];
            }
        }
        return $children;
    }
    
    // 获取一级分类
    public function getLevel1Categories() {
        $result = [];
        foreach ($this->categories as $id => $category) {
            if ($category['level'] === 1) {
                $result[] = [
                    'type_id' => $id,
                    'type_name' => $category['name']
                ];
            }
        }
        return $result;
    }
    
    // 从B站API获取视频列表
    // 从B站API获取视频列表
public function getVideoList($tid, $page = 1, $keyword = '') {
    $videos = [];
    
    if (!empty($keyword)) {
        return $this->searchVideos($keyword, $page);
    }
    
    // 热门推荐特殊处理
    if ($tid == 0) {
        return $this->getPopularVideos($page);
    }
    
    // 处理自定义分类
    if (is_string($tid) && !is_numeric($tid)) {
        return $this->getCustomCategoryVideos($tid, $page);
    }
    
    try {
        $url = "{$this->baseUrl}/x/web-interface/newlist?" . http_build_query([
            'rid' => $tid,
            'type' => 0,
            'pn' => $page,
            'ps' => 20
        ]);
        
        $response = $this->curlRequest($url);
        $data = json_decode($response, true);
        
        if (isset($data['data']['archives'])) {
            foreach ($data['data']['archives'] as $item) {
                $videos[] = $this->formatVideoData($item);
            }
        }
    } catch (Exception $e) {
        $videos = $this->getSampleVideos($tid);
    }
    
    return $videos;
}

// 新增方法：处理自定义分类
private function getCustomCategoryVideos($categoryId, $page = 1) {
    $videos = [];
    
    switch ($categoryId) {
        // 热门推荐细分
        case 'hot_today':
            return $this->getPopularVideos($page);
        case 'hot_week':
            return $this->getWeeklyPopularVideos($page);
        case 'hot_month':
            return $this->getMonthlyPopularVideos($page);
        case 'hot_year':
            return $this->getYearlyPopularVideos($page);
        case 'hot_soaring':
            return $this->getSoaringVideos($page);
        case 'hot_newcomer':
            return $this->getNewcomerVideos($page);
            
        // 地区分类 - 使用搜索API
        case 'region_china':
            return $this->searchVideos('中国', $page);
        case 'region_japan':
            return $this->searchVideos('日本', $page);
        case 'region_korea':
            return $this->searchVideos('韩国', $page);
        case 'region_usa':
            return $this->searchVideos('美国', $page);
        case 'region_europe':
            return $this->searchVideos('欧洲', $page);
            
        // 时间分类 - 结合年份搜索
        case 'time_2025':
            return $this->searchVideos('2025', $page);
        case 'time_2024':
            return $this->searchVideos('2024', $page);
        case 'time_2023':
            return $this->searchVideos('2023', $page);
        case 'time_2022':
            return $this->searchVideos('2022', $page);
        case 'time_2021':
            return $this->searchVideos('2021', $page);
        case 'time_classic':
            return $this->searchVideos('经典', $page);
            
        // 类型分类
        case 'genre_funny':
            return $this->searchVideos('搞笑', $page);
        case 'genre_healing':
            return $this->searchVideos('治愈', $page);
        case 'genre_hotblood':
            return $this->searchVideos('热血', $page);
        case 'genre_romance':
            return $this->searchVideos('恋爱', $page);
        case 'genre_mystery':
            return $this->searchVideos('悬疑', $page);
        case 'genre_horror':
            return $this->searchVideos('恐怖', $page);
            
        // UP主分类
        case 'uper_laofanqie':
            return $this->searchVideos('老番茄', $page);
        case 'uper_lexburner':
            return $this->searchVideos('LexBurner', $page);
        case 'uper_aochang':
            return $this->searchVideos('敖厂长', $page);
        case 'uper_wanggang':
            return $this->searchVideos('王刚', $page);
        case 'uper_liziqi':
            return $this->searchVideos('李子柒', $page);
        case 'uper_luoxiang':
            return $this->searchVideos('罗翔说刑法', $page);
            
        default:
            return $this->getSampleVideos($categoryId);
    }
}

// 新增方法：获取周榜、月榜等（这里可以用不同的API或搜索条件）
private function getWeeklyPopularVideos($page = 1) {
    // 可以使用不同的排序方式或时间范围
    return $this->getPopularVideos($page);
}

private function getMonthlyPopularVideos($page = 1) {
    return $this->getPopularVideos($page);
}

private function getYearlyPopularVideos($page = 1) {
    return $this->getPopularVideos($page);
}

private function getSoaringVideos($page = 1) {
    // 飙升榜可以使用搜索API按播放量增长率排序
    return $this->searchVideos('', $page);
}

private function getNewcomerVideos($page = 1) {
    // 新人榜可以搜索新UP主的视频
    return $this->searchVideos('新人', $page);
}
    
    // 获取热门视频
    private function getPopularVideos($page = 1) {
        try {
            $url = "{$this->baseUrl}/x/web-interface/popular?" . http_build_query([
                'pn' => $page,
                'ps' => 20
            ]);
            
            $response = $this->curlRequest($url);
            $data = json_decode($response, true);
            
            $videos = [];
            if (isset($data['data']['list'])) {
                foreach ($data['data']['list'] as $item) {
                    $videos[] = $this->formatVideoData($item);
                }
            }
            return $videos;
        } catch (Exception $e) {
            return $this->getSampleVideos(0);
        }
    }
    
    // 格式化视频数据 - 修复播放URL格式
    private function formatVideoData($item) {
        $aid = $item['aid'] ?? $item['id'] ?? '0';
        $bvid = $item['bvid'] ?? '';
        
        // 修复播放URL - 使用av号_cid格式
        $cid = $item['cid'] ?? $item['stat']['aid'] ?? $aid;
        $playUrl = $aid . '_' . $cid;
        
        return [
            'vod_id' => $aid,
            'vod_name' => $item['title'] ?? '未知标题',
            'vod_pic' => $item['pic'] ?? '',
            'vod_remarks' => $this->formatPlayCount($item['stat']['view'] ?? $item['play'] ?? 0),
            'vod_content' => $item['desc'] ?? $item['description'] ?? '',
            'vod_play_from' => 'B站',
            'vod_play_url' => "第1集$$playUrl"
        ];
    }
    
    // 搜索视频
    private function searchVideos($keyword, $page = 1) {
        try {
            $url = "{$this->baseUrl}/x/web-interface/search/type?" . http_build_query([
                'search_type' => 'video',
                'keyword' => $keyword,
                'page' => $page
            ]);
            
            $response = $this->curlRequest($url);
            $data = json_decode($response, true);
            
            $videos = [];
            if (isset($data['data']['result'])) {
                foreach ($data['data']['result'] as $item) {
                    $videos[] = $this->formatVideoData($item);
                }
            }
            return $videos;
        } catch (Exception $e) {
            $playUrl = "123456_789012"; // 示例ID
            return [[
                'vod_id' => 'search_1', 
                'vod_name' => '搜索结果: ' . $keyword, 
                'vod_pic' => '', 
                'vod_remarks' => '搜索',
                'vod_play_from' => 'B站',
                'vod_play_url' => "第1集$$playUrl"
            ]];
        }
    }
    
    // 获取视频详情
    public function getVideoDetail($aid) {
        try {
            $url = "{$this->baseUrl}/x/web-interface/view?aid=" . $aid;
            $response = $this->curlRequest($url);
            $data = json_decode($response, true);
            
            if (isset($data['data'])) {
                $video = $data['data'];
                $cid = $video['cid'] ?? $aid;
                $playUrl = $aid . '_' . $cid;
                
                return [
                    'vod_id' => $aid,
                    'vod_name' => $video['title'] ?? '未知标题',
                    'vod_pic' => $video['pic'] ?? '',
                    'vod_content' => $video['desc'] ?? '',
                    'vod_play_from' => 'B站',
                    'vod_play_url' => "第1集$$playUrl"
                ];
            }
        } catch (Exception $e) {
            $playUrl = $aid . '_' . $aid;
            return [
                'vod_id' => $aid,
                'vod_name' => 'B站视频详情 - ' . $aid,
                'vod_pic' => '',
                'vod_content' => '这是一个B站视频的详细描述',
                'vod_play_from' => 'B站',
                'vod_play_url' => "第1集$$playUrl"
            ];
        }
    }
    
    // 获取播放地址 - 采用三级获取策略
    public function getPlayUrl($id) {
        if (strpos($id, '_') === false) {
            return [
                'parse' => 0,
                'url' => '',
                'header' => $this->getHeaders()
            ];
        }
        
        list($avid, $cid) = explode('_', $id);
        $playUrl = '';
        
        // 第一级：官方API获取播放地址
        $playUrl = $this->getOfficialPlayUrl($avid, $cid);
        
        // 第二级：备用地址
        if (empty($playUrl)) {
            $playUrl = $this->getBackupPlayUrl($avid, $cid);
        }
        
        // 第三级：第三方解析
        if (empty($playUrl)) {
            $playUrl = $this->getThirdPartyPlayUrl($avid, $cid);
        }
        
        $headers = $this->getHeaders();
        $headers['Referer'] = 'https://www.bilibili.com/video/av' . $avid;
        
        return [
            'parse' => 0,  // 0=直接播放
            'url' => $playUrl,
            'header' => $headers
        ];
    }
    
    // 官方API获取播放地址
    private function getOfficialPlayUrl($avid, $cid) {
        try {
            $url = "{$this->baseUrl}/x/player/playurl";
            $params = [
                'avid' => $avid,
                'cid' => $cid,
                'qn' => 116, // 高清
                'fnval' => 16,
                'fourk' => 1
            ];
            
            $response = $this->curlRequest($url, $params);
            $data = json_decode($response, true);
            
            if (isset($data['data']['durl'][0]['url'])) {
                return $data['data']['durl'][0]['url'];
            }
        } catch (Exception $e) {
            // 忽略错误，继续尝试其他方法
        }
        
        return '';
    }
    
    // 获取备用播放地址
    private function getBackupPlayUrl($avid, $cid) {
        // 尝试多种备用地址格式
        $backupUrls = [
            "https://cn-bj-cc-01-12.bilivideo.com/upgcxcode/21/73/{$cid}/{$cid}-1-80.flv",
            "https://upos-sz-mirrorcos.bilivideo.com/upgcxcode/21/73/{$cid}/{$cid}-1-80.flv",
        ];
        
        foreach ($backupUrls as $url) {
            if ($this->checkUrlAccessible($url)) {
                return $url;
            }
        }
        
        return '';
    }
    
    // 获取第三方解析地址
    private function getThirdPartyPlayUrl($avid, $cid) {
        // 使用第三方B站解析服务
        $thirdPartyUrls = [
            "https://api.injahow.cn/bparse/?av={$avid}&cid={$cid}",
        ];
        
        foreach ($thirdPartyUrls as $url) {
            try {
                $result = $this->curlRequest($url);
                $data = json_decode($result, true);
                if (isset($data['url']) && !empty($data['url'])) {
                    return $data['url'];
                }
            } catch (Exception $e) {
                // 继续尝试下一个
            }
        }
        
        return '';
    }
    
    // 检查URL是否可访问
    private function checkUrlAccessible($url) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_NOBODY => true,
            CURLOPT_TIMEOUT => 5,
            CURLOPT_FOLLOWLOCATION => true
        ]);
        curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return $httpCode === 200;
    }
    
    // 获取请求头
    private function getHeaders() {
        return [
            'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer' => 'https://www.bilibili.com'
        ];
    }
    
    // 示例视频数据
    private function getSampleVideos($tid) {
        $samples = [];
        $categoryName = $this->getCategoryNameByTid($tid);
        
        for ($i = 1; $i <= 10; $i++) {
            $playUrl = "123456_789012";
            
            $samples[] = [
                'vod_id' => 'sample_' . $tid . '_' . $i,
                'vod_name' => $categoryName . '示例视频' . $i,
                'vod_pic' => '',
                'vod_remarks' => '示例',
                'vod_content' => '这是一个示例视频描述',
                'vod_play_from' => 'B站',
                'vod_play_url' => "第1集$$playUrl"
            ];
        }
        
        return $samples;
    }
    
    // 根据tid获取分类名称
    private function getCategoryNameByTid($tid) {
        foreach ($this->categories as $category) {
            if (isset($category['tid']) && $category['tid'] == $tid) {
                return $category['name'];
            }
        }
        return '未知分类';
    }
    
    // 格式化播放量
    private function formatPlayCount($count) {
        if ($count >= 10000) {
            return round($count / 10000, 1) . '万';
        }
        return $count;
    }
    
    // CURL请求
    private function curlRequest($url, $params = []) {
        $ch = curl_init();
        
        if (!empty($params)) {
            $url .= '?' . http_build_query($params);
        }
        
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            CURLOPT_REFERER => 'https://www.bilibili.com',
            CURLOPT_ENCODING => 'gzip'
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {
            throw new Exception('HTTP请求失败: ' . $httpCode);
        }
        
        return $response;
    }
}

// 初始化B站爬虫
$biliSpider = new BiliBiliSpider();

// 获取子分类
function getChildCategories($parentId) {
    global $biliSpider;
    return $biliSpider->getChildren($parentId);
}

// 获取分类信息
function getCategoryInfo($categoryId) {
    global $biliSpider;
    return $biliSpider->getCategory($categoryId);
}

// 主逻辑
switch ($ac) {
    case 'detail':
        if (!empty($ids)) {
            $videoDetail = $biliSpider->getVideoDetail($ids);
            $data = ['list' => [$videoDetail]];
            echo json_encode($data, JSON_UNESCAPED_UNICODE);
        } elseif (!empty($t)) {
            $filters = !empty($f) ? json_decode($f, true) : [];
            
            $isSubRequest = isset($filters['is_sub']) && $filters['is_sub'] === 'true';
            $categoryId = $filters['category_id'] ?? $t;
            
            $categoryInfo = getCategoryInfo($categoryId);
            $hasChildren = $categoryInfo['has_children'] ?? false;
            
            if ($isSubRequest && !$hasChildren) {
                $tid = $categoryInfo['tid'] ?? 0;
                $videos = $biliSpider->getVideoList($tid, $pg);
                
                $data = [
                    'list' => $videos,
                    'page' => intval($pg),
                    'pagecount' => 10,
                    'limit' => 20,
                    'total' => 200,
                    'current_category' => $categoryInfo['name'] ?? '',
                    'style' => ['type' => 'rect', 'ratio' => 0.75]
                ];
                echo json_encode($data, JSON_UNESCAPED_UNICODE);
            } else {
                $children = getChildCategories($t);
                
                if (empty($children)) {
                    $tid = $categoryInfo['tid'] ?? 0;
                    $videos = $biliSpider->getVideoList($tid, $pg);
                    
                    $data = [
                        'list' => $videos,
                        'page' => intval($pg),
                        'pagecount' => 10,
                        'limit' => 20,
                        'total' => 200,
                        'current_category' => $categoryInfo['name'] ?? '',
                        'style' => ['type' => 'rect', 'ratio' => 0.75]
                    ];
                } else {
                    $subList = [];
                    foreach ($children as $child) {
                        $subList[] = [
                            'vod_id' => $child['id'],
                            'vod_name' => $child['name'],
                            'vod_pic' => '',
                            'vod_remarks' => '分类'
                        ];
                    }
                    
                    $data = [
                        'is_sub' => true,
                        'list' => $subList,
                        'page' => intval($pg),
                        'pagecount' => 1,
                        'limit' => 20,
                        'total' => count($subList),
                        'parent_category' => $categoryInfo['name'] ?? '',
                        'style' => ['type' => 'rect', 'ratio' => 1.5]
                    ];
                }
                echo json_encode($data, JSON_UNESCAPED_UNICODE);
            }
        } else {
            $data = [
                'class' => $biliSpider->getLevel1Categories(),
                'list' => $biliSpider->getVideoList(0, 1), // 热门推荐
                'style' => ['type' => 'rect', 'ratio' => 1.33]
            ];
            echo json_encode($data, JSON_UNESCAPED_UNICODE);
        }
        break;
    
    case 'search':
        $videos = $biliSpider->getVideoList(0, $pg, $wd);
        $data = [
            'list' => $videos,
            'page' => intval($pg),
            'pagecount' => 10,
            'limit' => 20,
            'total' => count($videos)
        ];
        echo json_encode($data, JSON_UNESCAPED_UNICODE);
        break;
        
    case 'play':
        $playInfo = $biliSpider->getPlayUrl($id);
        echo json_encode($playInfo, JSON_UNESCAPED_UNICODE);
        break;
    
    default:
        $data = ['error' => 'Unknown action: ' . $ac];
        echo json_encode($data, JSON_UNESCAPED_UNICODE);
}
?>