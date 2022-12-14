from Level import *
from Monsters import *
from copy import copy
import math
import itertools
import text

class FlameTongue(Spell):

	def on_init(self):
		self.name = "Flame Tongue"
		self.level = 1
		self.damage = 6
		self.max_charges = 28
		self.range = 5

		self.tags = [Tags.Fire, Tags.Sorcery]

		self.description = "在一束范围内造成 [fire] 伤害。"

		self.upgrades['range'] = (3, 1)
		self.upgrades['damage'] = (5, 1)

	def get_impacted_tiles(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in Bolt(self.caster.level, start, target):
			yield point

	def cast(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in self.get_impacted_tiles(x, y):
			self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Fire, self)

		yield


class FireballSpell(Spell):

	def on_init(self):
		self.radius = 2
		self.damage = 9
		self.name = "Fireball"
		self.max_charges = 18
		self.range = 8
		self.element = Tags.Fire

		self.damage_type = Tags.Fire

		self.whiteflame_bonus = 0
		self.blueflame_bonus = 0

		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 1

		self.upgrades['radius'] = (1, 3)
		self.upgrades['damage'] = (8, 2)
		self.upgrades['max_charges'] = (8, 2)
		self.upgrades['range'] = (3, 1)

		self.upgrades['chaos'] = (1, 3, "Chaos Ball", "火球术随机造成 [physical]、[lightning] 或 [fire] 伤害。若单位对一种或多种伤害类型有抗性，火球术造成其抗性最低类型的伤害。", "damage type")
		self.upgrades['energy'] = (1, 4, "Energy Ball", "火球术随机造成 [arcane]、[holy] 或 [fire] 伤害。若单位对一种或多种伤害类型有抗性，火球术造成其抗性最低类型的伤害。", "damage type")
		self.upgrades['ash'] = (1, 5, "Ash Ball", "火球术随机造成 [poison]、[dark] 或 [fire] 伤害。若单位对一种或多种伤害类型有抗性，火球术造成其抗性最低类型的伤害。\n火球术致盲一回合。", "damage type")

	def get_description(self):
		return "对 [{radius}_格:radius] 冲程内的所有单位造成 [{damage}:damage] 点 [fire] 伤害。".format(**self.fmt_dict())

	def cast(self, x, y):
		target = Point(x, y)

		dtypes = [Tags.Fire]
		if self.get_stat('chaos'):
			dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
		elif self.get_stat('energy'):
			dtypes = [Tags.Fire, Tags.Arcane, Tags.Holy]
		elif self.get_stat('ash'):
			dtypes = [Tags.Fire, Tags.Dark, Tags.Poison]

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				damage = self.get_stat('damage')
				random.shuffle(dtypes)
				unit = self.caster.level.get_unit_at(point.x, point.y)
				if unit:
					dtype = min(((unit.resists[t], t) for t in dtypes), key=lambda t : t[0])[1]
				else:
					dtype = random.choice(dtypes)

				self.caster.level.deal_damage(point.x, point.y, damage, dtype, self)

				if self.get_stat('ash') and unit:
					unit.apply_buff(BlindBuff(), 1)
			yield

		return

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class MeteorShower(Spell):

	def on_init(self):
		self.name = "Meteor Shower"

		self.damage = 23
		self.num_targets = 7
		self.storm_radius = 7
		self.stats.append('storm_radius')
		self.radius = 2
		self.range = RANGE_GLOBAL
		self.requires_los = False
		self.stun_duration = 2

		self.max_charges = 1

		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 7

		self.max_channel = 5

		self.upgrades['num_targets'] = (3, 4)
		self.upgrades['stun_duration'] = (3, 2)
		self.upgrades['rock_size'] = (1, 2, "Meteor Size", "物理伤害和击晕范围从 0 提升至 1。")
		self.upgrades['max_channel'] = (5, 2)

	def get_description(self):
		return (
			"每回合在 [{storm_radius}_格:radius] 半径内随机地块上降下 [{num_targets}_个陨石:num_targets]。\n"
			"陨石造成 [{damage}_点物理:physical] 伤害，摧毁墙，施加击晕 [{stun_duration}_回合:duration]。\n"
			"陨石还在 [{radius}_格:radius] 半径内造成 [{damage}_点火焰:fire] 伤害。\n"
			"此咒语可引导至多 [{max_channel}_回合:duration]。引导时每回合重复此效果。").format(
			**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_ball(x, y, self.get_stat('storm_radius') + self.get_stat('radius'))

	def cast(self, x, y, channel_cast=False):

		if not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		points_in_ball = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('storm_radius')))

		for _ in range(self.get_stat('num_targets')):
			target = random.choice(points_in_ball)

			for stage in Burst(self.caster.level, target, self.get_stat('rock_size'), ignore_walls=True):
				for point in stage:
					self.caster.level.make_floor(point.x, point.y)
					self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Physical, self)
					unit = self.caster.level.get_unit_at(point.x, point.y)
					if unit:
						unit.apply_buff(Stun(), self.get_stat('stun_duration'))
				yield

			self.caster.level.show_effect(0, 0, Tags.Sound_Effect, 'hit_enemy')
			yield

			for stage in Burst(self.caster.level, target, self.get_stat('radius')):
				for point in stage:
					damage = self.get_stat('damage')
					self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)
				yield
			yield


class LightningBoltSpell(Spell):

	def on_init(self):
		self.damage = 12
		self.range = 10
		self.name = "Lightning Bolt"
		self.max_charges = 18
		self.element = Tags.Lightning

		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 1

		self.upgrades['damage'] = (9, 3)
		self.upgrades['range'] = (5, 2)
		self.upgrades['max_charges'] = (12, 2)
		self.upgrades['channel'] = (1, 3, "Channeling", "闪电箭可引导至多 10 个回合。")

		self.upgrades['judgement'] = (1, 6, "Judgement Bolt", "闪电箭还造成 [holy] 和 [dark] 伤害。", "bolt")
		self.upgrades['energy'] = (1, 6, "Energy Bolt", "闪电箭还造成 [fire] 和 [arcane] 伤害。", "bolt")

	def get_description(self):
		return "在一束范围内造成 [{damage}_点闪电:lightning] 伤害。".format(**self.fmt_dict())

	def cast(self, x, y, channel_cast=False):

		if self.get_stat('channel') and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), 10)
			return

		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		dtypes = [Tags.Lightning]

		if self.get_stat('judgement'):
			dtypes = [Tags.Lightning, Tags.Holy, Tags.Dark]
		if self.get_stat('energy'):
			dtypes = [Tags.Lightning, Tags.Fire, Tags.Arcane]

		for dtype in dtypes:
			for point in Bolt(self.caster.level, start, target):
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)

			for i in range(4):
				yield

	def get_impacted_tiles(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)
		return list(Bolt(self.caster.level, start, target))

class AnnihilateSpell(Spell):

	def on_init(self):
		self.range = 6
		self.name = "Annihilate"
		self.max_charges = 8
		self.damage = 16
		self.tags = [Tags.Chaos, Tags.Sorcery]
		self.level = 2
		self.cascade_range = 0  # Should be cascade range
		self.arcane = 0
		self.dark = 0

		self.upgrades['cascade_range'] = (4, 3, 'Cascade', '若主目标被消灭，歼灭术会跳跃并击中其附近的目标。')
		self.upgrades['dark'] = (1, 1, 'Dark Annihilation', '歼灭术额外造成一次 [dark] 伤害。')
		self.upgrades['arcane'] = (1, 1, 'Arcane Annihilation', '歼灭术额外造成一次 [arcane] 伤害。')
		self.upgrades['max_charges'] = (4, 2)

		self.can_target_empty = False

	def get_description(self):
		desc = "对目标造成 [{damage}_点火焰:fire] 伤害、[{damage}_点闪电:lightning] 伤害和 [{damage}_点物理:physical] 伤害。"
		return desc.format(**self.fmt_dict())

	def cast(self, x, y):

		cur_target = Point(x, y)
		dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
		if self.get_stat('arcane'):
			dtypes.append(Tags.Arcane)
		if self.get_stat('dark'):
			dtypes.append(Tags.Dark)
		for dtype in dtypes:
			if self.get_stat('cascade_range') and not self.caster.level.get_unit_at(cur_target.x, cur_target.y):
				other_targets = self.caster.level.get_units_in_ball(cur_target, self.get_stat('cascade_range'))
				other_targets = [t for t in other_targets if self.caster.level.are_hostile(t, self.caster)]
				if other_targets:
					cur_target = random.choice(other_targets)

			self.caster.level.deal_damage(cur_target.x, cur_target.y, self.get_stat('damage'), dtype, self)
			for i in range(9):
				yield

class MegaAnnihilateSpell(AnnihilateSpell):

	def on_init(self):
		self.damage = 99
		self.max_charges = 3
		self.name = "Mega Annihilate"

		self.tags = [Tags.Chaos, Tags.Sorcery]
		self.level = 5

		self.cascade_range = 0
		self.arcane = 0
		self.dark = 0

		self.upgrades['cascade_range'] = (4, 3, 'Cascade', '若主目标被消灭，歼灭术会跳跃并击中其附近的目标。')
		self.upgrades['dark'] = (1, 2, 'Dark Annihilation', '歼灭术额外造成一次 [dark] 伤害。')
		self.upgrades['arcane'] = (1, 2, 'Arcane Annihilation', '歼灭术额外造成一次 [arcane] 伤害。')
		self.upgrades['damage'] = (99, 4)

class Teleport(Spell):

	def on_init(self):
		self.range = 15
		self.requires_los = False
		self.name = "Teleport"
		self.max_charges = 1

		self.tags = [Tags.Sorcery, Tags.Arcane, Tags.Translocation]
		self.level = 5

		self.upgrades['max_charges'] = (2, 3)
		self.upgrades['range'] = (8, 2)
		self.upgrades['void_teleport'] = (1, 5, "Void Teleport", "传送术对目标地块视线内的所有敌方单位造成 [arcane] 伤害，数量为充能上限。")

	def get_description(self):
		return "传送到目标地块。"

	def can_cast(self, x, y):
		return Spell.can_cast(self, x, y) and self.caster.level.can_move(self.caster, x, y, teleport=True)

	def cast(self, x, y):
		start_loc = Point(self.caster.x, self.caster.y)

		self.caster.level.show_effect(self.caster.x, self.caster.y, Tags.Translocation)
		p = self.caster.level.get_summon_point(x, y)
		if p:
			yield self.caster.level.act_move(self.caster, p.x, p.y, teleport=True)
			self.caster.level.show_effect(self.caster.x, self.caster.y, Tags.Translocation)

		if self.get_stat('void_teleport'):
			for unit in self.owner.level.get_units_in_los(self.caster):
				if are_hostile(self.owner, unit):
					unit.deal_damage(self.get_stat('max_charges'), Tags.Arcane, self)

		if self.get_stat('lightning_blink') or self.get_stat('dark_blink'):
			dtype = Tags.Lightning if self.get_stat('lightning_blink') else Tags.Dark
			damage = math.ceil(2*distance(start_loc, Point(x, y)))
			for stage in Burst(self.caster.level, Point(x, y), 3):
				for point in stage:
					if point == Point(x, y):
						continue
					self.caster.level.deal_damage(point.x, point.y, damage, dtype, self)


class BlinkSpell(Teleport):

	def on_init(self):
		self.range = 5
		self.requires_los = True
		self.name = "Blink"
		self.max_charges = 6
		self.tags = [Tags.Arcane, Tags.Sorcery, Tags.Translocation]
		self.level = 3

		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "扑闪术施放无需视线。")
		self.upgrades['range'] = (3, 3)
		self.upgrades['max_charges'] = (5, 2)
		self.upgrades['lightning_blink'] = (1, 4, "Lightning Blink", "扑闪术在抵达时对 3_格 范围内造成 [lightning] 伤害，数量为移动距离的两倍，上整。", 'damage')
		self.upgrades['dark_blink'] = (1, 4, "Dark Blink", "扑闪术在抵达时对 3_格 范围内造成 [dark] 伤害，数量为移动距离的两倍，上整。", 'damage')

		#del(self.upgrades['void_teleport'])
class FlameGateBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Flame Gate"
		self.spell = spell
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'flame_gate']
		self.cast = True
		self.description = "每当你施放火焰咒语时，临时在目标旁召唤一个火元素。\n\n你移动或施放非火焰咒语时，此附魔结束。"

	def on_applied(self, owner):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.owner_triggers[EventOnPass] = self.on_pass
		self.color = Color(255, 0, 0)

	def on_advance(self):
		if self.cast == False:
			self.owner.remove_buff(self)
		self.cast = False

	def on_spell_cast(self, spell_cast_event):
		if Tags.Fire in spell_cast_event.spell.tags:
			self.owner.level.queue_spell(self.make_elemental(spell_cast_event))
			self.cast = True

	def on_pass(self, evt):
		if self.owner.has_buff(ChannelBuff):
			self.cast = True

	def make_elemental(self, spell_cast_event):
		if Tags.Fire in spell_cast_event.spell.tags:
			elemental = Unit()
			elemental.name = 'Fire Elemental'
			elemental.sprite.char = 'E'
			elemental.sprite.color = Color(255, 0, 0)
			elemental.spells.append(SimpleRangedAttack("Elemental Fire", self.spell.get_stat('minion_damage'), Tags.Fire, self.spell.get_stat('minion_range')))
			elemental.resists[Tags.Fire] = 100
			elemental.resists[Tags.Physical] = 50
			elemental.resists[Tags.Ice] = -100
			elemental.turns_to_death = self.spell.get_stat('minion_duration')
			elemental.max_hp = self.spell.get_stat('minion_health')
			elemental.team = self.owner.team
			elemental.tags = [Tags.Elemental, Tags.Fire]
			self.spell.summon(elemental, target=spell_cast_event)
		yield

class FlameGateSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Flame Gate"
		self.minion_duration = 9
		self.tags = [Tags.Fire, Tags.Enchantment, Tags.Conjuration]
		self.level = 3

		self.minion_damage = 7
		self.minion_health = 22
		self.minion_range = 4

		self.upgrades['minion_range'] = (2, 2)
		self.upgrades['minion_duration'] = (7, 2)
		self.upgrades['minion_damage'] = (7, 4)

	def cast(self, x, y):
		self.caster.apply_buff(FlameGateBuff(self), 0)
		yield

	def get_description(self):
		return ("每当你施放 [fire] 咒语时，在咒语目标处召唤一个火元素。\n"
				"火元素有 [{minion_health}_点生命:minion_health]、[100_点火焰:fire] 抗性、[50_点物理:physical] 抗性和 [-50_点寒冰:ice] 抗性。\n"
				"火元素的攻击造成 [{minion_damage}_点火焰:fire] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"火元素在 [{minion_duration}_回合:minion_duration] 后消失。\n"
				"此效果持续到你不施放火焰咒语为止。").format(**self.fmt_dict())

class LightningFormBuff(Buff):

	def __init__(self, phys_immune = False):
		Buff.__init__(self)
		self.transform_asset_name = "player_lightning_form"
		self.phys_immune = phys_immune
		self.name = "Lightning Form"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'lightning_form']
		self.color = Tags.Lightning.color
		self.description = "每当你施放闪电咒语时，若目标地块为空，传送到目标地块。\n\n你移动或施放非闪电咒语时，此附魔结束。"
		self.cast = True
		self.stack_type = STACK_TYPE_TRANSFORM

	def on_advance(self):
		if self.cast == False:
			self.owner.remove_buff(self)
		self.cast = False

	def on_applied(self, caster):
		self.resists[Tags.Lightning] = 100
		self.resists[Tags.Physical] = 100

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.owner_triggers[EventOnPass] = self.on_pass
		self.color = Color(122, 122, 200)

	def on_spell_cast(self, spell_cast_event):
		if Tags.Lightning in spell_cast_event.spell.tags:
			self.cast = True
			if self.owner.level.can_move(self.owner, spell_cast_event.x, spell_cast_event.y, teleport=True):
				self.owner.level.queue_spell(self.do_teleport(spell_cast_event.x, spell_cast_event.y))

	def on_pass(self, evt):
		if self.owner.has_buff(ChannelBuff):
			self.cast = True

	def do_teleport(self, x, y):
		if self.owner.level.can_move(self.owner, x, y, teleport=True):
			yield self.owner.level.act_move(self.owner, x, y, teleport=True)

class LightningFormSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 3
		self.name = "Lightning Form"
		self.physical_resistance = 0

		self.tags = [Tags.Lightning, Tags.Enchantment]
		self.level = 4

		self.upgrades['max_charges'] = (3, 2)

	def cast(self, x, y):
		self.caster.apply_buff(LightningFormBuff())
		yield

	def get_description(self):
		return ("每当你施放 [lightning] 咒语时，传送到该咒语的目标地块。\n"
				"获得 [100_点闪电:lightning] 抗性。\n"
				"获得 [100_点物理:physical] 抗性。\n"
				"此效果持续到你不施放 [lightning] 咒语的首个回合为止。").format(**self.fmt_dict())

class VoidBeamSpell(Spell):

	def on_init(self):
		self.range = 15
		self.max_charges = 7
		self.name = "Void Beam"
		self.requires_los = False
		self.damage = 25

		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.level = 3

		self.element = Tags.Arcane

		self.upgrades['damage'] = (21, 5)
		self.upgrades['range'] = (5, 2)
		self.upgrades['max_charges'] = (3, 2)

	def aoe(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)
		path = Bolt(self.caster.level, start, target, two_pass=False, find_clear=False)
		for point in path:
			yield point

	def cast(self, x, y):
		damage = self.get_stat('damage')
		for point in self.aoe(x, y):

			# Kill walls
			if not self.caster.level.tiles[point.x][point.y].can_see:
				self.caster.level.make_floor(point.x, point.y)

			cur_tile = self.caster.level.tiles[point.x][point.y]

			# Kill clouds
			if cur_tile.cloud:
				cur_tile.cloud.kill()

			# Deal damage
			self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
		yield

	def get_impacted_tiles(self, x, y):
		return list(self.aoe(x, y))

	def get_description(self):
		return "在一束范围内造成 [{damage}_点奥术:arcane] 伤害，并摧毁墙。".format(**self.fmt_dict())

class ThunderStrike(Spell):

	def on_init(self):
		self.range = 10
		self.max_charges = 9
		self.name = "Thunder Strike"
		self.damage = 24
		self.damage_type = Tags.Lightning
		self.radius = 2
		self.duration = 3

		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 2

		self.storm_power = 0
		self.upgrades['duration'] = (3, 2)
		self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "雷击术施放无需视线。")
		self.upgrades['damage'] = (36, 4)
		self.upgrades['storm_power'] = (1, 2, "Storm Power", "若目标在风暴云中，范围和击晕持续翻倍。")
		self.upgrades['heaven_strike'] = (1, 4, "Heaven Strike", "雷击术还造成 [holy] 伤害。")

	def get_description(self):
		return ("对目标造成 [{damage}_点闪电:lightning] 伤害。\n"
				"击晕目标周围 [{radius}_格:radius] 冲程内的所有敌人。").format(**self.fmt_dict())

	def cast(self, x, y):

		in_cloud = isinstance(self.caster.level.tiles[x][y].cloud, StormCloud)
		duration = self.get_stat('duration')
		radius = self.get_stat('radius')
		if in_cloud and self.get_stat('storm_power'):
			duration = self.get_stat('duration') * 2
			radius = radius * 2

		self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.damage_type, self)
		yield

		if self.get_stat('heaven_strike'):
			for i in range(3):
				yield

			self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Holy, self)

		for stage in Burst(self.caster.level, Point(x, y), radius):
			for point in stage:

				self.caster.level.flash(point.x, point.y, Tags.Physical.color)
				cur_target = self.caster.level.get_unit_at(point.x, point.y)
				if cur_target and self.caster.level.are_hostile(cur_target, self.caster):
					cur_target.apply_buff(Stun(), self.get_stat('duration'))
			yield

	def get_impacted_tiles(self, x, y):
		radius = self.get_stat('radius')
		if self.get_stat('storm_power') and isinstance(self.caster.level.tiles[x][y].cloud, StormCloud):
			radius = radius * 2

		return [p for stage in Burst(self.caster.level, Point(x, y), radius) for p in stage]

class GiantStrengthBuff(Buff):

	def on_applied(self, owner):
		hurl_boulder = SimpleRangedAttack(name="Hurl Boulder", damage=self.damage, range=6, damage_type=Tags.Physical)
		hurl_boulder.max_charges = 50
		self.spells = [hurl_boulder]
		self.resists[Tags.Physical] = 50
		self.color = Tags.Enchantment.color
		self.name = "Giant Strength"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'giant_form']

class GiantStrengthSpell(Spell):

	def on_init(self):
		self.name = "Stone Giant Form"
		self.duration = 15
		self.max_charges = 9
		self.damage = 25
		self.range = 0

		self.tags = [Tags.Nature, Tags.Enchantment]
		self.level = 2

		self.upgrades['damage'] = (15, 2)
		self.upgrades['duration'] = (15, 1)

	def get_description(self):
		return "临时获得物理抗性和投掷巨石的能力。"

	def cast(self, x, y):
		buff = GiantStrengthBuff()
		buff.damage = self.get_stat('damage')
		self.caster.apply_buff(buff, self.get_stat('duration'))
		yield

class ChaosBarrage(Spell):

	def on_init(self):
		self.name = "Chaos Barrage"
		self.range = 7
		self.damage = 9
		self.num_targets = 8
		self.angle = math.pi / 6
		self.max_charges = 8
		self.tags = [Tags.Chaos, Tags.Sorcery]
		self.can_target_self = False

		self.level = 2

		self.upgrades['max_charges'] = (4, 1)
		self.upgrades['damage'] = (4, 5)
		self.upgrades['num_targets'] = (5, 4, "Extra Bolts")

	def get_description(self):
		return ("在锥形范围内发射随机向单位发射有混沌能量的 [{num_targets}_支箭矢:num_targets]。\n"
				"每支箭矢随机造成 [{damage}_点火焰:fire]、[{damage}_点闪电:lightning] 或 [{damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

	def get_cone_burst(self, x, y):
		# TODO- this is very generous and frequently goes through walls, fix that
		target = Point(x, y)
		burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
		return [p for stage in burst for p in stage if self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y)]

	def cast(self, x, y):
		possible_targets = [self.caster.level.get_unit_at(p.x, p.y) for p in self.get_cone_burst(x, y)]
		possible_targets = [t for t in possible_targets if t and t != self.caster]

		for i in range(self.get_stat('num_targets')):

			possible_targets = [t for t in possible_targets if t.is_alive()]
			if not possible_targets:
				continue

			cur_enemy = random.choice(possible_targets)
			cur_element = random.choice([Tags.Fire, Tags.Lightning, Tags.Physical])

			start = Point(self.caster.x, self.caster.y)
			target = Point(cur_enemy.x, cur_enemy.y)
			path = Bolt(self.caster.level, start, target)
			for p in path:
				self.caster.level.deal_damage(p.x, p.y, 0, cur_element, self)
				yield

			self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), cur_element, self)

	def get_impacted_tiles(self, x, y):
		return self.get_cone_burst(x, y)

class InfernoCloud(Cloud):

	def __init__(self, owner, damage):
		Cloud.__init__(self)
		self.damage = damage
		self.owner = owner
		self.color = Color(180, 0, 0)
		self.spread_chance = .7
		self.duration = 5
		self.name = "Inferno"
		self.description = "一朵飘动的火云。每回合对捕捉的单位造成 %d 点伤害。"

	def on_advance(self):

		# Deal damage to units in the fire
		if self.level.get_unit_at(self.x, self.y):
			self.owner.level.deal_damage(self.x, self.y, self.get_stat('damage'), Tags.Fire, self)

		if random.random() < self.spread_chance:
			expansion_points = self.owner.level.get_adjacent_points(Point(self.x, self.y))

			expansion_points = [p for p in expansion_points if self.owner.level.can_walk(p.x, p.y)]

			point = random.choice(expansion_points)
			if not self.level.tiles[point.x][point.y].cloud:
				self.owner.level.add_obj(InfernoCloud(self.owner, self.get_stat('damage')), point.x, point.y)

class InfernoSpell(Spell):

	def on_init(self):
		self.range = 3
		self.max_charges = 1
		self.name = "Inferno"
		self.tags = [Tags.Fire]
		self.damage = 10

		self.level = 5

		self.requires_los = False
		self.range = 7

		self.upgrades['range'] = (5, 1)
		self.upgrades['max_charges'] = (2, 1)

	def get_description(self):
		return "生成一朵飘动的地狱火云，每回合对其中的所有单位造成伤害。"

	def cast(self, x, y):
		self.caster.level.add_obj(InfernoCloud(self.caster, self.get_stat('damage')), x, y)
		yield

class DispersalSpell(Spell):

	def on_init(self):
		self.range = 6
		self.max_charges = 15
		self.name = "Disperse"
		self.tags = [Tags.Arcane, Tags.Sorcery, Tags.Translocation]
		self.can_target_self = False
		self.radius = 3
		self.level = 2

		self.upgrades['radius'] = (2, 2)
		self.upgrades['max_charges'] = (10, 2)

	def get_description(self):
		return ("将 [{radius}_格:radius] 半径内的所有单位随机传送到新的地块。\n"
				"施法者不受影响。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))

	def cast(self, x, y):
		for p in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius')):
			target = self.caster.level.get_unit_at(p.x, p.y)

			if target == self.caster:
				continue

			possible_points = []
			for i in range(len(self.caster.level.tiles)):
				for j in range(len(self.caster.level.tiles[i])):
					if self.caster.level.can_stand(i, j, target):
						possible_points.append(Point(i, j))

			if not possible_points:
				return

			target_point = random.choice(possible_points)

			self.caster.level.show_effect(target.x, target.y, Tags.Translocation)
			yield
			self.caster.level.act_move(target, target_point.x, target_point.y, teleport=True)
			yield
			self.caster.level.show_effect(target.x, target.y, Tags.Translocation)

class PetrifySpell(Spell):

	def on_init(self):
		self.range = 8
		self.max_charges = 10
		self.name = "Petrify"

		self.duration = 10

		self.upgrades['max_charges'] = (5, 1)
		self.upgrades['glassify'] = (1, 3, 'Glassify', '改为将目标变为玻璃，而非石头。被璃化的目标 -100 物理抗性。')

		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.level = 2

	def cast(self, x, y):

		target = self.caster.level.get_unit_at(x, y)
		if not target:
			return

		self.caster.level.deal_damage(x, y, 0, Tags.Physical, self)
		buff = PetrifyBuff() if not self.get_stat('glassify') else GlassPetrifyBuff()
		target.apply_buff(buff, self.get_stat('duration'))
		yield

	def get_description(self):
		desc = "对目标施加 [petrify] ，持续 [{duration}_回合:duration]。\n"
		desc += text.petrify_desc
		return desc.format(**self.fmt_dict())

class StoneAuraBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Petrification Aura"
		self.description = "每回合石化附近的敌人。"

	def on_advance(self):
		BuffClass = GlassPetrifyBuff if self.spell.get_stat('glassify') else PetrifyBuff
		units = [u for u in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius'))]
		random.shuffle(units)
		stoned = 0
		for u in units:
			if not are_hostile(self.owner, u):
				continue
			if u.has_buff(BuffClass):
				continue
			u.apply_buff(BuffClass(), self.spell.get_stat('petrify_duration'))
			stoned += 1

			if stoned >= self.spell.get_stat('num_targets'):
				break


class StoneAuraSpell(Spell):

	def on_init(self):
		self.range = 0
		self.name = "Petrification Aura"
		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.level = 4

		self.max_charges = 3
		self.num_targets = 3

		self.duration = 7

		self.petrify_duration = 2
		self.radius = 7

		self.upgrades['petrify_duration'] = (2, 3)
		self.upgrades['num_targets'] = (2, 2)
		self.upgrades['duration'] = (15, 2)
		self.upgrades['glassify'] = (1, 6, "Glassify", "改为将敌人变为玻璃，而非石头，使其受到双倍的物理伤害，而非四分之一。")

	def get_description(self):
		return ("每回合在 [{radius}_格:radius] 半径内 [petrify] 至多 [{num_targets}:num_targets] 个未石化的敌方单位。\n" +
				text.petrify_desc + '\n'
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(StoneAuraBuff(self), self.get_stat('duration'))

class SummonWolfSpell(Spell):

	def on_init(self):
		self.max_charges = 12
		self.name = "Wolf"
		self.minion_health = 11
		self.minion_damage = 5
		self.upgrades['leap_range'] = (4, 3, "Pounce", "召唤的狼可进行跳跃攻击。")
		self.upgrades['minion_damage'] = 4
		self.upgrades['minion_health'] = (12, 3)

		self.upgrades['blood_hound'] = (1, 3, "Blood Hound", "改为召唤鲜血猎犬，而非狼。", "hound")
		self.upgrades['ice_hound'] = (1, 3, "Ice Hound", "改为召唤寒冰猎犬，而非狼。", "hound")
		self.upgrades['clay_hound'] = (1, 6, "Clay Hound", "改为召唤粘土猎犬，而非狼。", "hound")
		self.upgrades['wolf_pack'] = (1, 8, "Wolf Pack", "每次施放召狼术消耗 2 点充能并召唤 4 个狼。")


		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 1

		self.must_target_walkable = True
		self.must_target_empty = True

	def make_wolf(self):
		wolf = Unit()
		wolf.max_hp = self.get_stat('minion_health')

		wolf.sprite.char = 'w'
		wolf.sprite.color = Color(102, 77, 51)
		wolf.name = "Wolf"
		wolf.description = "A medium sized beast"
		wolf.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
		wolf.tags = [Tags.Living, Tags.Nature]

		if self.get_stat('leap_range'):
			wolf.spells.append(LeapAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Physical, range=self.get_stat('leap_range')))

		if self.get_stat('blood_hound'):
			wolf.name = "Blood Hound"
			wolf.asset_name = "blood_wolf"

			wolf.spells[0].onhit = bloodrage(2)
			wolf.spells[0].name = "Frenzy Bite"
			wolf.spells[0].description = "每次攻击获得 +2 伤害，持续 10 回合。"

			wolf.tags = [Tags.Demon, Tags.Nature]
			wolf.resists[Tags.Dark] = 75

		elif self.get_stat('ice_hound'):
			for s in wolf.spells:
				s.damage_type = Tags.Ice
			wolf.resists[Tags.Ice] = 100
			wolf.resists[Tags.Fire] = -50
			wolf.resists[Tags.Dark] = 50
			wolf.name = "Ice Hound"
			wolf.tags = [Tags.Demon, Tags.Ice]
			wolf.buffs.append(Thorns(4, Tags.Ice))

		elif self.get_stat('clay_hound'):
			wolf.name = "Clay Hound"
			wolf.asset_name = "earth_hound"

			wolf.resists[Tags.Physical] = 50
			wolf.resists[Tags.Fire] = 50
			wolf.resists[Tags.Lightning] = 50
			wolf.buffs.append(RegenBuff(3))


		wolf.team = self.caster.team

		return wolf

	def cast(self, x, y):
		num_wolves = 1
		if self.get_stat('wolf_pack'):
			num_wolves = 4
			self.cur_charges -= 1
			self.cur_charges = max(self.cur_charges, 0)
		for i in range(num_wolves):
			wolf = self.make_wolf()
			self.summon(wolf, Point(x, y))
			yield

	def get_description(self):
		return ("召唤一个狼。\n"
				"狼具有 [{minion_health}_点生命:minion_health]。\n"
				"狼的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

class SummonDireWolfSpell(Spell):

	def on_init(self):
		self.max_charges = 6
		self.name = "Dire Wolf"
		self.minion_health = 20
		self.minion_damage = 16
		self.leap_range = 0
		self.upgrades['leap_range'] = (3, 4)
		self.upgrades['minion_health'] = (15, 3)
		self.upgrades['minion_damage'] = (8, 1)

		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 2

		self.must_target_walkable = True

	def cast(self, x, y):

		wolf = Unit()
		wolf.max_hp = self.get_stat('minion_health')

		wolf.sprite.char = 'w'
		wolf.sprite.color = Color(202, 77, 51)
		wolf.name = "Dire Wolf"
		wolf.description = "大型野兽。"
		wolf.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))

		if self.get_stat('leap_range'):
			wolf.spells.append(LeapAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Physical, range=self.get_stat('leap_range')))

		wolf.team = self.caster.team

		wolf.tags = [Tags.Living, Tags.Nature]
		self.summon(wolf, Point(x, y))
		yield

	def get_description(self):
		return "召唤一个恐龙。"

class SummonGiantBear(Spell):

	def on_init(self):
		self.max_charges = 3
		self.name = "Giant Bear"
		self.minion_health = 65
		self.minion_damage = 10

		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 3

		self.minion_attacks = 1
		self.upgrades['minion_health'] = (30, 2)
		self.upgrades['minion_damage'] = (15, 4)
		self.upgrades['max_charges'] = (2, 3)
		self.upgrades['minion_attacks'] = (1, 3)
		self.upgrades['armored'] = (1, 3, "Armored Bear", "召唤一个装甲巨熊，而非巨熊。装甲巨熊有提升的物理抗性和 HP，但易受闪电伤害。", "species")
		self.upgrades['venom'] = (1, 4, "Venom Bear", "召唤一个毒液巨熊，而非巨熊。毒液巨熊的撕咬带毒，每当敌人受到毒性伤害时会治疗。", "species")
		self.upgrades['blood'] = (1, 5, "Blood Bear", "召唤一个鲜血巨熊，而非巨熊。鲜血巨熊有黑暗抗性，每次攻击不断提升伤害。", "species")

		self.must_target_walkable = True
		self.must_target_empty = True

	def cast(self, x, y):

		bear = Unit()
		bear.max_hp = self.get_stat('minion_health')

		bear.name = "Giant Bear"
		bear.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))

		bear.tags = [Tags.Living, Tags.Nature]

		if self.get_stat('venom'):
			bear.name = "Venom Beast"
			bear.asset_name = "giant_bear_venom"
			bear.resists[Tags.Poison] = 100
			bear.tags = [Tags.Living, Tags.Poison, Tags.Nature]

			bite = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), buff=Poison, buff_duration=5)
			bite.name = "Poison Bite"
			bear.spells = [bite]

			bear.buffs = [VenomBeastHealing()]

		elif self.get_stat('armored'):
			bear.max_hp += 14
			bear.name = "Armored Bear"
			bear.asset_name = "giant_bear_armored"
			bear.resists[Tags.Physical] = 50
			bear.resists[Tags.Lightning] = -50

		elif self.get_stat('blood'):
			bear = BloodBear()
			apply_minion_bonuses(self, bear)

		bear.spells[0].attacks = self.get_stat('minion_attacks')
		if self.get_stat('minion_attacks') > 1:
			bear.spells[0].description += "\n攻击 %d 次。" % self.get_stat('minion_attacks')

		self.summon(bear, Point(x, y))
		yield

	def get_description(self):
		return ("召唤一个巨熊。\n"
				"巨熊有 [{minion_health}_点生命:minion_health]。\n"
				"巨熊的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

class FeedingFrenzySpell(Spell):

	def on_init(self):
		self.max_charges = 3
		self.name = "Sight of Blood"
		self.duration = 4
		self.range = 10

		self.demon_units = 0
		self.upgrades['duration'] = (3, 3)
		self.upgrades['demon_units'] = (1, 2, "Demon Frenzy", "恶魔单位也受影响。")
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "鲜血视线施放无需视线。")

		self.tags = [Tags.Nature, Tags.Enchantment]
		self.level = 4

	def can_affect(self, unit):
		if Tags.Living not in unit.tags and not (self.get_stat('demon_units') and Tags.Demon in unit.tags):
			return False
		if unit == self.caster:
			return False
		return True

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.get_units_in_los(Point(x, y)) if self.can_affect(u)]

	def cast(self, x, y):

		target = self.caster.level.get_unit_at(x, y)
		if not target:
			return

		self.caster.level.deal_damage(x, y, 0, Tags.Fire, self)
		target.apply_buff(Stun(), self.get_stat('duration'))

		for unit in self.caster.level.get_units_in_los(target):
			if unit == target:
				continue
			if not self.can_affect(unit):
				continue
			unit.apply_buff(BerserkBuff(), self.get_stat('duration'))

		yield

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if not self.can_affect(unit):
			return False
		if unit.cur_hp == unit.max_hp:
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return ("必须以 [living] 单位为目标。\n"
				"目标被 [stunned]，持续 [{duration}_回合:duration]。\n"
				+ text.stun_desc + '\n'
				+ "目标视线内的所有 [living] 单位 [berserk]，持续 [{duration}_回合:duration]。\n"
				+ text.berserk_desc).format(**self.fmt_dict())


class DarknessBuff(Buff):

	def on_init(self):
		self.name = "Darkness"
		self.color = Tags.Dark.color
		self.description = "每回合致盲地图上所有的非恶魔、非不死的单位。"
		self.asset = ['status', 'darkness']
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		self.effect_unit(evt.unit)

	def on_applied(self, evt):
		units = list(self.owner.level.units)
		for unit in units:
			self.effect_unit(unit)

	def on_advance(self):
		units = list(self.owner.level.units)
		for unit in units:
			if not unit.get_buff(BlindBuff):
				self.effect_unit(unit)

	def on_unapplied(self):
		units = list(self.owner.level.units)
		for unit in units:
			buff = unit.get_buff(BlindBuff)
			if buff:
				unit.remove_buff(buff)

	def effect_unit(self, unit):
		if Tags.Demon in unit.tags:
			return
		if Tags.Undead in unit.tags:
			return
		unit.apply_buff(BlindBuff())

class Darkness(Spell):

	def on_init(self):
		self.name = "Darkness"
		self.duration = 5
		self.max_charges = 3
		self.level = 3
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.range = 0

		self.upgrades['duration'] = (3, 2)
		self.upgrades['max_charges'] = (3, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(DarknessBuff(), self.get_stat('duration'))

	def get_description(self):
		return ("每回合 [blind] 所有单位，持续 [1_回合:duration]。\n"
				+ text.blind_desc + '\n'
				"[Demon] 和 [undead] 单位不受影响。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class StormSpell(Spell):

	def on_init(self):
		self.max_charges = 4
		self.name = "Lightning Storm"
		self.duration = 10
		self.range = 9
		self.radius = 4
		self.damage = 12
		self.strikechance = 50

		self.upgrades['strikechance'] = (25, 2)
		self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "闪电风暴施放无需视线。")
		self.upgrades['radius'] = (2, 2)
		self.upgrades['damage'] = 7

		self.tags = [Tags.Lightning, Tags.Nature, Tags.Enchantment]
		self.level = 4

	def cast(self, x, y):

		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				cloud = StormCloud(self.caster)
				cloud.duration = self.get_stat('duration')
				cloud.damage = self.get_stat('damage')
				cloud.strikechance = self.get_stat('strikechance') / 100.0
				cloud.source = self
				yield self.caster.level.add_obj(cloud, p.x, p.y)

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

	def get_description(self):
		return ("生成一股 [{radius}_格:radius] 半径的闪电风暴。\n"
				"每回合风暴中的单位有 [{strikechance}%_几率:strikechance] 受到 [{damage}_点闪电:lightning] 伤害。\n"
				"风暴持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class ThornyPrisonSpell(Spell):

	def on_init(self):
		self.max_charges = 6
		self.name = "Prison of Thorns"
		self.range = 10
		self.minion_damage = 3
		self.minion_health = 7

		self.upgrades['minion_damage'] = (3, 2)
		self.upgrades['minion_health'] = (7, 2)
		self.upgrades['iron'] = (1, 5, "Iron Prison", "改为召唤铁棘监狱，额外造成 3 点伤害，对多种伤害有抗性。", 'prison')
		self.upgrades['icy'] = (1, 6, "Icy Prison", "改为召唤冰棘监狱，进行寒冰远程攻击。", 'prison')

		self.minion_duration = 15

		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 3

	def get_description(self):
		return ("用食肉植物包围一群敌人。\n"
				"植物有 [{minion_health}_点生命:minion_health] ，无法移动。\n"
				"植物的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。\n"
				"植物在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast(self, x, y):
		target_points = self.get_impacted_tiles(x, y)

		random.shuffle(target_points)

		for p in target_points:

			unit = Unit()
			unit.name = "Thorny Plant"
			unit.max_hp = self.get_stat('minion_health')
			unit.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
			unit.stationary = True
			unit.turns_to_death = self.get_stat('minion_duration')
			unit.tags = [Tags.Nature]

			if self.get_stat('iron'):
				unit.name = "Iron Thorn"
				unit.asset_name = "fae_thorn_iron"
				unit.tags.append(Tags.Metallic)
				unit.spells[0].damage += 3
			if self.get_stat('icy'):
				unit.name = "Icy Thorn"
				unit.asset_name = "spriggan_bush_icy"
				unit.spells = [SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=3 + self.get_stat('minion_range'), damage_type=Tags.Ice)]

			self.summon(unit, p, radius=0)

			yield


	def get_impacted_tiles(self, x, y):

		candidates = set([Point(x, y)])
		unit_group = set()

		while candidates:
			candidate = candidates.pop()
			unit = self.caster.level.get_unit_at(candidate.x, candidate.y)
			if unit and unit not in unit_group and are_hostile(unit, self.caster):
				unit_group.add(unit)

				for p in self.caster.level.get_adjacent_points(Point(unit.x, unit.y), filter_walkable=False):
					candidates.add(p)

		outline = set()
		for unit in unit_group:
			for p in self.caster.level.get_adjacent_points(Point(unit.x, unit.y)):
				if not self.caster.level.get_unit_at(p.x, p.y):
					outline.add(p)

		return list(outline)

class FlameStrikeSpell(Spell):

	def on_init(self):
		self.max_charges = 2
		self.radius = 1
		self.damage = 50
		self.element = Tags.Fire
		self.range = 10
		self.name = "Pillar of Fire"
		self.requires_los = False

		self.tags = [Tags.Fire, Tags.Holy, Tags.Sorcery]
		self.level = 5

		self.upgrades['radius'] = (1, 3)
		self.upgrades['damage'] = (30, 2)
		self.upgrades['max_charges'] = (2, 2)
		self.upgrades['channel'] = (1, 3, "Channeling", "火柱术变为引导咒语。")

	def cast(self, x, y, channel_cast=False):

		if self.get_stat('channel') and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)))
			return

		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				damage = self.get_stat('damage')
				if point.x == x and point.y == y:
					damage = damage * 2
				self.caster.level.deal_damage(point.x, point.y, damage, self.element, self)
			yield

		return

	def get_impacted_tiles(self, x, y):
			return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

	def get_description(self):
		return ("在 [{radius}_格:radius] 冲程内造成 [{damage}_点火焰:fire] 伤害。\n"
			    "对中心地块造成翻倍伤害。").format(**self.fmt_dict())

class CloudArmorBuff(Buff):

	def on_applied(self, owner):
		self.resists[Tags.Lightning] = 100
		self.resists[Tags.Physical] = 50
		self.color = Color(215, 215, 255)
		self.buff_type = BUFF_TYPE_BLESS

	def on_advance(self):
		self.owner.deal_damage(-self.hp_regen, Tags.Heal, self)

class CloudArmorSpell(Spell):

	def on_init(self):
		self.max_charges = 5
		self.duration = 8
		self.hp_regen = 5
		self.name = "Cloud Armor"
		self.range = 7

	def can_cast(self, x, y):
		if not Spell.can_cast(self, x, y):
			return False
		if not self.caster.level.is_point_in_bounds(Point(x, y)):
			return False
		if not self.caster.level.get_unit_at(x, y):
			return False
		return isinstance(self.caster.level.tiles[x][y].cloud, StormCloud)

	def get_description(self):
		return "目标在闪电风暴中的单位获得 100%% [lighting] 抗性、50%% [physical] 抗性和每回合 %d 生命回复，持续 %d 回合。"

	def cast(self, x, y):
		self.caster.level.tiles[x][y].cloud.kill()
		buff = CloudArmorBuff()
		buff.hp_regen = self.hp_regen
		self.caster.level.get_unit_at(x, y).apply_buff(buff, self.get_stat('duration'))
		yield
		return

class BloodlustBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.stack_type = STACK_INTENSITY
		self.name = "Blood Lust"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'bloodlust']
		self.color = Tags.Fire.color

		self.dtypes = [Tags.Fire, Tags.Physical]
		if spell.get_stat('holy_fury'):
			self.dtypes.append(Tags.Holy)
		if spell.get_stat('dark_fury'):
			self.dtypes.append(Tags.Dark)

	def qualifies(self, spell):
		if not hasattr(spell, 'damage'):
			return False
		if not hasattr(spell, 'damage_type'):
			return False
		if isinstance(spell.damage_type, list):
			for dtype in self.dtypes:
				if dtype in spell.damage_type:
					return True
			return False
		else:
			return spell.damage_type in self.dtypes

	def modify_spell(self, spell):
		if self.qualifies(spell):
			spell.damage += self.extra_damage

	def unmodify_spell(self, spell):
		if self.qualifies(spell):
			spell.damage -= self.extra_damage


class BloodlustSpell(Spell):

	def on_init(self):
		self.name = "Boiling Blood"
		self.max_charges = 9
		self.duration = 7
		self.extra_damage = 6
		self.range = 0

		self.tags = [Tags.Nature, Tags.Enchantment, Tags.Fire]
		self.level = 2

		self.upgrades['extra_damage'] = (6, 3)
		self.upgrades['duration'] = (7, 2)
		self.upgrades['holy_fury'] = (1, 3, "Holy Fury", "热血术还影响 [holy] 能力。")
		self.upgrades['dark_fury'] = (1, 3, "Dark Fury", "热血术还影响 [dark] 能力。")


	def get_description(self):
		return "所有友方单位的 [fire] 和 [physical] 能力获得叠加的 [{extra_damage}_点伤害:damage] 增益。\n持续 [{duration}_回合:duration]。".format(**self.fmt_dict())

	def cast(self, x, y):

		for unit in self.caster.level.units:
			if not self.caster.level.are_hostile(self.caster, unit) and unit != self.caster:
				buff = BloodlustBuff(self)
				buff.extra_damage = self.get_stat('extra_damage')
				unit.apply_buff(buff, self.get_stat('duration'))

				# For the graphic
				unit.deal_damage(0, Tags.Fire, self)
				yield

class HealMinionsSpell(Spell):

	def on_init(self):
		self.name = "Healing Light"
		self.heal = 25

		self.max_charges = 10
		self.range = 0

		self.upgrades['heal'] = (20, 1)
		self.upgrades['max_charges'] = (8, 2)
		self.upgrades['shields'] = (1, 2, "Shielding Light", "视线内的友方单位获得 1 点护盾。")

		self.tags = [Tags.Holy, Tags.Sorcery]
		self.level = 2

	def get_description(self):
		return "治疗视线内的所有友方单位 [{heal}_点生命:heal]。".format(**self.fmt_dict())

	def cast(self, x, y):

		for unit in self.caster.level.get_units_in_los(self.caster):
			if not self.caster.level.are_hostile(self.caster, unit) and unit != self.caster:

				# Dont heal the player if a gold drake is casting
				if unit.is_player_controlled:
					continue

				if unit.cur_hp < unit.max_hp:
					unit.deal_damage(-self.get_stat('heal'), Tags.Heal, self)

				if self.get_stat('shields'):
					unit.add_shields(self.get_stat('shields'))
				yield

class RegenAuraSpell(Spell):

	def on_init(self):
		self.name = "Regeneration Aura"
		self.heal = 4
		self.duration = 8
		self.range = 0
		self.radius = 10

		self.max_charges = 4
		self.level = 2

		self.tags = [Tags.Enchantment, Tags.Nature]

		self.whole_map = 0
		self.upgrades['heal'] = (4, 2)
		self.upgrades['duration'] = (8, 1)
		self.upgrades['whole_map'] = (1, 4, "Global", "光环治疗关卡内的所有友方单位。")

	def get_description(self):
		return ("每回合治疗 [{radius}_格:radius] 半径内的所有友方单位 [{heal}_点生命:heal]，持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(HealAuraBuff(self.get_stat('heal'), self.get_stat('radius'), whole_map=self.get_stat('whole_map')), self.get_stat('duration'))

class OrbBuff(Buff):

	def __init__(self, spell, dest):
		self.spell = spell
		self.dest = dest
		Buff.__init__(self)
		self.buff_type = BUFF_TYPE_PASSIVE

	def on_init(self):
		self.name = "Orb"
		self.description = "每回合向目标前进。"
		if self.spell.get_stat('melt_walls'):
			self.description += "\n\n消灭沿途的墙。"
		self.first = False

		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		self.owner.level.queue_spell(self.spell.on_orb_collide(self.owner, self.owner))

	def on_advance(self):
		# first advance: Radiate around self, do not move
		if self.first:
			self.first = False
			self.spell.on_orb_move(self.owner, self.owner)

		path = None
		if not self.spell.get_stat('melt_walls'):
			path = self.owner.level.find_path(self.owner, self.dest, self.owner, pythonize=True)
		else:
			path = self.owner.level.get_points_in_line(self.owner, self.dest)[1:]
		next_point = None
		if path:
			next_point = path[0]

		# Melt wall if needed
		if next_point and self.owner.level.tiles[next_point.x][next_point.y].is_wall() and self.spell.get_stat('melt_walls'):
			self.owner.level.make_floor(next_point.x, next_point.y)

		# otherwise- try to move one space foward
		if next_point and self.owner.level.can_move(self.owner, next_point.x, next_point.y, teleport=True):
			self.owner.level.act_move(self.owner, next_point.x, next_point.y, teleport=True)
			self.spell.on_orb_move(self.owner, next_point)
		else:
			self.spell.on_orb_move(self.owner, self.owner)

		if not next_point:
			self.owner.kill()


class OrbSpell(Spell):

	def __init__(self):
		self.melt_walls = False
		self.orb_walk = False
		Spell.__init__(self)
		# Do not require los, check points on the path instead
		self.requires_los = False

	def can_cast(self, x, y):
		if self.get_stat('orb_walk') and self.get_orb(x, y):
			return True

		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(x, y))
		if len(path) < 2:
			return False

		start_point = path[1]
		blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)
		if blocker:
			return False

		if not self.get_stat('melt_walls'):
			for p in path:
				if self.caster.level.tiles[p.x][p.y].is_wall():
					return False

		return Spell.can_cast(self, x, y)

	# Called before an orb is moved each turn
	def on_orb_move(self, orb, next_point):
		pass

	def on_orb_collide(self, orb, next_point):
		yield

	def on_orb_walk(self, existing):
		yield

	def on_make_orb(self, orb):
		return

	def get_orb_impact_tiles(self, orb):
		return [Point(orb.x, orb.y)]

	def get_orb(self, x, y):
		existing = self.caster.level.get_unit_at(x, y)
		if existing and existing.name == self.name:
			return existing
		return None

	def cast(self, x, y):
		existing = self.get_orb(x, y)
		if self.get_stat('orb_walk') and existing:
			for r in self.on_orb_walk(existing):
				yield r
			return

		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(x, y))
		if len(path) < 1:
			return

		start_point = path[1]

		# Clear a wall at the starting point if it exists so the unit can be placed
		if self.get_stat('melt_walls'):
			if self.caster.level.tiles[start_point.x][start_point.y].is_wall():
				self.caster.level.make_floor(start_point.x, start_point.y)

		unit = ProjectileUnit()
		unit.name = self.name
		unit.stationary = True
		unit.team = self.caster.team
		unit.turns_to_death = len(path) + 1

		unit.max_hp = self.get_stat('minion_health')

		# path[0] = caster, path[1] = start_point, path[2] = first point to move to
		buff = OrbBuff(spell=self, dest=Point(x, y))
		unit.buffs.append(buff)

		self.on_make_orb(unit)
		blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)

		# Should be taken care of by can_cast- but weird situations could cause this
		if blocker:
			return

		self.summon(unit, start_point)

	def get_collide_tiles(self, x, y):
		return []

	def get_impacted_tiles(self, x, y):
		existing = self.get_orb(x, y)
		if existing and self.get_stat('orb_walk'):
			return self.get_orb_impact_tiles(existing)
		else:
			return self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:] + self.get_collide_tiles(x, y)

class VoidOrbSpell(OrbSpell):

	def on_init(self):
		self.name = "Void Orb"
		self.minion_damage = 9
		self.fire_edge = 0
		self.range = 9
		self.max_charges = 4

		self.melt_walls = True

		self.minion_health = 15

		self.element = Tags.Arcane

		self.tags = [Tags.Arcane, Tags.Orb, Tags.Conjuration]
		self.level = 3

		self.upgrades['fire_edge'] = (1, 5, "Red Dwarf", "虚空法球额外造成一层 [fire] 伤害。")
		self.upgrades['range'] = (5, 2)
		self.upgrades['minion_damage'] = (9, 3)
		self.upgrades['orb_walk'] = (1, 2, "Void Walk", "指向另一个目标存在的虚空法球以引爆它，然后将你传送到该地块。")

	def on_orb_walk(self, existing):
		# Burst
		x = existing.x
		y = existing.y

		for stage in Burst(self.caster.level, Point(x, y), 3, ignore_walls=True):
			for point in stage:
				damage = self.get_stat('minion_damage')
				self.caster.level.deal_damage(point.x, point.y, damage, self.element, self)
				self.caster.level.make_floor(point.x, point.y)
			for i in range(3):
				yield

		existing.kill()
		self.caster.level.act_move(self.caster, x, y, teleport=True)

	def on_make_orb(self, orb):
		orb.resists[Tags.Arcane] = 0
		orb.shields = 3

	def on_orb_move(self, orb, next_point):
		x = next_point.x
		y = next_point.y
		level = orb.level

		for p in level.get_points_in_ball(x, y, 2, diag=True):
			damage = self.get_stat('minion_damage')
			unit = level.get_unit_at(p.x, p.y)
			if unit == orb:
				damage = 0

			if unit == self.caster:
				continue

			if distance(p, Point(x, y), diag=True) > 1:
				if self.get_stat('fire_edge'):
					level.deal_damage(p.x, p.y, damage, Tags.Fire, self)
			else:
				# Melt walls
				tile = level.tiles[p.x][p.y]
				#if not tile.is_chasm and not tile.can_walk:
				#	level.make_floor(p.x, p.y)
				level.deal_damage(p.x, p.y, damage, Tags.Arcane, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Arcane)
		yield

	def get_orb_impact_tiles(self, orb):
		return [p for stage in Burst(self.caster.level, orb, 3, ignore_walls=True) for p in stage]

	def get_description(self):
		return ("在施法者旁召唤一个虚空法球。\n"
				"法球沿途熔化墙，每回合对所有相邻单位造成 [{minion_damage}_点奥术:arcane] 伤害。\n"
				"法球没有意识，每回合向目标漂浮一格。\n"
				"法球可被 [arcane] 伤害摧毁。").format(**self.fmt_dict())

class SearingOrb(OrbSpell):

	def on_init(self):
		self.name = "Searing Orb"

		self.minion_damage = 3
		self.minion_health = 8
		self.max_charges = 3
		self.level = 6
		self.range = 9

		self.radius = 3

		self.tags = [Tags.Fire, Tags.Orb, Tags.Conjuration]

		self.upgrades['range'] = (5, 2)
		self.upgrades['melt_walls'] = (1, 4, "Matter Melting", "灼热法球可穿墙施放并熔化墙")

	def get_description(self):
		return ("在施法者旁召唤一个灼热法球\n"
				"法球每回合对视线内的所有单位造成 [{minion_damage}_点火焰:fire] 伤害。\n"
				"施法者免疫此伤害。\n"
				"法球没有意识，每回合向目标漂浮一格。\n"
				"法球可被 [ice] 伤害摧毁。").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Ice] = 0

	def on_orb_move(self, orb, next_point):
		damage = self.get_stat('minion_damage')
		for u in orb.level.get_units_in_los(next_point):
			if u == self.caster:
				continue
			if u == orb:
				continue
			u.deal_damage(damage, Tags.Fire, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Fire)
		yield

class BallLightning(OrbSpell):

	def on_init(self):
		self.name = "Ball Lightning"

		self.num_targets = 3
		self.minion_damage = 6
		self.minion_health = 12

		self.level = 5
		self.range = 9
		self.max_charges = 4

		self.radius = 4

		self.tags = [Tags.Orb, Tags.Lightning, Tags.Conjuration]

		self.upgrades['num_targets'] = (2, 3)
		self.upgrades['range'] = (5, 2)
		self.upgrades['minion_damage'] = (10, 5)
		self.upgrades['orb_walk'] = (1, 1, "Magnetic Pulse", "指向另一个目标存在的闪电法球以发射磁脉冲，将视线内的所有 [construct] 和 [lightning] 单位向法球拉动 3 格。")

	def get_description(self):
		return ("在施法者旁召唤一个闪电法球。\n"
				"法球每回合随机对视线内的单位发射 [{num_targets}_束:num_targets] 电光，每束造成 [{minion_damage}_点闪电:lightning] 伤害。\n"
				"法球没有意识，每回合向目标漂浮一格。\n"
				"法球可被 [lightning] 伤害摧毁。").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Lightning] = 0

	def on_orb_walk(self, orb):
		targets = [u for u in orb.level.get_units_in_los(orb) if are_hostile(u, self.caster) and (Tags.Construct in u.tags or Tags.Lightning in u.tags)]

		for t in targets:
			pull(t, orb, 3)
			t.deal_damage(self.get_stat('minion_damage'), Tags.Physical, self)
			yield

	def on_orb_move(self, orb, next_point):
		targets = [u for u in orb.level.get_units_in_los(next_point) if are_hostile(u, self.caster)]
		random.shuffle(targets)
		for i in range(self.get_stat('num_targets')):
			if not targets:
				break
			target = targets.pop()
			for p in orb.level.get_points_in_line(next_point, target, find_clear=True)[1:]:
				if orb.level.get_unit_at(p.x, p.y) == orb:
					continue
				orb.level.deal_damage(p.x, p.y, self.get_stat('minion_damage'), Tags.Lightning, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Lightning)
		yield

class GlassOrbSpell(OrbSpell):

	def on_init(self):
		self.name = "Glass Orb"

		self.minion_health = 8
		self.duration = 2
		self.level = 3
		self.max_charges = 4
		self.radius = 3
		self.range = 9

		self.tags = [Tags.Arcane, Tags.Orb, Tags.Conjuration]

		self.upgrades['duration'] = (1, 2)
		self.upgrades['range'] = (4, 2)
		self.upgrades['shield'] = (1, 1, "Shielding", "法球给范围内的随从 1 点护盾，上限为 3。")
		#self.upgrades['orb_walk'] = (1, 1, "Glassilution",
		#								   "Targeting an existing glass orb causes the existing orb to emit an explosion of glassifying energy."
		#								   "  The radius and duration of the glassification explosion are double normal.")
		self.upgrades['radius'] = (1, 3)

	def get_description(self):
		return ("在施法者旁召唤一个玻璃法球。\n"
				"法球每回合对 [{radius}_格:radius] 半径内的所有敌人施加 [glassify]。\n"
				+ text.glassify_desc + "\n" +
				"法球没有意识，每回合向目标漂浮一格。\n"
				"法球可被 [physical] 伤害摧毁。").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Physical] = -100
		orb.shields = 9

	def on_orb_move(self, orb, next_point):
		for p in orb.level.get_points_in_ball(next_point.x, next_point.y, self.get_stat('radius')):
			unit = orb.level.get_unit_at(p.x, p.y)
			if not unit:
				orb.level.show_effect(p.x, p.y, Tags.Glassification)

			if unit and unit != orb and unit != self.caster:
				if not are_hostile(orb, unit) and self.get_stat('shield'):
					if unit.shields < 3:
						unit.add_shields(1)
				elif are_hostile(orb, unit):
					unit.apply_buff(GlassPetrifyBuff(), self.get_stat('duration'))

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Physical)
		yield

	def on_orb_walk(self, orb):
		for stage in Burst(orb.level, orb, self.get_stat('radius') * 2):
			for point in stage:
				unit = orb.level.get_unit_at(point.x, point.y)

				if unit:
					if not are_hostile(orb, unit) and self.get_stat('shield'):
						if unit.shields < 3:
							unit.add_shields(1)
					else:
						unit.apply_buff(GlassPetrifyBuff(), self.get_stat('duration') * 2)
				# Todo- some glassier effect?
				orb.level.show_effect(point.x, point.y, Tags.Arcane)
			yield

class FrozenOrbSpell(OrbSpell):

	def on_init(self):
		self.name = "Ice Orb"

		self.minion_damage = 7
		self.radius = 3
		self.range = 9
		self.minion_health = 40
		self.level = 4

		self.max_charges = 5

		self.tags = [Tags.Orb, Tags.Conjuration, Tags.Ice]

		self.freeze_chance = 0
		self.upgrades['freeze_chance'] = (50, 3, "Freeze Chance", "法球有 50% 几率冻结受伤的目标，持续 1 回合。")
		self.upgrades['radius'] = (2, 2)
		self.upgrades['minion_damage'] = (5, 3)

	def get_description(self):
		return ("在施法者旁召唤一个寒冰法球。\n"
				"法球每回合对 [{radius}_格:radius] 半径内的所有敌人造成 [{minion_damage}_点寒冰:ice] 伤害。\n"
				+ text.frozen_desc +
				"法球没有意识，每回合向目标漂浮一格。\n"
				"法球可被 [fire] 伤害摧毁。").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Fire] = 0

	def on_orb_move(self, orb, next_point):
		for p in orb.level.get_points_in_ball(next_point.x, next_point.y, self.get_stat('radius')):
			unit = orb.level.get_unit_at(p.x, p.y)
			if unit and are_hostile(orb, unit):
				unit.deal_damage(self.get_stat('minion_damage'), Tags.Ice, self)
				if random.randint(0, 100) < self.get_stat('freeze_chance'):
					unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
			else:
				if random.random() < .5:
					orb.level.deal_damage(p.x, p.y, 0, Tags.Ice, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Ice)
		yield

class OrbControlSpell(Spell):

	def on_init(self):
		self.name = "Orb Control"

		self.tags = [Tags.Sorcery, Tags.Orb]

		self.range = 9

		self.level = 4
		self.requires_los = False
		self.max_charges = 11

	def get_description(self):
		return ("所有友方 [orbs:orb] 的目标改为目标地块。")

	def cast_instant(self, x, y, channel_cast=False):

		for u in self.caster.level.units:
			if u.team != self.caster.team:
				continue
			buff = u.get_buff(OrbBuff)
			if buff:
				path = self.caster.level.get_points_in_line(u, Point(x, y))[1:]
				u.turns_to_death = len(path) + 1
				buff.dest = Point(x, y)

	def get_impacted_tiles(self, x, y):
		tiles = set()
		for u in self.caster.level.units:
			if u.team != self.caster.team:
				continue
			buff = u.get_buff(OrbBuff)
			if buff:
				path = self.caster.level.get_points_in_line(u, Point(x, y))
				for p in path:
					tiles.add(p)
		return tiles

class DominateBuff(Buff):

	def __init__(self, caster, decay=False):
		Buff.__init__(self)
		self.caster = caster
		self.color = Color(255, 180, 180)
		self.stack_type = STACK_NONE
		self.buff_type = BUFF_TYPE_CURSE
		self.decay = decay

	def on_applied(self, owner):
		self.old_team = owner.team
		self.owner.team = self.caster.team

	def on_unapplied(self):
		self.owner.team = self.old_team
		if self.decay:
			self.owner.deal_damage(self.owner.cur_hp // 2, Tags.Physical, self)

class Dominate(Spell):

	def on_init(self):
		self.name = "Dominate"
		self.range = 5
		self.max_charges = 4

		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.level = 3

		self.hp_threshold = 40
		self.check_cur_hp = 0

		self.upgrades['max_charges'] = (2, 2)
		self.upgrades['hp_threshold'] = (40, 3, 'HP Threshold', '提升可选为目标的生命上限。')
		self.upgrades['check_cur_hp'] = (1, 4, 'Brute Force', '支配术的目标条件改为当前生命，而非生命上限。')

	def can_cast(self, x, y):
		if not Spell.can_cast(self, x, y):
			return False
		unit = self.caster.level.get_unit_at(x, y)
		if unit is None:
			return False
		if not are_hostile(unit, self.caster):
			return False
		hp = unit.cur_hp if self.get_stat('check_cur_hp') else unit.max_hp
		return hp <= self.get_stat('hp_threshold')

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		unit.team = self.caster.team
		yield

	def get_description(self):
		return ("目标 [{hp_threshold}_点生命:heal] 或更低的敌方单位变为你的小兵。").format(**self.fmt_dict())

class ElementalEyeBuff(Buff):

	def __init__(self, element, damage, freq, spell):
		Buff.__init__(self)
		self.element = element
		self.damage = damage
		self.freq = max(1, freq)
		self.cooldown = freq
		self.color = element.color
		self.buff_type = BUFF_TYPE_BLESS

		freq_str = "每回合" if self.freq == 1 else ("每 %d 回合" % self.freq)
		self.description = "%s 随机对视线内的一个敌人造成 %d 点 %s 伤害。" % (freq_str, self.damage, self.element.name)
		self.spell = spell

	def on_advance(self):

		self.cooldown -= 1
		if self.cooldown == 0:
			self.cooldown = self.freq


			possible_targets = self.owner.level.units
			possible_targets = [t for t in possible_targets if self.owner.level.are_hostile(t, self.owner)]
			possible_targets = [t for t in possible_targets if self.owner.level.can_see(t.x, t.y, self.owner.x, self.owner.y)]

			if possible_targets:
				target = random.choice(possible_targets)
				self.owner.level.queue_spell(self.shoot(Point(target.x, target.y)))
				self.cooldown = self.freq
			else:
				self.cooldown = 1


	def shoot(self, target):
		self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'sorcery_ally')
		path = self.owner.level.get_points_in_line(Point(self.owner.x, self.owner.y), target, find_clear=True)

		for point in path:
			self.owner.level.deal_damage(point.x, point.y, 0, self.element, self.spell)
			yield

		self.owner.level.deal_damage(target.x, target.y, self.damage, self.element, self.spell)
		self.on_shoot(target)

	def on_shoot(self, target):
		pass

class RageEyeBuff(ElementalEyeBuff):

	def __init__(self, freq, berserk_duration, spell):
		ElementalEyeBuff.__init__(self, Tags.Physical, 0, freq, spell)
		self.berserk_duration = berserk_duration
		self.name = "Eye of Rage"
		self.color = Tags.Nature.color
		self.asset = ['status', 'rage_eye']

	def on_shoot(self, target):
		unit = self.owner.level.get_unit_at(target.x, target.y)
		if unit:
			if self.spell.get_stat('lycanthrophy') and Tags.Living in unit.tags and unit.cur_hp <= 25:
				unit.kill()
				newunit = Werewolf()
				apply_minion_bonuses(self.spell, newunit)

				self.spell.summon(newunit, target=unit)
				newunit.apply_buff(BerserkBuff(), 14)

			else:
				unit.apply_buff(BerserkBuff(), self.berserk_duration)


# Split these into 2 classes so they stack properly
class LightningEyeBuff(ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		ElementalEyeBuff.__init__(self, Tags.Lightning, damage, freq, spell)
		self.name = "Eye of Lightning"
		self.color = Tags.Lightning.color
		self.asset = ['status', 'lightning_eye']

class FireEyeBuff(ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		ElementalEyeBuff.__init__(self, Tags.Fire, damage, freq, spell)
		self.name = "Eye of Fire"
		self.color = Tags.Fire.color
		self.asset = ['status', 'fire_eye']

class IceEyeBuff(ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		ElementalEyeBuff.__init__(self, Tags.Ice, damage, freq, spell)
		self.name = "Eye of Ice"
		self.color = Tags.Ice.color
		self.asset = ['status', 'ice_eye']


class EyeOfFireSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Fire"
		self.damage = 15
		self.element = Tags.Fire
		self.duration = 30
		self.shot_cooldown = 3

		self.upgrades['shot_cooldown'] = (-1, 1)
		self.upgrades['duration'] = 15
		self.upgrades['damage'] = (7, 2)

		self.tags = [Tags.Fire, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = FireEyeBuff(self.get_stat('damage'), self.get_stat('shot_cooldown'), self)
		buff.element = self.element
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每 [{shot_cooldown}_回合:shot_cooldown] 随机对视线内的一个敌方单位造成 [{damage}_点火焰:fire] 伤害。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class EyeOfLightningSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Lightning"
		self.damage = 15
		self.element = Tags.Lightning
		self.duration = 30
		self.shot_cooldown = 3

		self.upgrades['shot_cooldown'] = (-1, 1)
		self.upgrades['duration'] = 15
		self.upgrades['damage'] = (7, 2)

		self.tags = [Tags.Lightning, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = LightningEyeBuff(self.get_stat('damage'), self.get_stat('shot_cooldown'), self)
		buff.element = self.element
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每 [{shot_cooldown}_回合:shot_cooldown] 随机对视线内的一个敌方单位造成 [{damage}_点闪电:lightning] 伤害。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class EyeOfIceSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Ice"
		self.damage = 15
		self.element = Tags.Ice
		self.duration = 30
		self.shot_cooldown = 3

		self.upgrades['shot_cooldown'] = (-1, 1)
		self.upgrades['duration'] = 15
		self.upgrades['damage'] = (7, 2)

		self.tags = [Tags.Ice, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = IceEyeBuff(self.get_stat('damage'), self.get_stat('shot_cooldown'), self)
		buff.element = self.element
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每 [{shot_cooldown}_回合:shot_cooldown] 随机对视线内的一个敌方单位造成 [{damage}_点寒冰:ice] 伤害。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class EyeOfRageSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Rage"
		self.duration = 20
		self.shot_cooldown = 3

		self.berserk_duration = 2

		self.upgrades['shot_cooldown'] = (-1, 1)
		self.upgrades['duration'] = 15
		self.upgrades['berserk_duration'] = 2
		self.upgrades['lycanthrophy'] = (1, 5, "Lycanthropy", "当愤怒之眼以生命不超过 25 的 [living] 单位为目标时，立刻消灭该单位并将其复活为友方的狼人。该狼人 [berserk] 14 回合。")

		self.tags = [Tags.Nature, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = RageEyeBuff(self.shot_cooldown, self.get_stat('berserk_duration'), self)
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每 [{shot_cooldown}_回合:shot_cooldown] 随机对视线内的一个敌方单位施加 [berserk]，持续 [{berserk_duration}_回合:berserk]。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class NightmareBuff(DamageAuraBuff):

	def __init__(self, spell):
		self.spell = spell
		DamageAuraBuff.__init__(self, damage=self.spell.aura_damage, radius=self.spell.get_stat('radius'), damage_type=[Tags.Arcane, Tags.Dark], friendly_fire=False)

	def get_description(self):
		return "受到 %d 点伤害" % self.damage_dealt

	def on_unapplied(self):
		creatures = []

		if self.spell.get_stat("electric_dream"):
			creatures = [(Elf, 80), (Thunderbird, 35), (SparkSpirit, 25)]
		if self.spell.get_stat("dark_dream"):
			creatures = [(OldWitch, 80), (Werewolf, 35), (Raven, 25)]
		if self.spell.get_stat("fever_dream"):
			creatures = [(FireSpawner, 80), (FireSpirit, 35), (FireLizard, 25)]

		for spawner, cost in creatures:
			for i in range(self.damage_dealt // cost):
				unit = spawner()
				unit.turns_to_death = random.randint(4, 13)
				apply_minion_bonuses(self.spell, unit)
				self.summon(unit, sort_dist=False, radius=self.spell.get_stat('radius'))


class NightmareSpell(Spell):

	def on_init(self):

		self.range = 0
		self.max_charges = 2
		self.name = "Nightmare Aura"
		self.aura_damage = 2
		self.radius = 7
		self.duration = 30

		self.stats.append('aura_damage')

		self.upgrades['radius'] = (3, 2)
		self.upgrades['duration'] = 15
		self.upgrades['max_charges'] = (4, 2)

		self.upgrades['dark_dream'] = (1, 5, "Dark Dream", "结束时，基于咒语的总伤害临时召唤乌鸦、狼人和老巫婆。", "dream")
		self.upgrades['electric_dream'] = (1, 5, "Electric Dream", "结束时，基于咒语的总伤害临时召唤电光灵魂、雷鸟和精灵。", "dream")
		self.upgrades['fever_dream'] = (1, 5, "Fever Dream", "结束时，基于咒语的总伤害临时召唤火蜥蜴、火灵魂和女巫。", "dream")

		self.tags = [Tags.Enchantment, Tags.Dark, Tags.Arcane]
		self.level = 3

	def cast_instant(self, x, y):
		buff = NightmareBuff(self)
		buff.stack_type = STACK_REPLACE
		buff.color = Tags.Arcane.color
		buff.name = "Nightmare Aura"
		buff.source = self
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每回合对 [{radius}_格:radius] 半径内的所有敌人各随机造成 [{aura_damage}_点奥术:arcane] 或 [{aura_damage}_点黑暗:dark] 伤害。\n"
				"此伤害值固定，无法用神龛、被动或增益提升。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class CockatriceSkinSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Basilisk Armor"
		self.duration = 10

		self.upgrades['max_charges'] = 4
		self.upgrades['duration'] = 5

		self.tags = [Tags.Enchantment, Tags.Nature, Tags.Arcane]
		self.level = 3

	def cast_instant(self, x, y):
		self.caster.apply_buff(cockatriceScaleArmorBuff(), self.get_stat('duration'))

	def get_description(self):
		return ("每当一个敌方单位以咒语或攻击选你为目标时，该单位被 [petrified] [2:duration] 回合。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class WatcherFormBuff(Stun):

	def __init__(self, spell):
		Stun.__init__(self)
		self.spell = spell

	def on_applied(self, owner):
		self.name = "Watcher Eye"
		self.color = Tags.Enchantment.color

	def on_advance(self):

		possible_targets = self.owner.level.units
		possible_targets = [t for t in possible_targets if self.owner.level.are_hostile(t, self.owner)]
		possible_targets = [t for t in possible_targets if self.owner.level.can_see(t.x, t.y, self.owner.x, self.owner.y)]

		if possible_targets:
			random.shuffle(possible_targets)
			target = max(possible_targets, key=lambda t: distance(t, self.owner))
			self.owner.level.queue_spell(self.shoot(target))
		else:
			# Show the effect fizzling
			self.owner.deal_damage(0, Tags.Lightning, self)

	def shoot(self, target):
		points = self.owner.level.get_points_in_line(Point(self.owner.x, self.owner.y), Point(target.x, target.y), find_clear=True)[1:]
		for p in points:
			self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), self.spell.element, self.spell)
		yield

class WatcherFormDefenses(Buff):

	def on_init(self):
		self.transform_asset_name = "watcher"
		self.stack_type = STACK_TYPE_TRANSFORM
		self.resists[Tags.Physical] = 100
		self.resists[Tags.Lightning] = 100
		self.resists[Tags.Fire] = 100
		self.resists[Tags.Poison] = 100
		self.color = Tags.Enchantment.color
		self.name = "Watcher Form"

class WatcherFormSpell(Spell):

	def on_init(self):
		self.name = "Watcher Form"
		self.range = 0
		self.max_charges = 5
		self.duration = 5
		self.damage = 40
		self.element = Tags.Lightning
		self.tags = [Tags.Enchantment, Tags.Lightning, Tags.Arcane]
		self.level = 4

		self.upgrades['damage'] = (30, 3)
		self.upgrades['max_charges'] = (3, 2)
		self.upgrades['duration'] = 3

	def cast_instant(self, x, y):
		self.caster.apply_buff(WatcherFormBuff(self), self.get_stat('duration'))
		self.caster.apply_buff(WatcherFormDefenses(), self.get_stat('duration') + 1)

	def get_description(self):
		return ("每回合向视线内最远的敌人发射一道闪电箭，在束状内造成 [{damage}_点闪电:lightning] 伤害。\n"
				"你无法移动或施放咒语。\n"
				"获得 100 [physical] 抗性。\n"
				"获得 100 [fire] 抗性。\n"
				"获得 100 [lightning] 抗性。\n"
				"获得 100 [poison] 抗性。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class ImpCallBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Imp Call"
		self.description = "每回合召唤小鬼。"
		self.spell = spell
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'imp_call']


	def on_applied(self, owner):
		self.casts = 0
		self.cast_this_turn = False
		self.color = Tags.Conjuration.color

	def on_advance(self):
		self.owner.level.queue_spell(self.summon_imps())

	def summon_imps(self):
		self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'summon_3')
		for i in range(self.spell.get_stat('num_summons')):
			imp = random.choice(self.spell.get_imp_choices())()
			imp.turns_to_death = self.spell.get_stat('minion_duration')
			apply_minion_bonuses(self.spell, imp)
			self.spell.summon(imp, self.owner)
			yield

class ImpGateSpell(Spell):

	def on_init(self):
		self.name = "Imp Swarm"
		self.range = 0
		self.max_charges = 3
		self.duration = 5
		self.tags = [Tags.Enchantment, Tags.Conjuration, Tags.Chaos]
		self.level = 6

		self.minion_health = 5
		self.minion_damage = 4
		self.minion_duration = 11
		self.minion_range = 3
		self.num_summons = 2

		self.upgrades['minion_range'] = (2, 3)
		self.upgrades['num_summons'] = (1, 2)
		self.upgrades['minion_duration'] = (7, 2)
		self.upgrades['minion_damage'] = (5, 4)

		self.upgrades['metalswarm'] = (1, 6, "Metal Swarm", "小鬼群改为召唤铜质小鬼，而非电光小鬼，召唤熔炉小鬼，而非火焰小鬼。", "swarm")
		self.upgrades['darkswarm'] = (1, 5, "Dark Swarm", "小鬼群改为召唤腐烂小鬼、虚空小鬼和疯狂小鬼，而非火焰、电光和钢铁小鬼。", "swarm")
		self.upgrades['megaswarm'] = (1, 7, "Mega Swarm", "小鬼群改为召唤巨型小鬼，而非普通大小的。", "swarm")

		self.imp_choices = [FireImp, SparkImp, IronImp]

	def get_imp_choices(self):
		if self.get_stat('metalswarm'):
			return [CopperImp, FurnaceImp, TungstenImp]
		elif self.get_stat('darkswarm'):
			return [RotImp, VoidImp, InsanityImp]
		elif self.get_stat('megaswarm'):
			return [SparkImpGiant, FireImpGiant, IronImpGiant]
		else:
			return self.imp_choices

	def cast_instant(self, x, y):
		self.caster.apply_buff(ImpCallBuff(self), self.get_stat('duration'))

	def get_description(self):
		return ("每回合在施法者旁召唤 [{num_summons}_个小鬼:num_summons]。\n"
				"小鬼有 [{minion_health}_点生命:minion_health]，可飞行。\n"
				"小鬼的远程攻击造成 [{minion_damage}_点伤害:minion_damage]，射程 [{minion_range}_格:minion_range]。\n"
				"小鬼分别可能是 [fire]、[钢铁:physical] 或 [电光:lightning] 小鬼。\n"
				"小鬼分别持续 [{minion_duration}_回合:minion_duration]。此效果持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class LightningHaloBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell
		self.name = "Lightning Halo"
		self.description = "每回合对环状上造成 [lightning] 伤害。"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'lightning_halo']
		self.stack_type = STACK_REPLACE

	def on_init(self):
		self.radius = 1

	def on_applied(self, owner):
		self.color = Tags.Lightning.color

	def on_advance(self):
		self.owner.level.queue_spell(self.nova())

	def nova(self):
		self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'sorcery_ally')
		points = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius)
		points = [p for p in points if p != Point(self.owner.x, self.owner.y) and distance(self.owner, p) >= self.radius - 1]

		for p in points:
			self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), self.spell.element, self)

		yield

class LightningHaloSpell(Spell):

	def on_init(self):
		self.name = "Lightning Halo"
		self.range = 0
		self.max_charges = 5
		self.duration = 9
		self.tags = [Tags.Enchantment, Tags.Lightning]
		self.level = 3
		self.damage = 15
		self.element = Tags.Lightning

		self.radius = 3
		self.upgrades['radius'] = (1, 1)
		self.upgrades['duration'] = (3, 2)
		self.upgrades['damage'] = (10, 2)
		self.upgrades['max_charges'] = (3, 2)

	def cast_instant(self, x, y):

		buff = LightningHaloBuff(self)
		buff.radius = self.get_stat('radius')
		self.caster.apply_buff(buff, self.get_stat('duration'))

		# call this manually once
		buff.on_advance()

	def get_impacted_tiles(self, x, y):
		points = self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.get_stat('radius'))
		points = [p for p in points if p != Point(self.caster.x, self.caster.y) and distance(self.caster, p) >= self.get_stat('radius') - 1]
		return points

	def get_description(self):
		return ("每回合对 [{radius}_格:radius] 环状上的所有单位造成 [{damage}_点闪电:lightning] 伤害。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class ArcaneVisionSpell(Spell):

	def on_init(self):
		self.name = "Mystic Vision"
		self.range = 0
		self.max_charges = 4
		self.duration = 8
		self.bonus = 5
		self.tags = [Tags.Enchantment, Tags.Arcane]
		self.level = 3

		self.upgrades['max_charges'] = (3, 2)
		self.upgrades['duration'] = (8, 2)
		self.upgrades['bonus'] = (5, 4)
		self.upgrades['aura'] = (1, 5, "Vision Aura", "神秘视觉影响所有友方单位。")

	def cast_instant(self, x, y):
		buff = GlobalAttrBonus('range', self.get_stat('bonus'))
		buff.name = "Mystic Vision"
		self.caster.apply_buff(buff, self.get_stat('duration'))

		if self.get_stat('aura'):
			for u in self.owner.level.units:
				if are_hostile(self.owner, u):
					continue
				buff = GlobalAttrBonus('range', self.get_stat('bonus'))
				buff.name = "Mystic Vision"
				u.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("所有其他咒语获得 [{bonus}_格射程:range]。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class ArcaneDamageSpell(Spell):

	def on_init(self):
		self.name = "Mystic Power"
		self.range = 0
		self.max_charges = 7
		self.duration = 8
		self.bonus = 7
		self.tags = [Tags.Enchantment, Tags.Arcane]
		self.level = 3

		self.upgrades['duration'] = (8, 2)
		self.upgrades['bonus'] = (4, 4, "Damage Bonus", "神秘视觉的伤害增益提升 4。")
		self.upgrades['stackable'] = (1, 4, "Intensity", "神秘视觉改为叠加强度，而非持续。")

	def cast_instant(self, x, y):
		buff = GlobalAttrBonus('damage', self.get_stat('bonus'))
		buff.name = "Mystic Power"
		buff.stack_type = STACK_DURATION if not self.get_stat('stackable') else STACK_INTENSITY
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("所有其他咒语获得 [{bonus}_点伤害:damage]。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class PainBuff(GlobalAttrBonus):

	def __init__(self, bonus, self_damage):
		GlobalAttrBonus.__init__('damage', bonus)
		self.self_damage = self_damage

	def on_applied(self, owner):
		self.owner_triggers[EventOnMoved] = self.on_moved

	def advance(self):
		owner.deal_damage(self_damage, Tags.Dark, self)

	def on_moved(self):
		self.owner.remove_buff(self)

class PainSpell(Spell):

	def on_init(self):
		self.name = "Power of Pain"
		self.range = 0
		self.max_charges = 6
		self.bonus = 7
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.level = 4

		self.self_damage = 4
		self.upgrades['max_charges'] = 6
		self.upgrades['bonus'] = (5, 2)
		self.upgrades['self_damage'] = (-2, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(PainBuff(self.bonus))

	def get_description(self):
		return "你的咒语 +%d 伤害。每回合你受到 %d 点 [dark] 伤害。你移动时结束。" % (self.bonus, self.self_damage)

class FlameBurstSpell(Spell):

	def on_init(self):
		self.name = "Flame Burst"
		self.range = 0
		self.max_charges = 6
		self.damage = 35
		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 3
		self.radius = 6

		self.upgrades['radius'] = (3, 2)
		self.upgrades['damage'] = (15, 3)
		self.upgrades['max_charges'] = (3, 2)

		self.upgrades['meltflame'] = (1, 4, "Melting Flame", "熔化与目标相邻的墙。", "flame")
		self.upgrades['dawnflame'] = (1, 5, "Bright Flame", "炎爆术改为造成 [holy] 伤害，而非 [fire] 伤害，给友方单位护盾，而非对其造成伤害。", "flame")
		self.upgrades['spreadflame'] = (1, 7, "Spreading Flame", "每次施放炎爆术消耗所有剩余充能。\n每消耗一点充能，炎爆术 +1 范围且 +1 点伤害。\n击杀的敌人以一半的范围和伤害爆炸。", "flame")

	def get_impacted_tiles(self, x, y):
		radius = self.get_stat('radius')
		if self.get_stat('spreadflame'):
			radius += self.cur_charges
		return [p for stage in Burst(self.caster.level, Point(x, y), radius) for p in stage]

	def cast(self, x, y, secondary=False, last_radius=None, last_damage=None):

		if secondary:
			radius = last_radius // 2
			damage = last_damage // 2

			if radius < 2:
				return
			if damage < 0:
				return

		else:
			radius = self.get_stat('radius')
			damage = self.get_stat('damage')

		if not secondary and self.get_stat('spreadflame'):
			radius += self.cur_charges
			damage += self.cur_charges
			self.cur_charges = 0

		to_melt = set([Point(self.caster.x, self.caster.y)])
		slain = []

		stagenum = 0
		for stage in Burst(self.caster.level, Point(x, y), radius):
			dtype = Tags.Holy if self.get_stat('dawnflame') else Tags.Fire
			stagenum += 1

			for p in stage:
				if p.x == self.caster.x and p.y == self.caster.y:
					continue

				friendly = None
				if self.get_stat('dawnflame'):
					friendly = self.caster.level.get_unit_at(p.x, p.y)
					if friendly and are_hostile(self.caster, friendly):
						friendly = None

					if friendly:
						friendly.add_shields(1)

				if not friendly:
					unit = self.caster.level.get_unit_at(p.x, p.y)
					self.caster.level.deal_damage(p.x, p.y, damage, dtype, self)
					if unit and not unit.is_alive():
						slain.append(unit)

				if self.get_stat('meltflame'):
					for q in self.caster.level.get_points_in_ball(p.x, p.y, 1):
						if self.caster.level.tiles[q.x][q.y].is_wall():
							to_melt.add(q)

			yield

		if self.get_stat('spreadflame'):
			for unit in slain:
				self.owner.level.queue_spell(self.cast(unit.x, unit.y, secondary=True, last_damage=damage, last_radius=radius))

		if self.get_stat('meltflame'):
			for p in to_melt:
				self.caster.level.make_floor(p.x, p.y)
				self.caster.level.show_effect(p.x, p.y, Tags.Fire)

	def get_description(self):
		return ("在施法者 [{radius}_格:radius] 冲程内造成 [{damage}_点火焰:fire] 伤害。").format(**self.fmt_dict())

class SummonFireDrakeSpell(Spell):

	def on_init(self):
		self.name = "Fire Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Fire, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = FireDrake().spells[0].damage
		self.minion_range = 7
		self.upgrades['minion_health'] = (25, 3)
		self.upgrades['breath_damage'] = (10, 2)
		self.upgrades['dragon_mage'] = (1, 6, "Dragon Mage", "召唤的火焰巨龙可施放 3 回合冷却的火球术。\n此火球术获得你的所有升级和奖励。")


		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = FireDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')

		if self.get_stat('dragon_mage'):
			fball = FireballSpell()
			fball.statholder = self.caster
			fball.max_charges = 0
			fball.cur_charges = 0
			fball.cool_down = 3
			drake.spells.insert(1, fball)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("在目标地块上召唤一条火焰巨龙。\n"
				"火焰巨龙有 [{minion_health}_点生命:minion_health] 和 [100_点火焰:fire] 抗性，可飞行。\n"
				"火焰巨龙的吐息武器造成 [{breath_damage}_点火焰:fire] 伤害。\n"
				"火焰巨龙的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())


class LightningSwapBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast
		self.description = "被 [lightning] 咒语选为目标时，与主人换位。"

	def on_spell_cast(self, evt):
		if not self.spell.get_stat('drake_swap'):
			return
		if evt.caster != self.owner.source.owner:
			return
		if Tags.Lightning not in evt.spell.tags:
			return
		if evt.x != self.owner.x or evt.y != self.owner.y:
			return
		if not self.owner.level.can_stand(self.owner.x, self.owner.y, evt.caster, check_unit=False):
			return
		self.owner.level.act_move(self.owner, evt.caster.x, evt.caster.y, force_swap=True, teleport=True)

class SummonStormDrakeSpell(Spell):

	def on_init(self):
		self.name = "Storm Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Lightning, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = StormDrake().spells[0].damage
		self.minion_range = 7
		self.minion_physical_resist = 0
		self.upgrades['minion_health'] = (25, 2)

		self.upgrades['minion_physical_resist'] = (75, 3, "Cloudform", "召唤的风暴巨龙有 75% [physical] 抗性。")
		self.upgrades['drake_swap'] = (1, 2, "Drake Swap", "每当你以 [lightning] 咒语指定召唤的风暴巨龙为目标时，与其换位。")
		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "召唤的风暴巨龙可施放 3 回合冷却的闪电箭。\n此闪电箭获得你的所有升级和奖励。")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = StormDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')
		drake.resists[Tags.Physical] = self.get_stat('minion_physical_resist')

		if self.get_stat('drake_swap'):
			drake.buffs.append(LightningSwapBuff(self))

		if self.get_stat('dragon_mage'):
			lbolt = LightningBoltSpell()
			lbolt.statholder = self.caster
			lbolt.max_charges = 0
			lbolt.cur_charges = 0
			lbolt.cool_down = 3
			drake.spells.insert(1, lbolt)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("在目标地块上召唤一个风暴巨龙。\n"
				"风暴巨龙有 [{minion_health}_点生命:minion_health] 和 [100_点闪电:lightning] 抗性，可飞行。\n"
				"风暴巨龙的吐息武器生成风暴云，造成 [{breath_damage}_点闪电:lightning] 伤害。\n"
				"风暴巨龙的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

class EssenceDrakeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if not self.spell.get_stat('essence_drake'):
			return
		if not evt.damage_event:
			return
		if not are_hostile(self.owner, evt.unit):
			return
		if not evt.damage_event.source.owner == self.owner:
			return

		candidates = [u for u in self.owner.level.units if not are_hostile(u, self.owner) and u.turns_to_death]
		if not candidates:
			return

		candidate = random.choice(candidates)
		candidate.turns_to_death += 4


class SummonVoidDrakeSpell(Spell):

	def on_init(self):
		self.name = "Void Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Arcane, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = VoidDrake().spells[0].damage
		self.shields = 0
		self.minion_range = 7
		self.upgrades['minion_health'] = (25, 2)
		self.upgrades['shields'] = (3, 3)

		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "召唤的虚空巨龙可施放 3 回合冷却的魔法飞弹。\n此魔法飞弹获得你的所有升级和奖励。")
		self.upgrades['essence_drake'] = (1, 4, "Essence Drake", "每当召唤的虚空巨龙消灭敌方单位时，随机一个临时友军的持续时间 +4 回合。")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = VoidDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')
		drake.shields += self.get_stat('shields')
		drake.buffs.append(EssenceDrakeBuff(self))

		if self.get_stat('dragon_mage'):
			mmiss = MagicMissile()
			mmiss.statholder = self.caster
			mmiss.max_charges = 0
			mmiss.cur_charges = 0
			mmiss.cool_down = 3
			drake.spells.insert(1, mmiss)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("在目标地块上召唤一个虚空巨龙。\n"		
				"虚空巨龙有 [{minion_health}_点生命:minion_health] 和 [100_点奥术:arcane] 抗性，可飞行。\n"
				"虚空巨龙的吐息武器造成 [{minion_damage}_点奥术:arcane] 伤害且熔化墙。\n"
				"虚空巨龙的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

class SummonIceDrakeSpell(Spell):

	def on_init(self):
		self.name = "Ice Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Ice, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_range = 7
		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = 7
		self.duration = 2

		self.upgrades['minion_health'] = (25, 2)
		self.upgrades['duration'] = (3, 2, "Freeze Duration")
		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "召唤的寒冰巨龙可施放 8 回合冷却的死亡之寒。\n此死亡之寒获得你的所有升级和奖励。")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = IceDrake()

		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[0].freeze_duration = self.get_stat('duration')
		drake.spells[1].damage = self.get_stat('minion_damage')

		if self.get_stat('dragon_mage'):
			dchill = DeathChill()
			dchill.statholder = self.caster
			dchill.max_charges = 0
			dchill.cur_charges = 0
			dchill.cool_down = 8
			drake.spells.insert(1, dchill)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("在目标地块上召唤一个寒冰巨龙。\n"		
				"寒冰巨龙有 [{minion_health}_点生命:minion_health] 和 [100_点寒冰:ice] 抗性，可飞行。\n"
				"寒冰巨龙的吐息武器造成 [{minion_damage}_点寒冰:ice] 伤害并 [freeze] 单位。\n"
				"寒冰巨龙的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())


class SparkSpell(Spell):

	def on_init(self):
		self.name = "Spark"
		self.description = "对目标造成 [lightning] 伤害。连锁到有限数量附近的目标。"
		self.range = 8
		self.max_charges = 26
		self.level = 1
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.damage = 6

		self.num_targets = 3
		self.cascade_range = 3
		self.upgrades['num_targets'] = (2, 2)
		self.upgrades['damage'] = (6, 2)

	def cast(self, x, y):
		prev = self.caster
		target = Point(x, y)
		targets_left = self.get_stat('num_targets')

		while targets_left > 0 and target:
			targets_left -= 1
			for p in self.caster.level.get_points_in_line(prev, target)[1:]:
				self.caster.level.show_effect(p.x, p.y, Tags.Lightning)
				yield

			self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), Tags.Lightning, self)
			yield

			possible_targets = self.caster.level.get_units_in_ball(target, self.get_stat('cascade_range'))

			target_unit = self.caster.level.get_unit_at(target.x, target.y)
			if target_unit in possible_targets:
				possible_targets.remove(target_unit)
			if self.get_stat('no_friendly_fire'):
				possible_targets = [t for t in possible_targets if are_hostile(self.caster, t)]
			if not self.get_stat('wall_pen'):
				possible_targets = [t for t in possible_targets if self.caster.level.can_see(t.x, t.y, target.x, target.y)]

			prev = target
			if possible_targets:
				target = random.choice(possible_targets)
			else:
				target = None

class ChainLightningSpell(Spell):

	def on_init(self):
		self.name = "Chain Lightning"
		self.range = 9
		self.max_charges = 6
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 2
		self.damage = 8
		self.element = Tags.Lightning

		self.cascade_range = 4
		self.no_friendly_fire = 0
		self.overlap = 1

		self.upgrades['cascade_range'] = (4, 4)
		self.upgrades['damage'] = (8, 3)

		self.upgrades['weathercraft'] = (1, 3, "Cloud Conductance", "闪电链可弧入暴风雪和风暴云。")
		self.upgrades['shield'] = (1, 6, "Lightning Shield", "闪电链可弧入友方目标。\n被闪电链击中的友方单位改为获得 1 护甲，上限为 3，而非受到伤害。")

	def get_description(self):
		return ("发射一道弧状的电箭，造成 [{damage}_点闪电:lightning] 伤害。\n"
				"电箭在倾泻范围内反复弧入新目标。\n"
				"每道电弧沿着电束对所有单位造成伤害。\n"
				"电箭至多弧动 [{cascade_range}_格:radius]，不能穿墙。\n"
				"电箭无法弧动新目标时终结。").format(**self.fmt_dict())


	def cast(self, x, y):

		prev = self.caster
		target = self.caster.level.get_unit_at(x, y) or Point(x, y)
		already_hit = set()

		def hit_square(x, y):

			unit = self.caster.level.get_unit_at(x, y)
			if unit and not self.caster.level.are_hostile(unit, self.caster) and self.get_stat('shield'):
				if unit.shields < 3:
					unit.add_shields(1)
			else:
				self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)


		while target:

			# Overlap perk

			for p in self.caster.level.get_points_in_line(prev, target, find_clear=True)[1:]:
				if self.overlap:
					hit_square(p.x, p.y)
				else:
					self.caster.level.deal_damage(p.x, p.y, 0, self.element, self)
					yield

			if not self.overlap:
				hit_square(target.x, target.y)
				yield

			# Pause a bit after the bolts if overlap is on
			if self.overlap:
				for i in range(2):
					yield

			already_hit.add(Point(target.x, target.y))

			def can_arc(p, prev):
				if p in already_hit:
					return False
				if not self.caster.level.can_see(prev.x, prev.y, p.x, p.y):
					return False

				u = self.caster.level.get_unit_at(p.x, p.y)
				if u and are_hostile(self.caster, u):
					return True

				if u and not are_hostile(self.caster, u) and self.get_stat('shield'):
					return True

				c = self.caster.level.tiles[p.x][p.y].cloud
				if c and (type(c) in [StormCloud, BlizzardCloud]) and self.get_stat('weathercraft'):
					return True

				return False

			potential_targets = [p for p in self.caster.level.get_points_in_ball(target.x, target.y, self.get_stat('cascade_range')) if can_arc(p, target)]

			prev = target
			if potential_targets:
				target = random.choice(potential_targets)
			else:
				target = None


class DeathBolt(Spell):

	def on_init(self):
		self.name = "Death Bolt"
		self.tags = [Tags.Dark, Tags.Sorcery, Tags.Conjuration]
		self.level = 1
		self.damage = 9
		self.element = Tags.Dark
		self.range = 8
		self.max_charges = 18

		self.upgrades['damage'] = (12, 3)
		self.upgrades['max_charges'] = (10, 2)
		self.upgrades['minion_damage'] = (9, 3)

		self.upgrades['wither'] = (1, 2, "Withering", "被死亡之箭伤害的非 [living] 单位失去等量的生命上限。")
		self.upgrades['soulbattery'] = (1, 7, "Soul Battery", "每当死亡之箭击杀 [living] 目标时，永久获得 1 点伤害。")

		self.can_target_empty = False
		self.minion_damage = 5

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and Tags.Living in unit.tags:
			# Queue the skeleton raise as the first spell to happen after the damage so that it will pre-empt stuff like ghostfire
			self.caster.level.queue_spell(self.try_raise(self.caster, unit))
		damage = self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Dark, self)
		if unit and damage and self.get_stat('wither') and Tags.Living not in unit.tags:
			unit.max_hp -= damage
			unit.max_hp = max(unit.max_hp, 1)
		if unit and not unit.is_alive() and Tags.Living in unit.tags and self.get_stat('soulbattery'):
			self.damage += 1

	def try_raise(self, caster, unit):
		if unit and unit.cur_hp <= 0 and not self.caster.level.get_unit_at(unit.x, unit.y):
			skeleton = raise_skeleton(caster, unit, source=self)
			if skeleton:
				skeleton.spells[0].damage += self.get_stat('minion_damage') - 5
			yield

	def get_description(self):
		return ("对一个目标造成 [{damage}_点黑暗:dark] 伤害。\n"
				"击杀的 [living] 单位复活为骷髅。\n"
				"复活的骷髅生命上限与被击杀的单位相同，近战攻击造成 [{minion_damage}_点物理:physical] 伤害。\n"
				"飞行单位的骷髅可飞行。").format(**self.fmt_dict())

class DeathrouletteStack(Buff):

	def on_init(self):
		self.name = "Roulette"
		self.stack_type = STACK_INTENSITY
		self.color = Tags.Dark.color

class WheelOfFate(Spell):

	def on_init(self):
		self.name = "Wheel of Death"
		self.damage = 200
		self.range = 0
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.element = Tags.Dark
		self.level = 4
		self.max_charges = 5

		self.upgrades['max_charges'] = (3, 4)
		self.upgrades['cascade'] = (1, 7, "Death Roulette", "击杀时获得一层轮盘增益，持续 10 回合。\n你施放死亡之轮时每有一层轮盘增益，便额外击中一个敌人。")

	def cast(self, x, y):

		num_targets = 1 + len([b for b in self.owner.buffs if isinstance(b, DeathrouletteStack)])
		prev_hit = set()

		for i in range(num_targets):
			valid_targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(self.caster, u) and u not in prev_hit]
			if not valid_targets:
				return
			target = random.choice(valid_targets)
			prev_hit.add(target)
			target.deal_damage(self.get_stat('damage'), self.element, self)
			if self.get_stat('cascade') and not target.is_alive():
				self.owner.apply_buff(DeathrouletteStack(), self.get_stat('duration', 10))
			for i in range(3):
				yield

	def get_description(self):
		return "随机对一个敌方单位造成 [{damage}_点黑暗:dark] 伤害。".format(**self.fmt_dict())

class TouchOfDeath(Spell):

	def on_init(self):
		self.damage = 200
		self.element = Tags.Dark
		self.range = 1
		self.melee = True
		self.can_target_self = False
		self.max_charges = 9
		self.name = "Touch of Death"
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.level = 2

		self.can_target_empty = False

		self.fire_damage = 0
		self.arcane_damage = 0
		self.physical_damage = 0
		self.upgrades['arcane_damage'] = (150, 1, "Voidtouch", "死亡之触还造成 150 点 [arcane] 伤害。")
		self.upgrades['fire_damage'] = (150, 1, "Flametouch", "死亡之触还造成 150 点 [fire] 伤害。")
		self.upgrades['physical_damage'] = (150, 1, "Wrathtouch", "死亡之触还造成 150 点 [physical] 伤害。")
		self.upgrades['raise_raven'] = (1, 2, 'Touch of the Raven', '当 [living] 目标死于死亡之触时，它复活为友方的乌鸦。', 'raising')
		self.upgrades['raise_vampire'] = (1, 4, 'Touch of the Vampire', '当 [living] 目标死于死于死亡之触时，它复活为友方的吸血鬼。', 'raising')
		self.upgrades['raise_reaper']= (1, 6, 'Touch of the Reaper', '当 [living] 目标死于死于死亡之触时，它复活为友方的死神，持续 6 回合。', 'raising')

	def get_vamp(self):
		vamp = Vampire()
		apply_minion_bonuses(self, vamp)
		vamp.buffs[0].spawner = self.get_vamp_bat
		return vamp

	def get_vamp_bat(self):
		bat = VampireBat()
		apply_minion_bonuses(self, bat)
		bat.buffs[0].spawner = self.get_vamp
		return bat

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)
		if self.get_stat('arcane_damage'):
			self.caster.level.deal_damage(x, y, self.get_stat('arcane_damage'), Tags.Arcane, self)
		if self.get_stat('fire_damage'):
			self.caster.level.deal_damage(x, y, self.get_stat('fire_damage'), Tags.Fire, self)
		if self.get_stat('physical_damage'):
			self.caster.level.deal_damage(x, y, self.get_stat('physical_damage'), Tags.Physical, self)

		if unit and not unit.is_alive() and Tags.Living in unit.tags:
			if self.get_stat('raise_vampire'):
				vampire = self.get_vamp()
				self.summon(vampire, Point(unit.x, unit.y))
				unit.has_been_raised = True
			elif self.get_stat('raise_reaper'):
				reaper = Reaper()
				reaper.turns_to_death = self.get_stat('minion_duration', base=6)
				self.summon(reaper, Point(unit.x, unit.y))
				unit.has_been_raised = True
			elif self.get_stat('raise_raven'):
				hag = Raven()
				apply_minion_bonuses(self, hag),
				self.summon(hag, Point(unit.x, unit.y))
				unit.has_been_raised = True


	def get_description(self):
		return "对近战射程内的一个单位造成 [{damage}_点黑暗:dark]。".format(**self.fmt_dict())

class SealedFateBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell
		self.name = "Sealed Fate"
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'sealed_fate']

	def on_applied(self, owner):
		self.color = Tags.Dark.color

	def on_advance(self):
		if self.turns_left == 1:
			self.owner.deal_damage(self.spell.get_stat('damage'), Tags.Dark, self.spell)

			if self.spell.get_stat('spreads'):
				possible_targets = [u for u in self.owner.level.get_units_in_los(self.owner) if u != self.owner and are_hostile(u, self.spell.owner)]
				if possible_targets:
					target = random.choice(possible_targets)
					target.apply_buff(SealedFateBuff(self.spell), self.spell.get_stat('delay'))

class SealFate(Spell):

	def on_init(self):
		self.name = "Seal Fate"
		self.range = 8
		self.max_charges = 13
		self.tags = [Tags.Enchantment, Tags.Dark]
		self.level = 3
		self.delay = 4

		self.stats.append('delay')

		self.damage = 160
		self.upgrades['range'] = 7
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "封印命运施放无需视线。")
		self.upgrades['damage'] = (80, 2)
		self.upgrades['spreads'] = (1, 2, "Spreading Curse", "当封印命运的持续期满时，它随机跳向视线内一个敌人。")

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(SealedFateBuff(self), self.get_stat('delay'))

	def get_description(self):
		return "[{delay}_回合:duration] 后，对目标敌人造成 [{damage}_点黑暗:dark] 伤害。".format(**self.fmt_dict())

class Volcano(Spell):

	def on_init(self):
		self.name = "Volcanic Eruption"
		self.tags = [Tags.Fire]
		self.max_charges = 5
		self.radius = 6
		self.damage = 46
		self.element = Tags.Fire
		self.flow_range = 3

		self.cast_on_walls = True

		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 4
		self.range = 10

		self.upgrades['flow_range'] = (2, 3)
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "火山术施放无需视线。")
		self.upgrades['damage'] = (24, 3)
		self.upgrades['wall_cast']= (1, 4, "Wallcano", "除了虚空，火山术也可以墙为目标。如此作会将墙变为虚空。")

	def get_description(self):
		return ("在虚空中生成 [{radius}_格:radius] 冲程的岩浆。\n"
				"岩浆从虚空喷出至多 [{flow_range}_格:radius]。\n"
				"岩浆造成 [{damage}_点火焰:fire] 伤害。").format(**self.fmt_dict())

	def get_chasm_points(self, caster, x, y):
		chasm_points = set([Point(x, y)])

		for i in range(self.radius):
			for point in list(chasm_points):
				for adj in self.caster.level.get_points_in_ball(point.x, point.y, 1):
					tile = self.caster.level.tiles[adj.x][adj.y]
					if tile.is_chasm or (tile.is_wall() and self.get_stat('wall_cast')):
						chasm_points.add(adj)

		return chasm_points

	def get_impacted_tiles(self, x, y):
		aoe = set(self.get_chasm_points(self.caster, x, y))
		for i in range(self.get_stat('flow_range')):
			for point in set(aoe):
				for adj in self.caster.level.get_points_in_ball(point.x, point.y, 1):
					if self.caster.level.tiles[adj.x][adj.y].can_see:
						aoe.add(adj)
		return aoe

	def cast(self, x, y):
		aoe = set(self.get_chasm_points(self.caster, x, y))

		for point in aoe:
			if self.get_stat('wall_cast') and self.caster.level.tiles[point.x][point.y].is_wall():
				self.caster.level.make_chasm(point.x, point.y)
			self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
		yield
		for i in range(self.get_stat('flow_range')):
			for point in set(aoe):
				for adj in self.caster.level.get_points_in_ball(point.x, point.y, 1):
					if self.caster.level.tiles[adj.x][adj.y].can_see and adj not in aoe:
						self.caster.level.deal_damage(adj.x, adj.y, self.get_stat('damage'), self.element, self)
						aoe.add(adj)
			yield

	def can_cast(self, x, y):
		tile = self.caster.level.tiles[x][y]
		if self.get_stat('wall_cast'):
			if not tile.is_chasm and not tile.is_wall():
				return False
		else:
			if not tile.is_chasm:
				return False

		return Spell.can_cast(self, x, y)

class SoulSwap(Spell):

	def on_init(self):
		self.requires_los = False
		self.range = RANGE_GLOBAL

		self.name = "Soul Swap"

		self.max_charges = 9

		self.level = 2
		self.tags = [Tags.Dark, Tags.Sorcery, Tags.Translocation]

		self.upgrades['forced_transfer'] = (1, 2, 'Forced Transfer', '灵魂换位也可以敌方不死 [undead] 单位为目标。')
		self.upgrades['max_charges'] = (9, 2)

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if Tags.Undead not in unit.tags:
			return False
		if are_hostile(self.caster, unit) and not self.get_stat('forced_transfer'):
			return False
		if not self.caster.level.can_move(self.caster, x, y, teleport=True, force_swap=True):
			return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		if self.caster.level.can_move(self.caster, x, y, teleport=True, force_swap=True):
			self.caster.level.act_move(self.caster, x, y, teleport=True, force_swap=True)

	def get_description(self):
		return "与一个友方的 [undead] 单位换位。"

class UnderworldPortal(Spell):

	def on_init(self):
		self.requires_los = False
		self.range = 99
		self.name = "Underworld Passage"
		self.max_charges = 3
		self.tags = [Tags.Dark, Tags.Sorcery, Tags.Translocation]
		self.level = 3
		self.imps_summoned = 0

		self.upgrades['max_charges'] = 3

	def get_description(self):
		return ("传送到虚空旁的地块上。\n"
				"只能在虚空旁施放此咒语。")

	def can_cast(self, x, y):

		if not self.caster.level.can_stand(x, y, self.caster):
			return False

		for center in [self.caster, Point(x, y)]:
			next_to_chasm = False
			for p in self.caster.level.get_points_in_ball(center.x, center.y, 1.5, diag=True):
				if self.caster.level.tiles[p.x][p.y].is_chasm:
					next_to_chasm = True
					break
			if not next_to_chasm:
				return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		old_loc = Point(self.caster.x, self.caster.y)
		self.caster.level.act_move(self.caster, x, y, teleport=True)

		for point in [old_loc, self.caster]:
			for i in range(self.get_stat('imps_summoned')):
				p = self.caster.level.get_summon_point(point.x, point.y, sort_dist=False)
				if p:
					imp = random.choice([FireImp(), SparkImp(), IronImp()])
					imp.max_hp += self.get_stat('minion_health')
					imp.spells[0].damage += self.get_stat('minion_damage')
					imp.team = self.caster.team
					self.summon(imp, p)

class VoidSpawn(Spell):

	def on_init(self):

		self.name = "Void Spawning"
		self.max_charges = 10
		self.tags = [Tags.Arcane, Tags.Conjuration]
		self.level = 2

		self.minion_duration = 10

		self.upgrades['minion_duration'] = 10
		self.upgrades['requires_los'] = -1

	def get_description(self):
		return "召唤一个虚空孵卵者，持续 10 回合。虚空孵卵者是能召唤虚空轰炸者的固定 [arcane] 单位。"

	def get_impacted_tiles(self, x, y):
		targets = self.caster.level.get_tiles_in_ball(x, y, 1.5)
		targets = set(t for t in targets if t.can_walk and not t.unit)
		return targets

	def cast_instant(self, x, y):

		voidspawner = VoidSpawner()
		voidspawner.team = self.caster.team
		voidspawner.turns_to_death = self.get_stat('minion_duration')
		self.summon(voidspawner, Point(x, y))


class SummonEarthElemental(Spell):

	def on_init(self):
		self.tags = [Tags.Nature, Tags.Conjuration]
		self.name = "Earthen Sentinel"
		self.max_charges = 5
		self.level = 3
		self.minion_damage = 20
		self.minion_health = 120
		self.minion_duration = 15
		self.minion_attacks = 1
		self.upgrades['minion_damage'] = (15, 3)
		self.upgrades['minion_health'] = (80, 3)

		self.upgrades['earthquake_totem'] = (1, 6, "Earthquake Totem", "大地哨兵获得你的地震术，有 3 回合冷却。", "totem")
		self.upgrades['stinging_totem'] = (1, 5, "Stinging Totem", "大地哨兵获得你的毒刺术。", "totem")
		self.upgrades['holy_totem'] = (1, 7, "Holy Totem", "大地哨兵获得你的天堂冲击，有 2 回合冷却。", "totem")

		self.must_target_empty = True

	def can_cast(self, x, y):
		tile = self.caster.level.tiles[x][y]
		return tile.unit is None and tile.can_walk and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		ele = Unit()
		ele.name = "Earth Elemental"
		ele.sprite.char = 'E'
		ele.sprite.color = Color(190, 170, 140)
		ele.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage'), attacks=self.get_stat('minion_attacks')))
		ele.max_hp = self.get_stat('minion_health')
		ele.turns_to_death = self.get_stat('minion_duration')
		ele.stationary = True
		ele.resists[Tags.Physical] = 50
		ele.resists[Tags.Fire] = 50
		ele.resists[Tags.Lightning] = 50
		ele.tags = [Tags.Elemental]

		spell = None
		if self.get_stat('earthquake_totem'):
			spell = EarthquakeSpell()
			spell.cool_down = 3
		if self.get_stat('stinging_totem'):
			spell = PoisonSting()
		if self.get_stat('holy_totem'):
			spell = HolyBlast()
			spell.cool_down = 2

		if spell:
			spell.statholder = self.caster
			spell.max_charges = 0
			ele.spells.insert(0, spell)

		self.summon(ele, target=Point(x, y))

	def get_description(self):
		return ("召唤一个大地元素。\n"
				"大地元素有 [{minion_health}_点生命:minion_health]、[50_点物理:physical] 抗性、[50_点火焰:fire] 抗性、[50_点闪电:lightning] 抗性，无法移动。\n"
				"大地元素的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。"
				"大地元素在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())


class CallSpirits(Spell):

	def on_init(self):
		self.tags = [Tags.Dark, Tags.Conjuration, Tags.Sorcery]
		self.name = "Ghostball"
		self.radius = 1
		self.minion_damage = 1
		self.minion_health = 4
		self.minion_duration = 14
		self.max_charges = 6
		self.level = 3
		self.damage = 11

		self.upgrades['radius'] = (1, 3)
		self.upgrades['minion_duration'] = (15, 2)
		self.upgrades['minion_damage'] = (3, 3)

		self.upgrades['king'] = (1, 5, "Ghost King", "在幽灵球的中心召唤一个幽灵国王。", "center summon")
		self.upgrades['mass'] = (1, 4, "Ghost Mass", "在幽灵球的中心召唤一个幽灵团块。", "center summon")

	def cast_instant(self, x, y):

		points = self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))
		for point in points:
			unit = self.caster.level.tiles[point.x][point.y].unit
			if unit is None and self.caster.level.tiles[point.x][point.y].can_see:
				ghost = Ghost()
				if point.x == x and point.y == y:
					if self.get_stat('king'):
						ghost = GhostKing()
					elif self.get_stat('mass'):
						ghost = GhostMass()

				ghost.turns_to_death = self.get_stat('minion_duration')
				apply_minion_bonuses(self, ghost)
				self.summon(ghost, point)

			elif unit and are_hostile(unit, self.caster):
				unit.deal_damage(self.get_stat('damage'), Tags.Dark, self)

	def get_description(self):
		return ("在 [{radius}_格:radius] 半径内的所有敌方单位造成 [{damage}_点黑暗:dark] 伤害。\n"
				"在半径内的空地块上召唤幽灵。\n"
				"幽灵有 [{minion_health}_点生命:minion_health] 和 [100_点物理:physical] 抗性和 [50_点黑暗:dark] 抗性，可飞行，可被动扑闪。\n"
				"幽灵的近战攻击造成 [{minion_damage}_点黑暗:dark] 伤害。\n"
				"幽灵在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [p for p in self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))]

class MysticMemory(Spell):

	def on_init(self):
		self.tags = [Tags.Arcane]
		self.name = "Mystic Memory"
		self.max_charges = 1
		self.level = 6
		self.range = 0

		self.upgrades['max_charges'] = (1, 2)

	def cast_instant(self, x, y):
		spells = [s for s in self.caster.spells if s != self and s.cur_charges == 0]
		if spells:
			choice = random.choice(spells)
			choice.cur_charges = choice.get_stat('max_charges')

	def can_cast(self, x, y):
		if not [s for s in self.caster.spells if s != self and s.cur_charges == 0]:
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return "随机一种已无充能的其他咒语补满充能。"

class ConjureMemories(Spell):

	def on_init(self):
		self.tags = [Tags.Arcane, Tags.Conjuration]
		self.name = "Conjure Memories"
		self.max_charges = 1
		self.range = 0
		self.level = 4

		self.charges_regained = 1
		self.upgrades['charges_regained'] = (1, 2)
		self.upgrades['max_charges'] = (1, 2)

	def get_description(self):
		return "你的所有其他 [conjuration] 咒语各获得一个充能。"

	def cast_instant(self, x, y):

		for s in self.caster.spells:

			if s == self:
				continue

			if Tags.Conjuration not in s.tags:
				continue

			s.cur_charges += self.get_stat('charges_regained')
			s.cur_charges = min(s.get_stat('max_charges'), s.cur_charges)


class WovenSorceryBuff(Buff):

	def on_applied(self, owner):
		self.name = "Woven"
		self.color = Tags.Sorcery.color
		self.tag_bonuses[Tags.Sorcery]['damage'] = 3*len([s for s in owner.spells if Tags.Enchantment in s.tags])
		self.tag_bonuses[Tags.Sorcery]['duration'] = len([s for s in owner.spells if Tags.Sorcery in s.tags])
		self.tag_bonuses[Tags.Enchantment]['damage'] = 3*len([s for s in owner.spells if Tags.Enchantment in s.tags])
		self.tag_bonuses[Tags.Enchantment]['duration'] = len([s for s in owner.spells if Tags.Sorcery in s.tags])
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'woven']

class WovenSorcerySpell(Spell):

	def on_init(self):
		self.max_charges = 4
		self.duration = 20
		self.name = "Weave Sorcery"
		self.tags = [Tags.Sorcery, Tags.Enchantment]
		self.level = 4
		self.range = 0
		self.upgrades['duration'] = (20, 3)

	def get_description(self):
		return "你的 [sorcery] 和 [enchantment] 咒语获得增益：你每习得一种 [enchantment] 咒语便 +3 点伤害，每习得一种 [sorcery] 咒语便 +1 持续回合。持续 20 回合。"

	def cast_instant(self, x, y):
		self.caster.apply_buff(WovenSorceryBuff(), self.get_stat('duration'))

class PermenanceBuff(Buff):

	def on_init(self):
		' '
		self.global_bonuses['minion_duration'] = 5
		self.global_bonuses['duration'] = 5
		self.name = "Permanence"
		self.color = Tags.Enchantment.color
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'permenance']

class Permenance(Spell):

	def on_init(self):
		self.max_charges = 4
		self.duration = 20
		self.name = "Permanence"
		self.tags = [Tags.Enchantment]
		self.level = 4
		self.range = 0
		self.upgrades['duration'] = (20, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(PermenanceBuff(), self.get_stat('duration'))

	def get_description(self):
		return ("你的咒语和临时召唤物额外持续 [5_回合:duration]。\n"
				"此效果持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class DeathGazeSpell(Spell):

	def on_init(self):
		self.name = "Death Gaze"
		self.range = 0
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.level = 4
		self.max_charges = 10
		self.damage = 4
		self.element = Tags.Dark

		self.upgrades['damage'] = (4, 3)
		self.upgrades['max_charges'] = (6, 2)
		self.upgrades['vampiric'] = (1, 4, "Vampiric Gaze", "每个友方单位获得治疗，数量为造成的伤害量。")

	def get_description(self):
		return ("每个友方单位随机对其视线内的一个敌人造成 [{damage}_点黑暗:dark] 伤害。").format(**self.fmt_dict())

	def cast(self, x, y):
		bolts = []
		for unit in self.caster.level.units:
			if unit == self.caster or self.caster.level.are_hostile(self.caster, unit):
				continue

			possible_targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(unit, u) and self.caster.level.can_see(unit.x, unit.y, u.x, u.y)]
			if possible_targets:
				target = random.choice(possible_targets)
				bolts.append(self.bolt(unit, target))

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield

	def bolt(self, source, target):

		for point in Bolt(self.caster.level, source, target):
			# TODO- make a flash using something other than deal_damage
			self.caster.level.deal_damage(point.x, point.y, 0, self.element, self)
			yield True

		damage = self.get_stat('damage')
		dealt = target.deal_damage(damage, self.element, self)
		if dealt:
			source.deal_damage(-dealt, Tags.Heal, self)
		yield False

class BoneBarrageSpell(Spell):

	def on_init(self):
		self.name = "Bone Barrage"
		self.range = 14
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.level = 4
		self.max_charges = 7

		self.upgrades['beam'] = (1, 6, "Bone Spears", "白骨弹幕对从小兵到目标一束上的所有目标造成伤害。")
		self.upgrades['dark'] = (1, 5, "Cursed Bones", "白骨弹幕还造成一次 [dark] 伤害。")
		self.upgrades['animation'] = (1, 7, "Shambler Assembly", "白骨弹幕可以空地块为目标。\n若如此，在该地块上生成一个白骨蹒跚者，其生命为造成的伤害。")

	def can_cast(self, x, y):
		u = self.owner.level.get_unit_at(x, y)
		if not u and not self.get_stat('animation'):
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return ("目标视线内所有你的召唤的友军受到其生命一半的 [physical] 伤害。\n"
				"每个受影响的友军对目标造成等量 [physical] 伤害。")

	def get_impacted_tiles(self, x, y):
		start = Point(x, y)
		yield start
		for u in self.caster.level.get_units_in_los(start):
			if not are_hostile(u, self.caster) and u != self.caster:
				yield u
				if self.get_stat('beam'):
					for p in self.caster.level.get_points_in_line(u, Point(x, y), find_clear=True):
						yield p

	def cast(self, x, y):
		bolts = []
		target = self.caster.level.get_unit_at(x, y)

		total_damage = 0
		for u in self.caster.level.get_units_in_los(Point(x, y)):
			if u == self.caster:
				continue
			if are_hostile(u, self.caster):
				continue
			if u.resists[Tags.Physical] >= 100:
				continue

			half_hp = math.ceil(u.cur_hp / 2)
			damage = u.deal_damage(half_hp, Tags.Physical, self)
			total_damage += damage

			if damage > 0:
				bolts.append(self.bolt(u, Point(x, y), damage))

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield

		if not target and self.get_stat('animation') and total_damage:
			monster = BoneShambler(total_damage)
			self.summon(monster, target=Point(x, y))

	def hit(self, target, damage):
		target.deal_damage(damage, Tags.Physical, self)
		if self.get_stat('dark'):
			target.deal_damage(damage, Tags.Dark, self)

	def bolt(self, source, target, damage):

		for point in Bolt(self.caster.level, source, target):

			self.caster.level.projectile_effect(point.x, point.y, proj_name='bone_arrow', proj_origin=source, proj_dest=target)
			yield True

			unit = self.caster.level.get_unit_at(point.x, point.y)
			if self.get_stat('beam') and unit:
				self.hit(unit, damage)

		unit = self.caster.level.get_unit_at(target.x, target.y)
		if unit:
			self.hit(unit, damage)
		yield False


class InvokeSavagerySpell(Spell):

	def on_init(self):
		self.name = "Invoke Savagery"
		self.range = 0
		self.tags = [Tags.Nature, Tags.Sorcery]
		self.level = 2
		self.max_charges = 11
		self.damage = 14
		self.duration = 2

		self.upgrades['damage'] = (9, 2)
		self.upgrades['duration'] = (1, 2)

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster and not are_hostile(u, self.caster)]

	def cast(self, x, y):

		attack = SimpleMeleeAttack(damage=self.get_stat('damage'), buff=Stun, buff_duration=self.get_stat('duration'))

		for unit in self.caster.level.units:
			if unit == self.caster or are_hostile(self.caster, unit):
				continue
			if Tags.Living not in unit.tags:
				continue

			possible_targets = [u for u in self.caster.level.get_units_in_ball(unit, radius=1, diag=True) if are_hostile(u, self.caster)]
			if possible_targets:
				target = random.choice(possible_targets)
				attack.statholder = unit
				attack.caster = unit
				self.caster.level.act_cast(unit, attack, target.x, target.y, pay_costs=False)
				yield

	def get_description(self):
		return ("每个 [living] 友军随机攻击其近战射程内的一个敌方单位。\n"
				"攻击造成 [{damage}_点物理:physical]，施加 [{duration}_回合:duration] 的 [stun]。").format(**self.fmt_dict())

class MagicMissile(Spell):

	def on_init(self):
		self.name = "Magic Missile"
		self.range = 12
		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.level = 1

		self.damage = 11
		self.damage_type = Tags.Arcane

		self.max_charges = 20
		self.shield_burn = 0

		self.upgrades['max_charges'] = (15, 2)
		self.upgrades['damage'] = (10, 3)
		self.upgrades['range'] = (5, 1)
		self.upgrades['shield_burn'] = (3, 1, "Shield Burn", "魔法飞弹造成伤害前先移除目标至多 3 点护盾。")

		self.upgrades['slaughter'] = (1, 4, "Slaughter Bolt", "若魔法飞弹以 [living] 单位为目标，改为造成 [poison]、[dark] 和 [physical] 伤害，而非 [arcane]。", 'bolt')
		self.upgrades['holy'] = (1, 4, "Holy Bolt", "若魔法飞弹以 [undead] 单位为目标，除 [arcane] 伤害还额外造成 [holy] 伤害。", 'bolt')
		self.upgrades['disruption'] = (1, 6, "Disruption Bolt", "若魔法飞弹以 [arcane] 单位为目标，改为造成 [dark] 和 [holy] 伤害，而非 [arcane]。", 'bolt')


	def cast(self, x, y):
		dtypes = [Tags.Arcane]
		unit = self.caster.level.get_unit_at(x, y)

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			self.caster.level.show_effect(p.x, p.y, Tags.Arcane, minor=True)

		if unit:
			if self.get_stat('shield_burn'):
				unit.shields -= self.get_stat('shield_burn')
				unit.shields = max(unit.shields, 0)

			if self.get_stat('slaughter') and Tags.Living in unit.tags:
				dtypes = [Tags.Poison, Tags.Dark, Tags.Physical]
			if self.get_stat('disruption') and Tags.Arcane in unit.tags:
				dtypes = [Tags.Holy, Tags.Dark]
			if self.get_stat('holy') and (Tags.Undead in unit.tags or Tags.Demon in unit.tags):
				dtypes = [Tags.Holy, Tags.Arcane]

		for dtype in dtypes:
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype, self)
			if len(dtypes)> 1:
				for i in range(4):
					yield

	def get_description(self):
		return "对目标造成 [{damage}_点奥术:arcane] 伤害。".format(**self.fmt_dict())

class MindDevour(Spell):

	def on_init(self):
		self.name = "Devour Mind"
		self.range = 4
		self.tags = [Tags.Arcane, Tags.Dark, Tags.Sorcery]
		self.max_charges = 7
		self.level = 3

		self.damage = 25
		self.threshold = .5

		self.requires_los = False

		self.upgrades['damage'] = (18, 3)
		self.upgrades['spiriteater'] = (1, 4, "Spirit Eater", "能以 [demon] 和 [arcane] 单位为目标。")
		self.upgrades['gluttony'] = (1, 2, "Gluttony", "若吞噬心灵消灭目标，充能费用得到返还。")

		self.charges_gained = 1


	def get_description(self):
		return ("对一个敌方单位造成 [{damage}_点奥术:arcane] 伤害。\n"
				"然后若目标的生命低于 50%，额外对其造成 [{damage}_点黑暗:dark] 伤害。\n"
				"只能以 [living] 单位为目标。").format(**self.fmt_dict())

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False

		if not are_hostile(self.caster, unit):
			return False

		if Tags.Living in unit.tags:
			return Spell.can_cast(self, x, y)

		if self.get_stat('spiriteater') and (Tags.Demon in unit.tags or Tags.Arcane in unit.tags):
			return Spell.can_cast(self, x, y)

		return False

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)

		if not unit:
			return

		self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Arcane, self)

		if unit.cur_hp / unit.max_hp < .5:
			for i in range(3):
				yield

			self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Dark, self)

		if self.get_stat('gluttony') and not unit.is_alive():
			self.cur_charges += 1
			self.cur_charges = min(self.cur_charges, self.get_stat('max_charges'))

class DeathShock(Spell):

	def on_init(self):
		self.name = "Death Shock"
		self.range = 9
		self.tags = [Tags.Sorcery, Tags.Dark, Tags.Lightning]
		self.max_charges = 9
		self.level = 4
		self.damage = 17
		self.cascade_range = 4
		self.num_targets = 3

		self.can_target_empty = False

		self.upgrades['damage'] = (7, 3)
		self.upgrades['cascade_range'] = (5, 2)
		self.upgrades['infinite_bounces'] = (1, 4, "Infinite Cascades", "死亡冲击不限倾泻次数。")

	def get_description(self):
		return ("对目标造成 [{damage}_点闪电:lightning] 伤害和 [{damage}_点黑暗:dark] 伤害。\n"
				"若击杀目标，此效果随机跳向视线至多 [{cascade_range}_格:range] 的敌人。\n"
				"至多可击中 [{num_targets}_个目标:num_targets]。").format(**self.fmt_dict())

	def cast(self, x, y):

		unit = self.caster.level.get_unit_at(x, y)
		first_time = True
		targets_hit = 0
		delay = 5
		while unit or first_time:

			if targets_hit >= self.get_stat('num_targets') and not self.get_stat('infinite_bounces'):
				break

			for dtype in [Tags.Lightning, Tags.Dark]:
				target_point = Point(x, y) if first_time else unit
				self.caster.level.deal_damage(target_point.x, target_point.y, self.get_stat('damage'), dtype, self)
				for i in range(delay):
					yield
			if unit and unit.cur_hp <= 0:
				candidates = self.caster.level.get_units_in_los(unit)
				candidates = [c for c in candidates if are_hostile(c, self.caster)]
				candidates = [c for c in candidates if distance(c, unit) <= self.get_stat('cascade_range')]
				if candidates:
					unit = random.choice(candidates)
				else:
					unit = None
			else:
				unit = None

			# Speed up near the end to prevent waiting
			targets_hit += 1
			if targets_hit > 3:
				delay = max(2, delay - targets_hit // 4)
			if targets_hit > 100:
				delay = 1
			first_time = False

class MeltBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.resists[Tags.Physical] = -100
		if self.spell.get_stat('ice_resist'):
			self.resists[Tags.Ice] = -100
		self.stack_type = STACK_DURATION
		self.color = Color(255, 100, 100)
		self.name = "Armor Melted"
		self.buff_type = BUFF_TYPE_CURSE

class MeltSpell(Spell):

	def on_init(self):
		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 2
		self.max_charges = 15
		self.name = "Melt"
		self.damage = 22
		self.element = Tags.Fire
		self.range = 6
		self.duration = 3

		self.can_target_empty = False

		self.upgrades['damage'] = (16, 2)
		self.upgrades['max_charges'] = 10
		self.upgrades['ice_resist'] = (1, 3, "Ice Penetration", "熔化术还降低 100 [ice] 抗性。")

	def cast_instant(self, x, y):

		self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(MeltBuff(self), self.get_stat('duration'))

	def get_description(self):
		return "目标单位受到 [{damage}_点火焰:fire] 伤害，失去 [100_点物理:physical] 抗性。".format(**self.fmt_dict())

class DragonRoarBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Dragon Roar"
		self.color = Tags.Dragon.color
		self.stack_type = STACK_INTENSITY
		self.buff_type = BUFF_TYPE_BLESS

	def on_applied(self, owner):

		owner.cur_hp += self.spell.get_stat('hp_bonus')
		owner.max_hp += self.spell.get_stat('hp_bonus')

		for spell in owner.spells:

			if hasattr(spell, 'damage'):
				spell.damage += self.spell.get_stat('damage')

			if isinstance(spell, BreathWeapon):
				spell.cool_down -= 1
				spell.cool_down = max(0, spell.cool_down)

	def on_unapplied(self):

		self.owner.max_hp -= self.spell.get_stat('hp_bonus')
		self.owner.cur_hp = min(self.owner.max_hp, self.owner.cur_hp)

		for spell in self.owner.spells:

			if hasattr(spell, 'damage'):
				spell.damage -= self.spell.get_stat('damage')

			if isinstance(spell, BreathWeapon):
				spell.cool_down += 1
				spell.cool_down = max(0, spell.cool_down)

class DragonRoarSpell(Spell):

	def on_init(self):
		self.name = "Dragon Roar"
		self.tags = [Tags.Dragon, Tags.Nature, Tags.Enchantment]
		self.max_charges = 2
		self.level = 6
		self.range = 0

		self.hp_bonus = 25
		self.damage = 12

		self.duration = 25

		self.upgrades['hp_bonus'] = (20, 3)
		self.upgrades['max_charges'] = (1, 2)

		self.cooldown_reduction = 1
		self.stats.append('cooldown_reduction')

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if Tags.Dragon not in unit.tags:
				continue

			if are_hostile(unit, self.caster):
				continue

			unit.apply_buff(DragonRoarBuff(self), self.get_stat('duration'))


	def get_description(self):
		return "所有友方巨龙获得 [{hp_bonus}_点生命上限:minion_health] 和 [{damage}:damage] 点攻击伤害，冷却降低 [{cooldown_reduction}_回合:duration]。\n持续 [{duration}_回合:duration]。".format(**self.fmt_dict())

class IronSkinBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.name = "Ironized"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'protection']

	def on_init(self):
		for tag in [Tags.Physical, Tags.Fire, Tags.Lightning]:
			self.resists[tag] = self.spell.get_stat('resist')
		if self.spell.get_stat('resist_arcane'):
			self.resists[Tags.Arcane] = self.spell.get_stat('resist')

	def on_applied(self, owner):
		if Tags.Metallic not in self.owner.tags:
			self.nonmetal = True
			self.owner.tags.append(Tags.Metallic)
		else:
			self.nonmetal = False

	def on_unapplied(self):
		if self.nonmetal:
			self.owner.tags.remove(Tags.Metallic)

class ProtectMinions(Spell):

	def on_init(self):
		self.name = "Ironize"
		self.resist = 50
		self.duration = 10
		self.max_charges = 5
		self.level = 3

		self.tags = [Tags.Enchantment, Tags.Conjuration, Tags.Metallic]
		self.range = 0

		self.resist_arcane = 0
		self.upgrades['resist'] = (25, 2)
		self.upgrades['duration'] = 15
		self.upgrades['resist_arcane'] = (1, 2, "Arcane Insulation")

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if unit == self.caster:
				continue
			if self.caster.level.are_hostile(unit, self.caster):
				continue
			unit.apply_buff(IronSkinBuff(self), self.get_stat('duration'))
			unit.deal_damage(0, Tags.Physical, self)

	def get_description(self):
		return ("所有友方单位获得 [{resist}_点物理:physical] 抗性、[{resist}_点火焰:fire] 抗性和 [{resist}_点闪电:lightning] 抗性，变为 [metallic]。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class WordOfUndeath(Spell):

	def on_init(self):
		self.name = "Word of Undeath"
		self.duration = 4
		self.tags = [Tags.Dark, Tags.Word]
		self.element = Tags.Dark
		self.level = 7
		self.max_charges = 1
		self.range = 0

		self.upgrades['max_charges'] = (1, 2)

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]

	def get_description(self):
		return ("所有 [undead] 单位的当前生命和生命上限翻倍。\n"
				"施法者之外的所有其他单位失去一半的当前生命和生命上限。").format(**self.fmt_dict())

	def cast(self, x, y):
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if unit.is_player_controlled:
				continue
			if Tags.Undead in unit.tags:
				unit.max_hp *= 2
				unit.deal_damage(-unit.cur_hp, Tags.Heal, self)
			else:
				unit.cur_hp //= 2
				unit.cur_hp = max(1, unit.cur_hp)
				unit.max_hp //= 2
				unit.max_hp = max(1, unit.max_hp)
				self.owner.level.show_effect(unit.x, unit.y, Tags.Dark, minor=False)
				yield

class WordOfChaos(Spell):

	def on_init(self):
		self.name = "Word of Chaos"
		self.damage = 45
		self.duration = 6
		self.range = 0

		self.tags = [Tags.Chaos, Tags.Word]
		self.level = 7
		self.max_charges = 1

		self.upgrades['max_charges'] = (1, 2)
		self.upgrades['damage'] = (20, 2)

	def get_description(self):
		return ("[Stun] 所有敌人 [{duration}_回合:duration]，随机将其传送到新的地块。"
				"\n对所有 [fire] 敌人造成 [{damage}_点闪电:lightning] 伤害。"
				"\n对所有 [lightning] 敌人造成 [{damage}_点火焰:fire] 伤害。"
				"\n所有敌方 [construct] 失去所有 [physical] 抗性，受到 [{damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [u for u in self.owner.level.units if u != self.caster]

	def cast(self, x, y):
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if not self.caster.level.are_hostile(self.caster, unit):
				continue

			teleport_targets = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_stand(t.x, t.y, unit)]
			if not teleport_targets:
				continue

			teleport_target = random.choice(teleport_targets)

			self.caster.level.act_move(unit, teleport_target.x, teleport_target.y, teleport=True)
			unit.apply_buff(Stun(), self.get_stat('duration'))

			if Tags.Construct in unit.tags:
				unit.resists[Tags.Physical] = 0
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
			if Tags.Lightning in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)
			if Tags.Fire in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
			yield

class WordOfBeauty(Spell):

	def on_init(self):
		self.name = "Word of Beauty"
		self.damage = 25
		self.duration = 7
		self.range = 0
		self.tags = [Tags.Holy, Tags.Lightning, Tags.Word]
		self.level = 7
		self.max_charges = 1

		self.upgrades['max_charges'] = (1, 2)
		self.upgrades['damage'] = (17, 1)

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]

	def get_description(self):
		return ("完全治疗你和所有 [living] 单位。"
				"\n对所有 [demon] 和 [undead] 单位造成 [{damage}_点闪电:lightning] 伤害。"
				"\n[Stun] 所有 [arcane] 单位 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast(self, x, y):
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if unit.is_player_controlled or Tags.Living in unit.tags:
				unit.deal_damage(-unit.max_hp, Tags.Heal, self)
			if Tags.Demon in unit.tags or Tags.Undead in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
			if Tags.Arcane in unit.tags:
				unit.deal_damage(0, Tags.Physical, self)
				unit.apply_buff(Stun(), self.get_stat('duration'))
			yield

class WordOfMadness(Spell):

	def on_init(self):
		self.name = "Word of Madness"
		self.duration = 5
		self.tags = [Tags.Word, Tags.Dark, Tags.Chaos]
		self.level = 7
		self.max_charges = 1

		self.duration = 5
		self.range = 0

		self.upgrades['max_charges'] = (1, 2)
		self.upgrades['duration'] = (4, 5)

	def get_description(self):
		return ("除施法者外的所有单位 [Berserk] [{duration}_回合:duration]。\n"
				"对所有 [construct] 单位造成其当前生命一半的 [dark] 伤害。\n"
				"完全治疗所有 [demon] 单位。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]

	def cast(self, x, y):
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if unit == self.caster:
				continue
			unit.apply_buff(BerserkBuff(), self.get_stat('duration'))
			if Tags.Construct in unit.tags:
				unit.deal_damage(unit.cur_hp // 2, Tags.Dark, self)
			if Tags.Demon in unit.tags:
				unit.deal_damage(-unit.max_hp, Tags.Heal, self)
			yield

class SummonFloatingEye(Spell):

	def on_init(self):
		self.name = "Floating Eye"
		self.minion_duration = 4
		self.tags = [Tags.Eye, Tags.Arcane, Tags.Conjuration]
		self.level = 5
		self.max_charges = 6

		ex = FloatingEye()

		self.minion_health = ex.max_hp
		self.shields = ex.shields

		self.minion_duration = 16

		self.upgrades['minion_duration'] = (16, 2)
		self.upgrades['max_charges'] = (2, 3)

		self.must_target_empty = True

	def cast_instant(self, x, y):
		eye = FloatingEye()
		eye.spells = []
		eye.team = TEAM_PLAYER
		eye.max_hp += self.get_stat('minion_health')
		eye.turns_to_death = self.get_stat('minion_duration')

		p = self.caster.level.get_summon_point(x, y, flying=True)
		if p:
			# Ensure point exists before having the eye cast eye spells
			self.summon(eye, p)

			for spell in self.caster.spells:
				if Tags.Eye in spell.tags and spell != self:
					# Temporarily change caster of spell
					spell = type(spell)()
					spell.caster = eye
					spell.owner = eye
					spell.statholder = self.caster
					self.caster.level.act_cast(eye, spell, eye.x, eye.y, pay_costs=False)

	def get_description(self):
		return ("召唤一个漂浮之眼\n"
				"漂浮之眼有 [{minion_health}_点生命:minion_health]、[{shields}_点护盾:shields]，浮在空中，可被动扑闪。\n"
				"漂浮之眼自身无攻击方式，可施放召唤时你习得的 [eye] 咒语。\n"
				"漂浮之眼在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

class FarmiliarBuff(Buff):

	def __init__(self, summoner, tags):
		Buff.__init__(self)
		self.summoner = summoner
		self.tags = tags
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):

		if evt.caster != self.summoner:
			return

		if Tags.Sorcery not in evt.spell.tags:
			return

		has_tag = False
		for tag in self.tags:
			if tag in evt.spell.tags:
				has_tag = True

		if not has_tag:
			return

		spell = type(evt.spell)()
		spell.cur_charges = 1
		spell.caster = self.owner
		spell.owner = self.owner
		spell.statholder = self.summoner

		if spell.can_cast(evt.x, evt.y):
			self.owner.level.act_cast(self.owner, spell, evt.x, evt.y)


class ChimeraFarmiliar(Spell):

	def on_init(self):
		self.name = "Chimera Familiar"
		self.tags = [Tags.Chaos, Tags.Conjuration]
		self.level = 4
		self.max_charges = 2
		self.minion_health = 20
		self.minion_damage = 6
		self.minion_range = 4
		self.minion_resists = 0
		self.dark_casting = 0
		self.arcane_casting = 0
		self.nature_casting = 0
		self.minion_resists = 50
		self.upgrades['minion_resists'] = (50, 2)
		self.upgrades['max_charges'] = (2, 3)
		self.upgrades['nature_casting'] = (1, 1, "Nature Mimicry", "奇美拉还会模仿 [nature] [sorcery] 咒语。")
		self.upgrades['dark_casting'] = (1, 1, "Dark Mimicry", "奇美拉还会模仿 [dark] [sorcery] 咒语。")
		self.upgrades['arcane_casting'] = (1, 1, "Arcane Mimicry", "奇美拉还会模仿 [arcane] [sorcery] 咒语。")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_tags(self):
		tags = [Tags.Fire, Tags.Lightning, Tags.Chaos]
		if self.get_stat('dark_casting'):
			tags.append(Tags.Dark)
		if self.get_stat('nature_casting'):
			tags.append(Tags.Nature)
		if self.get_stat('arcane_casting'):
			tags.append(Tags.Arcane)
		return tags

	def get_description(self):
		tagstr = ' or '.join(t.name for t in self.get_tags())
		return ("召唤一个奇美拉佣兽\n"
				"奇美拉的攻击造成 [{minion_damage}_点火焰:fire] 和 [{minion_damage}_点闪电:lightning] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
			    "若你施放的 %s [sorcery] 咒语的目标在奇美拉的射程和实现内，它会模仿该咒语。"
			    % ' 或 '.join('[' + t.name.lower() + ']' for t in self.get_tags())).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		chimera = Unit()
		chimera.name = "Chimera"
		chimera.sprite.char = 'C'
		chimera.sprite.color = Tags.Sorcery.color
		chimera.max_hp = self.get_stat('minion_health')
		b1 = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Lightning)
		b1.cool_down = 2
		b2 = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Fire)
		b2.cool_down = 2
		chimera.spells.append(b1)
		chimera.spells.append(b2)
		chimera.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
		chimera.resists[Tags.Fire] = self.get_stat('minion_resists')
		chimera.resists[Tags.Lightning] = self.get_stat('minion_resists')
		chimera.buffs.append(FarmiliarBuff(self.caster, self.get_tags()))
		chimera.team = TEAM_PLAYER
		chimera.tags = [Tags.Living, Tags.Arcane]

		self.summon(chimera, Point(x, y))


class ArcLightning(Spell):

	def on_init(self):
		self.name = "Arc Lightning"
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.max_charges = 5
		self.level = 4
		self.num_targets = 3
		self.friendly_fire = 1

		self.damage = 16
		self.element = Tags.Lightning
		self.range = 8

		self.upgrades['num_targets'] = (3, 4)
		self.upgrades['damage'] = (9, 4)
		self.upgrades['cascade'] = (1, 5, "Echo Flash", "每个初始电弧目标触发的第二个电束分别造成一半的伤害，击晕一半的持续回合。")

	def get_description(self):
		return ("闪电从目标地块向 [{num_targets}_个:num_targets] 可见敌人弧动。\n"
				"每道电弧对一束上的所有单位造成 [{damage}_点闪电:lightning] 伤害。").format(**self.fmt_dict())

	def cast(self, x, y, is_echo=False):
		center_unit = self.caster.level.get_unit_at(x, y)

		if not center_unit or self.friendly_fire or self.caster.level.are_hostile(center_unit, self.caster):
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)
			yield 1

		targets = set(t for t in self.caster.level.get_units_in_los(Point(x, y)) if self.caster.level.are_hostile(t, self.caster))
		chosen_targets = []
		for i in range(self.get_stat('num_targets')):
			if not targets:
				break

			target = targets.pop()
			chosen_targets.append(target)

			for p in self.caster.level.get_points_in_line(Point(x, y), target, find_clear=True)[1:]:

				if not self.friendly_fire:
					unit = self.caster.level.get_unit_at(p.x, p.y)
					if unit and not self.caster.level.are_hostile(unit, self.caster):
						continue

				damage = self.get_stat('damage')
				if is_echo:
					damage //= 2
				self.caster.level.deal_damage(p.x, p.y, damage, self.element, self)

			yield 1

		if self.get_stat('cascade') and not is_echo:
			recursions = [self.cast(t.x, t.y, is_echo=True) for t in chosen_targets]
			while recursions:
				recursions = [r for r in recursions if next(r)]
				yield 1

		yield 0

class PoisonSting(Spell):

	def on_init(self):
		self.name = "Poison Sting"
		self.tags = [Tags.Sorcery, Tags.Nature]
		self.max_charges = 20
		self.duration = 30
		self.damage = 9
		self.range = 12
		self.level = 1

		self.upgrades['range'] = (4, 1)
		self.upgrades['max_charges'] = (10, 3)
		self.upgrades['duration'] = (60, 2)
		self.upgrades['antigen'] = (1, 2, "Acidity", "受伤的目标失去所有 [poison] 抗性。")

	def cast_instant(self, x, y):
		damage = self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Physical, self)

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			self.caster.level.show_effect(p.x, p.y, Tags.Poison, minor=True)

		unit = self.caster.level.get_unit_at(x, y)
		if unit and damage and self.get_stat('antigen'):
			unit.apply_buff(Acidified())
		if unit and unit.resists[Tags.Poison] < 100:
			unit.apply_buff(Poison(), self.get_stat('duration'))

	def get_description(self):
		return ("对目标单位造成 [{damage}_点物理:physical] 伤害。\n"
				"该单位 [poisoned] [{duration}_回合:duration]。\n"
				+ text.poison_desc).format(**self.fmt_dict())

class Flameblast(Spell):

	def on_init(self):
		self.name = "Fan of Flames"
		self.tags = [Tags.Sorcery, Tags.Fire]
		self.max_charges = 18
		self.damage = 9
		self.element = Tags.Fire
		self.range = 5
		self.angle = math.pi / 6.0
		self.level = 2
		self.can_target_self = False
		self.requires_los = False
		self.melt_walls = 0
		self.max_channel = 10

		self.upgrades['damage'] = (7, 3)
		self.upgrades['range'] = (2, 3)
		self.upgrades['max_charges'] = (10, 3)
		#self.upgrades['channel'] = (1, 2, "Channeling", "Fan of Flames can be channeled for up to 10 turns")
		self.channel = 1

	def get_description(self):
		return ("对锥形范围内的所有单位造成 [{damage}_点火焰:fire]。\n"
				"此咒语可引导至多 [{max_channel}_回合:duration]。引导时每回合重复此效果。").format(**self.fmt_dict())

	def aoe(self, x, y):
		origin = get_cast_point(self.caster.x, self.caster.y, x, y)
		target = Point(x, y)
		return Burst(self.caster.level,
				     Point(self.caster.x, self.caster.y),
				     self.get_stat('range'),
				     burst_cone_params=BurstConeParams(target, self.angle),
				     ignore_walls=self.get_stat('melt_walls'))

	def cast(self, x, y, channel_cast=False):

		if self.get_stat('channel') and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		for stage in self.aoe(x, y):
			for point in stage:
				if self.get_stat('melt_walls') and self.caster.level.tiles[point.x][point.y].is_wall():
					self.caster.level.make_floor(point.x, point.y)
				if point.x == self.caster.x and point.y == self.caster.y:
					continue
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
			yield

	def get_impacted_tiles(self, x, y):
		return [p for stage in self.aoe(x, y) for p in stage]

class SummonBlueLion(Spell):

	def on_init(self):
		self.name = "Blue Lion"
		self.tags = [Tags.Nature, Tags.Holy, Tags.Conjuration, Tags.Arcane]
		self.max_charges = 2
		self.level = 5
		self.minion_health = 28
		self.minion_damage = 7
		self.shield_max = 2
		self.shield_cooldown = 3

		self.upgrades['shield_max'] = (2, 4)
		self.upgrades['shield_cooldown'] = (-1, 2)
		self.upgrades['minion_damage'] = (9, 2)
		self.upgrades['holy_bolt'] = (1, 4, "Holy Bolt", "蓝色狮子的近战攻击替换为射程为 6 的神圣弹攻击。")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		lion = Unit()
		lion.name = "Blue Lion"
		lion.team = self.caster.team
		lion.sprite.char = 'L'
		lion.sprite.color = Color(100, 120, 255)
		lion.max_hp = self.get_stat('minion_health')

		lion.flying = True

		sheen_spell = ShieldSightSpell(self.get_stat('shield_cooldown'), self.get_stat('shield_max'))
		sheen_spell.name = "Blue Lion Sheen"

		lion.spells.append(sheen_spell)

		if self.get_stat('holy_bolt'):
			bolt = SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Holy, range=6 + self.get_stat('minion_range'))
			bolt.name = "Blue Lion Bolt"
			lion.spells.append(bolt)
		else:
			lion.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))


		lion.tags = [Tags.Nature, Tags.Arcane, Tags.Holy]
		lion.resists[Tags.Arcane] = 50
		lion.resists[Tags.Physical] = 50

		self.summon(lion, Point(x, y))


	def get_description(self):
		return ("召唤一个蓝色狮子。\n"
				"蓝色狮子有 [{minion_health}_点生命:minion_health]、[50_点奥术:arcane] 抗性和 [50_点物理:physical] 抗性，可飞行。\n"			
				"蓝色狮子有一种咒语，给自身和其视线内所有友军 [1_点护盾:shield] ，上限为 [{shield_max}_点护盾:shield]，冷却 [{shield_cooldown}_回合:duration]。\n"
				"蓝色狮子的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())


class DeathCleaveBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.stack_type = STACK_DURATION
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'death_cleave']
		self.color = Tags.Dark.color

	def on_init(self):
		self.name = "Death Cleave"
		self.description = "若咒语消灭主目标，会分裂向附近的目标。"
		self.cur_target = None
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		self.cur_target = evt.caster.level.get_unit_at(evt.x, evt.y)
		self.owner.level.queue_spell(self.effect(evt))

	def show_fizzle(self, center):
		points = list(self.owner.level.get_adjacent_points(center, filter_walkable=False))
		random.shuffle(points)
		for p in points:
			if p == center:
				continue
			etype = random.choice([Tags.Arcane, Tags.Dark])
			self.owner.level.show_effect(p.x, p.y, etype, minor=True)
			if random.random() < .5:
				yield

	def effect(self, evt):
		if self.cur_target and not self.cur_target.is_alive():

			def can_cleave(t):
				if not evt.caster.level.are_hostile(t, evt.caster):
					return False
				if not evt.spell.can_cast(t.x, t.y):
					return False
				if distance(t, self.cur_target) > self.spell.get_stat('cascade_range'):
					return False
				return True

			cleave_targets = [u for u in evt.caster.level.units if can_cleave(u)]

			if cleave_targets:
				target = random.choice(cleave_targets)
				yield

				# Draw chain
				for p in self.owner.level.get_points_in_line(self.cur_target, target)[:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)

				evt.caster.level.act_cast(evt.caster, evt.spell, target.x, target.y, pay_costs=False)
			# If no cleavable targets exist, show a fizzling out effect on the last target
			else:
				evt.caster.level.queue_spell(self.show_fizzle(evt.caster))

		elif self.cur_target and self.cur_target.is_alive():
			evt.caster.level.queue_spell(self.show_fizzle(self.cur_target))




class DeathCleaveSpell(Spell):

	def on_init(self):
		self.name = "Death Cleave"
		self.duration = 2
		self.upgrades['duration'] = (3, 3)
		self.upgrades['max_charges'] = (4, 2)
		self.upgrades['cascade_range'] = (3, 4)
		self.max_charges = 4
		self.cascade_range = 5
		self.range = 0
		self.level = 5
		self.tags = [Tags.Enchantment, Tags.Arcane, Tags.Dark]

	def cast_instant(self, x, y):
		self.caster.apply_buff(DeathCleaveBuff(self), self.get_stat('duration') + 1) # +1 so as to not count the current turn

	def get_description(self):
		return ("每当你施放的咒语消灭主目标时，随机对目标附近 [{cascade_range}_格:cascade_range] 内一个有效目标再施放该咒语。\n"
		  		"此过程持续进行，直到目标存活或附近无有效目标。\n"
		  		"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class CantripCascade(Spell):

	def on_init(self):
		self.name = "Cantrip Cascade"
		self.level = 5
		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.max_charges = 3
		self.angle = math.pi / 6
		self.range = 7
		self.upgrades['max_charges'] = (3, 2)
		self.upgrades['range'] = (3, 3)

	def get_impacted_tiles(self, x, y):
		target = Point(x, y)
		burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
		return [p for stage in burst for p in stage if self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y)]


	def cast_instant(self, x, y):
		units = [self.caster.level.get_unit_at(p.x, p.y) for p in self.get_impacted_tiles(x, y)]
		enemies = [u for u in units if u and are_hostile(u, self.caster)]
		spells = [s for s in self.caster.spells if s.level == 1 and Tags.Sorcery in s.tags]

		pairs = list(itertools.product(enemies, spells))

		random.shuffle(pairs)

		for enemy, spell in pairs:
			self.caster.level.act_cast(self.caster, spell, enemy.x, enemy.y, pay_costs=False)

	def get_description(self):
		return ("对锥形范围内的每个敌人施放你的 1 级 [sorcery] 咒语。")

class MulticastBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.stack_type = STACK_DURATION  # This may be OP but its also awesome
		self.color = Tags.Arcane.color
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'multicast']


	def on_init(self):
		self.name = "Multicast"
		self.description = "每当你施放 [sorcery] 咒语，将其复制。"
		self.can_copy = True
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if evt.spell.item:
			return
		if Tags.Sorcery not in evt.spell.tags:
			return

		if self.can_copy:
			self.can_copy = False
			for i in range(self.spell.get_stat('copies')):
				if evt.spell.can_cast(evt.x, evt.y) and evt.spell.can_pay_costs():
					evt.caster.level.act_cast(evt.caster, evt.spell, evt.x, evt.y, pay_costs=False)
			evt.caster.level.queue_spell(self.reset())

	def reset(self):
		self.can_copy = True
		yield

class MulticastSpell(Spell):

	def on_init(self):
		self.name = "Multicast"
		self.duration = 3
		self.copies = 1
		self.max_charges = 3
		self.multi_conjure = 0
		self.upgrades['copies'] = (1, 4)
		self.upgrades['duration'] = (4, 3)
		self.upgrades['max_charges'] = (4, 2)
		self.range = 0
		self.level = 7
		self.tags = [Tags.Enchantment, Tags.Arcane]

	def cast_instant(self, x, y):
		self.caster.apply_buff(MulticastBuff(self), self.get_stat('duration') + 1)

	def get_description(self):
		return ("每当你施放 [sorcery] 咒语，将其复制。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class FaeCourt(Spell):

	def on_init(self):
		self.name = "Fae Court"
		self.num_summons = 5
		self.max_charges = 2
		self.heal = 5
		self.minion_range = 4
		self.minion_duration = 15
		self.minion_health = 9
		self.shields = 1

		self.minion_damage = 4

		self.range = 0

		self.level = 5

		self.tags = [Tags.Nature, Tags.Arcane, Tags.Conjuration]

		self.upgrades['num_summons'] = (5, 4)
		self.upgrades['heal'] = (8, 3)
		self.upgrades['shields'] = (1, 2)
		self.upgrades['summon_queen'] = (1, 7, "Summon Queen", "还召唤一个仙灵女王。")
		self.upgrades['glass_fae'] = (1, 9, "Glass Faery", "改为召唤玻璃仙灵，而非普通仙灵。")

	def get_description(self):
		return ("在施法者旁召唤 [{num_summons}:num_summons] 个仙灵。\n"
				"仙灵有 [{minion_health}_点生命:minion_health]、[{shields}_点护盾:shields]、[75_点奥术:arcane] 抗性，可飞行，可被动扑闪。\n"
			    "仙灵可治疗友军 [{heal}_点生命:heal]，射程为 [{minion_range}_格:minion_range]。\n"
			    "仙灵的远程攻击造成 [{minion_damage}_点奥术:arcane] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
			    "仙灵在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast(self, x, y):
		if self.get_stat('summon_queen'):
			p = self.caster.level.get_summon_point(self.caster.x, self.caster.y, sort_dist=False, flying=True, radius_limit=4)
			if p:
				unit = ThornQueen()
				unit.max_hp += self.minion_health - 9
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage += self.minion_damage - 4
				unit.turns_to_death = self.get_stat('minion_duration')
				self.summon(unit, p)


		for i in range(self.get_stat('num_summons')):

			unit = Unit()
			unit.sprite.char = 'f'
			unit.sprite.color = Color(252, 141, 249)

			unit.flying = True
			unit.max_hp = self.get_stat('minion_health')
			unit.shields = self.get_stat('shields')
			unit.buffs.append(TeleportyBuff(chance=.5))
			unit.spells.append(HealAlly(heal=self.get_stat('heal'), range=self.get_stat('minion_range') + 2))

			unit.turns_to_death = self.get_stat('minion_duration')
			unit.team = self.caster.team
			unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living]
			unit.resists[Tags.Arcane] = 50

			if self.get_stat('glass_fae'):
				glassbolt = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Arcane, effect=Tags.Glassification, buff=GlassPetrifyBuff, buff_duration=1)
				glassbolt.name = "Glassification Bolt"
				unit.spells.append(glassbolt)
				unit.name = "Glass Faery"
				unit.asset_name = "faery_glass"
				unit.tags.append(Tags.Glass)
			else:
				unit.name = "Good Faery"
				unit.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Arcane))

			self.summon(unit, sort_dist=False)
			yield

class RingOfSpiders(Spell):

	def on_init(self):

		self.name = "Ring of Spiders"
		self.duration = 10
		self.range = 8

		self.level = 5
		self.max_charges = 2

		self.damage = 0
		self.aether_spiders = 0

		self.minion_health = 14
		self.minion_damage = 2

		self.upgrades['damage'] = (32, 3)
		self.upgrades['minion_health'] = (10, 2)
		self.upgrades['aether_spiders'] = (1, 6)

		self.tags = [Tags.Nature, Tags.Conjuration]

	def get_description(self):
		return ("在目标旁召唤一圈巨型蜘蛛，外面再绕一圈蛛网。\n"
			 	"阻挡蜘蛛的单位 [poisoned] [{duration}_回合:duration]，阻挡蛛网的单位 [stunned] [1_回合:duration]。\n"
			 	"巨型蜘蛛有 [{minion_health}_点生命:minion_health]，可吐蛛网。\n"
			 	"巨型蜘蛛的近战攻击造成 [{minion_damage}_点物理:physical]，施加 [5_回合:duration] 的 [poison]。\n"
			 	"蛛网 [stun] 步入的非 [spider] 单位 [1_回合:duration]。\n"
			 	+ text.poison_desc + text.stun_desc).format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_rect(x-2, y-2, x+2, y+2)

	def cast(self, x, y):

		for p in self.get_impacted_tiles(x, y):
			unit = self.caster.level.get_unit_at(p.x, p.y)

			rank = max(abs(p.x - x), abs(p.y - y))

			if rank == 0:
				if self.get_stat('damage'):
					self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Poison, self)
			elif rank == 1:
				if not unit:
					if self.get_stat('aether_spiders'):
						spider = PhaseSpider()
					else:
						spider = GiantSpider()
					spider.team = self.caster.team

					spider.spells[0].damage = self.get_stat('minion_damage')
					spider.max_hp = self.get_stat('minion_health')

					self.summon(spider, p)

				if unit:
					unit.apply_buff(Poison(), self.get_stat('duration'))
			else:
				if not unit:
					cloud = SpiderWeb()
					cloud.owner = self.caster
					self.caster.level.add_obj(cloud, *p)
				if unit:
					unit.apply_buff(Stun(), 1)
			yield

class HolyBlast(Spell):

	def on_init(self):

		self.name = "Heavenly Blast"
		self.range = 7
		self.radius = 1
		self.damage = 7

		self.damage_type = Tags.Holy

		self.max_charges = 14

		self.level = 2

		self.tags = [Tags.Holy, Tags.Sorcery]

		self.upgrades['range'] = (3, 2)
		self.upgrades['radius'] = (1, 2)
		self.upgrades['damage'] = (9, 3)
		self.upgrades['max_charges'] = (7, 2)
		self.upgrades['spiritbind'] = (1, 6, "Spirit Bind", "在击杀的敌人处生成临时的灵魂。灵魂是闪烁的 [undead] 生物，有 4 点生命，远程 [holy] 攻击造成 2 点伤害。")
		self.upgrades['shield'] = (1, 3, "Shield", "受影响的友方单位获得 2 点护盾，上限为 5。")
		self.upgrades['echo_heal'] = (1, 4, "Echo Heal", "每回合再次治疗受影响的友方单位，数量为初始值的一半，持续 5 回合。")

	def get_description(self):
		return "对 [{radius}_格:radius] 冲程内一束上的所有敌人造成 [{damage}_点神圣:holy] 伤害，所有友军治疗 [{damage}_点生命:heal]。".format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		burst = set(p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage)
		beam = set(Bolt(self.caster.level, self.caster, Point(x, y)))
		return burst.union(beam)

	def get_ai_target(self):
		enemy = self.get_corner_target(1)
		if enemy:
			return enemy
		else:
			allies = [u for u in self.caster.level.get_units_in_ball(self.caster, self.get_stat('range')) if u != self.caster and not are_hostile(self.caster, u) and not u.is_player_controlled]
			allies = [u for u in allies if self.caster.level.can_see(self.caster.x, self.caster.y, u.x, u.y)]
			allies = [u for u in allies if u.cur_hp < u.max_hp]
			if allies:
				return random.choice(allies)
		return None

	def cast(self, x, y):
		target = Point(x, y)

		def deal_damage(point):
			unit = self.caster.level.get_unit_at(point.x, point.y)
			if unit and not are_hostile(unit, self.caster) and not unit == self.caster and unit != self.statholder:
				unit.deal_damage(-self.get_stat('damage'), Tags.Heal, self)
				if self.get_stat('shield'):
					if unit.shields < 4:
						unit.add_shields(2)
					elif unit.shields == 4:
						unit.add_shields(1)
				if self.get_stat('echo_heal'):
					unit.apply_buff(RegenBuff(self.get_stat('damage') // 2), 5)
			elif unit == self.caster:
				pass
			elif unit and unit.is_player_controlled and not are_hostile(self.caster, unit):
				pass
			else:
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Holy, self)
				if unit and not unit.is_alive() and self.get_stat('spiritbind'):
					spirit = Unit()
					spirit.name = "Spirit"
					spirit.asset_name = "holy_ghost" # temp
					spirit.max_hp = 4
					spirit.spells.append(SimpleRangedAttack(damage=2, damage_type=Tags.Holy, range=3))
					spirit.turns_to_death = 7
					spirit.tags = [Tags.Holy, Tags.Undead]
					spirit.buffs.append(TeleportyBuff())
					apply_minion_bonuses(self, spirit)
					spirit.resists[Tags.Holy] = 100
					spirit.resists[Tags.Dark] = -100
					spirit.resists[Tags.Physical] = 100
					self.summon(spirit, target=unit)

		points_hit = set()
		for point in Bolt(self.caster.level, self.caster, target):
			deal_damage(point)
			points_hit.add(point)
			yield

		stagenum = 0
		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				if point in points_hit:
					continue
				deal_damage(point)

			stagenum += 1
			yield

class HolyFlame(Spell):

	def on_init(self):
		self.name = "Holy Fire"

		self.tags = [Tags.Fire, Tags.Holy, Tags.Sorcery]

		self.max_charges = 7

		self.damage = 22
		self.duration = 3
		self.lightning = 0
		self.cascade_range = 0
		self.radius = 2

		self.range = 7

		self.upgrades['duration'] = (3, 3)
		self.upgrades['damage'] = (14, 3)
		self.upgrades['radius'] = (2, 2)

		self.level = 3

	def get_description(self):
		return ("在一竖线上造成 [{damage}_点火焰:fire] 伤害，在一横线上造成 [{damage}_点神圣:holy] 伤害。\n"
				"[Stun] 影响区域内的所有 [demon] 和 [undead] 单位。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		rad = self.get_stat('radius')
		for i in range(-rad, rad + 1):
			yield Point(x+i, y)
			if i != 0:
				yield Point(x, y+i)

	def cast(self, x, y):
		cur_target = Point(x, y)
		dtypes = [Tags.Holy, Tags.Fire]
		if self.get_stat('lightning'):
			dtypes.append(Tags.Lightning)

		rad = self.get_stat('radius')
		for i in range(y - rad, y + rad + 1):
			if not self.caster.level.is_point_in_bounds(Point(x, i)):
				continue

			self.caster.level.deal_damage(x, i, self.get_stat('damage'), Tags.Fire, self)
			unit = self.caster.level.get_unit_at(x, i)
			if unit and (Tags.Demon in unit.tags or Tags.Undead in unit.tags):
				unit.apply_buff(Stun(), self.get_stat('duration'))
			yield

		for i in range(2):
			yield

		for i in range(x - rad, x + rad + 1):
			if not self.caster.level.is_point_in_bounds(Point(i, y)):
				continue

			self.caster.level.deal_damage(i, y, self.get_stat('damage'), Tags.Holy, self)
			unit = self.caster.level.get_unit_at(i, y)
			if unit and (Tags.Demon in unit.tags or Tags.Undead in unit.tags):
				unit.apply_buff(Stun(), self.get_stat('duration'))
			yield


class AngelSong(Spell):

	def on_init(self):
		self.name = "Sing"
		self.description = "治疗 [living] 和 [holy] 单位，对 [undead]、[demon] 和 [dark] 单位造成 [holy] 和 [fire] 伤害。"
		self.radius = 5
		self.damage = 2
		self.heal = 1
		self.range = 0

	def cast_instant(self, x, y):
		for unit in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius')):
			if unit.is_player_controlled:
				continue
			if (Tags.Living in unit.tags or Tags.Holy in unit.tags) and unit.cur_hp < unit.max_hp:
				unit.deal_damage(-self.get_stat('heal'), Tags.Heal, self)
			if Tags.Dark in unit.tags or Tags.Undead in unit.tags or Tags.Demon in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)
				unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)

	def get_ai_target(self):
		units = self.caster.level.get_units_in_ball(self.caster, self.get_stat('radius'))

		for unit in units:
			if unit.is_player_controlled:
				continue
			if (Tags.Living in unit.tags or Tags.Holy in unit.tags) and unit.cur_hp < unit.max_hp:
				return self.caster
			if Tags.Undead in unit.tags or Tags.Demon in unit.tags or Tags.Dark in unit.tags:
				return self.caster
		return None

class AngelicChorus(Spell):

	def on_init(self):
		self.name = "Choir of Angels"

		self.minion_health = 10
		self.shields = 1
		self.minion_duration = 10
		self.num_summons = 3
		self.heal = 1
		self.minion_damage = 2
		self.radius = 5

		self.range = 7

		self.tags = [Tags.Holy, Tags.Conjuration]
		self.level = 3

		self.max_charges = 5

		self.upgrades['shields'] = (2, 2)
		self.upgrades['num_summons'] = (3, 4)
		self.upgrades['minion_duration'] = (10, 2)
		self.upgrades['heal'] = (2, 3)

	def get_description(self):
		return ("召唤含有 [{num_summons}:num_summons] 个天使歌手的唱诗班。\n"
				"天使歌手有 [{minion_health}_点生命:minion_health]、[{shields}_点护盾:shields]、50% [fire] 和 [holy] 抗性、 100% [dark] 抗性。\n"
				"天使歌手的歌唱在 [{radius}_格:radius] 半径内对所有 [undead]、[demon] 和 [dark] 单位造成 [{minion_damage}_点火焰:fire] 和 [{minion_damage}_点神圣:holy] 伤害。"
				"治疗歌唱半径内的 [Living] 和 [holy] 单位 [{heal}_点生命:heal]。施法者无法以此法被治疗。\n"
				"天使歌手在 [{minion_duration}:minion_duration] 回合后消失。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [Point(x, y)]

	def cast(self, x, y):

		for i in range(self.get_stat('num_summons')):
			angel = Unit()
			angel.name = "Angelic Singer"
			angel.max_hp = self.get_stat('minion_health')
			angel.shields = self.get_stat('shields')

			song = AngelSong()
			song.damage = self.get_stat('minion_damage')
			song.heal = self.get_stat('heal')
			song.radius = self.get_stat('radius')

			angel.spells.append(song)

			angel.flying = True
			angel.tags = [Tags.Holy]
			angel.resists[Tags.Holy] = 50
			angel.resists[Tags.Fire] = 50
			angel.resists[Tags.Dark] = 100

			angel.sprite.char = 'a'
			angel.sprite.color = Tags.Holy.color

			angel.turns_to_death = self.get_stat('minion_duration')

			self.summon(angel, Point(x, y))
			yield

class HeavensWrath(Spell):

	def on_init(self):

		self.name = "Heaven's Wrath"

		self.num_targets = 3

		self.damage = 22

		self.level = 6
		self.max_charges = 4

		self.stun_duration = 0

		self.upgrades['culling'] = (1, 3, "Culling", "天堂之怒还对当前生命最低的单位造成伤害。")
		self.upgrades['damage'] = (11, 3)
		self.upgrades['stun_duration'] = (3, 3)

		self.tags = [Tags.Holy, Tags.Lightning, Tags.Sorcery]
		self.range = 0

	def get_description(self):
		return ("对当前生命最高的 [{num_targets}_个单位:num_targets] 造成 [{damage}_点闪电:lightning] 伤害和 [{damage}_点神圣:holy] 伤害。\n"
				"不以友方单位或大门为目标。").format(**self.fmt_dict())

	def cast(self, x, y):

		orders = [-1]
		if self.get_stat('culling'):
			orders.append(1)

		for order in orders:
			units = [u for u in self.caster.level.units if are_hostile(u, self.caster) and not u.is_lair]
			random.shuffle(units)
			units = sorted(units,  key=lambda u: order * u.cur_hp)
			units = units[:self.get_stat('num_targets')]

			for unit in units:
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
				for i in range(3):
					yield
				unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)
				for i in range(3):
					yield
				stun_duration = self.get_stat('stun_duration')
				if stun_duration:
					unit.apply_buff(Stun(), stun_duration)

class BestowImmortality(Spell):

	def on_init(self):

		self.name = "Suspend Mortality"
		self.tags = [Tags.Dark, Tags.Holy, Tags.Enchantment]

		self.lives = 1
		self.duration = 40
		self.level = 3

		self.max_charges = 8

		self.requires_los = False
		self.range = 8

		self.upgrades['lives'] = (3, 2)

	def get_description(self):
		return "目标友方单位获得死亡时重生的能力，持续 [{duration}_回合:duration]。".format(**self.fmt_dict())

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		return unit and unit != self.caster

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(ReincarnationBuff(self.get_stat('lives')), self.get_stat('duration'))

class SoulTax(Spell):

	def on_init(self):

		self.name = "Soul Tax"

		self.level = 5
		self.range = 4

		self.tags = [Tags.Sorcery, Tags.Dark, Tags.Holy]
		self.max_charges = 4
		self.arcane = 0

		self.upgrades['max_charges'] = (3, 4)
		self.upgrades['range'] = (3, 2)
		self.upgrades['arcane'] = (1, 2, "Arcane Taxation", "灵魂税额外造成剩余生命三分之一的 [arcane] 伤害。")

	def get_description(self):
		return ("对目标单位造成当前生命三分之一的 [holy] 伤害，然后造成剩余生命三分之一的 [dark] 伤害。\n"
				"治疗施法者若干生命，数量为伤害总量。").format(**self.fmt_dict())

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if not are_hostile(self.caster, unit):
			return False
		return Spell.can_cast(self, x, y)

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return
		dtypes = [Tags.Holy, Tags.Dark]
		if self.get_stat('arcane'):
			dtypes.append(Tags.Arcane)
		for dtype in dtypes:
			damage = unit.cur_hp // 3
			dealt = unit.deal_damage(damage, dtype, self)
			self.caster.deal_damage(-dealt, Tags.Heal, self)
			for i in range(4):
				yield

			# if the units dead, stop
			if not unit.is_alive():
				return


class HolyShieldBuff(Buff):

	def __init__(self, resist):
		Buff.__init__(self)
		self.name = "Holy Armor"
		self.buff_type = BUFF_TYPE_BLESS
		for tag in [Tags.Fire, Tags.Lightning, Tags.Dark, Tags.Physical]:
			self.resists[tag] = resist


class HolyShieldSpell(Spell):

	def on_init(self):
		self.name = "Holy Armor"

		self.tags = [Tags.Holy, Tags.Enchantment]
		self.level = 3
		self.duration = 9
		self.resist = 50
		self.max_charges = 6

		self.upgrades['duration'] = (7 , 3)
		self.upgrades['resist'] = 25

		self.range = 0

	def cast_instant(self, x, y):
		self.caster.apply_buff(HolyShieldBuff(self.get_stat('resist')), self.get_stat('duration'))

	def get_description(self):
		return ("获得 [{resist}_点物理:physical] 抗性。\n"
				"获得 [{resist}_点火焰:fire] 抗性。\n"
				"获得 [{resist}_点闪电:lightning] 抗性。\n"
				"获得 [{resist}_点黑暗:dark] 抗性。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class BlindingLightSpell(Spell):

	def on_init(self):
		self.name = "Blinding Light"

		self.range = 0
		self.max_charges = 4
		self.duration = 4
		self.damage = 5

		self.tags = [Tags.Holy, Tags.Sorcery]
		self.level = 3
		self.dark_units = 0
		self.upgrades['damage'] = (9, 4)
		self.upgrades['duration'] = (4, 2)
		self.upgrades['dark_units'] = (1, 2, "Dark Units", "[Dark] 单位还会受到 [holy] 伤害。")



	def get_description(self):
		return ("[Blind] 施法者视线内的所有单位，持续 [{duration}_回合:duration]。\n"
				+ text.blind_desc +
				"对受影响的 [undead] 和 [demon] 单位造成 [{damage}_点神圣:holy] 伤害。").format(**self.fmt_dict())

	def cast(self, x, y):
		targets = [u for u in self.caster.level.get_units_in_los(self.caster) if u != self.caster]
		targets = sorted(targets, key=lambda u: distance(u, self.caster))

		for target in targets:
			target.apply_buff(BlindBuff(), self.get_stat('duration'))

			if not (Tags.Undead in target.tags or Tags.Demon in target.tags or (self.get_stat('dark_units') and Tags.Dark in target.tags)):
				continue
			target.deal_damage(self.get_stat('damage'), Tags.Holy, self)

			yield

class FlockOfEaglesSpell(Spell):

	def on_init(self):

		self.name = "Flock of Eagles"

		self.minion_health = 18
		self.minion_damage = 6
		self.minion_range = 5
		self.num_summons = 4
		self.shields = 0

		self.max_charges = 2

		self.upgrades['dive_attack'] = (1, 4, "Dive Attack", "鹰可进行俯冲攻击。")
		self.upgrades['num_summons'] = (2, 3)
		self.upgrades['shields'] = (2, 4)
		self.upgrades['thunderbirds'] = 1, 4, "Thunderbirds", "改为召唤雷鸟，而非鹰。雷鸟造成 [lightning] 伤害，有该抗性。"

		self.range = 0

		self.level = 5
		self.tags = [Tags.Conjuration, Tags.Nature, Tags.Holy]

	def get_description(self):
		return ("在施法者旁召唤 [{num_summons}_个鹰:num_summons]。\n"
				"鹰有 [{minion_health}_点生命:minion_health]，可飞行。\n"
				"鹰的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for i in range(self.get_stat('num_summons')):
			eagle = Unit()
			eagle.name = "Eagle"

			dive = LeapAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), is_leap=True)
			peck = SimpleMeleeAttack(damage=self.get_stat('minion_damage'))

			dive.name = 'Dive'
			peck.name = 'Claw'

			eagle.spells.append(peck)
			if self.get_stat('dive_attack'):
				eagle.spells.append(dive)
			eagle.max_hp = self.get_stat('minion_health')
			eagle.team = self.caster.team

			eagle.flying = True
			eagle.tags = [Tags.Living, Tags.Holy, Tags.Nature]

			eagle.shields = self.get_stat('shields')

			if self.get_stat('thunderbirds'):
				for s in eagle.spells:
					s.damage_type = Tags.Lightning
				eagle.tags.append(Tags.Lightning)
				eagle.resists[Tags.Lightning] = 100
				eagle.name = "Thunderbird"

			self.summon(eagle, Point(x, y))

class FlamingSwordSwing(Spell):

	def __init__(self, parent_spell):
		self.parent_spell = parent_spell
		Spell.__init__(self)

	def on_init(self):
		self.name = "Flaming Arc"
		self.description = "挥舞燃烧的剑。"
		self.range = 1.5
		self.melee = True
		self.can_target_self = False
		self.max_charges = 50

	def get_impacted_tiles(self, x, y):
		ball = self.caster.level.get_points_in_ball(x, y, 1)
		aoe = [p for p in ball if 1 <= distance(p, self.caster, diag=True) < 2]
		return aoe

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			for dtype in [Tags.Fire, Tags.Holy]:
				self.caster.level.deal_damage(p.x, p.y, self.parent_spell.get_stat('damage'), dtype, self)
				yield

class FlamingSwordBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.color = Tags.Holy.color
		self.name = "Flaming Sword"

	def on_applied(self, owner):
		self.spell_slot = self.owner.spells.index(self.spell)
		self.owner.spells[self.spell_slot] = FlamingSwordSwing(self.spell)

		# Hack
		self.owner.spells[self.spell_slot].caster = self.owner

	def on_unapplied(self):
		self.owner.spells[self.spell_slot] = self.spell

class FlamingSwordSpell(Spell):

	def on_init(self):

		self.name = "Flaming Sword"
		self.description = "挥舞燃烧的剑。剑砍向所有相邻的敌人，造成 [fire] 和 [holy] 伤害。"
		self.duration = 15
		self.max_charges = 4

		self.tags = [Tags.Holy, Tags.Fire, Tags.Enchantment]
		self.level = 2
		self.range = 0

		self.damage = 14

		self.upgrades['damage'] = (14, 4)
		self.upgrades['duration'] = (30, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(FlamingSwordBuff(self), self.get_stat('duration'))

class BeautyIdolBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_applied(self, owner):
		self.name = "Beauty"

	def on_advance(self):
		units = self.owner.level.get_units_in_los(self.owner)
		for u in units:
			if u == self.owner:
				continue

			if are_hostile(u, self.owner):
				u.deal_damage(1, Tags.Holy, self)
				if Tags.Undead in u.tags or Tags.Demon in u.tags:
					u.deal_damage(1, Tags.Lightning, self)

			elif not u.is_player_controlled:
				u.deal_damage(-self.spell.get_stat('heal'), Tags.Heal, self)

class HeavenlyIdol(Spell):

	def on_init(self):

		self.name = "Heavenly Idol"

		self.level = 5
		self.tags = [Tags.Holy, Tags.Lightning, Tags.Conjuration]
		self.max_charges = 4

		self.minion_health = 35
		self.shields = 2
		self.fire_gaze = 0
		self.heal = 1
		self.minion_duration = 15

		self.upgrades['shields'] = (5, 3)
		self.upgrades['fire_gaze'] = (1, 4, "Fire Gaze", "雕像可进行火束攻击。")
		self.upgrades['heal'] = (1, 3)
		self.upgrades['minion_duration'] = (15, 1)

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个美丽雕像。\n"
				"雕像有 [{minion_health}_点生命:minion_health] 和 [{shields}_点护盾:shields]，固定不动。\n"
				"雕像的被动光环每回合影响视线内的所有单位。\n"
				"治疗受影响的友军 [{heal}_点生命:heal]。施法者无法以此法被治疗。\n"
				"对受影响的敌军造成 [1_点神圣:holy] 伤害。\n"
				"对受影响的 [undead] 和 [demon] 单位额外造成 [1_点闪电:lightning] 伤害。\n"
				"雕像在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		idol = Unit()
		idol.sprite.char = 'I'
		idol.sprite.color = Tags.Construct.color
		idol.asset_name = "idol"
		idol.name = "Idol of Beauty"
		idol.asset_name = "heavenly_idol"

		idol.max_hp = self.get_stat('minion_health')
		idol.shields = self.get_stat('shields')
		idol.stationary = True

		idol.resists[Tags.Physical] = 75

		idol.tags = [Tags.Construct, Tags.Holy]

		idol.buffs.append(BeautyIdolBuff(self))
		idol.turns_to_death = self.get_stat('minion_duration')

		if self.get_stat("fire_gaze"):
			gaze = SimpleRangedAttack(damage=8, range=10, beam=True, damage_type=Tags.Fire)
			gaze.name = "Fiery Gaze"
			idol.spells.append(gaze)

		self.summon(idol, Point(x, y))

class GoldGuardian(Upgrade):

	def on_init(self):
		self.prereq = SummonGoldDrakeSpell
		self.name = "Golden Crusade"
		self.level = 2
		self.description = "每当你进入有 [undead] 或 [demon] 单位的裂隙时，免费获得黄金巨龙的一点充能。"
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_add

	def on_unit_add(self, evt):
		for u in self.owner.level.units:
			if Tags.Undead in u.tags or Tags.Demon in u.tags:
				if self.prereq.cur_charges < self.prereq.get_stat('max_charges'):
					self.prereq.cur_charges += 1
					return

class SummonGoldDrakeSpell(Spell):

	def on_init(self):
		self.name = "Gold Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Holy, Tags.Conjuration, Tags.Dragon]
		self.level = 6

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = 9
		self.minion_range = 7
		self.shields = 0

		self.upgrades['minion_health'] = (25, 2)
		self.upgrades['breath_damage'] = (12, 4)
		self.upgrades['dragon_mage'] = (1, 4, "Dragon Mage", "召唤的黄金巨龙可施放 8 回合冷却的治愈之光。\n此治愈之光获得你的所有升级和奖励。")
		self.add_upgrade(GoldGuardian())

		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = GoldDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')
		drake.shields += self.get_stat('shields')

		if self.get_stat('dragon_mage'):
			hlight = HealMinionsSpell()
			hlight.statholder = self.caster
			hlight.max_charges = 0
			hlight.cur_charges = 0
			hlight.cool_down = 8
			drake.spells.insert(1, hlight)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("召唤一个黄金巨龙\n"
				"黄金巨龙有 [{minion_health}_点生命:minion_health] 和 [100_点神圣:holy] 抗性，可飞行。\n"
				"黄金巨龙的吐息武器造成 [{breath_damage}_点神圣:holy] 伤害，治疗友军 [{breath_damage}_点生命:heal]。\n"
				"黄金巨龙的近战攻击造成 [{minion_damage}_点物理:physical] 伤害。").format(**self.fmt_dict())

class SeraphimSwordSwing(Spell):

	def on_init(self):
		self.name = "Flaming Sword"
		self.description = "在弧状范围造成伤害。\n造成 [fire] 和 [holy] 伤害。"
		self.range = 1.5
		self.melee = True
		self.can_target_self = False

		self.damage = 0  # to be overwritten
		self.damage_type = [Tags.Fire, Tags.Holy]  # for bloodlust

	def get_impacted_tiles(self, x, y):
		ball = self.caster.level.get_points_in_ball(x, y, 1, diag=True)
		aoe = [p for p in ball if 1 <= distance(p, self.caster, diag=True) < 2]
		return aoe

	def cast(self, x, y):
		dtypes = [Tags.Fire, Tags.Holy]
		if self.arcane:
			dtypes += [Tags.Arcane]
		for p in self.get_impacted_tiles(x, y):
			for dtype in dtypes:
				# Never hit friendly units, is angel
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit and not are_hostile(self.caster, unit):
					continue
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), dtype, self)
				yield

class SummonSeraphim(Spell):

	def on_init(self):
		self.name = "Call Seraph"
		self.range = 4
		self.max_charges = 4
		self.tags = [Tags.Holy, Tags.Fire, Tags.Conjuration]

		self.minion_health = 33
		self.shields = 3
		self.minion_damage = 14

		self.minion_duration = 14
		self.heal = 0

		self.upgrades['minion_damage'] = (10, 4)
		self.upgrades['minion_duration'] = (14, 2)
		self.upgrades['moonblade'] = (1, 3, "Moonblade", "炽天使的分裂攻击除 [fire] 和 [holy] 伤害外还造成 [arcane] 伤害。")
		self.upgrades['essence'] = (1, 5, "Essence Aura", "炽天使每回合增加 5 格内所有其他临时友军 1 个持续回合。", "aura")
		self.upgrades['heal'] = (5, 2, "Heal Aura", "炽天使每回合治疗 5 格内的所有其他临时友军 5 点生命。", "aura")
		self.upgrades['holy_fire'] = (1, 5, "Holy Fire Aura", "炽天使每回合对 5 格内所有敌人造成 [2_点火焰:fire] 或 [2_点神圣:holy] 伤害。", "aura")
		self.level = 4

		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个炽天使。\n"
				"炽天使有 [{minion_health}_点生命:minion_health] 和 [{shields}_点护盾:shields]，可飞行。\n"
				"炽天使的分裂近战攻击造成 [{minion_damage}_点火焰:fire] 和 [{minion_damage}_点神圣:holy] 伤害。\n"
				"炽天使在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		angel = Unit()
		angel.name = "Seraph"
		angel.asset_name = "seraphim"
		angel.tags = [Tags.Holy]

		angel.sprite.char = 'S'
		angel.sprite.color = Tags.Holy.color

		angel.max_hp = self.get_stat('minion_health')
		angel.shields = self.get_stat('shields')

		angel.resists[Tags.Holy] = 100
		angel.resists[Tags.Dark] = 75
		angel.resists[Tags.Fire] = 75

		sword = SeraphimSwordSwing()
		sword.damage = self.get_stat('minion_damage')
		sword.arcane = self.get_stat('moonblade')
		angel.spells.append(sword)
		angel.flying = True
		if self.get_stat('heal'):
			angel.buffs.append(HealAuraBuff(self.get_stat('heal'), 5))

		if self.get_stat('essence'):
			aura = EssenceAuraBuff()
			aura.radius = 5
			angel.buffs.append(aura)

		if self.get_stat('holy_fire'):
			aura = DamageAuraBuff(damage=2, damage_type=[Tags.Fire, Tags.Holy], radius=5)
			angel.buffs.append(aura)

		angel.turns_to_death = self.get_stat('minion_duration')

		self.summon(angel, Point(x, y))

class ArchonLightning(Spell):

	def on_init(self):
		self.name = "Archon Lightning"
		self.description = "束状攻击。\n给攻击范围内的友军护盾。"

	def cast_instant(self, x, y):
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:]:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit and not are_hostile(unit, self.caster):
				unit.add_shields(1)
			else:
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Lightning, self)

class SummonArchon(Spell):

	def on_init(self):

		self.name = "Call Archon"
		self.tags = [Tags.Lightning, Tags.Holy, Tags.Conjuration]

		self.max_charges = 4

		self.minion_health = 77
		self.shields = 3
		self.minion_damage = 14

		self.minion_duration = 14
		self.minion_range = 8

		self.upgrades['minion_range'] = (7, 3)
		self.upgrades['minion_damage'] = (10, 4)
		self.upgrades['minion_duration'] = (14, 2)

		self.level = 4

		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个统领。\n"
				"统领有 [{minion_health}_点生命:minion_health] 和 [{shields}_点护盾:shields]，可飞行。\n"
				"统领的束状攻击对敌人造成 [{minion_damage}_点闪电:lightning] 伤害，给友军护盾。\n"
				"统领在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		angel = Unit()
		angel.name = "Archon"
		angel.tags = [Tags.Holy]

		angel.sprite.char ='A'
		angel.sprite.color = Tags.Holy.color

		angel.max_hp = self.get_stat('minion_health')
		angel.shields = self.get_stat('shields')

		angel.resists[Tags.Holy] = 100
		angel.resists[Tags.Dark] = 75
		angel.resists[Tags.Lightning] = 75

		lightning = ArchonLightning()
		lightning.damage = self.get_stat('minion_damage')
		lightning.range = self.get_stat('minion_range')
		angel.spells.append(lightning)
		angel.flying = True

		angel.turns_to_death = self.get_stat('minion_duration')

		self.summon(angel, Point(x, y))


class PainMirrorSpell(Spell):

	def on_init(self):
		self.name = "Pain Mirror"
		self.range = 0
		self.duration = 10

		self.level = 3

		self.max_charges = 5

		self.upgrades['duration'] = (10, 2)
		self.upgrades['max_charges'] = (4, 2)

		self.tags = [Tags.Dark, Tags.Enchantment]

	def cast_instant(self, x, y):
		buff = PainMirror(self)
		buff.asset = ["status", "pain_mirror"]
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每当你受伤时，对视线内的所有敌人造成等量的 [dark] 伤害。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class PyrostaticPulse(Spell):

	def on_init(self):
		self.name = "Pyrostatic Pulse"
		self.level = 4

		self.damage = 16

		self.max_charges = 8
		self.range = 8
		self.tags = [Tags.Fire, Tags.Lightning, Tags.Sorcery]

		self.upgrades['range'] = (4, 2)
		self.upgrades['damage'] = (9, 3)
		self.upgrades['max_charges'] = (8, 2)

	def get_description(self):
		return ("在一束内造成 [{damage}_点火焰:fire] 伤害。\n"
				"对一束相邻的地块造成 [{damage}_点闪电:lightning] 伤害。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		center_beam = self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:]
		side_beam = []
		for p in center_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if q not in center_beam and q not in side_beam:
					side_beam.append(q)
		return center_beam + side_beam

	def cast_instant(self, x, y):

		center_beam = self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:]
		side_beam = []
		for p in center_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if q not in center_beam and q not in side_beam:
					side_beam.append(q)

		for p in center_beam:
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Fire, self)

		for p in side_beam:
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Lightning, self)

class ThunderStone(Prop):

	def __init__(self):
		self.name = "Thunder Stone"
		self.asset = ['tiles', 'thunderstone']
		self.damage = 0

	def on_unit_enter(self, player):
		candidates = self.level.get_units_in_los(self)
		candidates = [u for u in candidates if are_hostile(player, u)]
		candidates = sorted(candidates, key=lambda u: -distance(u, player))
		if candidates:
			target = candidates[0]
		else:
			target = player
		self.level.queue_spell(self.arc(target))
		self.level.remove_obj(self)

	def arc(self, target):

		self.level.deal_damage(self.x, self.y, 0, Tags.Lightning), self
		for p in self.level.get_points_in_line(self, target)[1:]:
			unit = self.level.get_unit_at(point.x, point.y)
			if unit and unit.team == TEAM_PLAYER:
				continuenue
			self.level.deal_damage(p.x, p.y, self.damage, Tags.Lightning, self)
		yield

class ThunderStones(Spell):

	def on_init(self):
		self.name = "Thunder Stones"
		self.description = "在附近的地上生成几个雷石。当单位踩到雷石时，弧状闪电射向最远的可见敌人，在一束内对敌人造成伤害。"
		self.level = 2
		self.tags = [Tags.Lightning, Tags.Sorcery]

		self.damage = 14
		self.num_stones = 4
		self.max_charges = 12
		self.range = 0

		self.upgrades['damage'] = (9, 3)
		self.upgrades['num_stones'] = (2, 3)

	def cast_instant(self, x, y):

		candidate_points = self.caster.level.get_points_in_ball(x, y, 3)

		def can_target(p):
			tile = self.caster.level.tiles[p.x][p.y]
			if tile.prop:
				return False
			if not tile.can_walk:
				return False
			return True

		candidate_points = [p for p in candidate_points if can_target(p)]

		random.shuffle(candidate_points)

		for i in range(self.get_stat('num_stones')):
			if not candidate_points:
				break
			p = candidate_points.pop()
			prop = ThunderStone()
			prop.damage = self.get_stat('damage')
			self.caster.level.add_obj(prop, p.x, p.y)

class FireStone(Prop):

	def __init__(self):
		self.name = "Fire Stone"
		self.asset = ['tiles', 'firestone']
		self.damage = 0
		self.radius = 0

	def on_unit_enter(self, player):
		candidates = self.level.get_units_in_los(self)
		candidates = [u for u in candidates if are_hostile(player, u)]
		candidates = sorted(candidates, key=lambda u: -distance(u, player))
		if candidates:
			target = candidates[0]
		else:
			target = player
		self.level.queue_spell(self.explode())
		self.level.remove_obj(self)

	def explode(self):
		for stage in Burst(self.level, self, self.radius):
			for point in stage:
				unit = self.level.get_unit_at(point.x, point.y)
				if unit and unit.team == TEAM_PLAYER:
					continue
				self.level.deal_damage(point.x, point.y, self.damage, Tags.Fire, self)

			for i in range(3):
				yield

class FireStones(Spell):

	def on_init(self):
		self.name = "Fire Stones"
		self.description = "在附近的地上生成几个火石。当单位踩到火石时，火焰爆发，对范围内的敌人造成伤害。"
		self.level = 2
		self.tags = [Tags.Fire, Tags.Sorcery]

		self.damage = 16
		self.num_stones = 4
		self.radius = 3
		self.max_charges = 12
		self.range = 0

		self.upgrades['damage'] = (11, 3)
		self.upgrades['num_stones'] = (2, 2)
		self.upgrades['radius'] = (2, 3)

	def cast_instant(self, x, y):

		candidate_points = self.caster.level.get_points_in_ball(x, y, 3)

		def can_target(p):
			tile = self.caster.level.tiles[p.x][p.y]
			if tile.prop:
				return False
			if not tile.can_walk:
				return False
			return True

		candidate_points = [p for p in candidate_points if can_target(p)]

		random.shuffle(candidate_points)

		for i in range(self.get_stat('num_stones')):
			if not candidate_points:
				break
			p = candidate_points.pop()
			prop = FireStone()
			prop.damage = self.get_stat('damage')
			prop.radius = self.get_stat('radius')
			self.caster.level.add_obj(prop, p.x, p.y)

class VoidRip(Spell):

	def on_init(self):
		self.name = "Aether Swap"
		self.range = 7

		self.max_charges = 8
		self.damage = 16
		self.level = 3

		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "以太换位施放无需视线。")
		self.upgrades['range'] = (3, 1)
		self.upgrades['max_charges'] = (10, 3)

		self.tags = [Tags.Arcane, Tags.Translocation, Tags.Sorcery]

	def get_description(self):
		return ("与目标单位换位。\n"
				"对该单位造成 [{damage}_点奥术:arcane] 伤害。\n"
				"无法以免疫 [arcane] 的单位为目标。").format(**self.fmt_dict())

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if unit == self.caster:
			return False
		if unit.resists[Tags.Arcane] >= 100:
			return False
		if not self.caster.level.tiles[x][y].can_walk:
			return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		target = self.caster.level.get_unit_at(x, y)

		# Fizzle if attempting to cast on non walkable tile
		if self.caster.level.tiles[x][y].can_walk:
			self.caster.level.act_move(self.caster, x, y, teleport=True, force_swap=True)

		if target:
			target.deal_damage(self.get_stat('damage'), Tags.Arcane, self)

class ShieldSiphon(Spell):

	def on_init(self):
		self.name = "Siphon Shields"

		self.max_charges = 3
		self.level = 4

		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.range = 0

		self.shield_burn = 0
		self.shield_steal = 1

		self.upgrades['shield_burn'] = (5, 2, "Shield Burn", "每偷取一点护盾便造成 5 点 [fire] 伤害。")
		self.upgrades['shield_steal'] = (4, 1)

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster) and u.shields]

	def get_description(self):
		return ("偷取视线内所有敌方单位各至多 [{shield_steal}_点护盾:shields]。").format(**self.fmt_dict())

	def cast(self, x, y):

		total = 0
		targets = [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster)]
		for u in targets:

			if not u.shields:
				continue

			stolen = min(self.get_stat('shield_steal'), u.shields)

			self.caster.level.show_effect(u.x, u.y, Tags.Shield_Expire)
			u.shields -= stolen

			if self.get_stat('shield_burn'):
				u.deal_damage(stolen * self.get_stat('shield_burn'), Tags.Fire, self)

			total += stolen

			yield

		if total:
			self.caster.add_shields(total)

		yield


class VoidMaw(Spell):

	def on_init(self):
		self.name = "Hungry Maw"

		self.max_charges = 6
		self.level = 2
		self.tags = [Tags.Arcane, Tags.Conjuration]
		self.range = 7

		self.minion_range = 7
		self.minion_damage = 9
		self.minion_health = 8
		self.minion_duration = 15
		self.shields = 1

		self.upgrades['shields'] = (5, 3)
		self.upgrades['minion_range'] = (7, 2)
		self.upgrades['minion_damage'] = (12, 5)
		self.upgrades['range'] = (4, 1)

		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个饥肠怪。\n"
				"饥肠怪有 [{minion_health}_点生命:minion_health] 和 [{shields}_点护盾:shields]，漂浮且固定不动。\n"
				"饥肠怪的攻击造成 [{minion_damage}_点物理:physical]，把敌人拉向自己，射程为 [{minion_range}_格:minion_range]。\n"
				"饥肠怪在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		u = Unit()
		u.tags = [Tags.Arcane, Tags.Demon]
		u.name = "Hungry Maw"
		u.max_hp = self.get_stat('minion_health')
		u.shields = self.get_stat('shields')
		u.asset_name = 'floating_mouth'

		u.spells.append(PullAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), color=Tags.Tongue.color))

		u.flying = True
		u.stationary = True

		u.turns_to_death = self.get_stat('minion_duration')

		u.resists[Tags.Arcane] = 75
		u.resists[Tags.Dark] = 50
		u.resists[Tags.Lightning] = -50

		self.summon(u, Point(x, y))


class RotBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.color = Tags.Dark.color
		self.name = "Hollow Flesh"
		self.asset = ['status', 'rot']

	def on_applied(self, owner):
		self.owner.resists[Tags.Dark] += 100
		self.owner.resists[Tags.Fire] -= self.spell.get_stat('fire_vulnerability')
		self.owner.resists[Tags.Holy] -= 100
		self.owner.resists[Tags.Heal] = 100

		frac = self.spell.get_stat('max_health_loss') / 100

		self.owner.max_hp -= math.floor(self.owner.max_hp * frac)
		self.owner.max_hp = max(self.owner.max_hp, 1)
		if self.owner.cur_hp > self.owner.max_hp:
			self.owner.cur_hp = self.owner.max_hp

		self.owner.tags.append(Tags.Undead)
		if Tags.Living in self.owner.tags:
			self.owner.tags.remove(Tags.Living)

class HallowFlesh(Spell):

	def on_init(self):
		self.name = "Hollow Flesh"
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.level = 2
		self.max_charges = 9
		self.range = 6

		self.holy_vulnerability = 100
		self.fire_vulnerability = 0
		self.max_health_loss = 25

		self.upgrades['max_health_loss'] = (25, 2)
		self.upgrades['max_charges'] = (7, 2)
		self.upgrades['fire_vulnerability'] = (50, 2, "Fire Vulnerability")

	def get_description(self):
		return ("以不死菁华诅咒一群单位。\n"
				"受影响的的单位变为 [undead]，失去 [living]。\n"
				"受影响的的单位失去 [{max_health_loss}%:damage] 的生命上限。\n"
				"受影响的的单位失去 [100_点神圣:holy] 抗性。\n"
				"受影响的的单位获得 [100_点黑暗:dark] 抗性。\n"
				"受影响的的单位无法被治疗。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):

		candidates = set([Point(x, y)])
		unit_group = set()

		while candidates:
			candidate = candidates.pop()
			unit = self.caster.level.get_unit_at(candidate.x, candidate.y)
			if unit and unit not in unit_group:
				if Tags.Living not in unit.tags:
					continue
				if unit == self.caster:
					continue
				unit_group.add(unit)

				for p in self.caster.level.get_adjacent_points(Point(unit.x, unit.y), filter_walkable=False):
					candidates.add(p)

		return list(unit_group)

	def cast(self, x, y):
		points = self.get_impacted_tiles(x, y)

		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				unit.apply_buff(RotBuff(self))
				yield

class ConductanceBuff(Buff):

	def on_init(self):
		self.name = "Conductance"
		self.color = Tags.Lightning.color
		self.can_copy = True
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast
		self.resists[Tags.Lightning] = -50
		self.buff_type = BUFF_TYPE_CURSE
		self.copies = 1
		self.asset = ['status', 'conductance']

	def on_spell_cast(self, evt):
		if not (evt.x == self.owner.x and evt.y == self.owner.y):
			return
		if not self.can_copy:
			return
		if not Tags.Lightning in evt.spell.tags:
			return

		self.can_copy = False
		for i in range(self.copies):
			if evt.spell.can_cast(evt.x, evt.y):
				evt.caster.level.act_cast(evt.caster, evt.spell, evt.x, evt.y, pay_costs=False)
		evt.caster.level.queue_spell(self.reset())

	def reset(self):
		self.can_copy = True
		yield

class ConductanceSpell(Spell):

	def on_init(self):
		self.name = "Conductance"
		self.tags = [Tags.Lightning, Tags.Enchantment]
		self.level = 4
		self.max_charges = 12

		self.resistance_debuff = 50

		self.duration = 10
		self.copies = 1
		self.upgrades['copies'] = (1, 2, "Multicopy", "额外复制一份指向目标的 [lightning] 咒语。")
		self.upgrades['resistance_debuff'] = (50, 2)
		self.upgrades['max_charges'] = (6, 2)

	def can_cast(self, x, y):
		return self.caster.level.get_unit_at(x, y) and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			buff = ConductanceBuff()
			buff.copies = self.get_stat('copies')
			buff.resists[Tags.Lightning] = -self.get_stat('resistance_debuff')
			unit.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("以导体菁华诅咒一个单位。\n"
				"该敌人失去 [50_点闪电:lightning] 抗性。\n"
				"每当你以该敌人为目标施放 [lightning] 咒语时，复制该咒语。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class ShrapnelBlast(Spell):

	def on_init(self):
		self.name = "Shrapnel Blast"

		self.tags = [Tags.Fire, Tags.Metallic, Tags.Sorcery]
		self.level = 3
		self.max_charges = 6
		self.radius = 4
		self.range = 7
		self.damage = 12
		self.requires_los = False
		self.num_targets = 16

		self.upgrades['num_targets'] = (12, 3, "More Shrapnel", "额外发射 12 个碎片。")
		self.upgrades['puncture'] = (1, 2, "Puncturing Blast", "碎片可穿透或摧毁墙。")
		self.upgrades['homing'] = (1, 7, "Magnetized Shards", "碎片尽可能飞向敌人。")

	def get_description(self):
		return ("引爆目标墙。\n" 
				"对与墙相邻的敌人造成 [{damage}_点火焰:fire] 伤害。\n"
				"爆破在 [{radius}_格:radius] 冲程内随机发射 [{num_targets}_个碎片:num_targets]。\n"
				"每个碎片造成 [{damage}_点物理:physical] 伤害。").format(**self.fmt_dict())


	def can_cast(self, x, y):
		return self.caster.level.tiles[x][y].is_wall() and Spell.can_cast(self, x, y)

	def cast(self, x, y):
		target = Point(x, y)

		damage = self.get_stat('damage')

		for stage in Burst(self.caster.level, target, 1):
			for point in stage:
				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)

			for i in range(2):
				yield

		for i in range(self.get_stat('num_targets')):
			possible_targets = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))

			if not self.get_stat('puncture'):
				possible_targets = [t for t in possible_targets if self.caster.level.can_see(x, y, t.x, t.y, light_walls=True)]

			if self.get_stat('homing'):

				def can_home(t):
					u = self.caster.level.get_unit_at(t.x, t.y)
					if not u:
						return False
					return are_hostile(self.caster, u)

				enemy_targets = [t for t in possible_targets if can_home(t)]
				if enemy_targets:
					possible_targets = enemy_targets

			if possible_targets:
				target = random.choice(possible_targets)
				self.caster.level.deal_damage(target.x, target.y, damage, Tags.Physical, self)
				for i in range(2):
					yield

		self.caster.level.make_floor(x, y)
		return

	def get_impacted_tiles(self, x, y):
		fire_targets = [p for stage in Burst(self.caster.level, Point(x, y), 1) for p in stage]

		possible_targets = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))
		if not self.get_stat('puncture'):
			possible_targets = [t for t in possible_targets if self.caster.level.can_see(x, y, t.x, t.y, light_walls=True)]

		return set(fire_targets + possible_targets)


class PlagueOfFilth(Spell):

	def on_init(self):

		self.tags = [Tags.Nature, Tags.Dark, Tags.Conjuration]
		self.name = "Plague of Filth"
		self.minion_health = 12
		self.minion_damage = 2
		self.minion_range = 4

		self.minion_duration = 7
		self.num_summons = 2
		self.radius = 2

		self.max_channel = 15

		self.level = 3
		self.max_charges = 5

		self.upgrades['num_summons'] = (2, 4)
		self.upgrades['minion_duration'] = (4, 3)
		self.upgrades['minion_damage'] = (3, 3)
		self.upgrades['max_channel'] = (25, 1)
		self.upgrades['snakes'] = (1, 2, "Serpent Plague", "污秽瘟疫有 50% 几率改为召唤蛇，而非蟾蜍或苍蝇群。蛇有蟾蜍四分之三的生命，额外造成 1 点伤害。蛇的攻击命中时施加 5 层中毒。")

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['fly_health'] = d['minion_health'] // 2
		d['fly_damage'] = d['minion_damage'] // 2
		return d

	def get_description(self):
		return ("召唤 [{num_summons}:num_summons] 个蟾蜍和苍蝇群。\n"
				"蟾蜍有 [{minion_health}_点生命:minion_health]。\n"
				"蟾蜍的远程吐舌攻击造成 [{minion_damage}_点物理:physical] 伤害，把敌人拉向自己。\n"
				"蟾蜍可跳跃至多 [4_格:range]。\n"
				"苍蝇群有 [{fly_health}_点生命:minion_health]、[75_点黑暗:dark] 抗性、[75_点物理:physical] 抗性和 [-50_点寒冰:ice] 抗性，可飞行。\n"
				"苍蝇群的近战攻击造成 [{fly_damage}_点物理:physical] 伤害。\n"
				"召唤物在 [{minion_duration}_回合:minion_duration] 后消失。\n"
				"此咒语可引导至多 [{max_channel}_回合:duration]。").format(**self.fmt_dict())

	def cast(self, x, y, channel_cast=False):

		if not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		for i in range(self.get_stat('num_summons')):

			if self.get_stat('snakes') and random.random() < .5:
				unit = Snake()
				unit.max_hp = (self.get_stat('minion_health') * 3) // 4
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage = self.get_stat('minion_damage') + 1

			elif random.random() < .5:
				unit = HornedToad()
				unit.max_hp = self.get_stat('minion_health')
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage = self.get_stat('minion_damage')
			else:
				unit = FlyCloud()
				unit.max_hp = self.get_stat('minion_health') // 2
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage = self.get_stat('minion_damage') // 2

			unit.turns_to_death = self.get_stat('minion_duration')
			self.summon(unit, Point(x, y), radius=self.get_stat('radius'), sort_dist=False)
			yield

class SummonFieryTormentor(Spell):

	def on_init(self):
		self.name = "Fiery Tormentor"

		self.minion_health = 34
		self.minion_damage = 7
		self.minion_duration = 50
		self.minion_range = 2

		self.radius = 4

		self.max_charges = 7
		self.level = 4

		self.range = 7

		self.upgrades['minion_damage'] = (3, 2)
		self.upgrades['minion_health'] = (10, 2)
		self.upgrades['radius'] = (2, 3)

		self.upgrades['frostfire'] = (1, 3, "Frostfire Tormentor", "改为召唤霜火折磨者。", "variant")
		self.upgrades['ghostfire'] = (1, 3, "Ghostfire Tormentor", "改为召唤鬼火折磨者。", "variant")

		self.tags = [Tags.Dark, Tags.Fire, Tags.Conjuration]

		self.must_target_walkable = True
		self.must_target_empty = True

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['minion_leech_damage'] = d['minion_damage'] - 5
		return d

	def get_description(self):
		return ("召唤一个火热折磨者。\n"
				"折磨者有 [{minion_health}_点生命:minion_health]。\n"
				"折磨者的冲程攻击在 [{radius}_格:radius] 半径内造成 [{minion_damage}_点火焰:fire] 伤害。\n"
				"折磨者的远程吸血攻击造成 [{minion_leech_damage}_点黑暗:dark] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"折磨者在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				yield p

	def cast_instant(self, x, y):

		if self.get_stat('frostfire'):
			unit = FrostfireTormentor()
		elif self.get_stat('ghostfire'):
			unit = GhostfireTormentor()
		else:
			unit = FieryTormentor()

		apply_minion_bonuses(self, unit)
		unit.max_hp = self.get_stat('minion_health')

		for s in unit.spells:
			if 'Torment' in s.name:
				s.radius = self.get_stat('radius')

		unit.turns_to_death = self.get_stat('minion_duration')

		self.summon(unit, Point(x, y))

class DispersionFieldBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Dispersion Field"
		self.description = "每回合将附近的敌人传送走。"

	def on_advance(self):
		tped = 0
		units = self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius'))
		random.shuffle(units)
		for u in units:
			if not are_hostile(self.owner, u):
				continue

			possible_points = []
			for i in range(len(self.owner.level.tiles)):
				for j in range(len(self.owner.level.tiles[i])):
					if self.owner.level.can_stand(i, j, u):
						possible_points.append(Point(i, j))

			if not possible_points:
				continue

			target_point = random.choice(possible_points)

			self.owner.level.show_effect(u.x, u.y, Tags.Translocation)
			self.owner.level.act_move(u, target_point.x, target_point.y, teleport=True)
			self.owner.level.show_effect(u.x, u.y, Tags.Translocation)

			tped += 1
			if tped > self.spell.get_stat('num_targets'):
				break

class DispersionFieldSpell(Spell):

	def on_init(self):
		self.name = "Dispersion Field"
		self.level = 4
		self.tags = [Tags.Enchantment, Tags.Arcane, Tags.Translocation]

		self.max_charges = 3
		self.duration = 7
		self.num_targets = 3

		self.range = 0
		self.radius = 6

		self.upgrades['num_targets'] = (2, 2)
		self.upgrades['duration'] = (5, 1)
		self.upgrades['max_charges'] = (5, 4)

	def get_description(self):
		return ("每回合将 [{radius}_格:radius] 半径内随机 [{num_targets}_个敌人:num_targets] 传送到地图上的新地块。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(DispersionFieldBuff(self), self.get_stat('duration'))

class KnightBuff(Buff):

	def __init__(self, summoner):
		Buff.__init__(self)
		self.summoner = summoner

	def on_init(self):
		self.name = "Bound Knight"
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		self.summoner.deal_damage(40, Tags.Holy, self)

class SummonKnights(Spell):

	def on_init(self):
		self.name = "Knightly Oath"
		self.level = 7
		self.tags = [Tags.Conjuration, Tags.Holy]

		self.minion_health = 90

		self.max_charges = 2
		self.minion_damage = 7

		self.range = 0

		# Purely for shrine bonuses
		self.minion_range = 3

		self.upgrades['void_court'] = (1, 5, "Void Court", "改为召唤三个虚空骑士和一个虚空英雄。", "court")
		self.upgrades['storm_court'] = (1, 5, "Storm Court", "改为召唤三个风暴骑士和一个风暴英雄。", "court")
		self.upgrades['chaos_court'] = (1, 5, "Chaos Court", "改为召唤三个混沌骑士和一个混沌英雄。", "court")
		self.upgrades['max_charges'] = (1, 3)

	def get_description(self):
		return ("召唤虚空骑士、混沌骑士和风暴骑士各一个。\n"
				"每个骑士各有 [{minion_health}_点生命:minion_health]、不同的抗性和独特的魔法能力库。\n"
				"每当一个骑士死亡时，施法者受到 [40_点神圣:holy] 伤害。").format(**self.fmt_dict())

	def cast(self, x, y):

		knights = [VoidKnight(), ChaosKnight(), StormKnight()]
		if self.get_stat('void_court'):
			knights = [VoidKnight(), VoidKnight(), VoidKnight(), Champion(VoidKnight())]
		if self.get_stat('storm_court'):
			knights = [StormKnight(), StormKnight(), StormKnight(), Champion(StormKnight())]
		if self.get_stat('chaos_court'):
			knights = [ChaosKnight(), ChaosKnight(), ChaosKnight(), Champion(ChaosKnight())]

		for u in knights:
			apply_minion_bonuses(self, u)
			u.buffs.append(KnightBuff(self.caster))
			self.summon(u)
			yield

class ToxinBurst(Spell):

	def on_init(self):

		self.name = "Toxin Burst"
		self.level = 2

		self.tags = [Tags.Sorcery, Tags.Nature, Tags.Dark]

		self.damage = 1
		self.radius = 4
		self.duration = 20
		self.requires_los = False
		self.range = 12

		self.max_charges = 10

		self.upgrades['duration'] = (20, 1)
		self.upgrades['radius'] = (2, 2)
		self.upgrades['damage'] = (15, 3)

	def cast(self, x, y):
		points = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))
		random.shuffle(points)
		for p in points:

			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Poison, self)

			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				unit.apply_buff(Poison(), self.get_stat('duration'))

			if random.random() < .3:
				yield

	def get_description(self):
		return ("对 [{radius}_格:radius] 半径内的所有单位造成 [{damage}_点毒性:poison] 伤害，施加 [poison] [{duration}_回合:duration]。\n"
				+ text.poison_desc).format(**self.fmt_dict())

class ToxicSpore(Spell):

	def on_init(self):
		self.name = "Toxic Spores"

		self.level = 2
		self.tags = [Tags.Conjuration, Tags.Nature]
		self.range = 8
		self.max_charges = 16

		example = GreenMushboom()
		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage

		self.num_summons = 2
		self.minion_range = 2
		self.upgrades['num_summons'] = (2, 3)
		self.upgrades['grey_mushboom'] = (1, 2, "Grey Mushbooms", "改为召唤灰色爆菇，施加 [stun]，而非 [poison]。", "color")
		self.upgrades['red_mushboom'] = (1, 5, "Red Mushbooms", "改为召唤红色爆菇，造成 [fire] 伤害，但不施加 [poison]。", "color")
		self.upgrades['glass_mushboom'] = (1, 6, "Glass Mushbooms", "改为召唤玻璃爆菇，施加 [glassify]，而非 [poison]。", "color")


	def get_description(self):
		return ("召唤 [{num_summons}:num_summons] 个爆菇。\n"
				"爆菇有 [{minion_health}_点生命:minion_health]。\n"
				"爆菇的远程攻击造成 [{minion_damage}_点毒性:poison] 伤害，施加 [4_回合:duration] 的 [poison]。\n"
				"爆菇死亡时时对近战范围的单位施加 [12_回合:duration] 的 [poison]。").format(**self.fmt_dict())

	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			mushboom = GreenMushboom()
			if self.get_stat('grey_mushboom'):
				mushboom = GreyMushboom()
			if self.get_stat('red_mushboom'):
				mushboom = RedMushboom()
			if self.get_stat('glass_mushboom'):
				mushboom = GlassMushboom()
			apply_minion_bonuses(self, mushboom)
			self.summon(mushboom, target=Point(x, y))
			yield

class AmplifyPoisonBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Amplified Poison"
		self.asset = ['status', 'amplified_poison']
		self.stack_type = STACK_DURATION
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Poison.color
		self.resists[Tags.Poison] = -self.spell.get_stat('resistance_debuff')

class AmplifyPoisonSpell(Spell):

	def on_init(self):
		self.name = "Amplify Venom"

		self.duration = 10
		self.tags = [Tags.Enchantment, Tags.Nature]
		self.level = 3

		self.range = 0

		self.max_charges = 8

		self.resistance_debuff = 100
		self.upgrades['resistance_debuff'] = (100, 3)
		self.upgrades['duration'] = (10, 1)
		self.upgrades['max_charges'] = (12, 2)
		self.upgrades['spread'] = (1, 2, "Spread Poison", "增效毒性传播给附近的敌人（半径 2）")

	def get_description(self):
		return ("所有 [poisoned] 的敌人失去 [100_点毒性:poison] 抗性，持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast(self, x, y):

		units = [u for u in self.caster.level.units if are_hostile(u, self.caster) and u.has_buff(Poison)]
		random.shuffle(units)
		for u in units:

			# Unit died, or some crazy buff removed poison
			if not u.has_buff(Poison):
				continue

			if self.get_stat('spread'):
				for p in self.caster.level.get_points_in_ball(u.x, u.y, 2):
					unit = self.caster.level.get_unit_at(p.x, p.y)
					if unit and are_hostile(self.caster, unit):
						unit.apply_buff(Poison(), u.get_buff(Poison).turns_left)

			u.apply_buff(AmplifyPoisonBuff(self), self.get_stat('duration'))
			yield

class IgnitePoison(Spell):

	def on_init(self):
		self.name = "Combust Poison"
		self.level = 3
		self.tags = [Tags.Sorcery, Tags.Fire, Tags.Nature]

		self.max_charges = 9

		self.multiplier = 1
		self.radius = 2

		self.upgrades['radius'] = (1, 3)
		self.upgrades['max_charges'] = (9, 2)
		self.upgrades['multiplier'] = (1, 4)

		self.range = 0

	def get_impacted_tiles(self, x, y):
		tiles = set()
		for u in self.owner.level.units:
			if not u.has_buff(Poison):
				continue
			if not are_hostile(u, self.caster):
				continue
			points = [p for stage in Burst(self.caster.level, u, self.get_stat('radius')) for p in stage]
			for p in points:
				tiles.add(p)
		return tiles

	def get_description(self):
		return ("消耗敌方单位上的 [poison]。\n"
				"对每个受影响的敌人 [{radius}_格:radius] 冲程内造成 [fire] 伤害，数量为消耗毒性的 [{multiplier}:damage] 倍。").format(**self.fmt_dict())

	def cast(self, x, y):

		units = [u for u in self.caster.level.units if are_hostile(u, self.caster) and u.has_buff(Poison)]
		random.shuffle(units)

		for u in units:
			# Unit died, or some crazy buff removed poison
			if not u.has_buff(Poison):
				continue

			buff = u.get_buff(Poison)
			damage = buff.turns_left * self.get_stat('multiplier')
			for stage in Burst(self.caster.level, u, self.get_stat('radius')):
				for point in stage:
					self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)
				yield

			u.remove_buff(buff)

class VenomBeastThorns(Buff):

	def on_init(self):
		self.name = "Poison Skin"
		self.global_triggers[EventOnSpellCast] = self.on_spell
		self.description = "对近战攻击者施加中毒 5 回合。"
		self.color = Tags.Poison.color

	def on_spell(self, evt):
		if evt.x != self.owner.x or evt.y != self.owner.y:
			return
		# Distance is implied to be 1 if its a leap or a melee
		if not (isinstance(evt.spell, LeapAttack) or evt.spell.melee):
			return
		self.owner.level.queue_spell(self.do_thorns(evt.caster))

	def do_thorns(self, unit):
		unit.apply_buff(Poison(), 5)
		yield

class VenomBeastHealing(Buff):

	def on_init(self):
		self.name = "Venom Drinker"
		self.description = "每当有单位受到 [poison] 伤害时得到治疗。"
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if evt.damage_type != Tags.Poison:
			return
		self.owner.deal_damage(-evt.damage, Tags.Heal, self)

class VenomBeast(Spell):

	def on_init(self):
		self.name = "Venom Beast"

		self.level = 4
		self.tags = [Tags.Nature, Tags.Conjuration]
		self.minion_health = 70
		self.minion_damage = 12

		self.max_charges = 3

		self.upgrades['venom_skin'] = (1, 3, "Poison Skin", "毒液野兽的皮肤对近战攻击者施加中毒 5 回合。")
		self.upgrades['resists'] = (50, 2, "Resistances", "毒液野兽获得 [fire] 和 [lightning damage] 抗性。")
		self.upgrades['minion_health'] = (30, 3)
		self.upgrades['trample'] = (1, 2, "Trample Attack", "毒液野兽可进行 2 回合冷却的践踏攻击。")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个毒液野兽。\n"
				"毒液野兽有 [{minion_health}_点生命:minion_health]，每当有单位受到 [poison] 伤害时得到治疗。\n"
				"毒液野兽的近战攻击造成 [{minion_damage}_点物理:physical] 伤害，施加 [5_回合:duration] 的 [poison]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		beast = Unit()
		beast.name = "Venom Beast"
		beast.resists[Tags.Poison] = 100
		beast.tags = [Tags.Living, Tags.Poison, Tags.Nature]

		if self.get_stat('trample'):
			trample = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), trample=True)
			trample.cool_down = 2
			trample.name = "Trample"
			beast.spells.append(trample)

		bite = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), buff=Poison, buff_duration=5)
		bite.name = "Poison Bite"
		beast.spells.append(bite)

		beast.buffs = [VenomBeastHealing()]

		if self.get_stat('venom_skin'):
			beast.buffs.append(VenomBeastThorns())

		beast.max_hp = self.get_stat('minion_health')

		beast.resists[Tags.Fire] = self.get_stat('resists')
		beast.resists[Tags.Lightning] = self.get_stat('resists')

		self.summon(beast, target=Point(x, y))

class SummonSpiderQueen(Spell):

	def on_init(self):
		self.name = "Spider Queen"
		self.tags = [Tags.Nature, Tags.Conjuration]

		self.max_charges = 2
		self.level = 5

		self.upgrades["aether"] = (1, 3, "Aether Queen", "改为召唤乙太蜘蛛女王。", "species")
		self.upgrades["steel"] = (1, 3, "Steel Queen", "改为召唤钢铁蜘蛛女王。", "species")

		self.must_target_walkable = True
		self.must_target_empty = True

		self.minion_damage = GiantSpider().spells[0].damage
		self.minion_health = 10

		self.num_summons = 4


	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['queen_hp'] = 96 + self.get_stat('minion_health', base=0)
		d['spider_hp'] = 14 + self.get_stat('minion_health', base=0)
		return d

	def get_description(self):
		return ("召唤一个蜘蛛女王。\n"
				"蜘蛛女王有 [{queen_hp}_点生命:minion_health]。\n"
				"蜘蛛女王每 [12_回合:duration] 孵化蜘蛛宝宝。\n"
				"蜘蛛宝宝有 [3_HP:minion_health] ，倾向于逃跑而非攻击，[8_回合:duration] 后长大后变成有 [{spider_hp}_点生命:minion_health] 的巨型蜘蛛。\n"
				"巨型蜘蛛和蜘蛛女王的近战攻击造成 [{minion_damage}_点物理:physical] 伤害，施加 10 回合的 [poison]。").format(**self.fmt_dict())

	def spawn_with_bonuses(self, base_spawner):
		unit = base_spawner()
		apply_minion_bonuses(self, unit)
		return unit

	def cast_instant(self, x, y):

		spawner = GiantSpider

		if self.get_stat('aether'):
			spawner = PhaseSpider
		if self.get_stat('steel'):
			spawner = SteelSpider

		unit = spawner()
		unit.max_hp = 96
		apply_minion_bonuses(self, unit)

		unit.name = "%s Queen" % unit.name
		unit.asset_name += '_mother'

		def babyspider():
			unit = spawner()
			unit.max_hp = 3
			apply_minion_bonuses(self, unit)
			unit.name = "Baby %s" % unit.name
			unit.asset_name += '_child'

			for s in unit.spells:
				if hasattr(s, 'damage'):
					s.damage = 1

			unit.is_coward = True
			unit.buffs = [b for b in unit.buffs if not isinstance(b, SpiderBuff)]
			unit.buffs.append(MatureInto(lambda: self.spawn_with_bonuses(spawner), 8))
			unit.source = self
			return unit

		unit.spells.insert(0, SimpleSummon(babyspider, num_summons=self.get_stat('num_summons'), cool_down=12))

		self.summon(unit, target=Point(x, y))

class Freeze(Spell):

	def on_init(self):
		self.tags = [Tags.Enchantment, Tags.Ice]
		self.level = 2
		self.name = "Freeze"

		self.duration = 5

		self.max_charges = 20

		self.range = 8

		self.upgrades['duration'] = (4, 3)

	def can_cast(self, x, y):
		return self.caster.level.get_unit_at(x, y) and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		target = self.caster.level.get_unit_at(x, y)
		if not target:
			return
		target.apply_buff(FrozenBuff(), self.get_stat('duration'))

	def get_description(self):
		return ("[frozen] 目标单位 [{duration}_回合:duration]。\n"
			    + text.frozen_desc).format(**self.fmt_dict())

class Iceball(Spell):

	def on_init(self):
		self.tags = [Tags.Sorcery, Tags.Ice]
		self.level = 3
		self.name = "Iceball"

		self.damage = 14
		self.duration = 3
		self.radius = 2

		self.range = 7

		self.max_charges = 11

		self.upgrades['radius'] = (1, 2)
		self.upgrades['duration'] = (2, 2)
		self.upgrades['damage'] = (10, 2)
		self.upgrades['icecrush'] = (1, 6, "Ice Crush", "受影响区域内已被 [frozen] 的单位在被再次冻结前受到 [physical] 伤害。")


	def get_description(self):
		return ("在 [{radius}_格:radius] 冲程内造成 [{damage}_点寒冰:ice] 伤害。\n"
				"[frozen] 范围内受影响的单位 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast(self, x, y):
		target = Point(x, y)

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				unit = self.caster.level.get_unit_at(point.x, point.y)
				damage = self.get_stat('damage')

				if self.get_stat('icecrush'):
					if unit and unit.has_buff(FrozenBuff):
						unit.deal_damage(damage, Tags.Physical, self)

				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Ice, self)

				if unit:
					unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
			for i in range(3):
				yield

		return

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class BlizzardSpell(Spell):

	def on_init(self):

		self.name = "Blizzard"

		self.tags = [Tags.Enchantment, Tags.Ice, Tags.Nature]
		self.level = 4
		self.max_charges = 4

		self.range = 9
		self.radius = 4

		self.damage = 5
		self.duration = 5

		self.upgrades['damage'] = (5, 2)
		self.upgrades['radius'] = (2, 3)
		self.upgrades['duration'] = (5, 2)
		self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "暴风雪施放无需视线。")

	def get_description(self):
		return ("在 [{radius}_格:radius] 半径内生成暴风雪。\n" +
				"每回合暴风雪中的单位受到 [{damage}_点寒冰:ice] 伤害，有 50% 几率被 [frozen]。\n" +
				text.frozen_desc +
				"暴风雪持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast(self, x, y):

		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				cloud = BlizzardCloud(self.caster)
				cloud.duration = self.get_stat('duration')
				cloud.damage = self.get_stat('damage')
				cloud.source = self
				yield self.caster.level.add_obj(cloud, p.x, p.y)

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class SummonFrostfireHydra(Spell):

	def on_init(self):
		self.name = "Frostfire Hydra"

		self.tags = [Tags.Ice, Tags.Fire, Tags.Dragon, Tags.Conjuration]
		self.level = 3
		self.max_charges = 7

		self.minion_range = 9
		self.minion_damage = 7
		self.minion_health = 16
		self.minion_duration = 15

		self.upgrades['minion_range'] = (6, 3)
		self.upgrades['minion_duration'] = (10, 2)
		self.upgrades['minion_damage'] = (7, 4)

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个霜火多头龙。\n"
				"多头龙有 [{minion_health}_点生命:minion_health]，固定不动。\n"
				"多头龙的一种束状攻击造成 [{minion_damage}_点火焰:fire] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"多头龙的一种束状攻击造成 [{minion_damage}_点寒冰:ice] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"多头龙在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		unit = Unit()
		unit.max_hp = self.get_stat('minion_health')

		unit.name = "Frostfire Hydra"
		unit.asset_name = 'fire_and_ice_hydra'

		fire = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Fire, beam=True)
		fire.name = "Fire"
		fire.cool_down = 2

		ice = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Ice, beam=True)
		ice.name = "Ice"
		ice.cool_down = 2

		unit.stationary = True
		unit.spells = [ice, fire]

		unit.resists[Tags.Fire] = 100
		unit.resists[Tags.Ice] = 100

		unit.turns_to_death = self.get_stat('minion_duration')

		unit.tags = [Tags.Fire, Tags.Ice, Tags.Dragon]

		self.summon(unit, Point(x, y))

class StormNova(Spell):

	def on_init(self):
		self.name = "Storm Burst"
		self.level = 4
		self.tags = [Tags.Ice, Tags.Lightning, Tags.Sorcery]

		self.max_charges = 4

		self.damage = 21
		self.duration = 3
		self.radius = 5
		self.range = 0

		self.upgrades['duration'] = (2, 3)
		self.upgrades['clouds'] = (1, 2, "Cloud Nova", "新星留下风暴云和暴风雪")
		self.upgrades['radius'] = (2, 3)

	def get_description(self):
		return ("释放 [{radius}_格:radius] 冲程的风暴能量。\n"
				"爆发范围中的每个地块受到 [{damage}_点寒冰:ice] 或 [{damage}_点闪电:lightning] 伤害。\n"
				"受到 [ice] 伤害的单位被 [frozen] [{duration}_回合:duration]。\n"
				"受到 [lightning] 伤害的单位被 [stunned] [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for stage in Burst(self.caster.level, self.caster, self.get_stat('radius')):
			for p in stage:
				if (p.x, p.y) == (self.caster.x, self.caster.y):
					continue
				dtype = random.choice([Tags.Ice, Tags.Lightning])

				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), dtype, self)
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit:
					if dtype == Tags.Ice:
						unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
					if dtype == Tags.Lightning:
						unit.apply_buff(Stun(), self.get_stat('duration'))

				if self.get_stat('clouds'):
					if dtype == Tags.Ice:
						cloud = BlizzardCloud(self.caster)
					if dtype == Tags.Lightning:
						cloud = StormCloud(self.caster)
					self.caster.level.add_obj(cloud, p.x, p.y)

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class DeathChillDebuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Death Chill"
		self.color = Tags.Dark.color
		self.buff_type = BUFF_TYPE_CURSE
		self.owner_triggers[EventOnDeath] = self.on_death
		self.asset = ['status', 'deathchill']

	def on_advance(self):
		self.owner.deal_damage(self.spell.get_stat('damage'), Tags.Dark, self.spell)

	def on_death(self, evt):
		self.owner.level.queue_spell(self.burst())

	def burst(self):
		for unit in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius')):
			if are_hostile(self.spell.owner, unit):

				for p in self.owner.level.get_points_in_line(self.owner, unit)[1:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Ice, minor=True)

				damage = unit.deal_damage(self.spell.get_stat('damage'), Tags.Ice, self.spell)
				if damage:
					unit.apply_buff(FrozenBuff(), self.spell.get_stat('duration'))
				yield

class DeathChill(Spell):

	def on_init(self):

		self.name = "Death Chill"

		self.level = 3
		self.tags = [Tags.Enchantment, Tags.Dark, Tags.Ice]

		self.duration = 5
		self.radius = 3
		self.damage = 11

		self.range = 9

		self.max_charges = 12

		self.can_target_empty = False

		self.upgrades['radius'] = (1, 2)
		self.upgrades['damage'] = (6, 2)
		self.upgrades['duration'] = (4, 3)

	def get_description(self):
		return ("每回合对目标造成 [{damage}_点黑暗:dark] 伤害，持续 [{duration}_回合:duration]。\n"
				"若目标在此期间死亡，对 [{radius}_格:radius] 半径内的所有敌人造成 [{damage}_点寒冰:ice] 伤害并施加 [frozen] [{duration}_回合:duration]。\n"
				+ text.frozen_desc).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit or unit.cur_hp <= 0:
			return

		unit.apply_buff(DeathChillDebuff(self), self.get_stat('duration'))

class IcePhoenixBuff(Buff):

	def on_init(self):
		self.color = Tags.Ice.color
		self.owner_triggers[EventOnDeath] = self.on_death
		self.name = "Phoenix Freeze"

	def get_tooltip(self):
		return "死亡时生成寒冰冲击，对敌人造成 25 点 [ice] 伤害，对友军施加 2 点护盾。"

	def on_death(self, evt):
		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 6):
			unit = self.owner.level.get_unit_at(*p)
			if unit and not are_hostile(unit, self.owner):
				unit.add_shields(2)
			else:
				self.owner.level.deal_damage(p.x, p.y, 25, Tags.Ice, self)

class SummonIcePhoenix(Spell):

	def on_init(self):
		self.name = "Ice Phoenix"
		self.level = 5
		self.max_charges = 1
		self.tags = [Tags.Conjuration, Tags.Ice, Tags.Holy]

		self.minion_health = 74
		self.minion_damage = 9
		self.minion_range = 4
		self.lives = 1

		self.upgrades['lives'] = (2, 3, "复活", "凤凰额外复活 2 次。")
		self.upgrades['minion_damage'] = (9, 2)

		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个寒冰凤凰。\n"
				"凤凰有 [{minion_health}_点生命:minion_health]，可飞行，死亡时复活一次。\n"
				"凤凰的远程攻击造成 [{minion_damage}_点寒冰:ice] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"当凤凰死亡时，它会爆炸，在 [6_格:radius] 冲程内对敌人造成 [25_点寒冰:ice] 伤害，给友军 [2_点护盾:shields] 。"
			).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		phoenix = Unit()
		phoenix.max_hp = self.get_stat('minion_health')
		phoenix.name = "Ice Phoenix"

		phoenix.tags = [Tags.Ice, Tags.Holy]

		phoenix.sprite.char = 'P'
		phoenix.sprite.color = Tags.Ice.color

		phoenix.buffs.append(IcePhoenixBuff())
		phoenix.buffs.append(ReincarnationBuff(self.get_stat('lives')))

		phoenix.flying = True

		phoenix.resists[Tags.Ice] = 100
		phoenix.resists[Tags.Dark] = -50

		phoenix.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Ice))
		self.summon(phoenix, target=Point(x, y))

class WordOfIce(Spell):

	def on_init(self):
		self.name = "Word of Ice"
		self.level = 7
		self.tags = [Tags.Ice, Tags.Word]
		self.max_charges = 1
		self.duration = 5
		self.damage = 50
		self.range = 0

		self.upgrades['duration'] = (4, 3)
		self.upgrades['max_charges'] = (1, 2)

	def cast(self, x, y):
		units = [u for u in self.caster.level.units if are_hostile(u, self.caster)]
		random.shuffle(units)
		for u in units:
			if u.cur_hp < 50:
				u.apply_buff(FrozenBuff(), self.get_stat('duration'))
			if Tags.Fire in u.tags:
				u.deal_damage(self.get_stat('damage'), Tags.Ice, self)
			if random.random() < .3:
				yield

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if are_hostile(u, self.caster) and (u.resists[Tags.Ice] < 100 or Tags.Fire in u.tags)]

	def get_description(self):
		return ("没有 [ice] 免疫且生命低于 50 的所有敌人被 [frozen] [{duration}_回合:duration]。\n"
				"对所有 [fire] 单位造成 [{damage}_点寒冰:ice]。").format(**self.fmt_dict())

class IceWeave(Spell):

	def on_init(self):
		self.name = "Ice Weave"
		self.level = 3
		self.tags = [Tags.Enchantment, Tags.Ice]
		self.max_charges = 4
		self.range = 0

		self.duration = 4

		self.upgrades['duration'] = (2, 3)
		self.upgrades['max_charges'] = (4, 3)

	def get_description(self):
		return ("所有被 [frozen] 的敌人额外被 [frozen] [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(self.caster, u):
				continue

			buff = u.get_buff(FrozenBuff)
			if not buff:
				continue

			buff.turns_left += 4
			u.deal_damage(0, Tags.Ice, self)

class IcicleHarvest(Upgrade):

	def on_init(self):
		self.name = "Icicle Harvest"
		self.description = "每当被 [frozen] 的敌人死于 [ice] 伤害时，冰锥术获得一点充能。"
		self.global_triggers[EventOnDeath] = self.on_death
		self.level = 3

	def on_death(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not evt.unit.has_buff(FrozenBuff):
			return

		if self.prereq.cur_charges >= self.prereq.get_stat('max_charges'):
			return

		if not evt.damage_event or evt.damage_event.damage_type != Tags.Ice:
			return

		self.prereq.cur_charges += 1

class Icicle(Spell):

	def on_init(self):

		self.name = "Icicle"

		self.tags = [Tags.Ice, Tags.Sorcery]

		self.radius = 1
		self.damage = 6
		self.level = 1

		self.range = 9

		self.max_charges = 22

		self.upgrades['freezing'] = (1, 2, "Freezing", "冻结主目标 2 回合。")
		self.upgrades['radius'] = (1, 2)
		self.upgrades['damage'] = (9, 3)
		self.add_upgrade(IcicleHarvest())

	def get_description(self):
		return ("对目标造成 [{damage}_点物理:physical] 伤害。\n"
				"然后对目标和周围 [{radius}_格:radius] 范围造成 [{damage}_点寒冰:ice] 伤害。").format(**self.fmt_dict())

	def cast(self, x, y):

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			self.caster.level.show_effect(p.x, p.y, Tags.Physical, minor=True)

		self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Physical, self)
		unit = self.caster.level.get_unit_at(x, y)
		if unit and self.get_stat('freezing'):
			unit.apply_buff(FrozenBuff(), 2 + self.get_stat('duration'))

		yield

		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Ice, self)
			yield

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class IceWind(Spell):

	def on_init(self):
		self.name = "Chill Wind"

		self.level = 5
		self.tags = [Tags.Ice, Tags.Sorcery]

		self.max_charges = 2

		self.damage = 21
		self.duration = 6

		self.range = RANGE_GLOBAL
		self.requires_los = False

		self.upgrades['max_charges'] = (2, 3)
		self.upgrades['damage'] = (14, 2)

	def get_description(self):
		return ("对施法者为中心 [3_格:radius] 宽竖线内的单位造成 [{damage}_点寒冰:ice] 伤害，施加 [{duration}_回合:duration] 的 [frozen]。").format(**self.fmt_dict())

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Ice, self)
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
			if random.random() < .4:
				yield

	def get_impacted_tiles(self, x, y):
		line = self.caster.level.get_perpendicular_line(self.caster, Point(x, y))
		result = set()
		for p in line:
			for q in self.caster.level.get_points_in_rect(p.x-1, p.y-1, p.x+1, p.y+1):
				result.add(q)
		return result

class IceWall(Spell):

	def on_init(self):
		self.name = "Wall of Ice"
		self.minion_health = 36
		self.minion_duration = 15
		self.minion_range = 3
		self.minion_damage = 5

		self.level = 4
		self.max_charges = 6

		self.tags = [Tags.Conjuration, Tags.Ice]

		self.range = 7
		self.radius = 1

		self.upgrades['radius'] = (1, 2)
		self.upgrades['minion_range'] = (3, 3)
		self.upgrades['minion_damage'] = (5, 3)

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['width'] = 1 + 2*d['radius']
		return d

	def get_description(self):
		return ("在 [{width}_格:num_summons] 长度上召唤一排寒冰元素。\n"
				"寒冰元素有 [{minion_health}_点生命:minion_health]、[50_点物理:physical] 抗性、[100_点寒冰:ice] 抗性和 [-100_点火焰:fire] 抗性，无法移动。\n"
				"寒冰元素的远程攻击造成 [{minion_damage}_点寒冰:ice] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"寒冰元素在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			elemental = Unit()
			elemental.name = "Ice Elemental"
			snowball = SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Ice, range=self.get_stat('minion_range'))
			snowball.name = "Snowball"
			elemental.spells.append(snowball)
			elemental.max_hp = self.get_stat('minion_health')
			elemental.stationary = True

			elemental.tags = [Tags.Elemental, Tags.Ice]

			elemental.resists[Tags.Physical] = 50
			elemental.resists[Tags.Fire] = -100
			elemental.resists[Tags.Ice] = 100

			elemental.turns_to_death = self.get_stat('minion_duration')

			self.summon(elemental, target=p, radius=0)
			yield

	def get_impacted_tiles(self, x, y):
		points = self.caster.level.get_perpendicular_line(self.caster, Point(x, y), length=self.get_stat('radius'))
		points = [p for p in points if self.caster.level.can_walk(p.x, p.y, check_unit=True)]
		return points

class EarthquakeSpell(Spell):

	def on_init(self):
		self.name = "Earthquake"

		self.radius = 7
		self.max_charges = 4
		self.range = 0

		self.damage = 21
		self.level = 3
		self.tags = [Tags.Sorcery, Tags.Nature]

		self.upgrades['radius'] = (2, 3)
		self.upgrades['damage'] = (17, 3)
		self.upgrades['safety'] = (1, 2, "Safety", "地震不对友方单位造成伤害。")

	def get_description(self):
		return ("唤起 [{radius}_格:radius] 半径的地震。\n"
				"范围内的每个地块有 50% 几率受影响。\n"
				"受影响地块上的单位受到 [{damage}_点物理:physical] 伤害。\n"
				"受影响地块上的墙被摧毁。").format(**self.fmt_dict())

	def cast(self, x, y):
		points = list(self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, radius=self.get_stat('radius')))
		random.shuffle(points)
		for p in points:

			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit == self.caster:
				continue

			if self.get_stat('safety') and unit and not are_hostile(self.caster, unit):
				continue

			if random.random() < .5:
				continue

			self.caster.level.show_effect(p.x, p.y, Tags.Physical)

			if random.random() < .3:
				yield

			if unit:
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
				continue

			tile = self.caster.level.tiles[p.x][p.y]
			if not tile.can_walk:
				self.caster.level.make_floor(p.x, p.y)

class SearingSealBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Seal of Searing"
		self.charges = 0
		self.stack_type = STACK_REPLACE
		self.buff_type = BUFF_TYPE_BLESS
		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return "敌方单位受到 [fire] 伤害时获得等量的充能。\n当封印期满时，它每有 4 点充能便对视线内的所有敌人造成 [1_点火焰:fire] 伤害。\n\n当前充能：%d" % self.charges

	def on_damage(self, evt):
		if evt.damage_type != Tags.Fire:
			return

		self.charges += evt.damage

	def on_unapplied(self):
		self.owner.level.queue_spell(self.sear())

	def sear(self):
		enemies = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(self.owner, u)]
		damage = self.charges // 5
		for u in enemies:
			u.deal_damage(damage, Tags.Fire, self.spell)
			yield

class SearingSealSpell(Spell):

	def on_init(self):
		self.name = "Searing Seal"

		self.tags = [Tags.Fire, Tags.Enchantment]
		self.level = 4
		self.max_charges = 6
		self.range = 0
		self.duration = 6

		self.upgrades['max_charges'] = (6, 2)
		self.upgrades['duration'] = (6, 1)

	def get_description(self):
		return ("获得灼热封印。\n"
				"每当敌人受到 [fire] 伤害时，封印获得等量的充能。\n"
				"当封印期满时，它每有 4 点充能便对视线内的所有敌人造成 [1_点火焰:fire] 伤害。\n"
				"封印持续 [{duration}_回合:duration]。\n"
				"再次施放此咒语使当前封印期满，并生成一个新封印。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(SearingSealBuff(self), self.get_stat('duration'))

class PurityBuff(Buff):

	def on_init(self):
		self.name = "Purity"
		self.description = "免疫减益效果。"
		self.color = Tags.Holy.color
		self.asset = ['status', 'purity']

	def on_applied(self, owner):
		self.owner.debuff_immune = True

	def on_unapplied(self):
		self.owner.debuff_immune = False

class PuritySpell(Spell):

	def on_init(self):
		self.name = "Purity"

		self.duration = 6
		self.level = 4
		self.max_charges = 4

		self.upgrades['duration'] = (6, 3)
		self.upgrades['max_charges'] = (4, 3)
		self.range = 0

		self.tags = [Tags.Holy, Tags.Enchantment]

	def get_description(self):
		return ("失去所有减益效果。\n"
				"你无法获得减益效果。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		buffs = list(self.caster.buffs)
		for b in buffs:
			if b.buff_type == BUFF_TYPE_CURSE:
				self.caster.remove_buff(b)
		self.caster.apply_buff(PurityBuff(), self.get_stat('duration'))

class TwilightGazeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Twilight"
		self.buff_type = BUFF_TYPE_CURSE
		self.resists[Tags.Dark] = -self.spell.get_stat('resistance_debuff')
		self.resists[Tags.Holy] = -self.spell.get_stat('resistance_debuff')
		if self.spell.get_stat('arcane'):
			self.resists[Tags.Arcane] = -self.spell.get_stat('resistance_debuff')
		self.color = Tags.Dark.color
		self.stack_type = STACK_DURATION


class TwilightGazeSpell(Spell):

	def on_init(self):
		self.name = "Twilight Gaze"

		self.level = 6
		self.max_charges = 4

		self.resistance_debuff = 50
		self.duration = 10

		self.upgrades['resistance_debuff'] = (50, 3)
		self.upgrades['duration'] = (10, 2)
		self.upgrades['arcane'] = (1, 3, "Arcane Gaze", "暮光凝视还降低 [arcane] 抗性。")

		self.tags = [Tags.Holy, Tags.Dark, Tags.Enchantment]
		self.range = 0

	def get_description(self):
		return ("视线内的所有敌人失去 [{resistance_debuff}_点黑暗:dark] 抗性和 [{resistance_debuff}_点神圣:holy] 抗性。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast(self, x, y):
		units = [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster)]
		units.sort(key=lambda u: distance(self.caster, u))
		for u in units:
			u.apply_buff(TwilightGazeBuff(self), self.get_stat('duration'))
			yield

class SlimeformBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Slime Form"
		self.transform_asset_name = "slime_form"
		self.stack_type = STACK_TYPE_TRANSFORM
		self.resists[Tags.Poison] = 100
		self.resists[Tags.Physical] = 50

	def make_summon(self, base):
		unit = base()
		unit.max_hp = self.spell.get_stat('minion_health')
		unit.spells[0].damage = self.spell.get_stat('minion_damage')
		if not unit.spells[0].melee:
			unit.spells[0].range = self.spell.get_stat('minion_range')
		# Make sure bonuses propogate
		unit.buffs[0].spawner = lambda : self.make_summon(base)
		unit.source = self.spell
		return unit

	def on_advance(self):
		spawn_funcs = [GreenSlime]
		if self.spell.get_stat('fire_slimes'):
			spawn_funcs.append(RedSlime)
		if self.spell.get_stat('ice_slimes'):
			spawn_funcs.append(IceSlime)
		if self.spell.get_stat('void_slimes'):
			spawn_funcs.append(VoidSlime)

		spawn_func = random.choice(spawn_funcs)
		unit = self.make_summon(spawn_func)
		self.spell.summon(unit)

class SlimeformSpell(Spell):

	def on_init(self):
		self.name = "Slime Form"
		self.tags = [Tags.Arcane, Tags.Enchantment, Tags.Conjuration]
		self.level = 5
		self.max_charges = 2
		self.range = 0
		self.duration = 8

		self.upgrades['fire_slimes'] = (1, 1, "Fire Slime", "有相等几率召唤火焰史莱姆。")
		self.upgrades['ice_slimes'] = (1, 2, "Ice Slime", "有相等几率召唤寒冰史莱姆。")
		self.upgrades['void_slimes'] = (1, 3, "Void Slime", "有相等几率召唤虚空史莱姆。")
		self.upgrades['duration'] = (10, 4)

		ex = GreenSlime()

		self.minion_health = ex.max_hp
		self.minion_damage = ex.spells[0].damage
		self.minion_range = 3

	def get_description(self):
		return ("变为史莱姆形态 [{duration}_回合:duration]。\n"
				"史莱姆形态时获得 [50_点物理:physical] 抗性\n"
				"史莱姆形态时获得 [100_点毒性:poison] 抗性。\n"
				"史莱姆形态时每回合召唤一个友方的史莱姆。\n"
				"史莱姆有 [{minion_health}_点生命:minion_health]，每回合有 50% 几率获得 1 点生命上限，生命上限达到起始生命的两倍时分裂为两个史莱姆。\n"
				"史莱姆的近战攻击造成 [{minion_damage}_点毒性:poison] 伤害。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(SlimeformBuff(self), self.get_stat('duration'))

class Blazerip(Spell):

	def on_init(self):
		self.name = "Blazerip"
		self.tags = [Tags.Arcane, Tags.Fire, Tags.Sorcery]
		self.level = 2
		self.max_charges = 8
		self.damage = 12
		self.range = 6
		self.requires_los = False
		self.radius = 3

		self.upgrades['damage'] = (5, 2)
		self.upgrades['radius'] = (2, 2)

	def cast(self, x, y):
		points = self.get_impacted_tiles(x, y)
		for p in points:
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane, self)
			if self.owner.level.tiles[p.x][p.y].is_wall():
				self.owner.level.make_floor(p.x, p.y)
			yield

		for p in reversed(points):
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Fire, self)
			yield

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['width'] = 1 + 2*d['radius']
		return d

	def get_description(self):
		return ("对施法者为中心 [{width}_格:radius] 宽竖线内造成 [{damage}_点奥术:arcane] 和 [{damage}_点火焰:fire]。\n"
				"熔化受影响范围内的墙。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		points = self.caster.level.get_perpendicular_line(self.caster, Point(x, y), length=self.get_stat('radius'))
		return points

class IceVortex(Spell):

	def on_init(self):
		self.name = "Ice Vortex"
		self.damage = 11
		self.tags = [Tags.Ice, Tags.Arcane, Tags.Sorcery]
		self.level = 4
		self.max_charges = 6
		self.duration = 2
		self.range = 10
		self.requires_los = False

		self.radius = 5

		self.upgrades['damage'] = (11, 3)
		self.upgrades['duration'] = (2, 2)
		self.upgrades['radius'] = (3, 2)

	def can_cast(self, x, y):
		u = self.caster.level.get_unit_at(x, y)
		if not u:
			return False
		if not u.has_buff(FrozenBuff):
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return ("只能以被 [frozen] 的单位为目标。\n"
				"把 [{radius}_格:radius] 半径内的所有敌人拉向该单位，[frozen] [{duration}_回合:duration]，造成 [{damage}_点奥术:arcane] 和 [{damage}_点寒冰:ice] 伤害。").format(**self.fmt_dict())

	def modify_test_level(self, level):
		first_enemy = [u for u in level.units if u.team != TEAM_PLAYER][0]
		first_enemy.apply_buff(FrozenBuff(), 5)

	def cast(self, x, y):
		main_target = self.caster.level.get_unit_at(x, y)
		units = [u for u in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius')) if u != main_target]
		random.shuffle(units)
		units.sort(key=lambda u: distance(u, Point(x, y)))
		for u in units:

			if not are_hostile(u, self.caster):
				continue

			for p in self.caster.level.get_points_in_line(Point(x, y), u):
				dtype = random.choice([Tags.Ice, Tags.Arcane])
				self.caster.level.show_effect(p.x, p.y, dtype, minor=True)

			pull(u, Point(x, y), self.get_stat('radius'))
			yield
			u.apply_buff(FrozenBuff(), self.get_stat('duration'))
			yield
			u.deal_damage(self.get_stat('damage'), Tags.Arcane, self)
			yield
			u.deal_damage(self.get_stat('damage'), Tags.Ice, self)
			yield


class RestlessDeadBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.name = "Restless Dead"
		self.color = Tags.Dark.color

	def on_damaged(self, damage_event):
		if damage_event.unit.cur_hp > 0:
			return
		if not self.owner.level.are_hostile(self.owner, damage_event.unit):
			return

		if Tags.Living in damage_event.unit.tags:
			self.owner.level.queue_spell(self.raise_skeleton(damage_event.unit))
		elif Tags.Construct in damage_event.unit.tags and self.spell.get_stat('salvage'):
			self.owner.level.queue_spell(self.raise_golem(damage_event.unit))

		if (Tags.Fire in damage_event.unit.tags or Tags.Lightning in damage_event.unit.tags) and self.spell.get_stat('spirit_catcher'):
			self.owner.level.queue_spell(self.grant_sorcery(damage_event.unit))


	def raise_skeleton(self, unit):
		if unit and unit.cur_hp <= 0 and not self.owner.level.get_unit_at(unit.x, unit.y):
			skeleton = raise_skeleton(self.owner, unit, source=self.spell)
			if skeleton:
				skeleton.spells[0].damage += self.spell.get_stat('minion_damage') - 5
			yield

	def raise_golem(self, unit):
		if unit and unit.cur_hp <= 0 and not self.owner.level.get_unit_at(unit.x, unit.y):
			g = Golem()
			g.asset_name = 'golem_junk'
			g.name = "Junk Golem"
			g.spells = [SimpleMeleeAttack(self.spell.get_stat('minion_damage'))]
			g.tags.append(Tags.Undead)
			g.max_hp = unit.max_hp
			self.summon(g, target=unit)
		yield

	def grant_sorcery(self, unit):
		grantables = []
		if Tags.Fire in unit.tags:
			grantables.append(Tags.Fire)
		if Tags.Lightning in unit.tags:
			grantables.append(Tags.Lightning)
		if Tags.Ice in unit.tags:
			grantables.append(Tags.Ice)

		if not grantables:
			return

		candidates = [u for u in self.owner.level.units if not u.has_buff(TouchedBySorcery) and not are_hostile(u, self.owner) and u != self.owner]

		if not candidates:
			return

		candidate = random.choice(candidates)
		chosen_tag = random.choice(grantables)
		buff = TouchedBySorcery(chosen_tag)

		candidate.apply_buff(buff)
		self.owner.level.show_path_effect(unit, candidate, chosen_tag, minor=True)
		yield

	def get_description(self):
		return ("每当 [living] 敌人死亡时，将其复活为骷髅。")

class RestlessDead(Spell):

	def on_init(self):
		self.name = "The Restless Dead"
		self.level = 4
		self.tags = [Tags.Dark, Tags.Enchantment, Tags.Conjuration]
		self.duration = 15
		self.range = 0
		self.max_charges = 3
		self.minion_damage = 5

		self.upgrades['minion_damage'] = (4, 3)
		self.upgrades['duration'] = (15, 2)
		self.upgrades['max_charges'] = (2, 2)

		self.upgrades['salvage'] = (1, 3, "Junk Golems", "每当敌方的 [construct] 死亡时，将其复活为废料魔像。")
		self.upgrades['spirit_catcher'] = (1, 5, "Elemental Spirits", "每当敌方的 [fire]、[ice] 或 [lightning] 单位死亡时，随机一个召唤的友军获得 100 点该元素抗性，可进行该元素的远程攻击。每个友军只能获得一个此增益。")

	def get_description(self):
		return ("每当 [living] 敌人死亡时，将其复活为骷髅。\n"
				"骷髅的生命上限等于被击杀的单位，近战攻击造成 [{minion_damage}_点物理:physical] 伤害。\n"
				"飞行单位的骷髅可飞行。\n"
				"此效果持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(RestlessDeadBuff(self), self.get_stat('duration'))

class GustOfWind(Spell):

	def on_init(self):
		self.name = "Gust of Wind"
		self.level = 2
		self.tags = [Tags.Nature, Tags.Sorcery]
		self.range = 7
		self.max_charges = 10
		self.angle = math.pi / 6
		self.damage = 14
		self.force = 3
		self.stats.append('force')
		self.duration = 3

		self.upgrades['duration'] = (2, 2, "Stun Duration")
		self.upgrades['range'] = (4, 4)
		self.upgrades['damage'] = (10, 3)
		self.upgrades['force'] = (3, 3)

	def get_description(self):
		return ("将 [{force}:range] 格锥形范围的单位推走。\n"
				"若单位与墙、虚空或其他单位碰撞，该单位被 [stunned] [{duration}_回合:duration]，受到 [{damage}_点物理:physical] 伤害。\n"
				"固定不动的敌人不受影响。\n"
				"摧毁范围内的风暴云和蛛网。\n").format(**self.fmt_dict())


	def get_impacted_tiles(self, x, y):
		target = Point(x, y)
		burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
		return [p for stage in burst for p in stage if self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y)]

	def blow(self, unit, start_loc):
		for p in self.caster.level.get_points_in_line(start_loc, unit, find_clear=True):
			self.caster.level.leap_effect(p.x, p.y, Tags.Nature.color, unit)
			yield

	def cast_instant(self, x, y):
		to_push = []
		for p in self.get_impacted_tiles(x, y):

			cloud = self.caster.level.tiles[p.x][p.y].cloud
			if cloud:
				cloud.kill()

			unit = self.caster.level.get_unit_at(p.x, p.y)
			if not unit:
				continue
			if unit == self.caster:
				continue
			if unit.stationary:
				continue

			to_push.append(unit)

		to_push.sort(key=lambda u: -distance(u, self.caster))
		for unit in to_push:
			start_loc = Point(unit.x, unit.y)
			self.owner.level.queue_spell(self.blow(unit, start_loc))
			result = push(unit, self.caster, self.get_stat('force'))
			if not result:
				unit.apply_buff(Stun(), self.get_stat('duration'))
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)


class PyroStaticHexBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Pyrostatic Hex"
		self.beam = False
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Fire.color
		self.owner_triggers[EventOnDamaged] = self.on_damage
		self.asset = ['status', 'pyrostatic_hex']


	def on_damage(self, evt):
		if evt.damage_type != Tags.Fire:
			return

		self.owner.level.queue_spell(self.deal_damage(evt))

	def deal_damage(self, evt):

		redeal_targets = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(u, self.spell.owner) and u != self.owner]
		random.shuffle(redeal_targets)

		for t in redeal_targets[:2]:
			if not self.beam:
				for p in self.owner.level.get_points_in_line(self.owner, t)[1:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Lightning)
				t.deal_damage(evt.damage // 2, Tags.Lightning, self.spell)
			else:
				for p in self.owner.level.get_points_in_line(self.owner, t)[1:]:
					self.owner.level.deal_damage(evt.damage // 2, Tags.Lightning, self.spell)
		yield

class PyrostaticHexSpell(Spell):

	def on_init(self):
		self.name = "Pyrostatic Curse"

		self.tags = [Tags.Fire, Tags.Lightning, Tags.Enchantment]
		self.level = 5
		self.max_charges = 7

		self.radius = 4
		self.range = 9
		self.duration = 4

		self.upgrades['radius'] = (3, 2)
		self.upgrades['duration'] = (6, 3)
		self.upgrades['beam'] = (1, 5, "Linear Conductance", "在一束内造成 [lightning] 伤害，而非只伤害一个目标。")

	def get_description(self):
		return ("诅咒 [{radius}_格:radius] 半径内的所有目标 [{duration}_回合:duration]。\n"
				"每当受诅咒的目标受到 [fire] 伤害时，该单位视线内随机两个敌方单位受到一半的 [lightning] 伤害。\n").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for p in self.owner.level.get_points_in_ball(x, y, self.get_stat('radius')):
			u = self.owner.level.get_unit_at(p.x, p.y)
			if u and are_hostile(u, self.caster):
				u.apply_buff(PyroStaticHexBuff(self), self.get_stat('duration'))

class SpikeballFactory(Spell):

	def on_init(self):
		self.name = "Spikeball Factory"
		self.tags = [Tags.Metallic, Tags.Conjuration]

		self.level = 7

		self.max_charges = 1

		self.minion_health = 40
		self.range = 0

		#upgrades
		# 2 layers of factories
		# 1 more charge
		# minion hp
		# copper spikeballs
		self.upgrades['manufactory'] = (1, 6, "Manufactory", "再召唤一圈大门包围最初召唤的大门。")
		self.upgrades['copper'] = (1, 7, "Copper Spikeballs", "改为召唤铜制钉球，而非普通钉球。")
		self.upgrades['minion_health'] = (20, 3)
		self.upgrades['max_charges'] = (1, 3)

	def get_description(self):
		return "召唤钉球大门包围施法者。大门会生成钉球。"


	def spikeball(self):
		if self.get_stat('copper'):
			spikeball = SpikeBallCopper()
		else:
			spikeball = SpikeBall()
		return spikeball

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):

			gate = MonsterSpawner(self.spikeball)
			apply_minion_bonuses(self, gate)
			self.summon(gate, p)
			yield

	def get_impacted_tiles(self, x, y):
		points = set()
		for p in self.owner.level.get_adjacent_points(self.caster, filter_walkable=True, check_unit=True):
			points.add(p)
			yield p
		if self.get_stat('manufactory'):
			for p in points:
				for q in self.owner.level.get_adjacent_points(p, filter_walkable=True, check_unit=True):
					yield q

class MercurizeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		if self.spell.get_stat('corrosion'):
			self.resists[Tags.Physical] = -25

	def on_init(self):
		self.buff_type = BUFF_TYPE_CURSE
		self.name = "Mercurized"
		self.asset = ['status', 'mercurized']
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_advance(self):
		dtypes = [Tags.Physical, Tags.Poison]

		if self.spell.get_stat('dark'):
			dtypes.append(Tags.Dark)

		for dtype in dtypes:
			self.owner.deal_damage(self.spell.get_stat('damage'), dtype, self.spell)
			if not self.owner.is_alive():
				break

	def on_death(self, evt):
		geist = Ghost()
		geist.name = "Mercurial %s" % self.owner.name
		geist.asset_name = "mercurial_geist"
		geist.max_hp = self.owner.max_hp
		geist.tags.append(Tags.Metallic)
		trample = SimpleMeleeAttack(damage=self.spell.get_stat('minion_damage'))
		geist.spells = [trample]
		self.spell.summon(geist, target=self.owner)

		if self.spell.get_stat('noxious_aura'):
			geist.apply_buff(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=2))

		if self.spell.get_stat('vengeance'):
			geist.apply_buff(MercurialVengeance(self.spell))


class MercurialVengeance(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Mercurial Vengeance"
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		# cast a Mercurize with the summoner's buffs
		if evt.damage_event:
			spell = MercurizeSpell()
			spell.owner = self.owner
			spell.caster = self.owner
			spell.statholder = self.spell.statholder or self.spell.caster
			self.owner.level.act_cast(self.owner, spell, evt.damage_event.source.owner.x, evt.damage_event.source.owner.y, pay_costs=False)

class MercurizeSpell(Spell):

	def on_init(self):
		self.name = "Mercurize"

		self.level = 3
		self.tags = [Tags.Dark, Tags.Metallic, Tags.Enchantment, Tags.Conjuration]

		self.damage = 2

		self.max_charges = 6
		self.duration = 6

		self.range = 8

		self.minion_damage = 10

		self.upgrades['damage'] = (4, 4)
		self.upgrades['duration'] = (10, 3)
		self.upgrades['dark'] = (1, 2, "Morbidity", "汞化术还造成一次 [dark] 伤害。")
		self.upgrades['corrosion'] = (1, 2, "Corrosion", "汞化术的目标失去 25 点 [physical] 抗性。")
		self.upgrades['noxious_aura'] = (1, 5, "Toxic Fumes", "水银游魂的毒息光环每回合对 [2_格:radius] 内的敌方单位造成 1 点 [poison] 伤害。")
		self.upgrades['vengeance'] = (1, 5, "Mercurial Vengeance", "当水银游魂被消灭时，对消灭者施加汞化术。")

	def get_description(self):
		return("汞化目标。目标每回合受到 [{damage}_点毒性:poison] 和 [{damage}_点物理:physical] 伤害，持续 [{duration}_回合:duration]。\n"
			   "若目标被诅咒时死亡，将其复活为水银游魂。\n"
			   "水银游魂是可飞行的 [undead] [metallic] 单位，有诸多抗性和免疫。\n"
			   "水银游魂的生命上限等于被诅咒的单位，践踏攻击造成 [{minion_damage}_点物理:physical] 伤害。\n".format(**self.fmt_dict()))

	def can_cast(self, x, y):
		return self.caster.level.get_unit_at(x, y) is not None and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		for p in self.owner.level.get_points_in_line(self.caster, Point(x, y))[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(MercurizeBuff(self), self.get_stat('duration'))

class MagnetizeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Magnetized"
		self.asset = ['status', 'magnetized']

	def on_applied(self, owner):
		self.buff_type = BUFF_TYPE_CURSE if are_hostile(self.owner, self.spell.owner) else BUFF_TYPE_BLESS

	def on_advance(self):
		# pull stuff towards self
		units = [u for u in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius')) if u != self.owner]
		random.shuffle(units)
		units.sort(key=lambda u: distance(u, self.owner))
		for u in units:
			# Only hit targets hostile to the caster
			if not are_hostile(u, self.spell.owner):
				continue
			for p in self.owner.level.get_points_in_line(self.owner, u):
				self.owner.level.show_effect(p.x, p.y, Tags.Lightning, minor=True)

			pull(u, self.owner, self.spell.get_stat('pull_strength'))

			if distance(self.owner, u) < 2:
				u.apply_buff(Stun(), 1)


class MagnetizeSpell(Spell):

	def on_init(self):
		self.name = "Magnetize"
		self.tags = [Tags.Lightning, Tags.Metallic, Tags.Enchantment]

		self.level = 2
		self.max_charges = 10

		self.radius = 4
		self.pull_strength = 1

		self.range = 9
		self.requires_los = False

		self.duration = 5

		self.upgrades['radius'] = (2, 3)
		self.upgrades['pull_strength'] = (1, 3, "Pull Distance")
		self.upgrades['duration'] = (10, 3)
		self.upgrades['universal'] = (1, 4, "Universal Magnetism", "磁化术可以非 [metallic] 单位为目标。")


	def can_cast(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)

		if not unit:
			return False

		if not ((Tags.Metallic in unit.tags) or (self.get_stat('universal'))):
			return False

		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		unit = self.owner.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(MagnetizeBuff(self), self.get_stat('duration'))

	def get_description(self):
		return ("磁化术以 [metallic] 单位为目标。\n"
				"每回合将被磁化的单位 [{radius}_格:radius] 半径内的所有敌人向该单位拉动 [{pull_strength}_格:range]。\n"
				"然后相邻的敌方单位被 [stunned] 1 回合。\n"
				"持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

class SilverSpearSpell(Spell):

	def on_init(self):
		self.name = "Silver Spear"
		self.level = 3
		self.max_charges = 25
		self.tags = [Tags.Holy, Tags.Metallic, Tags.Sorcery]

		self.damage = 27

		self.range = 11
		self.radius = 1

		self.upgrades['radius'] = (1, 4)
		self.upgrades['damage'] = (15, 3)
		self.upgrades['max_charges'] = (12, 3)

	def get_description(self):
		return ("对目标造成 [{damage}_点物理:physical] 伤害。\n"
				"在弹道 [{radius}_格:radius] 内的 [dark] 和 [arcane] 单位造成 [{damage}_点神圣:holy] 伤害。".format(**self.fmt_dict()))

	def get_impacted_tiles(self, x, y):
		points = set()
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, self.get_stat('radius')):
				if q not in points:
					yield q
					points.add(q)

	def cast(self, x, y):
		hits = set()
		# todo- holy sparkles randomly around projectile?
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]:
			self.caster.level.projectile_effect(p.x, p.y, proj_name='silver_spear', proj_origin=self.caster, proj_dest=Point(x, y))
			units = self.owner.level.get_units_in_ball(p, self.get_stat('radius'))
			for unit in units:
				if unit in hits:
					continue
				hits.add(unit)
				if Tags.Arcane in unit.tags or Tags.Dark in unit.tags:
					unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)
			yield

		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)

def InfernoCannon():
	unit = Unit()
	unit.tags = [Tags.Construct, Tags.Metallic, Tags.Fire]
	unit.max_hp = 24
	unit.name = "Inferno Cannon"
	unit.asset_name = "goblin_cannon"
	unit.stationary = True

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = -100

	cannonball = SimpleRangedAttack(damage=11, range=12, radius=2, damage_type=[Tags.Physical, Tags.Fire])
	cannonball.name = "Cannon Blast"
	unit.spells = [cannonball]

	unit.buffs.append(DeathExplosion(damage=11, damage_type=Tags.Fire, radius=1))
	return unit

def SiegeGolem():
	unit = SiegeOperator(InfernoCannon)
	unit.name = "Golem Siege Mechanic"
	unit.asset_name = "golem"

	unit.max_hp = 25
	unit.tags = [Tags.Metallic, Tags.Construct]
	return unit

class SummonSiegeGolemsSpell(Spell):

	def on_init(self):
		self.name = "Siege Golems"
		self.tags = [Tags.Fire, Tags.Conjuration, Tags.Metallic]
		self.level = 4
		self.max_charges = 3
		self.range = 5

		self.minion_damage = 30
		self.minion_range = 15
		self.radius = 3

		self.minion_health = InfernoCannon().max_hp
		self.num_summons = 3

		self.upgrades['radius'] = (2, 4)
		self.upgrades['num_summons'] = (3, 3)
		self.upgrades['minion_range'] = (7, 2)

		#Upgrade- fires cluster firebombs instead of just explosions?

	def get_description(self):
		return ("召唤 [{num_summons}:num_summons] 个攻城魔像。\n"
				"攻城魔像会组装地狱火炮，若 [3_格:range] 内有则会操作之。\n"
				"地狱火炮在 [{radius}_格:radius] 半径内造成 [{minion_damage}_点火焰:fire] 伤害。\n"
				"地狱火炮被摧毁时会爆炸，在 [1_格:radius] 半径的单位造成 [{minion_damage}_点火焰:fire]。".format(**self.fmt_dict()))

	def cannon(self):
		unit = Unit()
		unit.tags = [Tags.Construct, Tags.Metallic, Tags.Fire]
		unit.max_hp = 24
		unit.name = "Inferno Cannon"
		unit.stationary = True

		unit.resists[Tags.Physical] = 50
		unit.resists[Tags.Fire] = -100

		cannonball = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), radius=self.get_stat('radius'), damage_type=Tags.Fire)
		cannonball.name = "Fire Blast"
		unit.spells = [cannonball]

		unit.buffs.append(DeathExplosion(damage=self.get_stat('minion_damage'), damage_type=Tags.Fire, radius=1))

		unit.max_hp = 18
		return unit

	def golem(self):
		golem = SiegeOperator(self.cannon)
		golem.spells[2].range = 3
		golem.spells[1].heal = 2
		golem.name = "Golem Siege Mechanic"
		golem.asset_name = "golem_siege"
		golem.max_hp = 25
		golem.tags = [Tags.Metallic, Tags.Construct]
		apply_minion_bonuses(self, golem)

		return golem

	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			golem = self.golem()
			self.summon(golem, target=Point(x, y))
			yield

# Lightning Spire
# Each turn fires lightning bolts a random X units in the aoe

class LightningSpireArc(Spell):

	def on_init(self):
		self.name = "Zap"

		self.damage = 5
		self.num_targets = 2
		self.range = 0
		self.radius = 4
		self.requires_los = True

	def get_ai_target(self):
		if self.get_targets():
			return self.owner
		else:
			return None

	def can_target(self, t):
		if t.resists[Tags.Lightning] >= 100:
			return False
		if not are_hostile(self.owner, t):
			return False
		if not self.owner.level.can_see(self.owner.x, self.owner.y, t.x, t.y):
			return self.get_stat('requires_los')
		return True

	def get_targets(self):
		potential_targets = self.owner.level.get_units_in_ball(self.owner, self.get_stat('radius'))
		potential_targets = [t for t in potential_targets if self.can_target(t)]
		random.shuffle(potential_targets)
		return potential_targets[:self.get_stat('num_targets')]

	def can_cast(self, x, y):
		return self.get_targets()

	def cast(self, x, y):
		targets = self.get_targets()
		for t in targets:
			for p in self.owner.level.get_points_in_line(self.owner, t)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Lightning, minor=True)
			self.owner.level.deal_damage(t.x, t.y, self.get_stat('damage'), Tags.Lightning, self)
			if self.get_stat('resistance_debuff'):
				t.apply_buff(Electrified())
			yield

class LightningSpire(Spell):

	def on_init(self):

		self.name = "Lightning Spire"
		self.minion_health = 25
		self.minion_damage = 6
		self.radius = 4
		self.max_charges = 5
		self.level = 3
		self.range = 6

		self.num_targets = 4

		self.tags = [Tags.Lightning, Tags.Metallic, Tags.Conjuration]

		self.upgrades['max_charges'] = (4, 3)
		self.upgrades['minion_damage'] = (4, 3)
		self.upgrades['num_targets'] = (3, 2)
		self.upgrades['radius'] = (2, 4)
		self.upgrades['blindcasting'] = (1, 5, "Wall Penetration", "尖塔可穿墙劈中敌人。")
		self.upgrades['resistance_debuff'] = (1, 5, "Resistance Penetration", "被劈中的单位永久失去 10 点 [lightning] 抗性。")


		self.must_target_empty = True

	def get_description(self):
		return ("召唤一个闪电尖塔。\n"
				"闪电尖塔是固定不动的 [metallic] [construct]，有 [{minion_health}:minion_health] 点生命上限。\n"
				"每回合尖塔劈中 [{radius}:minion_range] 各内至多 [{num_targets}:num_targets] 个敌方单位，造成 [{minion_damage}_点闪电:lightning] 伤害。").format(**self.fmt_dict())


	def get_impacted_tiles(self, x, y):
		for p in self.owner.level.get_points_in_ball(x, y, self.get_stat('radius')):
			if self.get_stat('blindcasting'):
				yield p
			elif self.owner.level.can_see(x, y, p.x, p.y):
				yield p

	def cast_instant(self, x, y):
		unit = Unit()
		unit.name = "Lightning Spire"

		unit.max_hp = self.get_stat('minion_health')
		unit.tags = [Tags.Metallic, Tags.Construct, Tags.Lightning]

		arc = LightningSpireArc()
		arc.damage = self.get_stat('minion_damage')
		arc.num_targets = self.get_stat('num_targets')
		arc.radius = self.get_stat('radius')
		arc.requires_los = self.get_stat('blindcasting')
		arc.resistance_debuff = self.get_stat('resistance_debuff')
		
		unit.spells = [arc]

		unit.stationary = True

		self.summon(unit, target=Point(x, y))

class EssenceFlux(Spell):

	def on_init(self):
		self.name = "Essence Flux"
		self.tags = [Tags.Arcane, Tags.Chaos, Tags.Enchantment]

		self.max_charges = 12
		self.level = 4
		self.range = 7

		self.upgrades['max_charges'] = (6, 2)

	def get_description(self):
		return ("交换一群单位的抗性类型。\n"
				"[Fire] 与 [ice] 交换。\n"
				"[Lightning] 与 [physical] 交换。\n"
				"[Dark] 与 [holy] 交换。\n"
				"[Poison] 与 [arcane] 交换。\n")

	def get_impacted_tiles(self, x, y):

		candidates = set([Point(x, y)])
		unit_group = set()

		while candidates:
			candidate = candidates.pop()
			unit = self.caster.level.get_unit_at(candidate.x, candidate.y)
			if unit and unit not in unit_group:

				# Probably best to not mess with the casters resists...
				if unit == self.caster:
					continue

				unit_group.add(unit)

				for p in self.caster.level.get_adjacent_points(Point(unit.x, unit.y), filter_walkable=False):
					candidates.add(p)

		return list(unit_group)

	def cast(self, x, y):
		points = self.get_impacted_tiles(x, y)
		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				old_resists = unit.resists.copy()
				for e1, e2 in [
					(Tags.Fire, Tags.Ice),
					(Tags.Lightning, Tags.Physical),
					(Tags.Dark, Tags.Holy),
					(Tags.Poison, Tags.Arcane)]:

					if old_resists[e1] == 0 and old_resists[e2] == 0:
						continue

					if old_resists[e1] == old_resists[e2]:
						continue

					unit.resists[e1] = old_resists[e2]
					unit.resists[e2] = old_resists[e1]

					color = e1.color if old_resists[e1] > old_resists[e2] else e2.color

					etype = random.choice([e1, e2])
					self.caster.level.show_effect(unit.x, unit.y, Tags.Debuff_Apply, fill_color=color)
					yield


all_player_spell_constructors = [
	#FlameTongue,
	#SparkSpell,
	FireballSpell, 
	LightningBoltSpell,
	AnnihilateSpell,
	LightningFormSpell,
	MegaAnnihilateSpell,
	Teleport,
	BlinkSpell,
	VoidBeamSpell,
	ThunderStrike,
	#GiantStrengthSpell,
	ChaosBarrage,
	DispersalSpell,
	PetrifySpell,
	SummonWolfSpell,
	#SummonDireWolfSpell,
	SummonGiantBear,
	FeedingFrenzySpell,
	StormSpell,
	ThornyPrisonSpell,
	FlameStrikeSpell,
	BloodlustSpell,
	HealMinionsSpell,
	RegenAuraSpell,
	VoidOrbSpell,
	Dominate,
	FlameGateSpell,
	EyeOfFireSpell,
	EyeOfLightningSpell,
	EyeOfIceSpell,
	NightmareSpell,
	CockatriceSkinSpell,
	WatcherFormSpell,
	ImpGateSpell,
	LightningHaloSpell,
	ArcaneVisionSpell,
	ArcaneDamageSpell,
	FlameBurstSpell,
	SummonFireDrakeSpell,
	SummonStormDrakeSpell,
	SummonVoidDrakeSpell,
	SummonIceDrakeSpell,
	ChainLightningSpell,
	DeathBolt,
	TouchOfDeath,
	SealFate,
	WheelOfFate,
	Volcano,
	UnderworldPortal,
	SummonEarthElemental,
	CallSpirits,
	MysticMemory,
	ConjureMemories,
	Permenance,
	DeathGazeSpell,
	MagicMissile,
	MindDevour,
	DeathShock,
	MeltSpell,
	DragonRoarSpell,
	ProtectMinions,
	WordOfChaos,
	WordOfUndeath,
	WordOfBeauty,
	SummonFloatingEye,
	EyeOfRageSpell,
	ChimeraFarmiliar,
	ArcLightning,
	Flameblast,
	PoisonSting,
	SummonBlueLion,
	DeathCleaveSpell,
	MulticastSpell,
	FaeCourt,
	RingOfSpiders,
	WordOfMadness,
	HolyBlast,
	HolyFlame,
	AngelicChorus,
	HeavensWrath,
	BestowImmortality,
	SoulTax,
	HolyShieldSpell,
	BlindingLightSpell,
	FlockOfEaglesSpell,
	#FlamingSwordSpell,
	HeavenlyIdol,
	SummonGoldDrakeSpell,
	SummonSeraphim,
	SummonArchon,
	PainMirrorSpell,
	PyrostaticPulse,
	#ThunderStones,
	#FireStones,  
	VoidRip,
	ShieldSiphon,
	VoidMaw,
	Darkness,
	HallowFlesh,
	CantripCascade,
	ConductanceSpell,
	InvokeSavagerySpell,
	MeteorShower,
	ShrapnelBlast,
	PlagueOfFilth,
	SearingOrb,
	BallLightning,
	OrbControlSpell,
	GlassOrbSpell,
	SummonFieryTormentor,
	StoneAuraSpell,
	DispersionFieldSpell,
	SummonKnights,
	ToxinBurst,
	ToxicSpore,
	#AmplifyPoisonSpell,
	IgnitePoison,
	#VenomBeast,
	SummonSpiderQueen,
	Freeze,
	Iceball,
	BlizzardSpell,
	SummonFrostfireHydra,
	StormNova,
	DeathChill,
	SummonIcePhoenix,
	WordOfIce,
	FrozenOrbSpell,
	#IceWeave,
	#ShatterShards,
	Icicle,
	IceWind,
	IceWall,
	BoneBarrageSpell,
	EarthquakeSpell,
	SearingSealSpell,
	SoulSwap,
	PuritySpell,
	TwilightGazeSpell,
	SlimeformSpell,
	Blazerip,
	IceVortex,
	RestlessDead,
	#GustOfWind,
	PyrostaticHexSpell,
	SpikeballFactory,
	MercurizeSpell,
	MagnetizeSpell,
	SilverSpearSpell,
	SummonSiegeGolemsSpell,
	LightningSpire,
	EssenceFlux
]

def make_player_spells():
	all_player_spells = []

	for c in all_player_spell_constructors:
		s = c()
	#	if Tags.Chaos not in s.tags and Tags.Holy not in s.tags and Tags.Word not in s.tags:
		all_player_spells.append(s)

	unit = Unit()
	for spell in all_player_spells:
		unit.add_spell(spell)

	# Insist that all spells are spells (to catch mod bugs mostly)
	for spell in all_player_spells:
		if not isinstance(spell, Spell):
			print(spell.name)
			assert(isinstance(spell, Spell))

	# Insist that no spells have none descs, a common bug
	for spell in all_player_spells:
		if not spell.get_description():
			print(spell.name)
			assert(spell.get_description())

	# Insist that no spells have no tags
	for spell in all_player_spells:
		if not spell.level or not len(spell.tags):
			print(spell.name)
			assert(spell.level)
			assert(len(spell.tags))

	# Insist that the spell has consistant desc
	for spell in all_player_spells:
		if spell.description:
			print(spell.name)
			assert(spell.description == spell.get_description())

	# sort by total req levels
	all_player_spells.sort(key=lambda s: (s.level, s.name))

	return all_player_spells

make_player_spells()
