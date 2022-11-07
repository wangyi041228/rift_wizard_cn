# Rift Wizard 汉化工程

## 起步

1. 导入 `.py` 以外的游戏文件
2. 将 `steamworks.zip` 解压到 `steamworks` 文件夹
3. 安装 Python 3.8.2
4. `pip install -r requirements.txt`
5. `python RiftWizard.py`

## 注意

* 技能和物品等文本会写进存档，尽量清空存档后再测试。
* 区分词汇：
  * `冲程`=`burst`，`半径`=`radius`，避开`范围`。
  * `咒语`=`spell`，`被动`=`skill`，`法术`=`sorcery`
  * `附近的`=`nearby`，`相邻的`=`adjacent`
  * `毒性`=`poison`，`毒液`=`venom`，`中毒`=`poisoned`
* 尽量不改变类的`name`，减少意外的错误。目前改动了：
  * `ShrineBuff()`。
  * 

## TODO

|模块|文件|进度|备注|
|----|----|----|----|
|主文件|[RiftWizard.py](RiftWizard.py)|99%|润色和修正|
|咒语|[Spells.py](Spells.py)|99%|润色和修正|
|被动|[Upgrades.py](Upgrades.py)|99%|润色和修正|
|游戏|[Game.py](Game.py)|99%|润色和修正|
|物品|[Cunsumables.py](Consumables.py)|99%|润色和修正|
|关卡|[Level.py](Level.py)|99%|润色和修正|
|怪物|[Monsters.py](Monsters.py)| |名称和衍生名称完工|
|变体怪物|[Variant.py](Variants.py)|0%||
|稀有怪物|[RareMonsters.py](RareMonsters.py)| |名称和衍生名称完工|
|通用|[CommonContent.py](CommonContent.py)| |校对|
|神龛|[Shrines.py](Shrines.py)| |校对|
|变体规则|[Mutators.py](Mutators.py)| |校对|
|NPC|[NPCs.py](NPCs.py)|0%||

* 左侧无法升级的用灰色。
* 战败的截图显示正确的可选升级数量。
* 翻译读写的日志文件。

## 考虑

* 拆分字典，这样`Giant Bear`根据单位或咒语拆分成`巨熊`和`召唤巨熊`。
* 统一套色格式。

## DONE

* 改写`draw_wrapped_string`函数，适应中文。
* 自动换行，但不切开ascii码字符，行首无`，、。：,.!`等标点。
* 数字前后的空格问题。（目前在ascii词后都加了空格，方便不完全汉化时游戏，等完全汉化后就没问题）
* 调用`draw_string`前查表替换。
* 角色表中咒语和被动各分三列。
* 左侧咒语分两列。
* 多选一的分支只算一个可选升级。
* 被动全满后升级按钮用灰色。
* 声音文件改为`192kbps`的`.mp3`。
* 缓存通关后的日志文件，防止循环读取文件。118行的日志会让游戏卡顿，只输出41行。（原版漏洞）
* 调整界面函数和参数。

## 说明

* 游戏代码和资源来自7月版本`Rift.Wizard.Build.8752580`。
* `steamworks`库来自网络。
* 后续劳动来自群友。
* 本项目仅供学习，绝不能商用。
