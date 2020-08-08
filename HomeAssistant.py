from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler


class HomeAssistant(AliceSkill):
	"""
	Author: LazzaAU
	Description: Connect alice to your home assistant
	"""

	@IntentHandler('MyIntentName')
	def dummyIntent(self, session: DialogSession, **_kwargs):
		pass
