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

## TODO

* 以下文件的翻译
  * [主文件 ????/5000+](RiftWizard.py)
  * [怪物 0/5365](Monsters.py)
  * [稀有怪物 0/3079](RareMonsters.py)
  * [关卡 0/3498](Level.py)
  * [NPCs 0/25](NPCs.py)
* 以下文件的润色、修正
  * [咒语](Spells.py)
  * [被动](Upgrades.py)
  * [通用](CommonContent.py)
  * [神殿](Shrines.py)
  * [变体规则](Mutators.py)
  * [游戏](Game.py)
* 字体、大小和界面等。

## 考虑

* 拆分字典，这样`Giant Bear`根据单位或咒语拆分成`巨熊`和`召唤巨熊`。
* 统一套色格式。

## DONE

* 改写`draw_wrapped_string`函数，适应中文。
* 自动换行，但不切开ascii码字符，行首无`，、。：,.!`等标点。
* 数字前后的空格问题。(目前在ascii词后都加了空格，方便不完全汉化时游戏，等完全汉化后就没问题)
* 调用`draw_string`前查表替换。
* 角色表中咒语和被动各分三列。再多需要写分页面。
* 多选一的分支只算一个可选升级。（原版漏洞）
* 左侧无法升级的用灰色。（原版不足，没做完）
* 被动全满后升级按钮用灰色。
* 声音文件改为`192kbps`的`.mp3`。
* 缓存通关后的日志文件，防止循环读取文件。118行的日志会让游戏卡顿，只输出41行。（原版漏洞）
* 调整一些界面函数和参数。
* 咒语、被动和物品的名称翻译。
* 物品描述的翻译。

## 说明

* 游戏代码和资源来自7月版本`Rift.Wizard.Build.8752580`。
* `steamworks`库来自网络。
* 后续劳动来自群友。
* 本项目仅供学习，绝不能商用。
