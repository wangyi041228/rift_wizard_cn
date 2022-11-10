Rift Wizard 汉化版
## 项目说明
* [Rift Wizard](https://store.steampowered.com/app/1271280) 是一款侧重施法战斗和角色培养的高难度复古类 Rogue 游戏。
* [SteamDB](https://steamdb.info/app/1271280) 显示：国区定价 50 元，史低 32.5 元，游戏整体特别好评，好评 718，差评 43。
* 作者已停止更新 RW，全力投入 RW2 的开发。
* 作者允许中文社区自行分发 RW 汉化版，希望喜欢游戏的玩家在 Steam 上购买一份支持作者。（增开测试频道及后续维护会占用作者精力）
* 项目基于2022年7月的客户端 `Rift.Wizard.Build.8752580` 进行开发。
* 本项目仅供游戏玩家学习交流，切勿商用。
* [Rift Wizard 官方 Discord](https://discord.gg/NngFZ7B)
* [类肉鸽粉丝QQ群](https://jq.qq.com/?_wv=1027&k=C1ejcsdb) `144321649`
## 快速启动
1. 准备资源文件夹 `rl_data`，将 `.wav` 文件转为 `.mp3`。
2. 准备仓库中的所有脚本文件。
3. 配置环境：`pip install -r requirements.txt`（Python和库版本不重要）
4. 开始游戏：`python RiftWizard.py`
## 汉化说明
* 建议将桌面分辨率调整为 900P 或 1080P。
* 图鉴文件 `stats.dat` 和选项文件 `options2` 可跨版本混用。
* 游戏数据写进存档 `/saves/*/game.dat`，切勿跨版本混用，以免发生严重错误。
* 易混词汇：
  * `冲程`=`burst`，`半径`=`radius`，避开`范围`。
  * `咒语`=`spell`，`被动`=`skill`，`法术`=`sorcery`
  * `附近的`=`nearby`，`相邻的`=`adjacent`
  * `毒性`=`poison`，`毒液`=`venom`，`中毒`=`poisoned`
* 绝不改变入图鉴的单位、玩家咒语和玩家被动的 `name`，可直接改动神龛和增益的 `name`。已改 `～～骷髅`的 `name`。
## 待办事项
* 鼠标悬浮在左侧技能时，右侧窗口无法升级的用灰色，额外显示神龛强化。
* 战败截图显示正确的可选升级数量。
* 拆分词典，得以能将同一英文单词映射成不同的中文词汇。
* 调整字体大小、文本位置和界面布局。
* 调查 118 行中文日志让游戏卡顿的问题，暂时只输出41行缓解。
* 调查汉化版新增的卡顿和性能问题。
* 进一步优化原版和汉化版。

|模块|文件|没翻译完|都需修正和润色|
|----|----|----|----|
|主文件|[RiftWizard.py](RiftWizard.py)| | |
|咒语|[Spells.py](Spells.py)| | |
|被动|[Upgrades.py](Upgrades.py)| | |
|游戏|[Game.py](Game.py)| | |
|物品|[Cunsumables.py](Consumables.py)| | |
|关卡|[Level.py](Level.py)| | |
|怪物|[Monsters.py](Monsters.py)| | |
|变体怪物|[Variant.py](Variants.py)|是| |
|稀有怪物|[RareMonsters.py](RareMonsters.py)|是| |
|通用|[CommonContent.py](CommonContent.py)| | |
|神龛|[Shrines.py](Shrines.py)| | |
|变体规则|[Mutators.py](Mutators.py)| | |
|NPC|[NPCs.py](NPCs.py)|是| |
## 已经完成
* 改写 `draw_wrapped_string` 函数。
  * 自动换行，不切开 ascii 码单词，行首无标点。
  * 中英混排加空格。
* 调用 `draw_string` 前查表替换。
* 角色界面中，咒语和被动各分三列。
* 左侧界面中，咒语和物品分两列。
* 多选一的分支只算一个可选升级。
* 被动全满后学习被动按钮用灰色。
* 声音文件改为 `192kbps` 的 `.mp3`。
* 缓存部分日志，防止循环读取。
* 调整部分界面函数和参数。
* 改进作弊模式：显示状态，可开可关，调整键位。