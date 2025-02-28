from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
from actions.query_analyse import QueryExpansion
from actions.query_decompose import QueryDecompose


class QueryAnalyst(Role):
    """ Assistant to analyse the query. """
    name: str = "TeleAnalyst"
    profile: str = "Query Analyst"
    goal: str = "to deeply understand and carefully analyze user queries, and associate them with the information provided in the table"

    def __init__(self, llm_config, prompt_template, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([QueryExpansion(config=llm_config, PROMPT_TEMPLATE=prompt_template)])
        # self.set_actions([MockAnalyse])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # By choosing the Action by order under the hood
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)  
        return msg


class QueryDecomposer(Role):
    """ Decoupling queries into multiple sub problems. """
    name: str = "TeleDec"
    profile: str = "Query Decomposer"
    goal: str = "to break down the user's query into multiple progressively concrete sub-queries based on a thorough analysis of user' query and a deep understanding of the context"

    def __init__(self, llm_config, prompt_template, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([QueryDecompose(config=llm_config, PROMPT_TEMPLATE=prompt_template)])
        # self.set_actions([MockAnalyse])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # By choosing the Action by order under the hood
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)  
        return msg

