"""
One-time seed script: populate library.json from existing data.
Run once: python tools/seed_library.py
"""
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib_db import _load, _save, DB_PATH

# Books extracted from READING GUIDE.md and RECORD/ folder structure
# Format: [title_cn, creator, title_orig, creator_orig, date_finished, tags, rating, status]
BOOKS = [
    # === 2025-01 (2501) ===
    ("霍乱时期的爱情", "加西亚·马尔克斯", "El amor en los tiempos del cólera", "Gabriel García Márquez",
     "2025-01", ["文学", "拉美文学", "爱情"], 9, "finished"),
    ("素食者", "韩江", "채식주의자", "Han Kang",
     "2025-01", ["文学", "女性主义", "韩国文学"], 8, "finished"),
    ("悉达多", "赫尔曼·黑塞", "Siddhartha", "Hermann Hesse",
     "2025-01", ["文学", "哲学", "德国文学"], 8, "finished"),
    ("银河帝国：基地七步曲", "艾萨克·阿西莫夫", "Foundation series", "Isaac Asimov",
     "2025-01", ["科幻", "美国文学"], 9, "finished"),
    ("美狄亚", "欧里庇得斯", "Μήδεια", "Euripides",
     "2025-01", ["文学", "女性主义", "戏剧", "古希腊"], 8, "finished"),
    ("万历十五年", "黄仁宇", "1587, a Year of No Significance", "Ray Huang",
     "2025-01", ["历史", "中国历史", "政治"], 9, "finished"),

    # === 2025-02 (2502) ===
    ("万物静默如迷", "维斯拉瓦·辛波斯卡", "Poems New and Collected", "Wisława Szymborska",
     "2025-02", ["诗歌", "波兰文学", "诺贝尔文学奖"], 8, "finished"),
    ("夜晚的潜水艇", "陈春成", "", "",
     "2025-02", ["文学", "中短篇小说", "中国当代文学", "幻想"], 8, "finished"),
    ("德米安：彷徨少年时", "赫尔曼·黑塞", "Demian", "Hermann Hesse",
     "2025-02", ["文学", "德国文学", "成长"], 8, "finished"),
    ("撒哈拉的故事", "三毛", "", "",
     "2025-02", ["文学", "散文", "中国文学", "旅行"], 7, "finished"),
    ("鱼不存在", "露露·米勒", "Why Fish Don't Exist", "Lulu Miller",
     "2025-02", ["科普", "传记", "美国"], 8, "finished"),
    ("鳗鱼的旅行", "帕特里克·斯文松", "The Book of Eels", "Patrik Svensson",
     "2025-02", ["科普", "自然写作", "瑞典"], 8, "finished"),

    # === 2025-03 (2503) ===
    ("死于黎明：洛尔迦诗选", "费德里科·加西亚·洛尔迦", "Poems of Federico García Lorca", "Federico García Lorca",
     "2025-03", ["诗歌", "西班牙文学", "戏剧"], 8, "finished"),
    ("儒林外史", "吴敬梓", "", "",
     "2025-03", ["文学", "中国古典文学", "讽刺"], 8, "finished"),
    ("如果我们无法以光速前行", "金草叶", "우리가 빛의 속도로 갈 수 없다면", "Kim Cho-yeop",
     "2025-03", ["科幻", "韩国文学", "中短篇小说", "女性"], 8, "finished"),
    ("树犹如此", "白先勇", "", "",
     "2025-03", ["文学", "散文", "中国台湾文学"], 8, "finished"),
    ("焚舟纪", "安吉拉·卡特", "Burning Your Boats", "Angela Carter",
     "2025-03", ["文学", "中短篇小说", "英国文学", "魔幻现实", "女性主义"], 9, "finished"),
    ("美的历程", "李泽厚", "", "",
     "2025-03", ["美学", "中国艺术史", "哲学"], 8, "finished"),
    ("美的沉思", "蒋勋", "", "",
     "2025-03", ["美学", "中国艺术史"], 8, "finished"),
    ("黑暗的左手", "厄休拉·勒古恩", "The Left Hand of Darkness", "Ursula K. Le Guin",
     "2025-03", ["科幻", "美国文学", "女性主义"], 9, "finished"),

    # === 2025-04 (2504) ===
    ("人的大地", "安托万·德·圣埃克苏佩里", "Terre des hommes", "Antoine de Saint-Exupéry",
     "2025-04", ["文学", "法国文学", "飞行", "散文"], 8, "finished"),
    ("回归故里", "迪迪埃·埃里蓬", "Retour à Reims", "Didier Eribon",
     "2025-04", ["社会学", "法国", "阶级", "自传"], 8, "finished"),
    ("夜航西飞", "柏瑞尔·马卡姆", "West with the Night", "Beryl Markham",
     "2025-04", ["文学", "飞行", "非洲", "英国文学", "女性"], 9, "finished"),
    ("她来自马里乌波尔", "娜塔莎·沃丁", "Sie kam aus Mariupol", "Natascha Wodin",
     "2025-04", ["文学", "历史", "二战", "东欧", "女性"], 8, "finished"),
    ("无条件投降博物馆", "杜布拉芙卡·乌格雷西奇", "The Museum of Unconditional Surrender", "Dubravka Ugrešić",
     "2025-04", ["文学", "东欧", "流亡", "女性"], 8, "finished"),
    ("马克瓦尔多", "伊塔洛·卡尔维诺", "Marcovaldo", "Italo Calvino",
     "2025-04", ["文学", "意大利文学", "城市"], 8, "finished"),

    # === 2025-05 (2505) ===
    ("不能承受的生命之轻", "米兰·昆德拉", "Nesnesitelná lehkost bytí", "Milan Kundera",
     "2025-05", ["文学", "哲学", "捷克文学", "法国文学"], 9, "finished"),
    ("哲学家与狼", "马克·罗兰兹", "The Philosopher and the Wolf", "Mark Rowlands",
     "2025-05", ["哲学", "动物", "英国"], 7, "finished"),
    ("佩德罗·巴拉莫", "胡安·鲁尔福", "Pedro Páramo", "Juan Rulfo",
     "2025-05", ["文学", "拉美文学", "魔幻现实", "墨西哥"], 9, "finished"),
    ("巴黎评论：女性作家访谈", "巴黎评论编辑部", "The Paris Review: Women Writers at Work", "",
     "2025-05", ["访谈", "写作", "女性", "文学"], 8, "finished"),
    ("明智的孩子", "安吉拉·卡特", "Wise Children", "Angela Carter",
     "2025-05", ["文学", "英国文学", "女性主义", "魔幻现实"], 8, "finished"),
    ("燃烧的原野", "胡安·鲁尔福", "El Llano en llamas", "Juan Rulfo",
     "2025-05", ["文学", "拉美文学", "中短篇小说", "墨西哥"], 9, "finished"),
    ("老派少女购物指南", "洪爱珠", "", "",
     "2025-05", ["散文", "美食", "中国台湾文学", "生活"], 8, "finished"),
    ("鱼翅与花椒", "扶霞·邓洛普", "Shark's Fin and Sichuan Pepper", "Fuchsia Dunlop",
     "2025-05", ["美食", "文化", "中国", "英国"], 7, "finished"),
    ("企鹅课", "汤姆·米切尔", "The Penguin Lessons", "Tom Michell",
     "2025-05", ["文学", "动物", "英国"], 7, "finished"),

    # === 2025-06 (2506) ===
    ("公主之死", "李贞德", "", "",
     "2025-06", ["历史", "法律", "女性", "中国"], 8, "finished"),

    # === 2025-07 (2507) ===
    ("N号房追踪记", "추적단 불꽃", "", "",
     "2025-07", ["非虚构", "女性主义", "韩国", "社会"], 8, "finished"),
    ("公羊的节日", "马里奥·巴尔加斯·略萨", "La fiesta del chivo", "Mario Vargas Llosa",
     "2025-07", ["文学", "拉美文学", "政治", "历史", "诺贝尔文学奖"], 8, "finished"),
    ("我将宇宙随身携带", "费尔南多·佩索阿", "Poemas de Alberto Caeiro", "Fernando Pessoa",
     "2025-07", ["诗歌", "葡萄牙文学", "哲学"], 9, "finished"),
    ("疼痛部", "杜布拉芙卡·乌格雷西奇", "The Ministry of Pain", "Dubravka Ugrešić",
     "2025-07", ["文学", "东欧", "流亡", "女性"], 8, "finished"),
    ("鲟鱼", "", "", "",
     "2025-07", ["文学"], 7, "finished"),

    # === 2025-08 (2508) ===
    ("查令十字街84号", "海莲·汉芙", "84, Charing Cross Road", "Helene Hanff",
     "2025-08", ["文学", "书信", "书与阅读", "美国"], 8, "finished"),
    ("献灯使", "多和田叶子", "献灯使", "Yoko Tawada",
     "2025-08", ["文学", "日本文学", "反乌托邦", "科幻"], 8, "finished"),
    ("老妓抄", "冈本加乃子", "", "Kanoko Okamoto",
     "2025-08", ["文学", "中短篇小说", "日本文学", "女性"], 8, "finished"),

    # === 2025-09 ===
    # (No records found for 2509)

    # === 2025-10 (2510) ===
    ("大师与玛格丽特", "米哈伊尔·布尔加科夫", "Мастер и Маргарита", "Mikhail Bulgakov",
     "2025-10", ["文学", "俄罗斯文学", "魔幻现实", "讽刺"], 9, "finished"),

    # === 2025-11 (2511) ===
    # Reflections on Camus, existentialism - no specific book recorded

    # === 2026-02 (2602) ===
    ("猎人", "双雪涛", "", "",
     "2026-02", ["文学", "中短篇小说", "中国当代文学", "东北"], 8, "finished"),

    # === 2026-03 (2603) ===
    ("表姐妹", "奥罗拉·本图里尼", "Las primas", "Aurora Venturini",
     "2026-03", ["文学", "阿根廷文学", "女性", "成长"], 8, "finished"),

    # === 2026-04 (2604) ===
    ("世界电影史", "大卫·波德维尔 / 克里斯汀·汤普森", "Film History: An Introduction", "David Bordwell / Kristin Thompson",
     "2026-04", ["电影", "历史", "学术"], None, "reading"),

    # === From READING GUIDE.md - books mentioned but no RECORD folder found ===
    ("百年孤独", "加西亚·马尔克斯", "Cien años de soledad", "Gabriel García Márquez",
     None, ["文学", "拉美文学", "魔幻现实", "历史"], 10, "finished"),
    ("红楼梦", "曹雪芹", "", "",
     None, ["文学", "中国古典文学", "美学"], 10, "finished"),
    ("都柏林人", "詹姆斯·乔伊斯", "Dubliners", "James Joyce",
     None, ["文学", "中短篇小说", "爱尔兰文学"], None, "to-read"),
    ("梦中的欢乐葬礼和十二个异乡故事", "加西亚·马尔克斯", "Strange Pilgrims", "Gabriel García Márquez",
     None, ["文学", "中短篇小说", "拉美文学", "魔幻现实"], None, "to-read"),
    ("王尔德奇异故事集", "奥斯卡·王尔德", "The Complete Short Stories", "Oscar Wilde",
     None, ["文学", "中短篇小说", "英国文学"], None, "to-read"),
    ("公羊的节日", "马里奥·巴尔加斯·略萨", "La fiesta del chivo", "Mario Vargas Llosa",
     None, ["文学", "拉美文学", "政治"], None, "to-read"),  # Already listed in 2507 but also in GUIDE
]

# Movies extracted from FILMS GUIDE.md and RECORD/ folder structure
MOVIES = [
    # === TOP MOVIES from FILMS GUIDE.md ===
    ("霸王别姬", "陈凯歌", "Farewell My Concubine", "Chen Kaige",
     "2025-02", ["剧情", "历史", "中国", "美", "痛苦"], 10, "finished"),
    ("星际穿越", "克里斯托弗·诺兰", "Interstellar", "Christopher Nolan",
     None, ["科幻", "时间", "爱"], 9, "finished"),
    ("奥本海默", "克里斯托弗·诺兰", "Oppenheimer", "Christopher Nolan",
     None, ["传记", "历史", "毁灭", "挣扎"], 9, "finished"),

    # === 2025-01 (2501) ===
    ("好东西", "邵艺辉", "Her Story", "Shao Yihui",
     "2025-01", ["剧情", "女性", "中国", "当代"], 8, "finished"),

    # === 2025-02 (2502) ===
    ("东京教父", "今敏", "Tokyo Godfathers", "Satoshi Kon",
     "2025-02", ["动画", "日本", "圣诞", "社会"], 9, "finished"),
    ("千年女优", "今敏", "Millennium Actress", "Satoshi Kon",
     "2025-02", ["动画", "日本", "爱情", "记忆"], 9, "finished"),
    ("未麻的部屋", "今敏", "Perfect Blue", "Satoshi Kon",
     "2025-02", ["动画", "日本", "悬疑", "心理"], 9, "finished"),
    ("红辣椒", "今敏", "Paprika", "Satoshi Kon",
     "2025-02", ["动画", "日本", "科幻", "梦境"], 9, "finished"),
    ("卧虎藏龙", "李安", "Crouching Tiger, Hidden Dragon", "Ang Lee",
     "2025-02", ["武侠", "中国", "爱情"], 9, "finished"),
    ("黑客帝国", "沃卓斯基姐妹", "The Matrix", "The Wachowskis",
     "2025-02", ["科幻", "动作", "哲学"], 9, "finished"),

    # === 2025-03 (2503) ===
    ("拾荒者统治", "Joseph Bennett", "Scavengers Reign", "",
     "2025-03", ["动画", "科幻", "生存", "生态"], 9, "finished"),
    ("初步举证", "", "Prima Facie", "",
     "2025-03", ["剧情", "女性主义", "法律", "英国"], 8, "finished"),
    ("还有明天", "宝拉·柯特莱西", "C'è ancora domani", "Paola Cortellesi",
     "2025-03", ["剧情", "女性主义", "意大利", "历史"], 9, "finished"),
    ("苦尽柑来遇见你", "", "", "",
     "2025-03", ["剧情", "韩国", "时代"], 8, "finished"),

    # === 2025-04 (2504) ===
    ("野马", "蒂尼斯·艾葛温", "Mustang", "Deniz Gamze Ergüven",
     "2025-04", ["剧情", "女性", "土耳其", "成长"], 8, "finished"),
    ("一次别离", "阿斯哈·法哈蒂", "جدایی نادر از سیمین", "Asghar Farhadi",
     "2025-04", ["剧情", "伊朗", "家庭", "社会"], 9, "finished"),
    ("出租车", "贾法尔·帕纳西", "تاکسی", "Jafar Panahi",
     "2025-04", ["剧情", "伊朗", "纪录片"], 8, "finished"),
    ("布达佩斯大饭店", "韦斯·安德森", "The Grand Budapest Hotel", "Wes Anderson",
     "2025-04", ["喜剧", "美学", "欧洲"], 9, "finished"),
    ("我在伊朗长大", "玛嘉·莎塔琵", "Persepolis", "Marjane Satrapi",
     "2025-04", ["动画", "自传", "伊朗", "女性"], 9, "finished"),
    ("月升王国", "韦斯·安德森", "Moonrise Kingdom", "Wes Anderson",
     "2025-04", ["剧情", "成长", "美学"], 8, "finished"),

    # === 2025-05 (2505) ===
    ("一一", "杨德昌", "Yi Yi", "Edward Yang",
     "2025-05", ["剧情", "家庭", "中国台湾", "生活"], 9, "finished"),
    ("冬冬的假期", "侯孝贤", "", "Hou Hsiao-hsien",
     "2025-05", ["剧情", "成长", "中国台湾"], 8, "finished"),
    ("哈尔的移动城堡", "宫崎骏", "Howl's Moving Castle", "Hayao Miyazaki",
     "2025-05", ["动画", "日本", "奇幻", "反战"], 9, "finished"),
    ("幽灵公主", "宫崎骏", "Princess Mononoke", "Hayao Miyazaki",
     "2025-05", ["动画", "日本", "自然", "史诗"], 9, "finished"),
    ("悲情城市", "侯孝贤", "A City of Sadness", "Hou Hsiao-hsien",
     "2025-05", ["剧情", "历史", "中国台湾"], 9, "finished"),
    ("海上花", "侯孝贤", "Flowers of Shanghai", "Hou Hsiao-hsien",
     "2025-05", ["剧情", "历史", "中国台湾"], 8, "finished"),
    ("牯岭街少年杀人事件", "杨德昌", "A Brighter Summer Day", "Edward Yang",
     "2025-05", ["剧情", "成长", "中国台湾", "历史"], 9, "finished"),
    ("童年往事", "侯孝贤", "The Time to Live and the Time to Die", "Hou Hsiao-hsien",
     "2025-05", ["剧情", "自传", "中国台湾"], 8, "finished"),
    ("棋魂", "", "Hikaru no Go", "",
     "2025-05", ["动漫", "围棋", "成长", "日本"], 8, "finished"),

    # === 2025-07 (2507) ===
    ("法式火锅", "陈英雄", "La Passion de Dodin Bouffant", "Trần Anh Hùng",
     "2025-07", ["剧情", "美食", "法国", "历史"], 8, "finished"),

    # === 2025-11 (2511) ===
    ("小森林", "森淳一", "Little Forest", "Junichi Mori",
     "2025-11", ["剧情", "美食", "日本", "自然", "治愈"], 9, "finished"),
]

# Music — from reading guide mentions and RECORD
MUSIC = [
    ("喜欢的歌", "", "", "",
     "2025-02", ["音乐", "收藏"], None, "collecting"),
]


def seed():
    """Populate library.json with all existing data."""
    db = _load()

    # Clear existing entries to avoid duplicates on re-run
    db["entries"] = []

    count = 0

    for item in BOOKS:
        title_cn, creator, title_orig, creator_orig, date_finished, tags, rating, status = item
        entry = {
            "id": str(uuid.uuid4())[:8],
            "type": "book",
            "title_cn": title_cn,
            "title_orig": title_orig,
            "creator": creator,
            "creator_orig": creator_orig,
            "date_finished": date_finished or "",
            "rating": rating,
            "tags": tags,
            "status": status,
            "notes": "",
            "cover_image": "",
            "source": "",
            "created_at": datetime.now().isoformat(),
        }
        db["entries"].append(entry)
        count += 1

    for item in MOVIES:
        title_cn, creator, title_orig, creator_orig, date_finished, tags, rating, status = item
        entry = {
            "id": str(uuid.uuid4())[:8],
            "type": "movie",
            "title_cn": title_cn,
            "title_orig": title_orig,
            "creator": creator,
            "creator_orig": creator_orig,
            "date_finished": date_finished or "",
            "rating": rating,
            "tags": tags,
            "status": status,
            "notes": "",
            "cover_image": "",
            "source": "",
            "created_at": datetime.now().isoformat(),
        }
        db["entries"].append(entry)
        count += 1

    for item in MUSIC:
        title_cn, creator, title_orig, creator_orig, date_finished, tags, rating, status = item
        entry = {
            "id": str(uuid.uuid4())[:8],
            "type": "music",
            "title_cn": title_cn,
            "title_orig": title_orig,
            "creator": creator,
            "creator_orig": creator_orig,
            "date_finished": date_finished or "",
            "rating": rating,
            "tags": tags,
            "status": status,
            "notes": "",
            "cover_image": "",
            "source": "",
            "created_at": datetime.now().isoformat(),
        }
        db["entries"].append(entry)
        count += 1

    _save(db)
    print(f"Seeded library.json with {count} entries ({len(BOOKS)} books, {len(MOVIES)} movies, {len(MUSIC)} music)")
    print(f"Database path: {DB_PATH}")


if __name__ == "__main__":
    seed()
