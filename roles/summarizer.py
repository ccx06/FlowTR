from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
from actions.llm_actions import LLMGenerate
from actions.summarize import ThoughtSummary


class Summarizer(Role):
    """ Summarize thought processes and output the final answer. """
    name: str = "TeleSum"
    profile: str = "Answer Summarizer"
    goal: str = "to summarize and generate the final answer to the user query, which is faithful to the context and follows the formatting requirements"

    def __init__(self, llm_config, prompt_template, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ThoughtSummary(config=llm_config, PROMPT_TEMPLATE=prompt_template)])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)
        return msg