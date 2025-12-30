# 角色定义
define n = Character("")

define heroine_001 = Character("小飞翔")
define protagonist_main = Character("星野翔太")

transform bg_full:
    xalign 0.5
    yalign 0.5
    xsize config.screen_width
    ysize config.screen_height


label start:
    # 第1章 (common_ch1)

    # === 第1幕: 初遇精灵林 ===
    # 场景: spirit_grove, 时间: 放学后
    # 背景: 森林童话风格，树木高大繁茂，树叶泛着微光，地面铺满柔软的青苔，静谧而温暖，充满探索与发现的乐趣。
    scene bg spirit_grove at bg_full

    n "放学铃声刚响，我独自走向学园后山那片传说中的精灵林。阳光透过枝叶洒下斑驳光影，空气中弥漫着淡淡的草木清香。我不知道自己为什么会来这里，只是觉得心里有种莫名的牵引感——仿佛有什么东西在呼唤我。"

    n "脚步踩在青苔上发出轻微的沙沙声，像是大地在低语。"

    show protagonist_main confused
    # 低声自语，手指无意识地摩挲着左手腕上的银戒
    protagonist_main "……这里真的存在吗？还是我只是太想找个地方躲起来？"

    n "戒指突然微微发热，像一颗跳动的心脏。"

    # 瞳孔微缩，呼吸变得急促

    n "一阵风掠过树梢，带来一丝清甜的气息，像是某种生物正靠近。"
    
    hide protagonist_main confused

    show heroine_001 nervous
    # 从一棵大树后探出半个身子，翅膀微微颤动
    heroine_001 "喂！你是不是……能看见我？"

    show protagonist_main surprised
    # 猛地后退一步，差点被树根绊倒
    protagonist_main "啊？！你、你是谁？！"

    n "她穿着淡金色的小裙子，眼睛亮得像星星，却带着一丝不安。"

    show heroine_001 normal
    # 挺起胸膛，但脚尖不自觉地抠进泥土里
    heroine_001 "我是小飞翔！我可是很厉害的精灵哦！虽然上次失败了……但我现在可以帮你！"

    show protagonist_main normal
    # 慢慢蹲下来，试图平视她的高度
    protagonist_main "等等，你说‘帮我’？我连你是谁都不知道……"

    n "那一刻，我忽然明白——不是我在找精灵，而是她一直在等一个愿意相信她的人。"

    show heroine_001 normal
    # 低头咬住嘴唇，手指绞在一起
    heroine_001 "那你愿意试试看吗？我可以带你去梦里最漂亮的地方！只要你不嫌弃我笨……"

    show protagonist_main gentle
    # 伸出手，掌心向上
    protagonist_main "……我不嫌弃。其实，我也很久没被人这样认真地问过‘要不要一起’了。"

    n "她迟疑了一下，然后轻轻飞到我的掌心，像一片羽毛落定。"

    show heroine_001 normal
    # 用翅膀轻触我的指尖
    heroine_001 "那……我们算是朋友了吗？"

    n "那一刻，我第一次感觉到——原来有人愿意为我停留，哪怕只是短短的一瞬。"

    # === 第2幕: 灵契初启 ===
    # 场景: spirit_grove, 时间: 放学后
    # 背景: 森林童话风格，树木高大繁茂，树叶泛着微光，地面铺满柔软的青苔，静谧而温暖，充满探索与发现的乐趣。
    scene bg spirit_grove

    n "小飞翔在我掌心轻轻颤抖，像是第一次感受到人类温度的生命体。我能感觉到她的情绪波动，就像心跳一样清晰。"

    show heroine_001 sad
    # 把头埋进翅膀里
    heroine_001 "你……不会觉得我很奇怪吧？我总是想证明自己值得被喜欢……"

    show protagonist_main serious
    # 轻轻抚摸她的翅膀
    protagonist_main "怎么会？你明明就很可爱啊。而且……我觉得你比任何人都更真诚。"

    n "戒指再次发热，这次不再是灼热，而是温润如春水。"

    show heroine_001 normal
    # 抬起头，眼中闪着泪光
    heroine_001 "真的吗？那……我们可以成为伙伴吗？"

    show protagonist_main normal
    # 微笑看着她
    protagonist_main "当然可以。不过……你要答应我一件事。"

    show heroine_001 delighted
    # 原地转了个圈
    heroine_001 "什么事？我都答应！"

    show protagonist_main determined
    # 握住她的手（翅膀）
    protagonist_main "以后不要总想着‘证明自己’，因为你的存在本身就已经足够好了。"

    n "一瞬间，整个森林似乎都安静了下来，只有我们的呼吸交织在一起。"

    show heroine_001 normal
    # 眼角湿润，但嘴角扬起
    heroine_001 "……谢谢你。这是我第一次听到有人说‘你本来就很好’。"

    show protagonist_main normal
    # 伸出小指
    protagonist_main "那我们就约定好了，无论将来发生什么，都要记得今天这一刻。"

    show heroine_001 happy
    # 也伸出小指勾住他的
    heroine_001 "嗯！拉钩！"

    n "那一刻，我知道，这不是结束，而是开始——一段关于爱与成长的故事，刚刚拉开帷幕。"

    show heroine_001 normal
    # 眨眨眼，声音突然压低
    heroine_001 "对了！我还有一件事要告诉你……"

    show protagonist_main curious
    # 身体前倾
    protagonist_main "什么事？"

    n "她没有回答，只是轻轻飞到我耳边，低声说了一句让我至今难忘的话。"

    # === 第3幕: 星光下的誓言 ===
    # 场景: spirit_grove, 时间: 放学后
    # 背景: 森林童话风格，树木高大繁茂，树叶泛着微光，地面铺满柔软的青苔，静谧而温暖，充满探索与发现的乐趣。
    scene bg spirit_grove

    n "夜幕悄然降临，精灵林的光芒变得更加柔和，像是无数颗星星落在了人间。小飞翔坐在我的肩头，安静得像个孩子。"

    show heroine_001 normal
    # 靠在我肩膀上
    heroine_001 "你知道吗？以前我总觉得，只有做得最好才能被人记住……但现在我明白了，被人记住是因为你真实地活过。"

    show protagonist_main normal
    # 望着星空，轻声呢喃
    protagonist_main "你说得太对了。我一直以为，爱是一种负担……但现在我发现，它更像是……一种勇气。"

    n "戒指突然发出微弱的金光，仿佛也在回应我们的话语。"

    show heroine_001 normal
    # 抬头看着我，眼神清澈
    heroine_001 "那……我们现在是不是已经算是‘灵契’了？"

    show protagonist_main gentle
    # 伸手摸了摸她的头发
    protagonist_main "是啊，我们之间已经有了某种看不见的联系。就像今晚的星光，即使看不见，也知道它在那里。"

    show heroine_001 normal
    # 紧紧抓住我的衣角
    heroine_001 "那……你会一直陪我吗？"

    show protagonist_main determined
    # 轻轻抱住她
    protagonist_main "当然会。因为你是我第一个真正愿意信任的人。"

    n "那一刻，我没有想到，这句承诺会在未来无数次动摇我的心跳。"

    show heroine_001 proud
    # 蹦跳着飞回空中
    heroine_001 "嘿嘿，那你可要记住哦！下次见面，我要给你看我最棒的飞行技巧！"

    show protagonist_main smile
    # 仰头望着她，手掌张开
    protagonist_main "好啊，我等着看你飞翔的样子。"

    n "她飞向夜空，小小的身影渐渐融入星光之中，留下一句轻飘飘却又沉甸甸的告别。"

    show heroine_001 normal
    # 挥舞翅膀，消失在林深处
    heroine_001 "明天见啦，翔太！"

    show protagonist_main normal
    # 站在原地，久久不动
    protagonist_main "……明天见。"

    n "我终于明白，有些相遇，注定不会平凡。而那个夜晚，就是一切故事的起点。"

    show protagonist_main normal
    # 握紧拳头，感受戒指的温度
    protagonist_main "原来……我不是一个人。"

    n "从此以后，我不再害怕孤独。因为我有了属于自己的光。"

    # === 第4幕: 归途余温 ===
    # 场景: spirit_grove, 时间: 放学后
    # 背景: 森林童话风格，树木高大繁茂，树叶泛着微光，地面铺满柔软的青苔，静谧而温暖，充满探索与发现的乐趣。
    scene bg spirit_grove

    n "走出精灵林时，夕阳已完全隐去，天空只剩下几颗星星。我回头望了一眼那片幽深的森林，心中涌起一股难以言喻的暖意。"

    show protagonist_main normal
    # 对着空气轻声说道
    protagonist_main "小飞翔……谢谢你。不是因为你能做什么，而是因为你让我重新相信了‘连接’的意义。"

    n "戒指微微发烫，仿佛在回应我的话语。"

    show heroine_001 normal
    # 从远处传来一声清脆的笑声
    heroine_001 "哼，你以为我会听不见吗？我才不会这么容易就忘记你呢！"

    show protagonist_main normal
    # 笑着摇头
    protagonist_main "……你真是个麻烦精。"

    n "那一刻，我意识到，这不仅仅是一场偶遇，而是一个全新的开始。"

    show protagonist_main normal
    # 迈步走向校门，脚步轻快
    protagonist_main "你说得对，我不是一个人了。"

    show heroine_001 normal
    # 在空中画了个圈，一闪而逝
    heroine_001 "那就别忘了我们的约定哦！下次见面，我要让你看到真正的我！"

    n "我笑了，那是我很久以来第一次发自内心的笑容。"

    show protagonist_main gentle
    # 挥手告别，转身离去
    protagonist_main "好，我等着。"

    n "我知道，这只是开始。真正的旅程，才刚刚启程。"

    show protagonist_main determined
    # 握紧拳头，朝天边望去
    protagonist_main "希望有一天，我也能像你一样，勇敢地做自己。"

    n "风吹过耳畔，像是某种无声的回应。"

    show heroine_001 normal
    # 从远处追来，笑声清脆
    heroine_001 "喂！你这个笨蛋！别走太快啦！"

    show protagonist_main normal
    # 停下脚步，等待她靠近
    protagonist_main "知道了，小麻烦精。"

    n "这就是我和小飞翔的故事，一个关于信任、勇气和一点点甜蜜的开始。"

    show protagonist_main gentle
    # 伸出手，等她飞过来
    protagonist_main "欢迎来到我的世界，小飞翔。"

    # === 第5幕: 灵契初现 ===
    # 场景: spirit_grove, 时间: 放学后
    # 背景: 森林童话风格，树木高大繁茂，树叶泛着微光，地面铺满柔软的青苔，静谧而温暖，充满探索与发现的乐趣。
    scene bg spirit_grove

    n "精灵林的夜色依旧温柔，我站在原地，看着小飞翔的身影远去，心中却不再空荡。我知道，这场冒险才刚刚开始。"

    show protagonist_main normal
    # 闭上眼睛，深深吸气
    protagonist_main "原来，遇见一个人，真的能让整个世界变得不一样。"

    n "戒指轻轻震动，像是在回应我的心情。"

    show heroine_001 normal
    # 突然出现在我面前，戳了戳我的脸
    heroine_001 "喂！你这个呆子！别发愣啊！我们还要一起去看更多地方呢！"

    show protagonist_main wry
    # 揉了揉被戳的脸颊
    protagonist_main "……你什么时候学会偷袭的？"

    n "她笑得像个孩子，眼里全是光。"

    show heroine_001 proud
    # 叉腰站立
    heroine_001 "因为你是我的搭档嘛！搭档就要互相监督！"

    show protagonist_main normal
    # 假装严肃
    protagonist_main "……好吧，我认输。不过，你能不能别总是这么吵？"

    show heroine_001 normal
    # 飞到半空，做出夸张的手势
    heroine_001 "哼！那要看你有没有本事让我安静下来！"

    n "我笑了，那种久违的、轻松的感觉回来了。"

    show protagonist_main normal
    # 摊手耸肩
    protagonist_main "行吧，那我就试着让你安静一会儿。"

    show heroine_001 normal
    # 捂住耳朵，假装哭泣
    heroine_001 "哇！你居然敢这么说！我生气了！"

    n "我忍不住笑出声，那一刻，我感觉自己好像找回了什么重要的东西。"

    show protagonist_main normal
    # 伸出手，让她降落在我掌心
    protagonist_main "好了好了，我错了。你是最棒的精灵，也是我最好的朋友。"

    show heroine_001 happy
    # 蹭了蹭我的手指
    heroine_001 "这才对嘛！这才是我认识的那个翔太！"

    n "我们就这样静静地站着，谁也没有说话，却感觉无比亲密。"

    show protagonist_main gentle
    # 轻声说
    protagonist_main "谢谢你，小飞翔。谢谢你让我知道，我不是一个人。"

    n "那一刻，我知道，无论未来有多难，只要有你在身边，我就有勇气走下去。"

    return
