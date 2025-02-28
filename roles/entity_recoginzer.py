from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
from actions.entity_associate import EntityLinking, RetrieveJudge


class EntityRecognizer(Role):
    """ Map or associate entities mentioned in user queries to a cell content in a table. """
    name: str = 'TeleLinker'
    profile: str = "Entity Recognizer"
    goal: str = "to identify and associate the entities in user query with category values in table columns."

    def __init__(self, llm_config, prompt_template_list, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([RetrieveJudge(config=llm_config, PROMPT_TEMPLATE=prompt_template_list[0]),
        EntityLinking(config=llm_config, PROMPT_TEMPLATE=prompt_template_list[1])])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)
        return msg
