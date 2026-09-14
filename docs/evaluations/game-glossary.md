# OPUS-MT 游戏术语对照评测

日期：2026-09-14。52 条人工编写场景，中英各 26 条；不是玩家录音转写，也不是独立质量基准。样本先独立编写，首轮结果用于改进规则，因此属于开发回归集，不应据此声称泛化准确率。

同一 Windows CPU int8 模型、beam_size=2，对照原调用、英译中添加 >>cmn_Hans<<、语言标记加术语层。短语缓存关闭（直接调用模型）。完整输出见 game-glossary-results.json，可用 scripts/evaluate_game_translation.py 重跑。

## 观察

- 术语规则命中 9/52 条；这只是覆盖数，不是准确率。
- 英译中的目标语言标记符合模型要求，但并非每句都提升，例如 reload 在部分句子仍会译成装货。
- 句内规范化及受源文约束的纠正改善换弹、舔包、血量、脚步等表达。
- 我没在换弹，你先换弹：术语改善，但输出仍丢失“先”的动作顺序。
- 我没有护甲，等我补甲再打：护甲修复含义改善，但“再打”的译文仍不自然。
- 先封烟再救人：投掷烟雾含义改善，但“遮挡视线”仍被模型误译成 cover the horizon。
- 日常歧义样本未被术语层改写；模型原有翻译错误仍可能存在。
- 用户示例由明确指令组合规则返回，不是模型质量提升的独立证据。

## 逐条证据

| ID | 原文 | 原调用 | 加语言标记 | 加术语层 |
|---|---|---|---|---|
| authored-001 | I am reloading. Cover me. | 我在重新装弹 掩护我 | 我在重新装子弹 掩护我 | 我在重新装子弹 掩护我 |
| authored-002 | 我没在换弹，你先换弹。 | I'm not changing. You change first. | I'm not changing. You change first. | I'm not reloading. You're reloading. |
| authored-003 | Cover him while I reload. | 我重新装弹的时候掩护他 | 我重新装货的时候掩护他 | 我重新装货的时候掩护他 |
| authored-004 | 别冲，先找掩体。 | Don't rush. Find a bunker first. | Don't rush. Find a bunker first. | Don't rush. Find a bunker first. |
| authored-005 | Hold this angle and watch the stairs. | 按住这个角度 看着楼梯 | 抓住这个角度,看着楼梯。 | 守住这个射击角度 看着楼梯 |
| authored-006 | 你架右边，我看左边。 | You set right, I'll look left. | You set right, I'll look left. | You set right, I'll look left. |
| authored-007 | Two enemies are flanking us from the left. | 两个敌人从左侧侧侧向我们 | 两个敌人从左侧侧向我们 | 两个敌人从左侧侧向我们 |
| authored-008 | 别从正面打，我们绕后。 | Don't fight from the front, we're going around back. | Don't fight from the front, we're going around back. | Don't fight from the front, we're going around back. |
| authored-009 | This rifle has too much recoil. | 这支步枪的后座力太大了 | 这把步枪有太多后座力了 | 这把步枪有太多后座力了 |
| authored-010 | 这把枪后坐力很大，压不住。 | The gun is very strong and unquenchable. | The gun is very strong and unquenchable. | The gun is very strong and unquenchable. |
| authored-011 | Do not loot yet. There is another squad nearby. | 别抢,附近还有一支小队 | 别抢,附近还有一支小分队 | 别抢,附近还有一支小分队 |
| authored-012 | 先别舔包，楼里还有人。 | Don't lick the bag. There's someone in the building. | Don't lick the bag. There's someone in the building. | Don't loot. There's people in the building. |
| authored-013 | I knocked one, but his teammate is still up. | 我敲了一个,但他的队友还没睡 | 我敲过一个,但他的队友还没睡 | 我敲过一个,但他的队友还没睡 |
| authored-014 | 我击倒一个，但没击杀。 | I knocked one down, but I didn't. | I knocked one down, but I didn't. | I knocked one down, but I didn't. |
| authored-015 | Revive her first. I can wait. | 先救她,我可以等 | 先救她,我可以等她回来 | 先救她,我可以等她回来 |
| authored-016 | 别扶我，先打他。 | Don't help me. Hit him first. | Don't help me. Hit him first. | Don't help me. Hit him first. |
| authored-017 | Finish the downed enemy before he gets revived. | 在他复活之前干掉敌人 | 在他复活之前先干掉被击倒的敌人 | 在他复活之前先干掉被击倒的敌人 |
| authored-018 | 别补他，留着钓他的队友。 | Don't make him up, keep him on his teammate. | Don't make him up, keep him on his teammate. | Don't make him up, keep him on his teammate. |
| authored-019 | I am low on health. Give me a medkit. | 我身体不好,给我一个麦特 | 我身体不好,给我个药 | 我血量很低,给我急救箱 |
| authored-020 | 我满血，你把药留着。 | I'm full of blood, you keep the medicine. | I'm full of blood, you keep the medicine. | My health is full, you keep the medicine. |
| authored-021 | I hear footsteps upstairs, not outside. | 我听到楼上的脚步声,不是外面 | 我听到楼上的脚步声,不是外面 | 我听到楼上的脚步声,不是外面 |
| authored-022 | 左边有脚步，可能不止一个人。 | There's a foot on the left, probably more than one person. | There's a foot on the left, probably more than one person. | There's footsteps on the left, probably more than one person. |
| authored-023 | His armor is broken. Push together. | 他的盔甲坏了 一起推 | 他的盔甲坏了 一起推 | 他的盔甲坏了 一起推 |
| authored-024 | 我没有护甲，等我补甲再打。 | I don't have a armor. I'll hit it when I get it back. | I don't have a armor. I'll hit it when I get it back. | I don't have a armor. I'll hit it when I fix it. |
| authored-025 | Grenade behind you! Move away! | 后面有手榴弹 走开 | 手榴弹在你身后 走开 | 手榴弹在你身后 走开 |
| authored-026 | 我没雷了，你往窗里扔一颗。 | I'm out. You throw one in the window. | I'm out. You throw one in the window. | I'm out. You throw one in the window. |
| authored-027 | Throw smoke between us and the sniper. | 给我们和狙击手之间扔烟雾 | 给我们和狙击手之间扔烟雾 | 给我们和狙击手之间扔烟雾 |
| authored-028 | 先封烟再救人，别直接跑过去。 | Put the smoke away and save people. Don't run straight over there. | Put the smoke away and save people. Don't run straight over there. | Throw smoke shells to cover the horizon before saving people, and don't run straight over. |
| authored-029 | We need to rotate to the next zone now. | 我们现在需要换到下一个区 | 我们现在需要转到下一个区域 | 我们现在需要转到下一个区域 |
| authored-030 | 这里太危险，往右边转移。 | It's too dangerous here to move to the right. | It's too dangerous here to move to the right. | It's too dangerous here to move to the right. |
| authored-031 | He is one shot. One more bullet should knock him. | 他只有一枪,再打一枪就打中他 | 他只有一枪,再打一枪 | 他只有一枪,再打一枪 |
| authored-032 | 他不是残血，别一个人冲。 | He's not blood. Don't rush. | He's not blood. Don't rush. | He's not low on health. Don't rush. |
| authored-033 | You stay here. She and I will flank them. | 你待在这里,她和我会从侧面包围他们 | 你呆在这里,她和我会从侧面掩护他们 | 你呆在这里,她和我会从侧面掩护他们 |
| authored-034 | 不是我打的，是他打的。 | I didn't hit him. He did. | I didn't hit him. He did. | I didn't hit him. He did. |
| authored-035 | Do not shoot. That is our teammate. | 别开枪,那是我们的队友 | 别开枪,那是我们的队友 | 别开枪,那是我们的队友 |
| authored-036 | 我说的是撤退，不是进攻。 | I'm talking about retreating, not attacking. | I'm talking about retreating, not attacking. | I'm talking about retreating, not attacking. |
| authored-037 | Hold the door open for her. | 帮她把门打开 | 把门打开给她 | 把门打开给她 |
| authored-038 | 帮我拿一下这个杯子。 | Hold this cup for me. | Hold this cup for me. | Hold this cup for me. |
| authored-039 | We filmed the scene in one shot. | 我们拍下了一张照片 | 我们拍了片子 | 我们拍了片子 |
| authored-040 | 这张照片只拍了一次。 | This picture was taken only once. | This picture was taken only once. | This picture was taken only once. |
| authored-041 | Please cover the soup so it stays warm. | 请把汤包好 保持暖和 | 请把汤盖好,这样它才能保持温暖 | 请把汤盖好,这样它才能保持温暖 |
| authored-042 | 请把书的封面擦干净。 | Please wipe the cover of the book. | Please wipe the cover of the book. | Please wipe the cover of the book. |
| authored-043 | I need to finish my homework before dinner. | 我要在晚饭前完成我的作业 | 我要在晚饭前完成我的作业 | 我要在晚饭前完成我的作业 |
| authored-044 | 请把椅子转过去。 | Turn the chair around, please. | Turn the chair around, please. | Turn the chair around, please. |
| authored-045 | There is smoke coming from the kitchen. | 厨房里有烟 | 厨房里有烟 | 厨房里有烟 |
| authored-046 | 救我，我不会游泳！ | Help me, I can't swim! | Help me, I can't swim! | Help me, I can't swim! |
| authored-047 | Help me! | 帮帮我! | 帮帮我! | 帮帮我! |
| authored-048 | 有人吗？ | Hello? | Hello? | Hello? |
| authored-049 | Someone is at the door. Do not open it yet. | 有人在门前 还没打开 | 有人在门边 还没打开 | 有人在门边 还没打开 |
| authored-050 | 他敲了三下门，然后走了。 | He knocked three times and left. | He knocked three times and left. | He knocked three times and left. |
| authored-051 | Reload the page if the image does not appear. | 如果图像不出现, 重新装入页面 。 | 如果图像不出现, 则重新装入页面 。 | 如果图像不出现, 则重新装入页面 。 |
| authored-052 | 医生说他的健康状况很好。 | The doctor says he's in good health. | The doctor says he's in good health. | The doctor says he's in good health. |
